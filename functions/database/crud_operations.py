from typing import List, Set, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.dialects.postgresql import insert
import re
from rapidfuzz import process, fuzz

from .postsql_db_connection import Article, get_db_session

def normalize_title(title: str) -> str:
    """Normalize title for fuzzy matching"""
    return " ".join(title.lower().split()) if title else ""

def batch_check_duplicates(scraped_articles: List[Dict[str, Any]], title_threshold: int = 85) -> Set[str]:
    """Check for duplicate articles using both exact URL matching and fuzzy title matching"""
    if not scraped_articles:
        return set()

    duplicate_urls = set()
    # Extract URLs from articles (using 'url' key, not 'source_url')
    source_urls = [a["url"] for a in scraped_articles if "url" in a]
    
    print(f"Processing {len(scraped_articles)} articles, {len(source_urls)} have URLs")

    with get_db_session() as db:
        try:
            # 1. Exact URL check in DB
            existing_urls = set()
            if source_urls:
                existing_urls = {
                    a.source_url for a in db.query(Article.source_url).filter(Article.source_url.in_(source_urls)).all()
                }
            duplicate_urls.update(existing_urls)
            print(f"Found {len(existing_urls)} exact URL duplicates")

            # 2. Recent titles for fuzzy check
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_titles = [
                normalize_title(a.title) for a in db.query(Article.title).filter(Article.created_at >= cutoff_time).all()
                if a.title
            ]
            print(f"Loaded {len(recent_titles)} recent titles for fuzzy matching")
            
        except Exception as e:
            print(f"Error fetching from DB: {e}")
            recent_titles = []

    seen_titles = set(recent_titles)
    fuzzy_duplicates = 0

    # 3. Fuzzy check for each article
    for article in scraped_articles:
        url = article.get("url")  # Use 'url' key directly
        title = normalize_title(article.get("original_title", ""))  # Use 'original_title' key

        if not url or url in duplicate_urls:
            continue  # Skip empty URL or already marked

        if not title:
            continue  # Skip if title missing

        # Best fuzzy match in seen_titles
        if seen_titles:
            best_match = process.extractOne(title, seen_titles, scorer=fuzz.token_set_ratio)
            if best_match and best_match[1] >= title_threshold:
                duplicate_urls.add(url)
                fuzzy_duplicates += 1
                print(f"Fuzzy duplicate: '{title}' (score: {best_match[1]})")
                continue

        # Not duplicate → keep & add to seen_titles
        seen_titles.add(title)

    print(f"Total duplicates: {len(duplicate_urls)} ({len(existing_urls)} exact + {fuzzy_duplicates} fuzzy)")
    return duplicate_urls

def save_articles_bulk_insert(articles: List[Article]) -> int:
    """Save articles using PostgreSQL bulk insert with ON CONFLICT handling"""
    if not articles:
        return 0
    
    with get_db_session() as db:
        try:
            # Convert articles to dictionaries for bulk insert
            articles_data = []
            for article in articles:
                article_dict = {
                    'source_name': article.source_name,
                    'source_url': article.source_url,
                    'title': article.title,
                    'author': article.author,
                    'published_at': article.published_at,
                    'image_url': article.image_url,
                    'content': article.content,
                    'category': article.category,
                    'created_at': article.created_at
                }
                articles_data.append(article_dict)
            
            # Use PostgreSQL's ON CONFLICT DO NOTHING for efficient bulk insert
            stmt = insert(Article).values(articles_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=['source_url'])
            
            result = db.execute(stmt)
            # Count how many were actually inserted
            inserted_count = result.rowcount
            print(f"✅ Successfully bulk inserted {inserted_count} new articles to database")
            return inserted_count
            
        except Exception as e:
            print(f"❌ Error bulk inserting articles: {e}")
            return 0




