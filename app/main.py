import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.articles import router as articles_router
from app.api.routes.internal import router as internal_router
from app.core.config import get_settings
from app.db import create_db_and_tables

settings = get_settings()
logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        create_db_and_tables()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


app.include_router(articles_router)
app.include_router(internal_router)
