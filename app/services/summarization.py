from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

from app.core.config import OPENROUTER_MODEL, get_settings
from app.models import Article

logger = logging.getLogger(__name__)
settings = get_settings()


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


def _build_fallback_articles(articles_data: list[dict[str, Any]]) -> list[Article]:
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

    response = client.chat.completions.create(**request_kwargs)
    return _extract_response_text(response)


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def summarize_articles_batch(articles_data: list[dict[str, Any]]) -> list[Article]:
    if not articles_data:
        return []

    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY is not configured; skipping summarization batch")
        return []

    categories = ", ".join(settings.permanent_categories)
    system_instruction = f"""
You are a professional news writer. You will be given a list of news articles in JSON format.

For each article:
1. Create a concise title with a maximum of 8 words.
2. Write a short factual summary with at least 50 words.
3. Categorize the article using exactly one of: {categories}.
4. Preserve factual accuracy.

Return a JSON object with an "articles" key that contains an array of objects with:
- source_url
- title
- content
- category
""".strip()
    retry_instruction = (
        system_instruction
        + "\n\nReturn only valid JSON. Do not include markdown, commentary, or any text before or after the JSON."
    )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )

    try:
        response_text = _request_summary(
            client,
            system_instruction=system_instruction,
            articles_data=articles_data,
            force_json_object=True,
        )
    except Exception:
        logger.exception(
            "Summarization request failed for model %r; using fallback articles",
            OPENROUTER_MODEL,
        )
        return _build_fallback_articles(articles_data)
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
            )
        except Exception:
            logger.exception(
                "Retry summarization request failed for model %r; using fallback articles",
                OPENROUTER_MODEL,
            )
            return _build_fallback_articles(articles_data)
        payload = _extract_json_payload(response_text)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        logger.exception("Failed to parse summarization response: %r", payload[:500])
        return _build_fallback_articles(articles_data)

    raw_articles = parsed.get("articles", parsed if isinstance(parsed, list) else [])
    if not isinstance(raw_articles, list):
        logger.warning("Summarization response did not contain an article list; using fallback")
        return _build_fallback_articles(articles_data)

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
                [article for article in articles_data if article["url"] in missing_urls]
            )
            result.extend(fallback_articles)
    return result
