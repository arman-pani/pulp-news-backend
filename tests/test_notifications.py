from app.models import Article, User


class FakeMessaging:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)
        return "message-id"


def test_notification_job_sends_for_recent_article(client, session, monkeypatch):
    article = Article(
        source_name="OdishaTV",
        source_url="https://example.com/notify-1",
        title="Notification title",
        content="Notification content" * 5,
        category="General",
    )
    user = User(
        auth_id="guest_user_1",
        fcm_token="token-123",
        is_notification_enabled=True,
    )
    session.add(article)
    session.add(user)
    session.commit()

    fake_messaging = FakeMessaging()
    monkeypatch.setattr(
        "app.services.notifications.get_messaging",
        lambda: fake_messaging,
    )

    response = client.post(
        "/internal/jobs/notifications",
        headers={"X-Internal-Api-Token": "test-internal-token"},
        json={"minutes_back": 15},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["status"] == "completed"
    assert payload["data"]["notification_result"]["sent_count"] == 1
    assert len(fake_messaging.sent) == 1
