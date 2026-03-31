import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["INTERNAL_API_TOKEN"] = "test-internal-token"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.deps import get_db_session
from app.main import app
from app.models import Article


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def guest_tokens(client: TestClient):
    response = client.post("/auth/guest")
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def seeded_articles(session: Session):
    articles = [
        Article(
            source_name="OdishaTV",
            source_url="https://example.com/politics-1",
            title="Politics headline",
            author="Author 1",
            content="Election and assembly coverage with detailed update." * 3,
            category="Politics",
        ),
        Article(
            source_name="OdishaBytes",
            source_url="https://example.com/sports-1",
            title="Sports headline",
            author="Author 2",
            content="Sports update covering a major Odisha event." * 3,
            category="Sports",
        ),
        Article(
            source_name="OdishaTV",
            source_url="https://example.com/politics-2",
            title="Political search match",
            author="Author 3",
            content="This article includes the keyword election in the content." * 3,
            category="Politics",
        ),
    ]
    session.add_all(articles)
    session.commit()
    for article in articles:
        session.refresh(article)
    return articles
