"""Add refresh sessions

Revision ID: 0002_add_refresh_sessions
Revises: 0001_initial_schema
Create Date: 2026-03-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_refresh_sessions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_auth_id", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_session_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["user_auth_id"], ["users.auth_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refresh_sessions_user_auth_id"),
        "refresh_sessions",
        ["user_auth_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_sessions_token_hash"),
        "refresh_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_sessions_expires_at"),
        "refresh_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_sessions_revoked_at"),
        "refresh_sessions",
        ["revoked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_sessions_revoked_at"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_expires_at"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_token_hash"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_user_auth_id"), table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
