from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlmodel import Session

import cron_runner
from app.models import Article, SeenArticle
from app.services.jobs import run_cleanup_job, run_scrape_and_notify_job


def test_run_scrape_and_notify_job(session: Session, monkeypatch):
    article = Article(
        source_name="Sambad",
        source_url="https://example.com/sambad-1",
        title="Saved headline",
        content="Saved content " * 5,
        category="General",
    )

    def fake_scrape_and_collect(db_session, schedule_name=None):
        db_session.add(article)
        db_session.flush()
        return (
            {
                "schedule": "2pm",
                "description": "2 PM IST",
                "sources": ["sambadenglish"],
                "scraped_articles": 1,
                "saved_articles": 1,
            },
            [article],
        )

    def fake_notify(db_session, articles):
        assert articles == [article]
        return {"status": "completed", "sent_count": 1}

    monkeypatch.setattr("app.services.jobs.scrape_and_collect", fake_scrape_and_collect)
    monkeypatch.setattr("app.services.jobs.send_notifications_for_new_articles", fake_notify)

    result = run_scrape_and_notify_job(session, schedule_name="2pm")

    assert result["schedule"] == "2pm"
    assert result["saved_articles"] == 1
    assert result["notification_result"]["sent_count"] == 1


def test_run_cleanup_job(session: Session):
    stale_article = Article(
        source_name="OdishaTV",
        source_url="https://example.com/old-cleanup",
        title="Old cleanup article",
        content="Old cleanup content " * 5,
        category="General",
        published_at=datetime.now(timezone.utc) - timedelta(days=60),
    )
    session.add(stale_article)
    session.commit()
    session.add(SeenArticle(user_auth_id="guest_cleanup", article_id=stale_article.id))
    session.commit()

    result = run_cleanup_job(session, days_old=7)

    assert result["articles_deleted"] == 1
    assert result["seen_articles_deleted"] == 1


def test_send_notifications_for_new_articles_service(session: Session, monkeypatch):
    from app.services.notifications import send_notifications_for_new_articles

    article = Article(
        source_name="OdishaTV",
        source_url="https://example.com/notify-1",
        title="Notification title",
        content="Notification content " * 5,
        category="General",
    )
    session.add(article)
    session.commit()

    class FakeMessaging:
        def __init__(self):
            self.sent = []

        def send(self, message):
            self.sent.append(message)
            return "message-id"

    fake_messaging = FakeMessaging()
    monkeypatch.setattr(
        "app.services.notifications.get_messaging",
        lambda: fake_messaging,
    )

    from app.models import User

    session.add(User(auth_id="guest_user_1", fcm_token="token-123", is_notification_enabled=True))
    session.commit()

    result = send_notifications_for_new_articles(session, [article])

    assert result["status"] == "completed"
    assert result["notification_result"]["sent_count"] == 1
    assert len(fake_messaging.sent) == 1


def test_cron_runner_dispatches_scrape_job(monkeypatch):
    calls = []

    class DummySettings:
        def validate_runtime_configuration(self):
            return None

    @contextmanager
    def fake_session_scope():
        yield "session-token"

    def fake_scrape_job(session):
        calls.append(("scrape", session))
        return {"status": "ok"}

    def fake_cleanup_job(session):
        calls.append(("cleanup", session))
        return {"status": "ok"}

    monkeypatch.setattr("app.core.config.get_settings", lambda: DummySettings())
    monkeypatch.setattr("app.db.session_scope", fake_session_scope)
    monkeypatch.setattr("app.services.jobs.run_scrape_and_notify_job", fake_scrape_job)
    monkeypatch.setattr("app.services.jobs.run_cleanup_job", fake_cleanup_job)
    monkeypatch.setattr(sys, "argv", ["cron_runner.py", "--job", "scrape_and_notify"])

    cron_runner.main()

    assert calls == [("scrape", "session-token")]


def test_cron_runner_exits_on_config_error(monkeypatch):
    class DummySettings:
        def validate_runtime_configuration(self):
            raise ValueError("bad config")

    monkeypatch.setattr("app.core.config.get_settings", lambda: DummySettings())
    monkeypatch.setattr(sys, "argv", ["cron_runner.py", "--job", "cleanup"])

    with pytest.raises(SystemExit) as exc:
        cron_runner.main()

    assert exc.value.code == 1
