# API Documentation

## Authentication

Protected routes require an app-issued guest access token:

```http
Authorization: Bearer <access_token>
```

Access tokens are issued by the backend. Refresh tokens are returned in JSON responses and rotated on every refresh.

## Auth routes

### `POST /auth/guest`

Creates a guest user and returns:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "access_token_expires_in": 900,
  "refresh_token_expires_in": 2592000,
  "user_id": "guest_..."
}
```

### `POST /auth/refresh`

```json
{
  "refresh_token": "..."
}
```

### `POST /auth/logout`

```json
{
  "refresh_token": "..."
}
```

## Public article routes

### `GET /articles/by-category`

Query params:
- `category` required
- `limit` optional
- `offset` optional

### `GET /articles/search`

Query params:
- `q` required
- `limit` optional
- `offset` optional
- `category` optional

### `GET /articles/bundled`

Query params:
- `limit_per_category` optional

## Authenticated user routes

### `GET /articles/unseen`

Returns the latest unseen articles for the authenticated guest user and marks them as seen.

### `POST /users/me/fcm-token`

Request body:

```json
{
  "fcm_token": "device-token"
}
```

### `POST /users/me/notification-preference`

Request body:

```json
{
  "is_enabled": true,
  "fcm_token": "device-token"
}
```

## Internal job routes

These routes are protected with:

```http
X-Internal-Api-Token: <internal_token>
```

### `POST /internal/jobs/scrape`

```json
{
  "schedule_name": "8am"
}
```

### `POST /internal/jobs/cleanup`

```json
{
  "days_old": 7
}
```

### `POST /internal/jobs/notifications`

```json
{
  "minutes_back": 15
}
```

## Notification behavior

- FCM tokens are stored on the authenticated user record.
- Only users with `is_notification_enabled=true` and a valid `fcm_token` receive pushes.
- The notification job selects the most recent article created within the configured delay window.
- Invalid FCM tokens are cleared and notifications are disabled for those users.
