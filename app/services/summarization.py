from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from sarvamai import SarvamAI

from openai import OpenAI

from app.core.config import (
    OPENROUTER_MODEL,
    SARVAM_AI_BASE_URL,
    SARVAM_AI_MODEL,
    SUMMARIZATION_TIMEOUT_SECONDS,
    get_settings,
)
from app.models import Article

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Language-specific system prompts
# ---------------------------------------------------------------------------

_CATEGORIES_PLACEHOLDER = "{categories}"

_SYSTEM_PROMPTS: dict[str, str] = {
    "english": """
You are a professional news writer. For each article:
1. Create a concise title with a maximum of 8 words.
2. Write a short factual summary with at least 50 words in English.
3. Categorize the article using exactly one of: {categories}.
4. Preserve factual accuracy.

Return a JSON object with an "articles" key that contains an array of objects with:
- source_url
- title
- content
- category
""".strip(),

    "odia": """
You are a professional Odia-language (ଓଡ଼ିଆ) news writer. For each article:
1. Write a concise title in Odia script (ଓଡ଼ିଆ), maximum 8 Odia words.
2. Write a factual summary in Odia script with at least 50 Odia words.
3. Categorize the article using exactly one of: {categories}.
4. Preserve factual accuracy. Output ONLY Odia script for title and content.

Return a JSON object with an "articles" key that contains an array of objects with:
- source_url
- title  (in Odia script)
- content (in Odia script)
- category
""".strip(),

    "bengali": """
You are a professional Bengali-language (বাংলা) news writer. For each article:
1. Write a concise title in Bengali script (বাংলা), maximum 8 Bengali words.
2. Write a factual summary in Bengali script with at least 50 Bengali words.
3. Categorize the article using exactly one of: {categories}.
4. Preserve factual accuracy. Output ONLY Bengali script for title and content.

Return a JSON object with an "articles" key that contains an array of objects with:
- source_url
- title   (in Bengali script)
- content (in Bengali script)
- category
""".strip(),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_json_response(response_text: str) -> str:
    cleaned = response_text.strip()
    if "```json" in cleaned:
        start = cleaned.find("```json") + 7
        end = cleaned.find("```", start)
        if end != -1:
            return cleaned[start:end].strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        return cleaned[3:-3].strip()
    return cleaned


def _extract_json_payload(response_text: str) -> str:
    cleaned = _clean_json_response(response_text)
    if not cleaned:
        return ""

    decoder = json.JSONDecoder()
    for start_index, char in enumerate(cleaned):
        if char not in "[{":
            continue
        try:
            _, end_index = decoder.raw_decode(cleaned[start_index:])
            return cleaned[start_index : start_index + end_index]
        except json.JSONDecodeError:
            continue
    return cleaned


def _extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content

    refusal = getattr(message, "refusal", None)
    if isinstance(refusal, str) and refusal.strip():
        return refusal

    function_call = getattr(message, "function_call", None)
    if function_call is not None:
        arguments = getattr(function_call, "arguments", None)
        if isinstance(arguments, str) and arguments.strip():
            return arguments

    tool_calls = getattr(message, "tool_calls", None) or []
    for tool_call in tool_calls:
        function = getattr(tool_call, "function", None)
        if function is None:
            continue
        arguments = getattr(function, "arguments", None)
        if isinstance(arguments, str) and arguments.strip():
            return arguments

    return ""


def _build_fallback_articles(
    articles_data: list[dict[str, Any]],
    language: str = "english",
) -> list[Article]:
    fallback_articles: list[Article] = []
    for article in articles_data:
        authors = article.get("authors") or []
        author = ", ".join(authors) if isinstance(authors, list) else str(authors)
        original_title = str(article.get("original_title") or "").strip()
        original_content = str(article.get("original_content") or "").strip()
        title = original_title or "Untitled article"
        content = original_content or "Summary unavailable. Original content could not be summarized."
        fallback_articles.append(
            Article(
                source_name=article["source_name"],
                source_url=article["url"],
                title=title,
                author=author or None,
                published_at=article["publish_date"],
                image_url=article.get("image_url") or None,
                content=content,
                category="General",
                language=language,
                created_at=datetime.now(timezone.utc),
            )
        )
    return fallback_articles


def _request_summary(
    client: OpenAI,
    *,
    system_instruction: str,
    articles_data: list[dict[str, Any]],
    force_json_object: bool,
    timeout: int = SUMMARIZATION_TIMEOUT_SECONDS,
) -> str:
    request_kwargs: dict[str, Any] = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": json.dumps(
                    _json_safe(articles_data),
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
        "temperature": 0.2,
        "top_p": 0.9,
    }
    if force_json_object:
        request_kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**request_kwargs, timeout=timeout)
    return _extract_response_text(response)


