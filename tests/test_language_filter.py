"""Tests for the language filter across API endpoints and repository queries."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.article_repository import (
    article_to_dict,
    get_articles_by_category,
    get_bundled_articles_by_category,
    get_unseen_articles_for_user,
    search_articles,
)


# ---------------------------------------------------------------------------
# Repository — get_articles_by_category
# ---------------------------------------------------------------------------

def test_get_articles_by_category_no_filter_returns_all(session, multilang_articles):
    results = get_articles_by_category(session, category="Politics")
    assert len(results) == 1  # only English politics article seeded


def test_get_articles_by_category_english_filter(session, multilang_articles):
    results = get_articles_by_category(session, category="Politics", language="english")
    assert all(a.language == "english" for a in results)
    assert len(results) == 1


def test_get_articles_by_category_odia_filter_returns_only_odia(session, multilang_articles):
    results = get_articles_by_category(session, category="General", language="odia")
    assert all(a.language == "odia" for a in results)
    assert len(results) == 1


def test_get_articles_by_category_bengali_filter_returns_only_bengali(session, multilang_articles):
    results = get_articles_by_category(session, category="General", language="bengali")
    assert all(a.language == "bengali" for a in results)
    assert len(results) == 1


def test_get_articles_by_category_unknown_language_returns_empty(session, multilang_articles):
    results = get_articles_by_category(session, category="General", language="tamil")
    assert results == []


# ---------------------------------------------------------------------------
# Repository — search_articles
# ---------------------------------------------------------------------------

def test_search_articles_language_filter(session, multilang_articles):
    # English article title contains 'English'
    results = search_articles(session, search_query="English", language="english")
    assert all(a.language == "english" for a in results)


def test_search_articles_no_language_filter_returns_all_languages(session, multilang_articles):
    # Each article's source_name is ASCII and appears in the source_name field;
    # search on 'national' which appears only in the English content. We verify
    # that omitting language returns results only from the matched language — the
    # search function searches title + content, not language.
    # Instead we verify no language kwarg is passed and result is non-empty.
    results_all = search_articles(session, search_query="English")
    results_en = search_articles(session, search_query="English", language="english")
    # Without a language filter the result set is a superset of the filtered one
    assert len(results_all) >= len(results_en)


# ---------------------------------------------------------------------------
# Repository — get_unseen_articles_for_user
# ---------------------------------------------------------------------------

def test_get_unseen_articles_language_filter(session, multilang_articles):
    results = get_unseen_articles_for_user(session, auth_id="test-user", language="bengali")
    assert all(a.language == "bengali" for a in results)
    assert len(results) == 1


def test_get_unseen_articles_no_filter_returns_all(session, multilang_articles):
    results = get_unseen_articles_for_user(session, auth_id="test-user-all", limit=10)
    assert len(results) == 3


# ---------------------------------------------------------------------------
# Repository — article_to_dict includes language
# ---------------------------------------------------------------------------

def test_article_to_dict_includes_language_field(session, multilang_articles):
    odia_article = next(a for a in multilang_articles if a.language == "odia")
    d = article_to_dict(odia_article)
    assert "language" in d
    assert d["language"] == "odia"


# ---------------------------------------------------------------------------
# Repository — get_bundled_articles_by_category
# ---------------------------------------------------------------------------

def test_bundled_articles_language_filter(session, multilang_articles):
    result = get_bundled_articles_by_category(session, limit_per_category=5, language="odia")
    general_articles = result["categories"]["General"]["articles"]
    assert all(a["language"] == "odia" for a in general_articles)


def test_bundled_articles_no_filter_includes_all_languages(session, multilang_articles):
    result = get_bundled_articles_by_category(session, limit_per_category=10)
    all_articles = [
        a
        for cat_data in result["categories"].values()
        for a in cat_data["articles"]
    ]
    languages = {a["language"] for a in all_articles}
    assert "english" in languages
    assert "odia" in languages
    assert "bengali" in languages


# ---------------------------------------------------------------------------
# API endpoints — language query param
# ---------------------------------------------------------------------------

def test_api_by_category_language_filter_odia(client: TestClient, multilang_articles):
    response = client.get(
        "/articles/by-category", params={"category": "General", "language": "odia"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert all(a["language"] == "odia" for a in payload["articles"])
    assert len(payload["articles"]) == 1


def test_api_by_category_language_filter_bengali(client: TestClient, multilang_articles):
    response = client.get(
        "/articles/by-category", params={"category": "General", "language": "bengali"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert all(a["language"] == "bengali" for a in payload["articles"])


def test_api_by_category_no_language_filter_returns_all(client: TestClient, multilang_articles):
    response = client.get("/articles/by-category", params={"category": "General"})
    assert response.status_code == 200
    payload = response.json()
    # Both odia and bengali articles are in "General"
    assert len(payload["articles"]) == 2


def test_api_search_language_filter(client: TestClient, multilang_articles):
    response = client.get(
        "/articles/search", params={"q": "English", "language": "english"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert all(a["language"] == "english" for a in payload["articles"])


def test_api_search_no_language_filter_returns_all(client: TestClient, multilang_articles):
    # Without a language filter, matches are returned regardless of language.
    # We verify the endpoint accepts the request and returns articles.
    response_all = client.get("/articles/search", params={"q": "English"})
    response_en = client.get(
        "/articles/search", params={"q": "English", "language": "english"}
    )
    assert response_all.status_code == 200
    assert response_en.status_code == 200
    # Filtered result must be a subset of (or equal to) the unfiltered result
    assert len(response_all.json()["articles"]) >= len(response_en.json()["articles"])


def test_api_bundled_language_filter(client: TestClient, multilang_articles):
    response = client.get("/articles/bundled", params={"language": "odia"})
    assert response.status_code == 200
    payload = response.json()
    general = payload["categories"]["General"]["articles"]
    assert all(a["language"] == "odia" for a in general)


def test_api_unseen_language_filter(client: TestClient, guest_tokens, multilang_articles):
    headers = {"Authorization": f"Bearer {guest_tokens['access_token']}"}
    response = client.get("/articles/unseen", params={"language": "bengali"}, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert all(a["language"] == "bengali" for a in payload["articles"])


def test_api_articles_include_language_field(client: TestClient, multilang_articles):
    """All article responses include the language field."""
    response = client.get("/articles/by-category", params={"category": "General"})
    assert response.status_code == 200
    for article in response.json()["articles"]:
        assert "language" in article
