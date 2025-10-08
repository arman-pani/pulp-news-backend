"""
Main entry point for Odia GenAI Backend
This file serves as the entry point for Firebase Functions
"""
from api.main import (
    get_unseen_articles_endpoint,
    get_articles_by_category_endpoint,
    search_articles_endpoint,
    get_bundled_articles_endpoint,
    update_fcm_token_endpoint,
    set_notification_preference_endpoint,
)

# Test endpoints disabled for production
# from api.test_endpoints import (
#     trigger_notification_scheduler,
#     test_get_unseen_articles_endpoint,
#     test_get_articles_by_category_endpoint,
#     test_search_articles_endpoint,
#     test_get_bundled_articles_endpoint,
#     test_manual_scraping_endpoint
# )

# Import cron job
from cron.cron_scraper import scheduled_news_scraping

from cron.notification_cron import scheduled_article_notifications

# Make functions available for Firebase Functions
__all__ = [
    # Production endpoints (with authentication)
    'get_unseen_articles_endpoint',
    'get_articles_by_category_endpoint',
    'search_articles_endpoint', 
    'get_bundled_articles_endpoint',
    'update_fcm_token_endpoint',
    'set_notification_preference_endpoint',

    # # Test endpoints disabled for production
    # 'test_get_unseen_articles_endpoint',
    # 'test_get_articles_by_category_endpoint',
    # 'test_search_articles_endpoint',
    # 'test_get_bundled_articles_endpoint',
    # 'test_manual_scraping_endpoint',

    # Test Notification endpoints
    # 'trigger_notification_scheduler',
    # 'test_simple_fcm_notification',

    # Cron job
    'scheduled_news_scraping',
    'scheduled_article_notifications'
]
