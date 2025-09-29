from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc, func, text
from .postsql_db_connection import User, Article, SeenArticle, get_db_session
import time
import logging
from config.config import config

# Get permanent categories from config
PERMANENT_CATEGORIES = config.PERMANENT_CATEGORIES

# Set up logging
logger = logging.getLogger(__name__)

def retry_db_operation(func, max_retries=3, delay=1):
    """
    Retry database operations with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                raise e
            
            logger.warning(f"Database operation attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

def get_or_create_user(auth_id: str) -> Optional[User]:
    """Get existing user or create new user"""
    with get_db_session() as db:
        try:
            # Try to get existing user
            user = db.query(User).filter(User.auth_id == auth_id).first()
            
            if not user:
                # Create new user
                user = User(auth_id=auth_id)
                db.add(user)
                db.flush()  # Flush to get the ID without committing
                print(f"Created new user: {auth_id}")
            else:
                print(f"Found existing user: {auth_id}")
            
            # Detach the user from the session so it can be used outside the context
            db.expunge(user)
            return user
        except Exception as e:
            print(f"Error getting/creating user: {e}")
            return None


def get_unseen_articles(user_auth_id: str, limit: int = 10, category: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch the most recent unseen articles for a user and mark them as seen in a single DB session.
    """
    with get_db_session() as db:
        try:
            # LEFT JOIN to find unseen articles
            query = db.query(Article).outerjoin(
                SeenArticle,
                and_(
                    Article.id == SeenArticle.article_id,
                    SeenArticle.user_auth_id == user_auth_id
                )
            ).filter(
                SeenArticle.id.is_(None)
            )

            # Filter by category if provided
            if category:
                query = query.filter(Article.category == category)

            # # Get total count of unseen articles (before applying limit)
            # total_count = query.count()

            # Fetch articles (limit applied)
            articles = query.order_by(desc(Article.created_at)).limit(limit).all()
            articles_data = [article_to_dict(article) for article in articles]

            # Mark fetched articles as seen in bulk
            if articles:
                new_seen_articles = [
                    SeenArticle(user_auth_id=user_auth_id, article_id=article.id)
                    for article in articles
                ]
                db.add_all(new_seen_articles)

            return articles_data

        except Exception as e:
            print(f"Error in get_and_mark_unseen_articles: {e}")
            return []


