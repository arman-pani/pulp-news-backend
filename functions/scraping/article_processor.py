"""
Article processing and filtering functionality
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import logging
import time
import gc
import psutil
import os
from dateutil import parser as date_parser

from database.crud_operations import save_articles_bulk_insert, batch_check_duplicates
from scraping.summarize_article import summarize_articles_batch
from scraping.config import BATCH_SIZE, RATE_LIMIT_DELAY, MAX_ARTICLE_AGE_DAYS

logger = logging.getLogger(__name__)

def log_memory_usage(stage: str):
    """Log current memory usage for monitoring"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"Memory usage at {stage}: {memory_mb:.2f} MB")
        return memory_mb
    except Exception as e:
        logger.warning(f"Could not get memory usage: {e}")
        return 0

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

def summarize_articles_in_small_batches(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize articles in small batches with memory management"""
    if not articles:
        return []
    
    logger.info(f"Summarizing {len(articles)} articles in batches of {BATCH_SIZE}...")
    log_memory_usage("Before summarization")
    
    processed_articles = []
    total_batches = (len(articles) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        batch_number = i // BATCH_SIZE + 1
        
        try:
            log_memory_usage(f"Before batch {batch_number}/{total_batches}")
            
            # Process small batch
            batch_processed = summarize_articles_batch(batch)
            processed_count = len(batch_processed)
            processed_articles.extend(batch_processed)
            
            # Clear batch from memory
            del batch
            del batch_processed
            
            # Force garbage collection after each batch
            gc.collect()
            
            logger.info(f"Batch {batch_number}/{total_batches} completed: {processed_count} articles processed")
            log_memory_usage(f"After batch {batch_number}/{total_batches}")
            
            # Rate limiting delay between batches
            if i + BATCH_SIZE < len(articles):
                logger.info(f"Waiting {RATE_LIMIT_DELAY} seconds before next batch...")
                time.sleep(RATE_LIMIT_DELAY)
                
        except Exception as e:
            logger.error(f"Error processing batch {batch_number}: {e}")
            # Continue with next batch instead of failing completely
            continue
    
    # Final garbage collection
    gc.collect()
    log_memory_usage("After summarization")
    
    logger.info(f"Summarized {len(processed_articles)} articles")
    return processed_articles

def process_articles_optimized(articles: List[Dict[str, Any]]) -> int:
    """Process articles through the complete pipeline with memory optimization"""
    if not articles:
        logger.warning("No articles found to process")
        return 0
    
    log_memory_usage("Start of article processing")
    
    # Filter articles by date (remove articles older than 2 days)
    logger.info("Filtering articles by date (removing articles older than 2 days)...")
    articles = filter_articles_by_date(articles, max_age_days=MAX_ARTICLE_AGE_DAYS)
    log_memory_usage("After date filtering")
    
    if not articles:
        logger.warning("No recent articles found after date filtering")
        return 0
    
    # Check for duplicates
    articles = check_and_filter_duplicates(articles)
    log_memory_usage("After duplicate filtering")
    
    if not articles:
        logger.warning("No new articles to process after duplicate filtering")
        return 0

    # Summarize articles in small batches with memory management
    processed_articles = summarize_articles_in_small_batches(articles)
    
    if not processed_articles:
        logger.warning("No articles to save after summarization")
        return 0
    
    # Save to database
    logger.info("Saving articles to database...")
    processed_count = len(processed_articles)
    saved_count = save_articles_bulk_insert(processed_articles)
    
    # Final cleanup
    del articles
    del processed_articles
    gc.collect()
    log_memory_usage("End of article processing")
    
    logger.info(f"Processed {processed_count} unique articles, saved {saved_count} to database")
    return saved_count

# Keep backward compatibility
def process_articles(articles: List[Dict[str, Any]]) -> int:
    """Backward compatibility alias for process_articles_optimized"""
    return process_articles_optimized(articles)
