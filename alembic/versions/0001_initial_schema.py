"""Initial FastAPI schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("auth_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        sa.Column("is_notification_enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("auth_id"),
    )
    op.create_index(op.f("ix_users_fcm_token"), "users", ["fcm_token"], unique=False)
    op.create_index(
        op.f("ix_users_is_notification_enabled"),
        "users",
        ["is_notification_enabled"],
        unique=False,
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_articles_category"), "articles", ["category"], unique=False)
    op.create_index(op.f("ix_articles_created_at"), "articles", ["created_at"], unique=False)
    op.create_index(op.f("ix_articles_published_at"), "articles", ["published_at"], unique=False)
    op.create_index(op.f("ix_articles_source_url"), "articles", ["source_url"], unique=True)

    op.create_table(
        "seen_articles",
        sa.Column("user_auth_id", sa.String(length=255), nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.ForeignKeyConstraint(["user_auth_id"], ["users.auth_id"]),
        sa.PrimaryKeyConstraint("user_auth_id", "article_id"),
    )
    op.create_index(op.f("ix_seen_articles_seen_at"), "seen_articles", ["seen_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_seen_articles_seen_at"), table_name="seen_articles")
    op.drop_table("seen_articles")
    op.drop_index(op.f("ix_articles_source_url"), table_name="articles")
    op.drop_index(op.f("ix_articles_published_at"), table_name="articles")
    op.drop_index(op.f("ix_articles_created_at"), table_name="articles")
    op.drop_index(op.f("ix_articles_category"), table_name="articles")
    op.drop_table("articles")
    op.drop_index(op.f("ix_users_is_notification_enabled"), table_name="users")
    op.drop_index(op.f("ix_users_fcm_token"), table_name="users")
    op.drop_table("users")
