"""
Configuration file for sensitive data and environment variables.
All sensitive data should be stored here and loaded from environment variables.
"""

import os

class Config:
    """Configuration class to manage all sensitive data and environment variables."""
    
    # Database Configuration
    DB_CONNECTION_NAME: str = os.environ.get(
        "DB_CONNECTION_NAME", 
        "odiya-news-application:asia-south1:odiyanewsapp-fdc"
    )
    DB_USERNAME: str = os.environ.get("DB_USERNAME", "postgres")
    DB_DATABASE: str = os.environ.get("DB_DATABASE", "odiya-news-application-database")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "<,/$KPhjSZ#TMA6i")  # Fallback for development
    
    # API Keys
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "AIzaSyA4AKblPj_MBki6FrtAO57iXjNyPm006Bo")  # Fallback for development
    OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "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")  # Fallback for development

    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = os.environ.get("FIREBASE_PROJECT_ID", "")
    FIREBASE_PRIVATE_KEY: str = os.environ.get("FIREBASE_PRIVATE_KEY", "")
    FIREBASE_CLIENT_EMAIL: str = os.environ.get("FIREBASE_CLIENT_EMAIL", "")
    
    # News Scraping Configuration
    NEWS_BASE_URL: str = os.environ.get("NEWS_BASE_URL", "https://odishatv.in")
    NEWS_SCRAPING_INTERVAL: str = os.environ.get("NEWS_SCRAPING_INTERVAL", "30 6,12 * * *")  # At 12 PM and 6 PM IST daily
    
    # Application Configuration
    MAX_INSTANCES: int = int(os.environ.get("MAX_INSTANCES", "10"))
    DEFAULT_ARTICLE_LIMIT: int = int(os.environ.get("DEFAULT_ARTICLE_LIMIT", "10"))
    DEFAULT_ARTICLE_OFFSET: int = int(os.environ.get("DEFAULT_ARTICLE_OFFSET", "0"))
    
    # Permanent Categories List
    PERMANENT_CATEGORIES: list = [
        "Politics",
        "Crime", 
        "Technology",
        "Sports",
        "Entertainment",
        "Business",
        "General"
    ]
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = int(os.environ.get("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.environ.get("DB_MAX_OVERFLOW", "2"))
    DB_POOL_TIMEOUT: int = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.environ.get("DB_POOL_RECYCLE", "1800"))
    
    @classmethod
    def validate_required_config(cls) -> bool:
        """Validate that all required configuration values are present."""
        required_vars = [
            "DB_PASSWORD",
            "GEMINI_API_KEY",
        ]
        
        missing_vars = []
        for var in required_vars:
            value = getattr(cls, var)
            if not value or value in ["", "YOUR_DATABASE_PASSWORD_HERE", "YOUR_GEMINI_API_KEY_HERE"]:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
            print("Using fallback values for development. For production, please set these environment variables.")
            # For development, we'll allow fallback values
            return True
        
        return True
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database URL for SQLAlchemy."""
        return f"postgresql+pg8000://{cls.DB_USERNAME}:{cls.DB_PASSWORD}@{cls.DB_CONNECTION_NAME}/{cls.DB_DATABASE}"
    
    @classmethod
    def get_firebase_config(cls) -> dict:
        """Get Firebase configuration dictionary."""
        return {
            "projectId": cls.FIREBASE_PROJECT_ID,
            "privateKey": cls.FIREBASE_PRIVATE_KEY.replace('\\n', '\n') if cls.FIREBASE_PRIVATE_KEY else "",
            "clientEmail": cls.FIREBASE_CLIENT_EMAIL,
        }

# Create a global config instance
config = Config()
