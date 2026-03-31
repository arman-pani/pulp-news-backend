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


def test_unseen_articles_requires_auth(client, seeded_articles):
    response = client.get("/articles/unseen", params={"limit": 2})
    assert response.status_code == 401


def test_guest_auth_bootstrap_returns_tokens(client):
    response = client.post("/auth/guest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["user_id"].startswith("guest_")


def test_unseen_articles_with_auth_marks_seen(client, guest_tokens, seeded_articles):
    headers = {"Authorization": f"Bearer {guest_tokens['access_token']}"}
    first_response = client.get("/articles/unseen", params={"limit": 2}, headers=headers)
    second_response = client.get("/articles/unseen", params={"limit": 2}, headers=headers)
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["user_id"] == guest_tokens["user_id"]
    assert len(first_response.json()["articles"]) == 2
    assert len(second_response.json()["articles"]) == 1


def test_refresh_rotates_tokens(client, guest_tokens):
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": guest_tokens["refresh_token"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] != guest_tokens["access_token"]
    assert payload["refresh_token"] != guest_tokens["refresh_token"]
    reused_response = client.post(
        "/auth/refresh",
        json={"refresh_token": guest_tokens["refresh_token"]},
    )
    assert reused_response.status_code == 401


def test_logout_revokes_refresh_token(client, guest_tokens):
    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": guest_tokens["refresh_token"]},
    )
    assert logout_response.status_code == 200
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": guest_tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401


def test_internal_job_requires_token(client):
    response = client.post("/internal/jobs/cleanup", json={})
    assert response.status_code == 401


def test_update_fcm_token(client, guest_tokens, seeded_articles):
    response = client.post(
        "/users/me/fcm-token",
        json={"fcm_token": "token-123"},
        headers={"Authorization": f"Bearer {guest_tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "FCM token updated successfully"


def test_set_notification_preference(client, guest_tokens, seeded_articles):
    response = client.post(
        "/users/me/notification-preference",
        json={"is_enabled": True, "fcm_token": "token-123"},
        headers={"Authorization": f"Bearer {guest_tokens['access_token']}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_notification_enabled"] is True


def test_notification_job_requires_internal_token(client):
    response = client.post("/internal/jobs/notifications", json={})
    assert response.status_code == 401
