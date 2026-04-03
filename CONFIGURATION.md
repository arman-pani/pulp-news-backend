# Configuration

The backend reads settings from `.env`.

## Required for local development

- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `JWT_SECRET_KEY`
- `FIREBASE_CREDENTIALS_JSON` only if FCM notifications are used

## Required outside development

- `DATABASE_URL`
- `JWT_SECRET_KEY`

## Supported settings

```env
APP_NAME=Odia News Backend
APP_ENV=development
DEBUG=false

DATABASE_URL=postgresql+psycopg://postgres:change-me@localhost:5432/odiya_news
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free
JWT_SECRET_KEY=change-me-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=30

FIREBASE_CREDENTIALS_JSON=
FIREBASE_PROJECT_ID=

AUTO_CREATE_TABLES=false
BATCH_SIZE=10
RATE_LIMIT_DELAY=2
MAX_ARTICLE_AGE_DAYS=2
ARTICLE_RETENTION_DAYS=7
SCRAPER_TIMEOUT_SECONDS=30
MAX_ARTICLES_PER_SOURCE=10
DEFAULT_ARTICLE_LIMIT=10
DEFAULT_ARTICLE_OFFSET=0
```

## Migrations

Use Alembic for schema management:

```bash
alembic upgrade head
```

For local development, start PostgreSQL first:

```bash
docker compose up -d
docker compose ps
```

You can validate the database connection with:

```bash
PGPASSWORD=change-me psql -h localhost -U postgres -d odiya_news -c '\dt'
```

## Runtime notes

- Docker Compose is the default local Postgres workflow for this repo.
- `AUTO_CREATE_TABLES` should stay `false` for local Postgres and production-style environments; use Alembic instead.
- JWT settings are used for app authentication.
- Firebase Admin credentials are used only for FCM push delivery.
