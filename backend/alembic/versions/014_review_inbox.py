"""review inbox threads, attachments, quick replies

Revision ID: 014_review_inbox
Revises: 013_system_email
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014_review_inbox"
down_revision: Union[str, Sequence[str], None] = "013_system_email"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "skill_reviews",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="unread"),
    )
    op.add_column(
        "skill_reviews",
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("skill_reviews", sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("skill_reviews", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("skill_reviews", sa.Column("creator_last_read_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "skill_reviews",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "review_thread_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_role", sa.String(length=20), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_review_thread_messages_review_id", "review_thread_messages", ["review_id"])

    op.create_table(
        "review_message_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("review_thread_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "creator_quick_replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "creator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "creator_review_notification_settings",
        sa.Column(
            "creator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("notify_mode", sa.String(length=20), nullable=False, server_default="all"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("creator_review_notification_settings")
    op.drop_table("creator_quick_replies")
    op.drop_table("review_message_attachments")
    op.drop_index("ix_review_thread_messages_review_id", table_name="review_thread_messages")
    op.drop_table("review_thread_messages")
    op.drop_column("skill_reviews", "updated_at")
    op.drop_column("skill_reviews", "creator_last_read_at")
    op.drop_column("skill_reviews", "resolved_at")
    op.drop_column("skill_reviews", "first_response_at")
    op.drop_column("skill_reviews", "is_read")
    op.drop_column("skill_reviews", "status")