import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timezone
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
import re
from html import unescape
import logging
from dateutil import parser as date_parser

from database.crud_operations import save_articles_bulk_insert, batch_check_duplicates
from scraping.summarize_article import summarize_articles_batch
from database.postsql_db_connection import test_database_connection

# Set up logging
logger = logging.getLogger(__name__)

# Configuration for multiple Odisha news websites with RSS feeds
NEWS_WEBSITES = {
    "odishatv": {
        "base_url": "https://odishatv.in",
        "rss_url": "https://odishatv.in/rss",
        "source_name": "OdishaTV",
        "url_patterns": ["https://odishatv.in/odisha/"]
    },
    "odishabytes": {
        "base_url": "https://odishabytes.com",
        "rss_url": "https://odishabytes.com/category/odisha/rss",
        "source_name": "OdishaBytes",
        "url_patterns": ["https://odishabytes.com/"]
    },
    "sambadenglish": {
        "base_url": "https://sambadenglish.com",
        "rss_url": "https://sambadenglish.com/rss",
        "source_name": "Sambad English",
        "url_patterns": ["/latest-news/", "/news-from-around-the-state/"]
    },
    "orissapost": {
        "base_url": "https://www.orissapost.com",
        "rss_url": "https://www.orissapost.com/state-news/rss",
        "source_name": "Orissa Post",
        "url_patterns": ["https://www.orissapost.com"]
    },
}


