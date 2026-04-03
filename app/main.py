import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.articles import router as articles_router
from app.api.routes.users import router as users_router
from app.core.config import APP_ENV, APP_NAME, AUTO_CREATE_TABLES, DEBUG, get_settings
from app.db import create_db_and_tables

settings = get_settings()
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime_configuration()
    if AUTO_CREATE_TABLES:
        create_db_and_tables()
    yield


app = FastAPI(title=APP_NAME, debug=DEBUG, lifespan=lifespan)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": APP_ENV}


app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(users_router)
