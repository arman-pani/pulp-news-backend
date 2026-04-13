"""Add language column to articles

Revision ID: 0003_add_article_language
Revises: 0002_add_refresh_sessions
Create Date: 2026-04-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_add_article_language"
down_revision = "0002_add_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column(
            "language",
            sa.String(length=20),
            nullable=False,
            server_default="english",
        ),
    )
    op.create_index("ix_articles_language", "articles", ["language"])


def downgrade() -> None:
    op.drop_index("ix_articles_language", table_name="articles")
    op.drop_column("articles", "language")
