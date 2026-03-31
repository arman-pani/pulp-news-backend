import json
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services import summarization
from app.services.summarization import (
    _build_fallback_articles,
    _extract_json_payload,
    _extract_response_text,
    summarize_articles_batch,
)


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


def test_build_fallback_articles_preserves_original_content():
    articles = _build_fallback_articles(
        [
            {
                "source_name": "OdishaTV",
                "url": "https://example.com/a",
                "original_title": "Original title",
                "original_content": "Original content body",
                "publish_date": datetime.now(timezone.utc),
                "authors": ["Reporter"],
            }
        ]
    )
    assert articles[0].source_url == "https://example.com/a"
    assert articles[0].title == "Original title"
    assert articles[0].content == "Original content body"


def test_summarize_articles_batch_falls_back_when_model_returns_empty(monkeypatch):
    monkeypatch.setattr(summarization.settings, "openrouter_api_key", "test-key")
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
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

    monkeypatch.setattr(summarization, "OpenAI", FakeClient)

    result = summarize_articles_batch(
        [
            {
                "source_name": "OdishaTV",
                "url": "https://example.com/a",
                "original_title": "Original title",
                "original_content": "Original content body",
                "publish_date": datetime.now(timezone.utc),
                "authors": ["Reporter"],
            }
        ]
    )

    assert len(calls) == 2
    assert calls[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in calls[1]
    assert result[0].title == "Original title"
    assert result[0].content == "Original content body"
