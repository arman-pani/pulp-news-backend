def test_get_articles_by_category(client, seeded_articles):
    response = client.get("/articles/by-category", params={"category": "Politics", "limit": 10, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "Politics"
    assert len(payload["articles"]) == 2


def test_search_articles(client, seeded_articles):
    response = client.get("/articles/search", params={"q": "election", "limit": 10, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "election"
    assert len(payload["articles"]) == 2


def test_get_bundled_articles(client, seeded_articles):
    response = client.get("/articles/bundled", params={"limit_per_category": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_categories"] >= 2
    assert payload["categories"]["Politics"]["limit"] == 1
    assert len(payload["categories"]["Politics"]["articles"]) == 1


def test_unseen_articles_without_tracking_returns_latest(client, seeded_articles):
    response = client.get("/articles/unseen", params={"limit": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["tracking_enabled"] is False
    assert len(payload["articles"]) == 2


def test_unseen_articles_with_tracking_marks_seen(client, seeded_articles):
    first_response = client.get("/articles/unseen", params={"limit": 2}, headers={"X-Client-Id": "device-1"})
    second_response = client.get("/articles/unseen", params={"limit": 2}, headers={"X-Client-Id": "device-1"})
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(first_response.json()["articles"]) == 2
    assert len(second_response.json()["articles"]) == 1


def test_internal_job_requires_token(client):
    response = client.post("/internal/jobs/cleanup", json={})
    assert response.status_code == 401
