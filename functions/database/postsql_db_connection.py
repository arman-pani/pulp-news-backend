from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import uuid
from config.config import config
from contextlib import contextmanager

Base = declarative_base()
SessionLocal = None
pool = None

def utc_now():
    return datetime.now(timezone.utc)

def init_engine():
    global pool, SessionLocal
    if pool is None:  # Initialize only once per instance
        connector = Connector()
        connection_name = config.DB_CONNECTION_NAME
        username = config.DB_USERNAME
        db = config.DB_DATABASE
        password = config.DB_PASSWORD

        def getconn():
            return connector.connect(
                connection_name,
                "pg8000",
                user=username,
                password=password,
                db=db
            )

        pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_timeout=config.DB_POOL_TIMEOUT,
            pool_recycle=config.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        pool.dialect.description_encoding = None
        SessionLocal = scoped_session(sessionmaker(bind=pool, autoflush=False, autocommit=False))
        
    return pool

def get_db():
    if SessionLocal is None:
        init_engine()
    return SessionLocal()

@contextmanager
def get_db_session():
    """
    Context manager for database session.
    Automatically commits on success, rolls back on exception, and closes session.
    """
    db = get_db()
    try:
        yield db  # Provide the session to the block using `with`
        db.commit()  # Commit only if everything went well
    except Exception:
        db.rollback()  # Rollback if any exception occurs
        raise
    finally:
        db.close()  # Always close the session


# Validate configuration before proceeding (only when actually using the database)
def validate_config_on_demand():
    """Validate configuration only when needed, not at import time"""
    if not config.validate_required_config():
        raise ValueError("Missing required configuration. Please check your environment variables.")

# Define User model
class User(Base):
    __tablename__ = 'users'

    auth_id = Column(String(255), unique=True, nullable=False, primary_key=True)  # Firebase auth ID
    created_at = Column(DateTime, default=utc_now)
    
    # Relationship to seen articles
    seen_articles = relationship("SeenArticle", back_populates="user")

    def __repr__(self):
        return f"<User(auth_id='{self.auth_id}')>"

# Define SeenArticle model
class SeenArticle(Base):
    __tablename__ = 'seen_articles'

    id = Column(Integer, primary_key=True)
    user_auth_id = Column(String(255), ForeignKey('users.auth_id'), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False)
    seen_at = Column(DateTime, default=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="seen_articles")
    article = relationship("Article", back_populates="seen_by")

    def __repr__(self):
        return f"<SeenArticle(user_auth_id={self.user_auth_id}, article_id={self.article_id})>"

# Define Article model
class Article(Base):
    __tablename__ = 'articles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(100), default='OdishaTV')
    source_url = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    author = Column(Text)
    published_at = Column(DateTime, default=utc_now)
    image_url = Column(Text)
    content = Column(Text, nullable=False)
    category = Column(String(50), default='General')
    created_at = Column(DateTime, default=utc_now)
    
    # Relationship to seen articles
    seen_by = relationship("SeenArticle", back_populates="article")

    def __repr__(self):
        return f"<Article(title='{self.title[:20]}...', category='{self.category}')>"

def test_database_connection():
    with get_db_session() as db:
        try:
            result = db.execute(sqlalchemy.text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Database connected: {version}")
            return True
        except Exception as e:
            print(f"❌ DB connection failed: {e}")
            return False