def create_session_with_retries() -> requests.Session:
    """Create a requests session with retry strategy"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def matches_url_pattern(url: str, patterns: List[str], base_url: str) -> bool:
    """Check if URL matches any of the specified patterns, handling relative URLs"""
    for pattern in patterns:
        # If pattern is relative, make it absolute
        if not pattern.startswith('http'):
            pattern = urljoin(base_url, pattern)
        
        if pattern in url:
            return True
    return False


def clean_html_content(html_content: str) -> str:
    """Clean HTML content and extract plain text"""
    if not html_content:
        return ""
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode HTML entities
    clean_text = unescape(clean_text)
    
    # Clean up whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text


def parse_rss_date(date_str: str) -> str:
    """Parse RSS date string using dateutil for robust parsing"""
    try:
        # Use dateutil.parser for robust date parsing
        dt = date_parser.parse(date_str)
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def extract_image_url(item: ET.Element, base_url: str) -> str:
    """Extract image URL from RSS item, checking multiple sources"""
    image_url = ""
    
    # Check enclosure tag
    enclosure = item.find('enclosure')
    if enclosure is not None and enclosure.get('type', '').startswith('image'):
        image_url = enclosure.get('url', '')
    
    # Check media:content tag
    if not image_url:
        media_content = item.find('.//{http://search.yahoo.com/mrss/}content')
        if media_content is not None and media_content.get('type', '').startswith('image'):
            image_url = media_content.get('url', '')
    
    # Check media:thumbnail tag
    if not image_url:
        media_thumbnail = item.find('.//{http://search.yahoo.com/mrss/}thumbnail')
        if media_thumbnail is not None:
            image_url = media_thumbnail.get('url', '')
    
    # Make relative URLs absolute
    if image_url and not image_url.startswith('http'):
        image_url = urljoin(base_url, image_url)
    
    return image_url


def extract_author(item: ET.Element) -> List[str]:
    """Extract author information from RSS item"""
    authors = []
    
    # Check for dc:creator
    creator = item.find('.//{http://purl.org/dc/elements/1.1/}creator')
    if creator is not None and creator.text:
        authors.append(creator.text.strip())
    
    # Check for author tag
    author = item.find('author')
    if author is not None and author.text:
        authors.append(author.text.strip())
    
    return authors


def parse_rss_items(root: ET.Element, website_config: Dict[str, Any], max_articles: Optional[int] = None) -> List[Dict[str, Any]]:
    """Parse RSS 2.0 items"""
    articles = []
    base_url = website_config["base_url"]
    
    items = root.findall('.//item')
    if max_articles:
        items = items[:max_articles]
    
    for item in items:
        try:
            # Extract basic information
            link_elem = item.find('link')
            title_elem = item.find('title')
            description_elem = item.find('description')
            pub_date_elem = item.find('pubDate')
            
            if link_elem is None or link_elem.text is None:
                continue
                
            url = link_elem.text.strip()
            
            # Check if URL matches patterns
            if not matches_url_pattern(url, website_config['url_patterns'], base_url):
                continue
            
            # Extract title
            title = ""
            if title_elem is not None and title_elem.text:
                title = clean_html_content(title_elem.text)
            
            # Extract content from description
            content = ""
            if description_elem is not None and description_elem.text:
                content = clean_html_content(description_elem.text)
            
            # Skip if no title or content
            if not title or not content:
                logger.debug(f"Skipping article with missing content: {url}")
                continue
            
            # Extract publish date
            publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            if pub_date_elem is not None and pub_date_elem.text:
                publish_date = parse_rss_date(pub_date_elem.text)
            
            # Extract image URL
            image_url = extract_image_url(item, base_url)
            
            # Extract authors
            authors = extract_author(item)
            
            articles.append({
                "original_title": title,
                "original_content": content,
                "image_url": image_url,
                "url": url,
                "source_name": website_config["source_name"],
                "authors": authors,
                "publish_date": publish_date
            })
            
            logger.info(f"Extracted article from {website_config['source_name']}: {title[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing RSS item: {e}")
            continue
    
    return articles


def parse_atom_entries(root: ET.Element, website_config: Dict[str, Any], max_articles: Optional[int] = None) -> List[Dict[str, Any]]:
    """Parse Atom feed entries"""
    articles = []
    base_url = website_config["base_url"]
    
    entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
    if max_articles:
        entries = entries[:max_articles]
    
    for entry in entries:
        try:
            link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
            
            if link_elem is None:
                continue
                
            href = link_elem.get('href')
            if not href:
                continue
            
            # Make relative URLs absolute
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # Check if URL matches patterns
            if not matches_url_pattern(href, website_config['url_patterns'], base_url):
                continue
            
            # Extract title
            title = ""
            if title_elem is not None and title_elem.text:
                title = clean_html_content(title_elem.text)
            
            # Extract content
            content = ""
            if summary_elem is not None and summary_elem.text:
                content = clean_html_content(summary_elem.text)
            
            # Skip if no title or content
            if not title or not content:
                logger.debug(f"Skipping article with missing content: {href}")
                continue
            
            # Extract publish date
            publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            if updated_elem is not None and updated_elem.text:
                publish_date = parse_rss_date(updated_elem.text)
            
            # Extract image URL (for Atom feeds)
            image_url = extract_image_url(entry, base_url)
            
            # Extract authors
            authors = []
            author_elem = entry.find('{http://www.w3.org/2005/Atom}author')
            if author_elem is not None:
                name_elem = author_elem.find('{http://www.w3.org/2005/Atom}name')
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            
            articles.append({
                "original_title": title,
                "original_content": content,
                "image_url": image_url,
                "url": href,
                "source_name": website_config["source_name"],
                "authors": authors,
                "publish_date": publish_date
            })
            
            logger.info(f"Extracted article from {website_config['source_name']}: {title[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing Atom entry: {e}")
            continue
    
    return articles


def extract_articles_from_rss(website_config: Dict[str, Any], max_articles: Optional[int] = None) -> List[Dict[str, Any]]:
    """Extract article data directly from RSS feed"""
    try:
        logger.info(f"Fetching RSS feed from {website_config['source_name']}: {website_config['rss_url']}")
        
        session = create_session_with_retries()
        response = session.get(
            website_config["rss_url"], 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, 
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch RSS feed from {website_config['source_name']}: {response.status_code}")
            return []
        
        # Parse XML RSS feed
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            logger.error(f"XML parsing error for {website_config['source_name']}: {e}")
            return []
        
        articles = []
        
        # Try RSS 2.0 format first
        rss_items = root.findall('.//item')
        if rss_items:
            logger.debug(f"Parsing RSS 2.0 format with {len(rss_items)} items")
            articles = parse_rss_items(root, website_config, max_articles)
        else:
            # Try Atom format
            atom_entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            if atom_entries:
                logger.debug(f"Parsing Atom format with {len(atom_entries)} entries")
                articles = parse_atom_entries(root, website_config, max_articles)
        
        logger.info(f"Extracted {len(articles)} articles from {website_config['source_name']}")
        return articles
        
    except Exception as e:
        logger.error(f"Error extracting articles from {website_config['source_name']} RSS: {e}")
        return []


def scrape_and_process_articles(max_articles_per_source: Optional[int] = None):
    """Main function to scrape, process, and save articles from all Odisha news websites using RSS feeds"""
    logger.info(f"Starting RSS-based Odisha news scraping at: {datetime.now(timezone.utc).isoformat()}")
    
    # Test connection first
    if not test_database_connection():
        logger.error("Cannot proceed without database connection")
        return 0
    
    try:
        all_articles = []
        
        # Extract articles from all RSS feeds
        for website_key, website_config in NEWS_WEBSITES.items():
            logger.info(f"Processing {website_config['source_name']} RSS...")
            articles = extract_articles_from_rss(website_config, max_articles_per_source)
            all_articles.extend(articles)
        
        logger.info(f"Total articles extracted from all RSS feeds: {len(all_articles)}")
        
        if not all_articles:
            logger.warning("No articles found to process")
            return 0
        
        # Batch check for duplicates
        logger.info("Checking for duplicate articles...")
        source_urls = [article["url"] for article in all_articles]
        duplicates = batch_check_duplicates(source_urls)
        
        # Filter out duplicates
        unique_articles = [article for article in all_articles if article["url"] not in duplicates]
        logger.info(f"Filtered out {len(duplicates)} duplicate articles, {len(unique_articles)} unique articles remaining")
        
        if not unique_articles:
            logger.warning("No new articles to process after duplicate filtering")
            return 0
        
        # Summarize all articles in batch
        logger.info("Summarizing articles...")
        processed_articles = summarize_articles_batch(unique_articles)
        logger.info(f"Summarized {len(processed_articles)} articles")
        
        if not processed_articles:
            logger.warning("No articles to save after summarization")
            return 0
        
        # Save to database
        logger.info("Saving articles to database...")
        saved_count = save_articles_bulk_insert(processed_articles)
        
        logger.info(f"RSS-based scraping completed at: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"Processed {len(processed_articles)} unique articles, saved {saved_count} to database")
        
        return saved_count
        
    except Exception as e:
        logger.error(f"Error in RSS-based scraping function: {e}")
        return 0


# Legacy functions for backward compatibility
def extract_article_urls_from_rss(website_config: Dict[str, Any]) -> List[str]:
    """Legacy function - extract URLs only (for backward compatibility)"""
    articles = extract_articles_from_rss(website_config)
    return [article["url"] for article in articles]


def extract_article_urls() -> List[str]:
    """Legacy function - extract URLs from all RSS feeds (for backward compatibility)"""
    all_urls = []
    for website_key, website_config in NEWS_WEBSITES.items():
        urls = extract_article_urls_from_rss(website_config)
        all_urls.extend(urls)
    return all_urls


def scrape_articles(urls: List[str]) -> List[Dict[str, Any]]:
    """Legacy function - not used in new RSS-based approach"""
    logger.warning("scrape_articles() is deprecated. Use extract_articles_from_rss() instead.")
    return []