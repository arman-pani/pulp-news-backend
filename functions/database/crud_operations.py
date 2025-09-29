from typing import List, Set
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from .postsql_db_connection import Article, get_db_session

# def check_if_article_exists(source_url: str) -> bool:
#     """Check if an article with this source_url already exists"""
#     db = get_db()
#     try:
#         article = db.query(Article).filter(Article.source_url == source_url).first()
#         return article is not None
#     except Exception as e:
#         print(f"Error checking if article exists: {e}")
#         return False
#     finally:
#         db.close()


def batch_check_duplicates(source_urls: List[str]) -> Set[str]:
    """Check for duplicate articles in batch using source URLs"""
    if not source_urls:
        return set()
    
    with get_db_session() as db:
        try:
            # Query database for existing source URLs in one go
            existing_articles = db.query(Article.source_url).filter(Article.source_url.in_(source_urls)).all()
            existing_urls = {article.source_url for article in existing_articles}
            return existing_urls
        except Exception as e:
            print(f"Error batch checking duplicates: {e}")
            return set()

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




