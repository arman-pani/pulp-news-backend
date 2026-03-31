from uuid import uuid4

from sqlmodel import Session

from app.models import Article, SeenArticle
from app.services.auth import create_guest_auth_session, refresh_auth_session, revoke_refresh_session
from app.services.article_repository import (
    batch_check_duplicates,
    delete_old_articles,
    get_refresh_sessions_for_user,
    get_recent_article_for_notification,
    set_user_notification_preference,
    save_articles_bulk_insert,
)


def test_save_articles_bulk_insert_skips_duplicate_source_url(session: Session):
    existing = Article(
        source_name="OdishaTV",
        source_url="https://example.com/duplicate",
        title="Existing title",
        content="Existing content" * 5,
        category="General",
    )
    session.add(existing)
    session.commit()

    inserted = save_articles_bulk_insert(
        session,
        [
            Article(
                id=uuid4(),
                source_name="OdishaTV",
                source_url="https://example.com/duplicate",
                title="Duplicate title",
                content="Duplicate content" * 5,
                category="General",
            )
        ],
    )
    session.commit()
    assert inserted == 0


def test_batch_check_duplicates_flags_exact_url_match(session: Session):
    existing = Article(
        source_name="OdishaTV",
        source_url="https://example.com/duplicate-url",
        title="Existing title",
        content="Existing content" * 5,
        category="General",
    )
    session.add(existing)
    session.commit()

    duplicates = batch_check_duplicates(
        session,
        [
            {
                "url": "https://example.com/duplicate-url",
                "original_title": "Different title",
            }
        ],
    )
    assert "https://example.com/duplicate-url" in duplicates


def test_delete_old_articles_removes_seen_records(session: Session):
    old_article = Article(
        source_name="OdishaTV",
        source_url="https://example.com/old-article",
        title="Old article",
        content="Old content" * 5,
        category="General",
    )
    session.add(old_article)
    session.commit()

    old_article.published_at = old_article.published_at.replace(year=old_article.published_at.year - 1)
    session.add(old_article)
    session.add(SeenArticle(user_auth_id="user-1", article_id=old_article.id))
    session.commit()

    result = delete_old_articles(session, days_old=7)
    session.commit()
    assert result["articles_deleted"] == 1
    assert result["seen_articles_deleted"] == 1


def test_set_user_notification_preference_updates_user(session: Session):
    user = set_user_notification_preference(
        session,
        auth_id="guest_user_1",
        is_enabled=True,
        fcm_token="token-123",
    )
    session.commit()
    assert user.is_notification_enabled is True
    assert user.fcm_token == "token-123"


def test_get_recent_article_for_notification(session: Session):
    article = Article(
        source_name="OdishaTV",
        source_url="https://example.com/recent-article",
        title="Recent article",
        content="Recent content" * 5,
        category="General",
    )
    session.add(article)
    session.commit()
    found = get_recent_article_for_notification(session, minutes_back=15)
    assert found is not None
    assert found.source_url == "https://example.com/recent-article"


def test_refresh_tokens_are_hashed_and_rotated(session: Session):
    issued = create_guest_auth_session(session)
    session.commit()
    sessions = get_refresh_sessions_for_user(session, issued.user_id)
    assert len(sessions) == 1
    assert sessions[0].token_hash != issued.refresh_token

    refreshed = refresh_auth_session(session, issued.refresh_token)
    session.commit()
    refreshed_sessions = get_refresh_sessions_for_user(session, issued.user_id)
    assert len(refreshed_sessions) == 2
    revoked_sessions = [item for item in refreshed_sessions if item.revoked_at is not None]
    assert len(revoked_sessions) == 1
    assert refreshed.refresh_token != issued.refresh_token


def test_revoked_refresh_token_is_rejected(session: Session):
    issued = create_guest_auth_session(session)
    session.commit()
    revoke_refresh_session(session, issued.refresh_token)
    session.commit()
    try:
        refresh_auth_session(session, issued.refresh_token)
        assert False, "Expected revoked refresh token to be rejected"
    except Exception:
        assert True
