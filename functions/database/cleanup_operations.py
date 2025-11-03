"""
Database cleanup operations for removing old articles and related data
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import logging
from sqlalchemy import and_

from database.postsql_db_connection import get_db_session, Article, SeenArticle

logger = logging.getLogger(__name__)


def delete_old_articles(days_old: int = 7) -> Dict[str, int]:
    """
    Delete articles older than specified days and their related seen_articles records.
    
    Args:
        days_old: Number of days old to consider for deletion (default: 7)
        
    Returns:
        Dict with counts of deleted records
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
    
    try:
        with get_db_session() as db:
            # Step 1: Find old article IDs
            old_articles = db.query(Article).filter(
                Article.published_at < cutoff_date
            ).all()
            
            if not old_articles:
                logger.info("No old articles found to delete")
                return {"articles_deleted": 0, "seen_articles_deleted": 0}
            
            old_article_ids = [article.id for article in old_articles]
            logger.info(f"Found {len(old_article_ids)} old articles to delete")
            
            # Step 2: Delete seen_articles for those article IDs
            seen_articles_deleted = db.query(SeenArticle).filter(
                SeenArticle.article_id.in_(old_article_ids)
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {seen_articles_deleted} seen_articles records")
            
            # Step 3: Delete articles
            articles_deleted = db.query(Article).filter(
                Article.id.in_(old_article_ids)
            ).delete(synchronize_session=False)
            
            logger.info(f"Deleted {articles_deleted} articles")
            
            # Commit the transaction
            db.commit()
            
            result = {
                "articles_deleted": articles_deleted,
                "seen_articles_deleted": seen_articles_deleted
            }
            
            logger.info(f"Cleanup completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error during article cleanup: {e}")
        raise


def get_old_articles_count(days_old: int = 7) -> int:
    """
    Get count of articles that would be deleted without actually deleting them.
    
    Args:
        days_old: Number of days old to consider
        
    Returns:
        Count of old articles
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
    
    try:
        with get_db_session() as db:
            count = db.query(Article).filter(
                Article.published_at < cutoff_date
            ).count()
            
            logger.info(f"Found {count} articles older than {days_old} days")
            return count
            
    except Exception as e:
        logger.error(f"Error counting old articles: {e}")
        return 0
