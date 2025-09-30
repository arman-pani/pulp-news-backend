"""
Article processing and filtering functionality
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import logging
import time
from dateutil import parser as date_parser

from database.crud_operations import save_articles_bulk_insert, batch_check_duplicates
from scraping.summarize_article import summarize_articles_batch
from scraping.config import BATCH_SIZE, RATE_LIMIT_DELAY, MAX_ARTICLE_AGE_DAYS

logger = logging.getLogger(__name__)

def filter_articles_by_date(articles: List[Dict[str, Any]], max_age_days: int = MAX_ARTICLE_AGE_DAYS) -> List[Dict[str, Any]]:
    """Filter out articles older than specified number of days"""
    if not articles:
        return articles
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    filtered_articles = []
    removed_count = 0
    
    for article in articles:
        try:
            publish_date_str = article.get('publish_date', '')
            if not publish_date_str:
                filtered_articles.append(article)
                continue
            
            article_date = date_parser.parse(publish_date_str)
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=timezone.utc)
            
            if article_date >= cutoff_date:
                filtered_articles.append(article)
            else:
                removed_count += 1
                logger.info(f"Removed old article: {article.get('original_title', 'Unknown')[:50]}... (published: {publish_date_str})")
                
        except Exception as e:
            logger.warning(f"Could not parse date '{publish_date_str}' for article '{article.get('original_title', 'Unknown')[:50]}...': {e}")
            filtered_articles.append(article)
    
    logger.info(f"Date filtering: Removed {removed_count} articles older than {max_age_days} days, kept {len(filtered_articles)} articles")
    return filtered_articles

def check_and_filter_duplicates(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check for duplicates and filter them out"""
    if not articles:
        return articles
    
    logger.info("Checking for duplicate articles...")
    
    # Pass articles directly to batch_check_duplicates (no copying needed)
    duplicates = batch_check_duplicates(articles)
    
    # Filter out duplicates
    unique_articles = [article for article in articles if article["url"] not in duplicates]
    logger.info(f"Filtered out {len(duplicates)} duplicate articles, {len(unique_articles)} unique articles remaining")
    
    return unique_articles

def summarize_articles_in_batches(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize articles in batches to handle rate limits"""
    if not articles:
        return []
    
    logger.info("Summarizing articles...")
    processed_articles = []
    
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        logger.info(f"Processing summarization batch {i//BATCH_SIZE + 1}/{(len(articles) + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} articles)")
        
        batch_processed = summarize_articles_batch(batch)
        processed_articles.extend(batch_processed)
        
        # Small delay between batches to respect rate limits
        if i + BATCH_SIZE < len(articles):
            time.sleep(RATE_LIMIT_DELAY)
    
    logger.info(f"Summarized {len(processed_articles)} articles")
    return processed_articles

def process_articles(articles: List[Dict[str, Any]]) -> int:
    """Process articles through the complete pipeline: date filtering, duplicate checking, summarization, and saving"""
    if not articles:
        logger.warning("No articles found to process")
        return 0
    
    # Filter articles by date (remove articles older than 2 days)
    logger.info("Filtering articles by date (removing articles older than 2 days)...")
    articles = filter_articles_by_date(articles, max_age_days=MAX_ARTICLE_AGE_DAYS)
    
    if not articles:
        logger.warning("No recent articles found after date filtering")
        return 0
    
    # Check for duplicates
    articles = check_and_filter_duplicates(articles)
    
    if not articles:
        logger.warning("No new articles to process after duplicate filtering")
        return 0

    # Summarize articles in batches
    processed_articles = summarize_articles_in_batches(articles)
    
    if not processed_articles:
        logger.warning("No articles to save after summarization")
        return 0
    
    # Save to database
    logger.info("Saving articles to database...")
    saved_count = save_articles_bulk_insert(processed_articles)
    
    logger.info(f"Processed {len(processed_articles)} unique articles, saved {saved_count} to database")
    return saved_count
