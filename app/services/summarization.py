from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

from app.core.config import get_settings
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

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )

    response = client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": json.dumps(articles_data, ensure_ascii=False, indent=2)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        top_p=0.9,
    )

    payload = _clean_json_response(response.choices[0].message.content or "")
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        logger.exception("Failed to parse summarization response")
        return []

    raw_articles = parsed.get("articles", parsed if isinstance(parsed, list) else [])
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
    return result
