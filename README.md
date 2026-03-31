# Odia News Backend

FastAPI backend for scraping Odisha news, summarizing articles with an LLM, storing them in PostgreSQL, and serving article APIs with guest JWT auth and FCM notifications.

## Stack

- FastAPI
- SQLModel + PostgreSQL
- Alembic migrations
- Guest JWT access + refresh tokens
- Firebase Cloud Messaging
- Protected internal job endpoints for scrape, cleanup, and delayed notifications

## Local setup

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Copy `.env.example` to `.env` if needed and fill in:
   - `OPENROUTER_API_KEY`
   - `INTERNAL_API_TOKEN`
   - `JWT_SECRET_KEY`
   - `FIREBASE_CREDENTIALS_JSON` or `FIREBASE_CREDENTIALS_PATH` if you want FCM notifications
3. Start local PostgreSQL with Docker Compose:
   ```bash
   docker compose up -d
   ```
4. Wait for the database to become healthy:
   ```bash
   docker compose ps
   ```
5. Run migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the app:
   ```bash
   uvicorn main:app --reload
   ```

## Local database

- Docker Compose is the default local Postgres path.
- Host: `localhost`
- Port: `5432`
- Database: `odiya_news`
- User: `postgres`
- Password: `change-me`

### Verify the database manually

```bash
PGPASSWORD=change-me psql -h localhost -U postgres -d odiya_news -c '\dt'
```

### Stop the local database

```bash
docker compose down
```

## Main routes

- `GET /health`
- `POST /auth/guest`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /articles/unseen`
- `GET /articles/by-category`
- `GET /articles/search`
- `GET /articles/bundled`
- `POST /users/me/fcm-token`
- `POST /users/me/notification-preference`
- `POST /internal/jobs/scrape`
- `POST /internal/jobs/cleanup`
- `POST /internal/jobs/notifications`

## Scheduler sequence

1. Trigger `/internal/jobs/scrape` on the configured scrape windows.
2. Trigger `/internal/jobs/notifications` after the configured delay window.
3. Trigger `/internal/jobs/cleanup` on the retention schedule.

## Test

```bash
pytest -q
```
