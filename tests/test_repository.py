from uuid import uuid4

from sqlmodel import Session

from app.models import Article
from app.services.article_repository import (
    batch_check_duplicates,
    delete_old_articles,
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
    session.commit()

    result = delete_old_articles(session, days_old=7)
    session.commit()
    assert result["articles_deleted"] == 1