def get_articles_by_category(category: str, limit: int = 10, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    """Get articles by category with pagination"""
    with get_db_session() as db:
        try:
            query = db.query(Article).filter(Article.category == category)
                        
            # Apply ordering and limit (no offset needed - always get freshest articles)
            articles = query.order_by(desc(Article.created_at)).limit(limit).offset(offset).all()
            
            # Convert to dictionaries
            articles_data = [article_to_dict(article) for article in articles]
            
            return articles_data
        except Exception as e:
            print(f"Error getting articles by category: {e}")
            return []


def search_articles(search_query: str, limit: int = 10, offset: int = 0, category: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """Search articles by title and content with pagination"""
    with get_db_session() as db:
        try:
            # Build search query
            search_filter = or_(
                Article.title.ilike(f"%{search_query}%"),
                Article.content.ilike(f"%{search_query}%")
            )
            
            query = db.query(Article).filter(search_filter)
            
            # Filter by category if provided
            if category:
                query = query.filter(Article.category == category)
            
            # Apply ordering and limit (offset needed - always get freshest articles)
            articles = query.order_by(desc(Article.created_at)).limit(limit).offset(offset).all()
            
            # Convert to dictionaries
            articles_data = [article_to_dict(article) for article in articles]
            
            return articles_data
        except Exception as e:
            print(f"Error searching articles: {e}")
            return []
       


def get_bundled_articles_by_category(limit_per_category: int = 5) -> Dict[str, Any]:
    """
    Fetch articles from each category and bundle them together using a single query.
    """

    def _execute_query():
        with get_db_session() as db:
            try:
                categories = PERMANENT_CATEGORIES
                if not categories:
                    return {"categories": {}, "total_categories": 0, "success": True}

                # Single query: Get top N articles + total count per category
                query = text("""
                    WITH ranked_articles AS (
                        SELECT 
                            id, title, source_name, source_url, author, content, category,
                            image_url, published_at, created_at,
                            ROW_NUMBER() OVER (PARTITION BY category ORDER BY published_at DESC) AS rn,
                            COUNT(*) OVER (PARTITION BY category) AS total_count
                        FROM articles
                        WHERE category = ANY(:categories)
                    )
                    SELECT * FROM ranked_articles
                    WHERE rn <= :limit_per_category
                    ORDER BY category, published_at DESC
                """)

                result = db.execute(query, {
                    "categories": categories,
                    "limit_per_category": limit_per_category
                }).fetchall()

                # Prepare response dictionary
                bundled_data = {
                    cat: {"articles": [], "total": 0, "limit": limit_per_category}
                    for cat in categories
                }

                for row in result:
                    article = {
                        "id": str(row.id),
                        "title": row.title,
                        "source_name": row.source_name,
                        "source_url": row.source_url,
                        "author": row.author,
                        "content": row.content,
                        "category": row.category,
                        "image_url": row.image_url,
                        "published_at": row.published_at.isoformat() if row.published_at else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                    bundled_data[row.category]["articles"].append(article)
                    bundled_data[row.category]["total"] = row.total_count  # total from window function

                return {
                    "categories": bundled_data,
                    "total_categories": len(categories),
                    "success": True
                }

            except Exception as e:
                logger.error(f"Error getting bundled articles by category: {e}")
                return {"categories": {}, "total_categories": 0, "success": False, "error": str(e)}

    return retry_db_operation(_execute_query)


def article_to_dict(article: Article) -> Dict[str, Any]:
    """Convert SQLAlchemy Article object to dictionary"""
    return {
        "id": article.id,
        "source_name": article.source_name,
        "source_url": article.source_url,
        "title": article.title,
        "author": article.author,
        "image_url": article.image_url,
        "content": article.content,
        "category": article.category,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat() if article.created_at else None
    }



# def mark_articles_as_seen(user_auth_id: str, article_ids: List[str]) -> bool:
#     """Mark multiple articles as seen by a user in bulk"""
#     if not article_ids:
#         return True
    
#     db = get_db()
#     try:
#         # Get existing seen articles to avoid duplicates
#         existing_articles = db.query(SeenArticle.article_id).filter(
#             and_(
#                 SeenArticle.user_auth_id == user_auth_id,
#                 SeenArticle.article_id.in_(article_ids)
#             )
#         ).all()
        
#         existing_ids = {row.article_id for row in existing_articles}
        
#         # Create new seen articles for those not already seen
#         new_seen_articles = [
#             SeenArticle(user_auth_id=user_auth_id, article_id=article_id)
#             for article_id in article_ids
#             if article_id not in existing_ids
#         ]
        
#         if new_seen_articles:
#             db.add_all(new_seen_articles)
#             db.commit()
        
#         return True
#     except Exception as e:
#         print(f"Error marking articles as seen: {e}")
#         db.rollback()
#         return False
#     finally:
#         db.close()




# def get_unseen_articles(user_auth_id: str, limit: int = 10, category: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
#     """
#     Get articles that user hasn't seen yet using efficient LEFT JOIN.
#     Always returns the most recent unseen articles (no offset needed).
    
#     Performance Benefits:
#     - Uses LEFT JOIN instead of subquery with IN clause
#     - Single database query instead of two separate queries
#     - Better performance with large datasets
#     - More efficient index usage
#     - Always returns freshest content (no pagination needed)
#     """
#     db = get_db()
#     try:
#         # Use LEFT JOIN to find articles that user hasn't seen
#         # This is much more efficient than using subqueries
#         query = db.query(Article).outerjoin(
#             SeenArticle, 
#             and_(
#                 Article.id == SeenArticle.article_id,
#                 SeenArticle.user_auth_id == user_auth_id
#             )
#         ).filter(
#             SeenArticle.id.is_(None)  # Articles where no seen record exists
#         )
        
#         # Filter by category if provided
#         if category:
#             query = query.filter(Article.category == category)
     
#         # Apply ordering and limit (no offset needed - always get freshest articles)
#         articles = query.order_by(desc(Article.created_at)).limit(limit).all()

#         total_count = articles.count()
#         # Convert to dictionaries
#         articles_data = [article_to_dict(article) for article in articles]
        
#         return articles_data, total_count
#     except Exception as e:
#         print(f"Error getting unseen articles: {e}")
#         return [], 0
#     finally:
#         db.close()