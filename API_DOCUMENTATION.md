# API Documentation

Base URL: `https://<your-railway-domain>`

---

## Authentication

Guest access tokens are required for protected routes:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after `ACCESS_TOKEN_TTL_MINUTES` (default 15 min). Use `POST /auth/refresh` to obtain a new pair before expiry.

---

## Health

### `GET /health`

Returns the service status. Used by Railway as the health check endpoint.

**Response `200`**
```json
{ "status": "ok", "environment": "production" }
```

---

## Auth

### `POST /auth/guest`

Creates a new anonymous guest user and issues a token pair. No request body required.

**Response `200`**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<token>",
  "token_type": "bearer",
  "access_token_expires_in": 900,
  "refresh_token_expires_in": 2592000,
  "user_id": "guest_<uuid>"
}
```

---

### `POST /auth/refresh`

Rotates the refresh token. The old token is invalidated; both a new access token and refresh token are returned.

**Request body**
```json
{ "refresh_token": "<token>" }
```

**Response `200`** — same shape as `POST /auth/guest`

---

### `POST /auth/logout`

Revokes the refresh token, ending the session.

**Request body**
```json
{ "refresh_token": "<token>" }
```

**Response `200`**
```json
{ "success": true, "message": "Refresh token revoked successfully" }
```

---

## Articles

### `GET /articles/unseen` 🔒

Returns articles not yet seen by the authenticated user and marks them as seen.

**Query params**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | `10` | Max articles to return (1–100) |
| `category` | string | — | Filter by category |

**Response `200`**
```json
{
  "success": true,
  "articles": [ /* ArticleRead[] */ ],
  "limit": 10,
  "category": null,
  "user_id": "guest_<uuid>"
}
```

---

### `GET /articles/by-category`

Returns articles filtered by category, with pagination.

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `category` | string | ✅ | — | e.g. `Politics`, `Sports` |
| `limit` | int | | `10` | Max articles (1–100) |
| `offset` | int | | `0` | Pagination offset (≥ 0) |

**Response `200`**
```json
{
  "success": true,
  "articles": [ /* ArticleRead[] */ ],
  "category": "Politics",
  "limit": 10,
  "offset": 0
}
```

---

### `GET /articles/search`

Full-text fuzzy search across article titles and content.

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `q` | string | ✅ | — | Search query (min length 1) |
| `limit` | int | | `10` | Max articles (1–100) |
| `offset` | int | | `0` | Pagination offset (≥ 0) |
| `category` | string | | — | Narrow to a specific category |

**Response `200`**
```json
{
  "success": true,
  "articles": [ /* ArticleRead[] */ ],
  "query": "odisha flood",
  "category": null,
  "limit": 10,
  "offset": 0
}
```

---

### `GET /articles/bundled`

Returns the latest articles grouped by every permanent category in a single request.

**Query params**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit_per_category` | int | `5` | Articles per category (1–50) |

**Response `200`**
```json
{
  "success": true,
  "total_categories": 7,
  "limit_per_category": 5,
  "categories": {
    "Politics": {
      "articles": [ /* ArticleRead[] */ ],
      "total": 5,
      "limit": 5
    },
    "Sports": { "..." }
  }
}
```

---

## Article object

All article responses share the same `ArticleRead` shape:

```json
{
  "id": "<uuid>",
  "source_name": "Sambad",
  "source_url": "https://...",
  "title": "...",
  "author": "...",
  "image_url": "https://...",
  "content": "...",
  "category": "Politics",
  "published_at": "2026-04-02T08:00:00Z",
  "created_at": "2026-04-02T08:05:12Z"
}
```

`author` and `image_url` may be `null`.

---

## Users

### `POST /users/me/fcm-token` 🔒

Register or update the FCM device token for the authenticated user.

**Request body**
```json
{ "fcm_token": "<device-token>" }
```

**Response `200`**
```json
{ "success": true, "message": "FCM token updated successfully" }
```

---

### `POST /users/me/notification-preference` 🔒

Enable or disable push notifications. Optionally update the FCM token at the same time.

**Request body**
```json
{
  "is_enabled": true,
  "fcm_token": "<device-token>"
}
```

`fcm_token` is optional — omit to leave the existing token unchanged.

**Response `200`**
```json
{
  "success": true,
  "message": "Notifications enabled successfully",
  "is_notification_enabled": true
}
```

---

## Push notifications

- Only users with `is_notification_enabled = true` **and** a valid `fcm_token` receive pushes.
- The `scrape_and_notify` cron job sends one notification per run featuring the most recently saved article.
- If delivery fails due to an invalid or expired FCM token, the token is automatically cleared and notifications are disabled for that user.

---

## Permanent categories

The following category values are always present in the system:

`Politics` · `Crime` · `Technology` · `Sports` · `Entertainment` · `Business` · `General`

---

## Error responses

All errors follow FastAPI's standard shape:

```json
{ "detail": "Error message here" }
```

| Status | Meaning |
|--------|---------|
| `401` | Missing or invalid access token |
| `422` | Validation error (missing required field, wrong type, etc.) |
| `500` | Unexpected server error |
