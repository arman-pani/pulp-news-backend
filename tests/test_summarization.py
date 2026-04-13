import json
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services import summarization
from app.services.summarization import (
    _SYSTEM_PROMPTS,
    _build_fallback_articles,
    _extract_json_payload,
    _extract_response_text,
    summarize_articles_batch,
)


# ---------------------------------------------------------------------------
# JSON helpers (unchanged)
# ---------------------------------------------------------------------------

def test_extract_json_payload_from_fenced_response():
    payload = _extract_json_payload(
        """```json
        {"articles": [{"source_url": "https://example.com/a"}]}
        ```"""
    )
    parsed = json.loads(payload)
    assert parsed["articles"][0]["source_url"] == "https://example.com/a"


def test_extract_json_payload_from_wrapped_response():
    payload = _extract_json_payload(
        'Here is the result: {"articles": [{"source_url": "https://example.com/a"}]} Thanks.'
    )
    parsed = json.loads(payload)
    assert parsed["articles"][0]["source_url"] == "https://example.com/a"


def test_extract_json_payload_handles_empty_response():
    assert _extract_json_payload("") == ""


def test_extract_response_text_uses_tool_call_arguments():
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    refusal=None,
                    function_call=None,
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                arguments='{"articles": [{"source_url": "https://example.com/a"}]}'
                            )
                        )
                    ],
                )
            )
        ]
    )
    assert "https://example.com/a" in _extract_response_text(response)


# ---------------------------------------------------------------------------
# Language-aware system prompts
# ---------------------------------------------------------------------------

def test_system_prompts_defined_for_all_languages():
    assert "english" in _SYSTEM_PROMPTS
    assert "odia" in _SYSTEM_PROMPTS
    assert "bengali" in _SYSTEM_PROMPTS


def test_odia_prompt_mentions_odia_script():
    assert "ଓଡ଼ିଆ" in _SYSTEM_PROMPTS["odia"]


def test_bengali_prompt_mentions_bengali_script():
    assert "বাংলা" in _SYSTEM_PROMPTS["bengali"]


def test_english_prompt_does_not_contain_native_scripts():
    prompt = _SYSTEM_PROMPTS["english"]
    assert "ଓଡ଼ିଆ" not in prompt
    assert "বাংলা" not in prompt


# ---------------------------------------------------------------------------
# _build_fallback_articles — language propagation
# ---------------------------------------------------------------------------

def _make_raw(url="https://example.com/a", source="Sambad"):
    return {
        "source_name": source,
        "url": url,
        "original_title": "Original title",
        "original_content": "Original content body",
        "publish_date": datetime.now(timezone.utc),
        "authors": ["Reporter"],
    }


def test_build_fallback_articles_preserves_original_content():
    articles = _build_fallback_articles([_make_raw()])
    assert articles[0].source_url == "https://example.com/a"
    assert articles[0].title == "Original title"
    assert articles[0].content == "Original content body"


def test_build_fallback_articles_stamps_english_language_by_default():
    articles = _build_fallback_articles([_make_raw()])
    assert articles[0].language == "english"


def test_build_fallback_articles_stamps_given_language():
    articles = _build_fallback_articles([_make_raw()], language="odia")
    assert articles[0].language == "odia"

    articles = _build_fallback_articles([_make_raw()], language="bengali")
    assert articles[0].language == "bengali"


# ---------------------------------------------------------------------------
# summarize_articles_batch — language param flows through to Article objects
# ---------------------------------------------------------------------------

def _fake_client(monkeypatch, summary_json: str):
    """Patch OpenAI to return a fixed JSON string."""
    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=summary_json,
                            refusal=None,
                            function_call=None,
                            tool_calls=None,
                        )
                    )
                ]
            )

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(summarization.settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(summarization, "OpenAI", FakeClient)


def test_summarize_articles_batch_stamps_english_language(monkeypatch):
    url = "https://example.com/a"
    response = json.dumps({
        "articles": [{"source_url": url, "title": "English T", "content": "English C", "category": "General"}]
    })
    _fake_client(monkeypatch, response)

    result = summarize_articles_batch([_make_raw(url)], language="english")
    assert result[0].language == "english"


def test_summarize_articles_batch_stamps_odia_language(monkeypatch):
    url = "https://example.com/od"
    response = json.dumps({
        "articles": [{"source_url": url, "title": "ଓଡ଼ିଆ ଶୀର୍ଷ", "content": "ଓଡ଼ିଆ ବିବରଣ", "category": "General"}]
    })
    _fake_client(monkeypatch, response)

    result = summarize_articles_batch([_make_raw(url, "Sambad")], language="odia")
    assert result[0].language == "odia"
    assert "ଓଡ଼ିଆ" in result[0].title


def test_summarize_articles_batch_stamps_bengali_language(monkeypatch):
    url = "https://example.com/bn"
    response = json.dumps({
        "articles": [{"source_url": url, "title": "বাংলা শিরোনাম", "content": "বাংলা বিবরণ", "category": "General"}]
    })
    _fake_client(monkeypatch, response)

    result = summarize_articles_batch([_make_raw(url, "ABP Ananda")], language="bengali")
    assert result[0].language == "bengali"


def test_summarize_articles_batch_fallback_stamps_language_on_api_failure(monkeypatch):
    """When the API raises, fallback articles still carry the correct language."""
    class FailingCompletions:
        def create(self, **kwargs):
            raise RuntimeError("unreachable")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(completions=FailingCompletions())

    monkeypatch.setattr(summarization.settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(summarization, "OpenAI", FakeClient)

    result = summarize_articles_batch([_make_raw()], language="odia")
    assert result[0].language == "odia"


def test_summarize_articles_batch_falls_back_when_model_returns_empty(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="",
                            refusal=None,
                            function_call=None,
                            tool_calls=None,
                        )
                    )
                ]
            )

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(summarization.settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(summarization, "OpenAI", FakeClient)

    result = summarize_articles_batch([_make_raw()], language="english")
    assert result[0].title == "Original title"
    assert result[0].content == "Original content body"
    assert result[0].language == "english"
