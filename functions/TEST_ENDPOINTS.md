# Test Endpoints - Odia GenAI Backend

**⚠️ WARNING: These endpoints are for TESTING and DEVELOPMENT ONLY. They bypass authentication and should NOT be used in production.**

## Overview

Test endpoints provide the same functionality as production endpoints but without Firebase authentication requirements. This makes them ideal for:

- **Development Testing**: Quick API testing during development
- **Integration Testing**: Automated testing without auth setup
- **Debugging**: Troubleshooting API issues
- **Health Checks**: Verifying service status

## Test Endpoints

### 1. Health Check
**Endpoint**: `GET /test_health_check_endpoint`

**Description**: Basic health check to verify the service is running.

**Authentication**: None required

**Example Request:**
```bash
curl -X GET "https://your-function-url/test_health_check_endpoint"
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Odia GenAI Backend is running",
  "test_mode": true,
  "success": true
}
```

### 2. Database Connection Test
**Endpoint**: `GET /test_database_connection_endpoint`

**Description**: Test if the database connection is working.

**Authentication**: None required

**Example Request:**
```bash
curl -X GET "https://your-function-url/test_database_connection_endpoint"
```

**Response:**
```json
{
  "database_connection": true,
  "test_mode": true,
  "success": true
}
```

### 3. Test Get Unseen Articles
**Endpoint**: `GET /test_get_unseen_articles_endpoint`

**Description**: Get articles that a test user hasn't seen yet (uses test user ID).

**Authentication**: None required

**Query Parameters:**
- `limit` (optional): Number of articles to return (default: 10)
- `category` (optional): Filter by specific category

**Example Request:**
```bash
curl -X GET "https://your-function-url/test_get_unseen_articles_endpoint?limit=5&category=Politics"
```

**Response:**
```json
{
  "articles": [
    {
      "id": "uuid-here",
      "title": "Article Title",
      "content": "Article content...",
      "category": "Politics",
      "source_name": "OdishaTV",
      "published_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 25,
  "limit": 5,
  "category": "Politics",
  "test_mode": true,
  "test_user_id": "test_user_123",
  "success": true
}
```

### 4. Test Get Articles by Category
**Endpoint**: `GET /test_get_articles_by_category_endpoint`

**Description**: Get articles filtered by category with pagination.

**Authentication**: None required

**Query Parameters:**
- `category` (required): Category to filter by
- `limit` (optional): Number of articles to return (default: 10)
- `offset` (optional): Number of articles to skip (default: 0)

**Example Request:**
```bash
curl -X GET "https://your-function-url/test_get_articles_by_category_endpoint?category=Politics&limit=10&offset=0"
```

**Response:**
```json
{
  "articles": [...],
  "total": 50,
  "category": "Politics",
  "limit": 10,
  "offset": 0,
  "test_mode": true,
  "success": true
}
```

### 5. Test Search Articles
**Endpoint**: `GET /test_search_articles_endpoint`

**Description**: Search articles by title and content.

**Authentication**: None required

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of articles to return (default: 10)
- `offset` (optional): Number of articles to skip (default: 0)
- `category` (optional): Filter by specific category

**Example Request:**
```bash
curl -X GET "https://your-function-url/test_search_articles_endpoint?q=odisha&limit=5&category=Politics"
```

**Response:**
```json
{
  "articles": [...],
  "total": 15,
  "query": "odisha",
  "category": "Politics",
  "limit": 5,
  "offset": 0,
  "test_mode": true,
  "success": true
}
```

### 6. Test Get Bundled Articles
**Endpoint**: `GET /test_get_bundled_articles_endpoint`

**Description**: Get articles from each category bundled together.

**Authentication**: None required

**Query Parameters:**
- `limit_per_category` (optional): Number of articles per category (default: 5)

**Example Request:**
```bash
curl -X GET "https://your-function-url/test_get_bundled_articles_endpoint?limit_per_category=3"
```

**Response:**
```json
{
  "categories": {
    "Politics": {
      "articles": [...],
      "total": 25,
      "limit": 3
    },
    "Sports": {
      "articles": [...],
      "total": 15,
      "limit": 3
    }
  },
  "total_categories": 2,
  "limit_per_category": 3,
  "test_mode": true,
  "success": true
}
```

## Key Differences from Production Endpoints

