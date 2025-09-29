# Odia News Application Backend API Documentation

This backend provides a comprehensive API for the Odia news application, including web scraping, article summarization, user management, and article retrieval with Firebase authentication.

## Features

- **Automated News Scraping**: Cron job runs every 3 hours to scrape Odisha TV news
- **Article Summarization**: AI-powered article summarization using Google GenAI
- **User Management**: Firebase anonymous authentication with user tracking
- **Article Tracking**: Track which articles users have seen
- **Search & Filter**: Search articles by content and filter by category
- **Pagination**: All endpoints support pagination with limit and offset

## Database Schema

### Articles Table
- `id`: Primary key
- `source_id`: Unique identifier from source website
- `source_name`: Name of the news source (default: 'OdishaTV')
- `source_url`: Original article URL
- `title`: Article title
- `author`: Article author
- `published_at`: Publication date
- `image_url`: Article image URL
- `content`: Full article content
- `category`: Article category
- `created_at`: Record creation timestamp

### Users Table
- `id`: Primary key
- `auth_id`: Firebase authentication ID (unique)
- `created_at`: User creation timestamp

### Seen Articles Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `article_id`: Foreign key to articles table
- `seen_at`: When the article was marked as seen

## API Endpoints

**⚠️ IMPORTANT: All endpoints now require Firebase authentication. See [API_AUTHENTICATION.md](functions/API_AUTHENTICATION.md) for detailed authentication guide.**

### 1. Get Unseen Articles
**Endpoint**: `GET /get_unseen_articles_endpoint`

**Description**: Get articles that the authenticated user hasn't seen yet. **Note**: All returned articles are automatically marked as "seen" in the database.

**Authentication**: Required - Firebase ID token

**Headers**:
- `Authorization: Bearer <firebase_token>`

**Query Parameters**:
- `limit` (optional): Number of articles to return (default: 10)
- `category` (optional): Filter by category

**Response**:
```json
{
  "articles": [...],
  "total": 150,
  "limit": 10,
  "success": true
}
```

**Important**: 
- This endpoint automatically marks all returned articles as "seen" for the authenticated user
- Subsequent calls will not return these articles again
- Always returns the most recent unseen articles (no pagination/offset needed)

### 2. Get Articles by Category
**Endpoint**: `GET /get_articles_by_category_endpoint`

**Description**: Get articles filtered by category with pagination.

**Authentication**: Required - Firebase ID token

**Headers**:
- `Authorization: Bearer <firebase_token>`

**Query Parameters**:
- `category` (required): Category name
- `limit` (optional): Number of articles to return (default: 10)
- `offset` (optional): Number of articles to skip (default: 0)

**Response**:
```json
{
  "articles": [...],
  "total": 50,
  "category": "Politics",
  "limit": 10,
  "offset": 0,
  "success": true
}
```

### 3. Search Articles
**Endpoint**: `GET /search_articles_endpoint`

**Description**: Search articles by title and content with pagination.

**Authentication**: Required - Firebase ID token

**Headers**:
- `Authorization: Bearer <firebase_token>`

**Query Parameters**:
- `q` (required): Search query
- `limit` (optional): Number of articles to return (default: 10)
- `offset` (optional): Number of articles to skip (default: 0)
- `category` (optional): Filter by category

**Response**:
```json
{
  "articles": [...],
  "total": 25,
  "query": "election",
  "category": "Politics",
  "limit": 10,
  "offset": 0,
  "success": true
}
```

### 4. Get Bundled Articles by Category
**Endpoint**: `GET /get_bundled_articles_endpoint`

**Description**: Fetch articles from each category and bundle them together. This endpoint provides a comprehensive view of all categories with their latest articles in a single request.

**Authentication**: Required - Firebase ID token

**Headers**:
- `Authorization: Bearer <firebase_token>`

**Query Parameters**:
- `limit_per_category` (optional): Number of articles to return per category (default: 5)

**Response**:
```json
{
  "categories": {
    "Politics": {
      "articles": [...],
      "total": 25,
      "limit": 5
    },
    "Sports": {
      "articles": [...],
      "total": 18,
      "limit": 5
    },
    "Technology": {
      "articles": [...],
      "total": 12,
      "limit": 5
    }
  },
  "total_categories": 3,
  "limit_per_category": 5,
  "success": true
}
```

**Use Cases**:
- Homepage/dashboard views showing latest articles from all categories
- Category overview pages
- Bulk data loading for mobile apps
- Analytics and reporting


## Scheduled Functions

### Automated News Scraping
- **Function**: `scheduled_news_scraping`
- **Schedule**: Every 3 hours (`0 */3 * * *`)
- **Description**: Automatically scrapes and processes new articles from Odisha TV

## Authentication

All user-specific endpoints require Firebase authentication:

1. **Firebase Anonymous Sign-in**: Users sign in anonymously using Firebase
2. **Token Verification**: Each request includes a Firebase ID token in the Authorization header
3. **User Creation**: Users are automatically created in the database on first API call
4. **Token Format**: `Authorization: Bearer <firebase_id_token>`

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "success": false
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing parameters)
- `401`: Unauthorized (invalid/missing token)
- `500`: Internal Server Error

## Deployment

This backend is designed for Firebase Functions deployment:

1. **Database**: Google Cloud SQL (PostgreSQL)
2. **Functions**: Firebase Functions
3. **Authentication**: Firebase Authentication
4. **Scheduling**: Firebase Functions Scheduler

## Environment Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Firebase project and enable:
   - Firebase Functions
   - Firebase Authentication (Anonymous)
   - Cloud SQL (PostgreSQL)

3. Deploy functions:
```bash
firebase deploy --only functions
```

## Usage Examples

### Get unseen articles for authenticated user (automatically marks them as seen):
```bash
curl -X GET "https://your-region-your-project.cloudfunctions.net/get_unseen_articles_endpoint?limit=5&category=Politics" \
  -H "Authorization: Bearer <firebase_token>"
```

### Search articles:
```bash
curl -X GET "https://your-region-your-project.cloudfunctions.net/search_articles_endpoint?q=election&limit=10&offset=0" \
  -H "Authorization: Bearer <firebase_token>"
```

### Get articles by category:
```bash
curl -X GET "https://your-region-your-project.cloudfunctions.net/get_articles_by_category_endpoint?category=Politics&limit=10&offset=0" \
  -H "Authorization: Bearer <firebase_token>"
```

### Get bundled articles from all categories:
```bash
curl -X GET "https://your-region-your-project.cloudfunctions.net/get_bundled_articles_endpoint?limit_per_category=3" \
  -H "Authorization: Bearer <firebase_token>"
```

## Categories

The system uses a predefined set of categories for article classification:

- **Politics**: Political news and government affairs
- **Crime**: Crime reports and legal matters  
- **Technology**: Tech news and innovations
- **Sports**: Sports news and events
- **Entertainment**: Entertainment and cultural news
- **Business**: Business and economic news
- **General**: General news and other topics

These categories are used consistently across the system for article classification and filtering.

## Notes

- All timestamps are in ISO 8601 format
- Pagination is 0-indexed (offset=0 means first page)
- Article content includes both original and summarized text
- Categories are automatically assigned during scraping using AI
- The system prevents duplicate articles using source_id
