# API Authentication Guide - Odia GenAI Backend

All API endpoints now require Firebase authentication. This document explains how to authenticate and use the API.

## Authentication

All endpoints require a valid Firebase ID token in the `Authorization` header.

### Header Format
```
Authorization: Bearer <firebase_id_token>
```

### Getting a Firebase ID Token

#### For Web Applications
```javascript
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();
```

#### For Mobile Applications (React Native)
```javascript
import auth from '@react-native-firebase/auth';

const user = auth().currentUser;
const idToken = await user.getIdToken();
```

#### For Server-to-Server
Use Firebase Admin SDK to create custom tokens or verify existing tokens.

## API Endpoints

All endpoints return JSON responses and require authentication.

### 1. Get Unseen Articles
**Endpoint:** `GET /get_unseen_articles`

**Description:** Get articles that the authenticated user hasn't seen yet.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Query Parameters:**
- `limit` (optional): Number of articles to return (default: 10)
- `category` (optional): Filter by specific category

**Example Request:**
```bash
curl -X GET "https://your-function-url/get_unseen_articles?limit=5&category=Politics" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json"
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
  "success": true
}
```

### 2. Get Articles by Category
**Endpoint:** `GET /get_articles_by_category`

**Description:** Get articles filtered by category with pagination.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Query Parameters:**
- `category` (required): Category to filter by
- `limit` (optional): Number of articles to return (default: 10)
- `offset` (optional): Number of articles to skip (default: 0)

**Example Request:**
```bash
curl -X GET "https://your-function-url/get_articles_by_category?category=Politics&limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
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
**Endpoint:** `GET /search_articles`

**Description:** Search articles by title and content.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of articles to return (default: 10)
- `offset` (optional): Number of articles to skip (default: 0)
- `category` (optional): Filter by specific category

**Example Request:**
```bash
curl -X GET "https://your-function-url/search_articles?q=odisha&limit=5&category=Politics" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json"
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
  "success": true
}
```

### 4. Get Bundled Articles
**Endpoint:** `GET /get_bundled_articles`

**Description:** Get articles from each category bundled together.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Query Parameters:**
- `limit_per_category` (optional): Number of articles per category (default: 5)

**Example Request:**
```bash
curl -X GET "https://your-function-url/get_bundled_articles?limit_per_category=3" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json"
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
  "success": true
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Missing or invalid Authorization header",
  "success": false
}
```

```json
{
  "error": "Invalid or expired token",
  "success": false
}
```

### 400 Bad Request
```json
{
  "error": "category parameter is required",
  "success": false
}
```

```json
{
  "error": "query parameter 'q' is required",
  "success": false
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to get or create user",
  "success": false
}
```

```json
{
  "error": "Error fetching articles: Detailed error message",
  "success": false
}
```

## Security Features

1. **Token Validation**: All requests are validated against Firebase Auth
2. **User Management**: Users are automatically created/retrieved on first request
3. **Consistent Error Handling**: All endpoints return consistent error responses
4. **Rate Limiting**: Firebase Functions provide built-in rate limiting
5. **CORS Support**: Proper CORS headers for web applications

## Client Implementation Examples

### JavaScript/TypeScript
```typescript
class OdiaNewsAPI {
  private baseUrl: string;
  private auth: any;

  constructor(baseUrl: string, auth: any) {
    this.baseUrl = baseUrl;
    this.auth = auth;
  }

  private async getAuthHeaders() {
    const token = await this.auth.currentUser?.getIdToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getUnseenArticles(limit = 10, category?: string) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (category) params.append('category', category);
    
    const response = await fetch(`${this.baseUrl}/get_unseen_articles?${params}`, {
      headers: await this.getAuthHeaders()
    });
    
    return response.json();
  }

  async searchArticles(query: string, limit = 10, category?: string) {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    if (category) params.append('category', category);
    
    const response = await fetch(`${this.baseUrl}/search_articles?${params}`, {
      headers: await this.getAuthHeaders()
    });
    
    return response.json();
  }
}
```

### Python
```python
import requests
import firebase_admin
from firebase_admin import auth

class OdiaNewsAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.app = firebase_admin.initialize_app()
    
    def get_auth_headers(self, id_token: str):
        return {
            'Authorization': f'Bearer {id_token}',
            'Content-Type': 'application/json'
        }
    
    def get_unseen_articles(self, id_token: str, limit=10, category=None):
        params = {'limit': limit}
        if category:
            params['category'] = category
        
        response = requests.get(
            f"{self.base_url}/get_unseen_articles",
            headers=self.get_auth_headers(id_token),
            params=params
        )
        return response.json()
```

## Migration Notes

- **Breaking Change**: All endpoints now require authentication
- **User Creation**: Users are automatically created on first authenticated request
- **Backward Compatibility**: API response format remains the same
- **Error Handling**: Enhanced error responses for authentication failures

## Testing

Use tools like Postman or curl to test the endpoints:

```bash
# Test with invalid token
curl -X GET "https://your-function-url/get_unseen_articles" \
  -H "Authorization: Bearer invalid_token"

# Expected response: 401 Unauthorized
```

```bash
# Test with valid token
curl -X GET "https://your-function-url/get_unseen_articles" \
  -H "Authorization: Bearer YOUR_VALID_FIREBASE_TOKEN"

# Expected response: 200 OK with articles
```
