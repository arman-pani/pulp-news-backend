"""
Structured news article extraction module using feedparser and newspaper4k.
Simplified version with robust content extraction and fallback handling.
"""

import re
import logging
import feedparser
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
import pytz
from dateutil import parser as date_parser

# Content extraction libraries
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logging.warning("newspaper4k not available")

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logging.warning("trafilatura not available")

logger = logging.getLogger(__name__)


class ArticleExtractor:
    """Extract structured news articles from RSS feeds using feedparser and newspaper4k."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.1 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        })


    def extract_articles(
        self,
        rss_url: str,
        url_patterns: List[str],
        source_name: str,
        max_articles: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract structured articles from RSS feed."""
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                logger.warning(f"No entries found in {rss_url}")
                return []

            articles = []
            for entry in feed.entries[:max_articles]:
                article = self._extract_single_article(entry, url_patterns, source_name)
                if article:
                    articles.append(article)

            logger.info(f"{len(articles)} articles extracted from {source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error extracting from {rss_url}: {e}")
            return []

    def _extract_single_article(
        self, entry: Any, url_patterns: List[str], source_name: str
    ) -> Optional[Dict[str, Any]]:
        """Extract a single article from an RSS entry."""
        try:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", "").strip()
            if not url or not title or not self._matches_url_patterns(url, url_patterns):
                return None

            publish_date = self._extract_publish_date(entry)
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
                "publish_date": publish_date,
            }
        except Exception as e:
            logger.debug(f"Failed to extract article: {e}")
            return None

    def _matches_url_patterns(self, url: str, patterns: List[str]) -> bool:
        """Return True if URL matches any pattern."""
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

    def _extract_publish_date(self, entry: Any) -> str:
        """Extract normalized UTC publish date."""
        for field in ["published", "updated", "created", "pubDate"]:
            date_val = getattr(entry, field, None)
            if date_val:
                try:
                    dt = date_parser.parse(str(date_val))
                    if not dt.tzinfo:
                        dt = pytz.UTC.localize(dt)
                    else:
                        dt = dt.astimezone(pytz.UTC)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def _extract_article_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract article content using newspaper4k or trafilatura."""
        try:
            if NEWSPAPER_AVAILABLE:
                data = self._extract_with_newspaper(url)
                if data:
                    return data
            if TRAFILATURA_AVAILABLE:
                data = self._extract_with_trafilatura(url)
                if data:
                    return data
            return None
        except Exception as e:
            logger.debug(f"Extraction failed for {url}: {e}")
            return None

    def _extract_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract article using newspaper4k with custom headers."""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                return None

            article = Article(url)
            article.download(input_html=resp.text)
            article.parse()

            if not article.text or len(article.text.strip()) < 100:
                return None

            return {
                "content": article.text.strip(),
                "image_url": article.top_image or "",
                "authors": article.authors or [],
            }
        except Exception as e:
            logger.debug(f"Newspaper4k failed: {e}")
            return None

    def _extract_with_trafilatura(self, url: str) -> Optional[Dict[str, Any]]:
        """Fallback extraction using trafilatura."""
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

            meta = trafilatura.extract_metadata(html)
            author = [meta["author"]] if meta and meta.get("author") else []
            image_url = self._extract_image_from_html(html, url)

            return {"content": content.strip(), "image_url": image_url, "authors": author}
        except Exception as e:
            logger.debug(f"Trafilatura failed: {e}")
            return None

    def _extract_image_from_html(self, html: str, base_url: str) -> str:
        """Extract first valid image URL from HTML."""
        for pattern in [
            r'<img[^>]+src=["\']([^"\']+)["\']',
            r'<img[^>]+data-src=["\']([^"\']+)["\']',
        ]:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for m in matches:
                if m and not m.startswith(("data:", "#")):
                    return m if m.startswith("http") else urljoin(base_url, m)
        return ""

    def close(self):
        self.session.close()


def extract_articles_from_rss(
    rss_url: str,
    url_patterns: List[str],
    source_name: str,
    max_articles: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Convenience function for one-line extraction."""
    extractor = ArticleExtractor()
    try:
        return extractor.extract_articles(rss_url, url_patterns, source_name, max_articles)
    finally:
        extractor.close()
