"""
Structured news article extraction module using feedparser and trafilatura/newspaper3k.
Replaces manual XML/regex parsing with robust content extraction.
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
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logging.warning("trafilatura not available, falling back to newspaper3k")

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logging.warning("newspaper3k not available")

logger = logging.getLogger(__name__)


class ArticleExtractor:
    """
    Extract structured news articles from RSS feeds using feedparser and content extraction.
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the article extractor.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_articles(
        self,
        rss_url: str,
        url_patterns: List[str],
        source_name: str,
        max_articles: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract structured articles from RSS feed.
        
        Args:
            rss_url: RSS/Atom feed URL
            url_patterns: List of URL patterns to filter articles
            source_name: Name of the news source
            max_articles: Maximum number of articles to extract
            
        Returns:
            List of article dictionaries with structured data
        """
        logger.info(f"Starting article extraction from {source_name} ({rss_url})")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing had issues: {feed.bozo_exception}")
            
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {rss_url}")
                return []
            
            logger.info(f"Found {len(feed.entries)} entries in RSS feed")
            
            # Filter and extract articles
            articles = []
            processed_count = 0
            skipped_count = 0
            
            for entry in feed.entries:
                if max_articles and processed_count >= max_articles:
                    break
                
                try:
                    article = self._extract_single_article(entry, url_patterns, source_name)
                    if article:
                        articles.append(article)
                        processed_count += 1
                        logger.debug(f"Successfully extracted article: {article.get('original_title', 'No title')[:50]}...")
                    else:
                        skipped_count += 1
                        logger.debug(f"Skipped article (missing required fields or invalid content)")
                        
                except Exception as e:
                    logger.error(f"Error processing article entry: {e}")
                    skipped_count += 1
                    continue
            
            logger.info(f"Successfully extracted {len(articles)} articles from {source_name} (skipped {skipped_count} incomplete articles)")
            return articles
            
        except Exception as e:
            logger.error(f"Error extracting articles from {rss_url}: {e}")
            return []
    
    def _extract_single_article(
        self,
        entry: Any,
        url_patterns: List[str],
        source_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract a single article from RSS entry.
        
        Args:
            entry: RSS feed entry
            url_patterns: URL patterns to match
            source_name: Source name
            
        Returns:
            Article dictionary or None if extraction fails
        """
        try:
            # Get article URL
            article_url = getattr(entry, 'link', None)
            if not article_url:
                logger.debug("No link found in RSS entry")
                return None
            
            # Check if URL matches patterns
            if not self._matches_url_patterns(article_url, url_patterns):
                logger.debug(f"URL doesn't match patterns: {article_url}")
                return None
            
            # Extract basic info from RSS entry
            title = getattr(entry, 'title', '').strip()
            if not title:
                logger.debug("No title found in RSS entry")
                return None
            
            # Get publish date from RSS entry
            publish_date = self._extract_publish_date(entry)
            
            # Fetch and extract content from article URL
            content_data = self._extract_article_content(article_url)
            if not content_data:
                logger.debug(f"Could not extract content from: {article_url}")
                return None
            
            # Build article dictionary
            article = {
                "original_title": title,
                "original_content": content_data.get('content', ''),
                "image_url": content_data.get('image_url', ''),
                "url": article_url,
                "source_name": source_name,
                "authors": content_data.get('authors', []),
                "publish_date": publish_date
            }
            
            # Validate article has ALL required fields with meaningful content
            if not self._validate_article_completeness(article, article_url):
                logger.debug(f"Article missing required fields: {article_url}")
                return None
            
            return article
            
        except Exception as e:
            logger.error(f"Error extracting single article: {e}")
            return None
    
    def _matches_url_patterns(self, url: str, patterns: List[str]) -> bool:
        """
        Check if URL matches any of the given patterns.
        
        Args:
            url: Article URL to check
            patterns: List of URL patterns (substrings or regex)
            
        Returns:
            True if URL matches any pattern
        """
        if not patterns:
            return True
        
        for pattern in patterns:
            try:
                # Try regex pattern first
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            except re.error:
                # If regex fails, treat as substring
                if pattern.lower() in url.lower():
                    return True
        
        return False
    
    def _validate_article_completeness(self, article: Dict[str, Any], article_url: str) -> bool:
        """
        Validate that article has all required fields with meaningful content.
        
        Args:
            article: Article dictionary to validate
            article_url: Article URL for logging
            
        Returns:
            True if article has all required fields, False otherwise
        """
        required_fields = {
            'original_title': 'Title',
            'original_content': 'Content', 
            'url': 'URL',
            'source_name': 'Source Name',
            'publish_date': 'Publish Date'
        }
        
        missing_fields = []
        empty_fields = []
        
        # Check for missing or empty required fields
        for field, display_name in required_fields.items():
            if field not in article:
                missing_fields.append(display_name)
            elif not article[field] or (isinstance(article[field], str) and not article[field].strip()):
                empty_fields.append(display_name)
        
        # Check optional fields that should have meaningful content if present
        if article.get('authors') is not None and not article['authors']:
            empty_fields.append('Authors (empty list)')
        
        # Log validation results
        if missing_fields:
            logger.debug(f"Article missing fields: {missing_fields} - {article_url}")
            return False
            
        if empty_fields:
            logger.debug(f"Article has empty fields: {empty_fields} - {article_url}")
            return False
        
        # Additional content quality checks
        if len(article['original_content'].strip()) < 100:
            logger.debug(f"Article content too short ({len(article['original_content'])} chars) - {article_url}")
            return False
            
        if len(article['original_title'].strip()) < 10:
            logger.debug(f"Article title too short ({len(article['original_title'])} chars) - {article_url}")
            return False
        
        # Validate URL format
        if not article_url.startswith('http'):
            logger.debug(f"Invalid URL format: {article_url}")
            return False
        
        # Validate date format (should be YYYY-MM-DD HH:MM:SS)
        try:
            datetime.strptime(article['publish_date'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.debug(f"Invalid date format: {article['publish_date']} - {article_url}")
            return False
        
        logger.debug(f"Article validation passed: {article_url}")
        return True
    
    def _extract_publish_date(self, entry: Any) -> str:
        """
        Extract and normalize publish date from RSS entry.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Normalized UTC date string (YYYY-MM-DD HH:MM:SS)
        """
        try:
            # Try different date fields
            date_fields = ['published', 'updated', 'created', 'pubDate']
            
            for field in date_fields:
                date_value = getattr(entry, field, None)
                if date_value:
                    try:
                        # Parse the date
                        parsed_date = date_parser.parse(str(date_value))
                        
                        # Convert to UTC if timezone aware
                        if parsed_date.tzinfo is not None:
                            parsed_date = parsed_date.astimezone(pytz.UTC)
                        else:
                            # Assume UTC if no timezone
                            parsed_date = pytz.UTC.localize(parsed_date)
                        
                        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                        
                    except Exception as e:
                        logger.debug(f"Error parsing date field {field}: {e}")
                        continue
            
            # Fallback to current time
            return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.debug(f"Error extracting publish date: {e}")
            return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    def _extract_article_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content from article URL using trafilatura or newspaper3k.
        
        Args:
            url: Article URL to extract content from
            
        Returns:
            Dictionary with content, image_url, and authors
        """
        for attempt in range(self.max_retries):
            try:
                # Fetch the article
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                html_content = response.text
                
                # Try trafilatura first (preferred)
                if TRAFILATURA_AVAILABLE:
                    content_data = self._extract_with_trafilatura(html_content, url)
                    if content_data:
                        return content_data
                
                # Fallback to newspaper3k
                if NEWSPAPER_AVAILABLE:
                    content_data = self._extract_with_newspaper(url)
                    if content_data:
                        return content_data
                
                logger.debug(f"Could not extract content from: {url}")
                return None
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch article after {self.max_retries} attempts: {url}")
                    return None
                continue
                
            except Exception as e:
                logger.error(f"Error extracting content from {url}: {e}")
                return None
        
        return None
    
    def _extract_with_trafilatura(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content using trafilatura.
        
        Args:
            html_content: HTML content of the article
            url: Article URL
            
        Returns:
            Dictionary with extracted content data
        """
        try:
            # Extract main content
            content = trafilatura.extract(html_content, include_comments=False, include_tables=True)
            
            if not content or len(content.strip()) < 100:
                return None
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(html_content)
            
            # Extract image URL
            image_url = self._extract_image_from_html(html_content, url)
            
            # Extract authors
            authors = []
            if metadata and metadata.get('author'):
                authors = [metadata['author']]
            elif metadata and metadata.get('authors'):
                authors = metadata['authors']
            
            return {
                'content': content.strip(),
                'image_url': image_url,
                'authors': authors
            }
            
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {e}")
            return None
    
    def _extract_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content using newspaper3k.
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary with extracted content data
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if not article.text or len(article.text.strip()) < 100:
                return None
            
            # Extract authors
            authors = []
            if article.authors:
                authors = article.authors
            
            return {
                'content': article.text.strip(),
                'image_url': article.top_image or '',
                'authors': authors
            }
            
        except Exception as e:
            logger.debug(f"Newspaper3k extraction failed: {e}")
            return None
    
    def _extract_image_from_html(self, html_content: str, base_url: str) -> str:
        """
        Extract main image URL from HTML content.
        
        Args:
            html_content: HTML content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Image URL or empty string
        """
        try:
            # Try to find the main image using various patterns
            patterns = [
                r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
                r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>',
                r'<img[^>]+data-lazy-src=["\']([^"\']+)["\'][^>]*>',
                r'<img[^>]+data-original=["\']([^"\']+)["\'][^>]*>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if match and not match.startswith('data:') and not match.startswith('#'):
                        # Convert relative URL to absolute
                        if not match.startswith('http'):
                            match = urljoin(base_url, match)
                        return match
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting image: {e}")
            return ""
    
    def close(self):
        """Close the session."""
        if hasattr(self, 'session'):
            self.session.close()


def extract_articles_from_rss(
    rss_url: str,
    url_patterns: List[str],
    source_name: str,
    max_articles: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to extract articles from RSS feed.
    
    Args:
        rss_url: RSS/Atom feed URL
        url_patterns: List of URL patterns to filter articles
        source_name: Name of the news source
        max_articles: Maximum number of articles to extract
        
    Returns:
        List of article dictionaries
    """
    extractor = ArticleExtractor()
    try:
        return extractor.extract_articles(rss_url, url_patterns, source_name, max_articles)
    finally:
        extractor.close()
