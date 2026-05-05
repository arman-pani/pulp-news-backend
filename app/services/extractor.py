from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import feedparser
import requests
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

try:
    from newspaper import Article as NewspaperArticle
except ImportError:  # pragma: no cover
    NewspaperArticle = None

try:
    import trafilatura
except ImportError:  # pragma: no cover
    trafilatura = None


class ArticleExtractor:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/127.0.0.1 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
            }
        )

    def extract_articles(
        self,
        rss_url: str,
        url_patterns: list[str],
        source_name: str,
        max_articles: int | None = None,
    ) -> list[dict[str, Any]]:
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                logger.warning("No entries found in %s", rss_url)
                return []

            results: list[dict[str, Any]] = []
            for entry in feed.entries:
                if max_articles and len(results) >= max_articles:
                    break
                article = self._extract_single_article(entry, url_patterns, source_name)
                if article:
                    results.append(article)

            logger.info("%s articles extracted from %s", len(results), source_name)
            return results
        except Exception:
            logger.exception("Error extracting feed %s", rss_url)
            return []

    def _extract_single_article(
        self, entry: Any, url_patterns: list[str], source_name: str
    ) -> dict[str, Any] | None:
        try:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", "").strip()
            if not url or not title or not self._matches_url_patterns(url, url_patterns):
                return None

            content_data = self._extract_article_content(url)
            if not content_data:
                return None

            content = content_data.get("content", "").strip()
            if len(content) < 100:
                return None

            return {
                "original_title": title,
                "original_content": content,
                "image_url": content_data.get("image_url", ""),
                "url": url,
                "source_name": source_name,
                "authors": content_data.get("authors", []),
                "publish_date": self._extract_publish_date(entry),
            }
        except Exception:
            logger.exception("Failed to extract article from %s", getattr(entry, "link", "unknown"))
            return None

    def _matches_url_patterns(self, url: str, patterns: list[str]) -> bool:
        if not patterns:
            return True
        for pattern in patterns:
            try:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            except re.error:
                if pattern.lower() in url.lower():
                    return True
        return False

    def _extract_publish_date(self, entry: Any) -> datetime:
        for field in ["published", "updated", "created", "pubDate"]:
            date_value = getattr(entry, field, None)
            if not date_value:
                continue
            try:
                parsed = date_parser.parse(str(date_value))
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                continue
        return datetime.now(timezone.utc)

    def _extract_article_content(self, url: str) -> dict[str, Any] | None:
        if NewspaperArticle is not None:
            data = self._extract_with_newspaper(url)
            if data:
                return data
        if trafilatura is not None:
            data = self._extract_with_trafilatura(url)
            if data:
                return data
        return None

    def _extract_with_newspaper(self, url: str) -> dict[str, Any] | None:
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                return None

            article = NewspaperArticle(url)
            article.download(input_html=response.text)
            article.parse()
            if not article.text or len(article.text.strip()) < 100:
                return None

            return {
                "content": article.text.strip(),
                "image_url": article.top_image or "",
                "authors": article.authors or [],
            }
        except Exception:
            logger.debug("newspaper4k failed for %s", url, exc_info=True)
            return None

    def _extract_with_trafilatura(self, url: str) -> dict[str, Any] | None:
        try:
            html = trafilatura.fetch_url(
                url,
                user_agent=self.session.headers["User-Agent"],
                no_fallback=True,
            )
            if not html:
                return None

            content = trafilatura.extract(html)
            if not content or len(content.strip()) < 100:
                return None

            metadata = trafilatura.extract_metadata(html)
            author = [metadata.author] if metadata and getattr(metadata, "author", None) else []
            image_url = self._extract_image_from_html(html, url)
            return {"content": content.strip(), "image_url": image_url, "authors": author}
        except Exception:
            logger.debug("trafilatura failed for %s", url, exc_info=True)
            return None

    def _extract_image_from_html(self, html: str, base_url: str) -> str:
        patterns = [
            r'<img[^>]+src=["\']([^"\']+)["\']',
            r'<img[^>]+data-src=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match and not match.startswith(("data:", "#")):
                    return match if match.startswith("http") else urljoin(base_url, match)
        return ""

    def close(self) -> None:
        self.session.close()


def extract_articles_from_rss(
    rss_url: str,
    url_patterns: list[str],
    source_name: str,
    max_articles: int | None = None,
) -> list[dict[str, Any]]:
    extractor = ArticleExtractor()
    try:
        return extractor.extract_articles(rss_url, url_patterns, source_name, max_articles)
    finally:
        extractor.close()
