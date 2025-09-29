# Test Endpoints - Quick Reference

**⚠️ FOR TESTING ONLY - NO AUTHENTICATION REQUIRED**

## Available Test Endpoints

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `/test_health_check_endpoint` | Basic health check | ❌ No |
| `/test_database_connection_endpoint` | Test database connection | ❌ No |
| `/test_get_unseen_articles_endpoint` | Get unseen articles | ❌ No |
| `/test_get_articles_by_category_endpoint` | Get articles by category | ❌ No |
| `/test_search_articles_endpoint` | Search articles | ❌ No |
| `/test_get_bundled_articles_endpoint` | Get bundled articles | ❌ No |
| `/test_manual_scraping_endpoint` | Manually trigger news scraping | ❌ No |

## Quick Test Commands

```bash
# Health check
curl "https://your-function-url/test_health_check_endpoint"

# Database test
curl "https://your-function-url/test_database_connection_endpoint"

# Get 5 unseen articles
curl "https://your-function-url/test_get_unseen_articles_endpoint?limit=5"

# Get Politics articles
curl "https://your-function-url/test_get_articles_by_category_endpoint?category=Politics&limit=10"

# Search for "odisha"
curl "https://your-function-url/test_search_articles_endpoint?q=odisha&limit=5"

# Get bundled articles
curl "https://your-function-url/test_get_bundled_articles_endpoint?limit_per_category=3"

# Manually trigger news scraping
curl "https://your-function-url/test_manual_scraping_endpoint"
```

## Response Format

All test endpoints return responses with `"test_mode": true`:

```json
{
  "data": "...",
  "test_mode": true,
  "success": true
}
```

## Test User ID

All test endpoints use: `"test_user_id": "test_user_123"`

## Security Warning

🚨 **NEVER USE IN PRODUCTION** 🚨

These endpoints bypass all authentication and should only be used for:
- Development testing
- Integration testing  
- Debugging
- Health checks