def _request_summary_sarvam(
    *,
    system_instruction: str,
    articles_data: list[dict[str, Any]],
) -> str:
    """Request summarization from Sarvam AI using the official SDK."""
    if not settings.sarvam_ai_api_key:
        logger.error("SARVAM_AI_API_KEY is not configured")
        return ""

    # Note: sarvam-30b has 64K context length. With BATCH_SIZE=5, we are well within limits.
    client = SarvamAI(api_subscription_key=settings.sarvam_ai_api_key)

    try:
        response = client.chat.completions(
            model=SARVAM_AI_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": json.dumps(
                        _json_safe(articles_data),
                        ensure_ascii=False,
                        indent=2,
                    ),
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        logger.exception("Sarvam AI SDK request failed")
        return ""


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize_articles_batch(
    articles_data: list[dict[str, Any]],
    language: str = "english",
) -> list[Article]:
    """Summarise *articles_data* using the AI model and return ``Article`` objects.

    The *language* parameter selects the system prompt so that Odia and Bengali
    articles are summarised in their native scripts rather than English.
    """
    if not articles_data:
        return []

    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY is not configured; skipping summarization batch")
        return []

    categories = ", ".join(settings.permanent_categories)
    prompt_template = _SYSTEM_PROMPTS.get(language, _SYSTEM_PROMPTS["english"])
    system_instruction = prompt_template.replace("{categories}", categories)
    retry_instruction = (
        system_instruction
        + "\n\nReturn only valid JSON. Do not include markdown, commentary, or any text before or after the JSON."
    )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )

    is_english = language.lower() == "english"

    if is_english:
        try:
            response_text = _request_summary(
                client,
                system_instruction=system_instruction,
                articles_data=articles_data,
                force_json_object=True,
                timeout=SUMMARIZATION_TIMEOUT_SECONDS,
            )
        except Exception:
            logger.exception(
                "Summarization request failed for model %r (language=%s); using fallback articles",
                OPENROUTER_MODEL,
                language,
            )
            return _build_fallback_articles(articles_data, language=language)
    else:
        # Non-English: Use Sarvam AI
        response_text = _request_summary_sarvam(
            system_instruction=system_instruction,
            articles_data=articles_data,
        )
        if not response_text:
            logger.warning(
                "Sarvam AI summarization failed (language=%s); using fallback articles",
                language,
            )
            return _build_fallback_articles(articles_data, language=language)

    payload = _extract_json_payload(response_text)
    if not payload:
        logger.warning(
            "Structured summarization returned empty content; retrying without response_format"
        )
        try:
            response_text = _request_summary(
                client,
                system_instruction=retry_instruction,
                articles_data=articles_data,
                force_json_object=False,
                timeout=SUMMARIZATION_TIMEOUT_SECONDS,
            )
        except Exception:
            logger.exception(
                "Retry summarization request failed for model %r (language=%s); using fallback",
                OPENROUTER_MODEL,
                language,
            )
            return _build_fallback_articles(articles_data, language=language)
        payload = _extract_json_payload(response_text)

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        logger.exception("Failed to parse summarization response: %r", payload[:500])
        return _build_fallback_articles(articles_data, language=language)

    raw_articles = parsed.get("articles", parsed if isinstance(parsed, list) else [])
    if not isinstance(raw_articles, list):
        logger.warning("Summarization response did not contain an article list; using fallback")
        return _build_fallback_articles(articles_data, language=language)

    result: list[Article] = []
    for original_article in articles_data:
        source_url = original_article["url"]
        summarized = next(
            (item for item in raw_articles if item.get("source_url") == source_url),
            None,
        )
        if summarized is None:
            continue

        authors = original_article.get("authors") or []
        author = ", ".join(authors) if isinstance(authors, list) else str(authors)
        result.append(
            Article(
                source_name=original_article["source_name"],
                source_url=source_url,
                title=summarized.get("title") or original_article.get("original_title", ""),
                author=author or None,
                published_at=original_article["publish_date"],
                image_url=original_article.get("image_url") or None,
                content=summarized.get("content") or original_article.get("original_content", ""),
                category=summarized.get("category", "General"),
                language=language,
                created_at=datetime.now(timezone.utc),
            )
        )

    if len(result) != len(articles_data):
        missing_urls = {article["url"] for article in articles_data} - {
            article.source_url for article in result
        }
        if missing_urls:
            logger.warning(
                "Summarization omitted %s article(s); filling with fallback content",
                len(missing_urls),
            )
            fallback_articles = _build_fallback_articles(
                [article for article in articles_data if article["url"] in missing_urls],
                language=language,
            )
            result.extend(fallback_articles)

    return result
