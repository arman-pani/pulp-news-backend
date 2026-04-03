# Configuration

The backend reads settings from `.env`.

## Required for local development

- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `JWT_SECRET_KEY`
- `FIREBASE_CREDENTIALS_JSON`

## Required outside development

- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `JWT_SECRET_KEY`
- `FIREBASE_CREDENTIALS_JSON`

## Supported settings

```env
DATABASE_URL=postgresql+psycopg://postgres:change-me@localhost:5432/odiya_news
OPENROUTER_API_KEY=
JWT_SECRET_KEY=change-me-jwt-secret
FIREBASE_CREDENTIALS_JSON=
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
- JWT settings are used for app authentication.
- Firebase Admin credentials are used only for FCM push delivery.
- The following defaults are now code-owned rather than env-driven: app name, app environment, debug flag, OpenRouter model slug, JWT algorithm, token TTLs, article limits, scrape batch/rate settings, and retention windows.
