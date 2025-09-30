"""
RSS and Atom feed parsing functionality
"""

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

logger = logging.getLogger(__name__)

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
        if not pattern.startswith('http'):
            pattern = urljoin(base_url, pattern)
        if pattern in url:
            return True
    return False

def clean_html_content(html_content: str) -> str:
    """Clean HTML content and extract plain text"""
    if not html_content:
        return ""
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    clean_text = unescape(clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def parse_rss_date(date_str: str) -> str:
    """Parse RSS date string using dateutil for robust parsing"""
    try:
        dt = date_parser.parse(date_str)
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
    
    # Check for image tags in description/content
    if not image_url:
        description = item.find('description')
        if description is not None and description.text:
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            img_matches = re.findall(img_pattern, description.text, re.IGNORECASE)
            if img_matches:
                image_url = img_matches[0]
    
    # Check for content:encoded with images
    if not image_url:
        content_encoded = item.find('.//{http://purl.org/rss/1.0/modules/content/}encoded')
        if content_encoded is not None and content_encoded.text:
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            img_matches = re.findall(img_pattern, content_encoded.text, re.IGNORECASE)
            if img_matches:
                image_url = img_matches[0]
    
    # Check for WordPress featured image
    if not image_url:
        wp_thumbnail = item.find('.//{http://wordpress.org/export/1.2/}post_thumbnail')
        if wp_thumbnail is not None and wp_thumbnail.text:
            image_url = wp_thumbnail.text
    
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
            link_elem = item.find('link')
            title_elem = item.find('title')
            description_elem = item.find('description')
            pub_date_elem = item.find('pubDate')
            
            if link_elem is None or link_elem.text is None:
                continue
                
            url = link_elem.text.strip()
            
            if not matches_url_pattern(url, website_config['url_patterns'], base_url):
                continue
            
            title = ""
            if title_elem is not None and title_elem.text:
                title = clean_html_content(title_elem.text)
            
            content = ""
            if description_elem is not None and description_elem.text:
                content = clean_html_content(description_elem.text)
            
            if not title or not content:
                logger.info(f"Skipping article with missing content: {url}")
                continue
            
            publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            if pub_date_elem is not None and pub_date_elem.text:
                publish_date = parse_rss_date(pub_date_elem.text)
            
            image_url = extract_image_url(item, base_url)
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
            
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            
            if not matches_url_pattern(href, website_config['url_patterns'], base_url):
                continue
            
            title = ""
            if title_elem is not None and title_elem.text:
                title = clean_html_content(title_elem.text)
            
            content = ""
            if summary_elem is not None and summary_elem.text:
                content = clean_html_content(summary_elem.text)
            
            if not title or not content:
                logger.info(f"Skipping article with missing content: {href}")
                continue
            
            publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            if updated_elem is not None and updated_elem.text:
                publish_date = parse_rss_date(updated_elem.text)
            
            image_url = extract_image_url(entry, base_url)
            
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