| Feature | Production Endpoints | Test Endpoints |
|---------|---------------------|----------------|
| **Authentication** | Required (Firebase token) | None required |
| **User Management** | Real user creation/retrieval | Uses test user ID |
| **Response Format** | Standard format | Includes `test_mode: true` |
| **Error Handling** | Full auth error handling | Simplified error handling |
| **Use Case** | Production traffic | Development/testing only |

## Test User ID

All test endpoints use a hardcoded test user ID: `"test_user_123"`

This means:
- No real user data is affected
- All test requests use the same user context
- Perfect for consistent testing scenarios

## Development Workflow

### 1. Local Development
```bash
# Test health check
curl http://localhost:5001/your-project/us-central1/test_health_check_endpoint

# Test database connection
curl http://localhost:5001/your-project/us-central1/test_database_connection_endpoint

# Test API functionality
curl "http://localhost:5001/your-project/us-central1/test_get_unseen_articles_endpoint?limit=5"
```

### 2. Integration Testing
```python
import requests

def test_api_endpoints():
    base_url = "https://your-function-url"
    
    # Test health check
    response = requests.get(f"{base_url}/test_health_check_endpoint")
    assert response.status_code == 200
    
    # Test database connection
    response = requests.get(f"{base_url}/test_database_connection_endpoint")
    assert response.json()["database_connection"] == True
    
    # Test article retrieval
    response = requests.get(f"{base_url}/test_get_unseen_articles_endpoint?limit=5")
    assert response.status_code == 200
    assert response.json()["test_mode"] == True
```

### 3. Postman Collection
Create a Postman collection with all test endpoints for easy API testing.

## Security Considerations

**⚠️ IMPORTANT SECURITY NOTES:**

1. **Never Deploy to Production**: These endpoints should be removed or disabled in production
2. **No Authentication**: Anyone can access these endpoints
3. **Test Data Only**: Uses test user ID, not real user data
4. **Rate Limiting**: Consider implementing rate limiting for test endpoints
5. **Monitoring**: Monitor usage to ensure they're not being used in production

## Deployment Strategy

### Development Environment
- Deploy all endpoints including test endpoints
- Use test endpoints for development and testing

### Production Environment
- Deploy only production endpoints
- Remove or disable test endpoints
- Use environment variables to control endpoint availability

### Example Environment Control
```python
# In test_endpoints.py
import os

if os.getenv('ENVIRONMENT') == 'production':
    # Disable test endpoints in production
    pass
```

## Monitoring and Logging

All test endpoints include `"test_mode": true` in their responses, making it easy to:
- Identify test endpoint usage in logs
- Monitor for production usage of test endpoints
- Filter test traffic from production analytics

## 7. Test Manual Scraping Endpoint

**Endpoint:** `test_manual_scraping_endpoint`  
**Method:** GET  
**Authentication:** None required (test mode)

### Description
Manually trigger news scraping for testing purposes. This endpoint allows you to manually trigger the scraping process without waiting for the scheduled cron job.

### Query Parameters
None

### Example Usage

```bash
curl "https://us-central1-odiya-news-application.cloudfunctions.net/test_manual_scraping_endpoint"
```

### Response Format
```json
{
  "message": "Manual scraping completed successfully",
  "articles_saved": 15,
  "test_mode": true,
  "success": true
}
```

### Error Response
```json
{
  "error": "Error in manual scraping: [error details]",
  "test_mode": true,
  "success": false
}
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Use `test_database_connection_endpoint` to verify database access
   - Check Cloud SQL instance status
   - Verify connection configuration

2. **Empty Article Responses**
   - Check if articles exist in database
   - Verify scraping job has run
   - Check category filters

3. **Function Timeout**
   - Test endpoints have same timeout as production
   - Check database query performance
   - Monitor function logs

### Debug Commands
```bash
# Check service health
curl "https://your-function-url/test_health_check_endpoint"

# Test database
curl "https://your-function-url/test_database_connection_endpoint"

# Get sample articles
curl "https://your-function-url/test_get_unseen_articles_endpoint?limit=1"

# Test search
curl "https://your-function-url/test_search_articles_endpoint?q=test"
```

## Best Practices

1. **Use for Development Only**: Never use test endpoints in production
2. **Consistent Testing**: Use the same test user ID for consistent results
3. **Monitor Usage**: Track test endpoint usage to prevent production misuse
4. **Document Changes**: Update test endpoints when production endpoints change
5. **Clean Up**: Remove test endpoints before production deployment
