import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-with-32-chars"
os.environ["OPENROUTER_API_KEY"] = "test-openrouter-key"
os.environ["FIREBASE_CREDENTIALS_JSON"] = '{"type":"service_account","project_id":"test-project"}'
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

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
            language="english",
        ),
        Article(
            source_name="OdishaBytes",
            source_url="https://example.com/sports-1",
            title="Sports headline",
            author="Author 2",
            content="Sports update covering a major Odisha event." * 3,
            category="Sports",
            language="english",
        ),
        Article(
            source_name="OdishaTV",
            source_url="https://example.com/politics-2",
            title="Political search match",
            author="Author 3",
            content="This article includes the keyword election in the content." * 3,
            category="Politics",
            language="english",
        ),
    ]
    session.add_all(articles)
    session.commit()
    for article in articles:
        session.refresh(article)
    return articles


@pytest.fixture
def multilang_articles(session: Session):
    """Seed one article per language for language-filter tests."""
    articles = [
        Article(
            source_name="Times of India",
            source_url="https://example.com/en-1",
            title="English headline",
            content="English content body covering national news." * 3,
            category="Politics",
            language="english",
        ),
        Article(
            source_name="Sambad",
            source_url="https://example.com/od-1",
            title="ଓଡ଼ିଆ ଶୀର୍ଷ ଖବର",
            content="ଓଡ଼ିଆ ଭାଷାରେ ଲେଖା ଏକ ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ଖବର।" * 3,
            category="General",
            language="odia",
        ),
        Article(
            source_name="ABP Ananda",
            source_url="https://example.com/bn-1",
            title="বাংলা সংবাদ শিরোনাম",
            content="বাংলা ভাষায় লেখা একটি গুরুত্বপূর্ণ সংবাদ।" * 3,
            category="General",
            language="bengali",
        ),
    ]
    session.add_all(articles)
    session.commit()
    for article in articles:
        session.refresh(article)
    return articles
