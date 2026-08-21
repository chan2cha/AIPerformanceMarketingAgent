"""Add collection scheduling and source ownership.

Revision ID: 20260821_0005
Revises: 20260821_0004
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0005"
down_revision: str | Sequence[str] | None = "20260821_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("collection_sources", sa.Column("created_by_user_id", sa.UUID()))
    op.add_column(
        "collection_sources",
        sa.Column("sync_interval_hours", sa.Integer(), server_default="24", nullable=False),
    )
    op.add_column(
        "collection_sources", sa.Column("next_sync_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "collection_sources", sa.Column("last_attempt_at", sa.DateTime(timezone=True))
    )
    op.execute("UPDATE collection_sources SET next_sync_at = now() WHERE status = 'active'")
    op.create_check_constraint(
        "valid_collection_sync_interval",
        "collection_sources",
        "sync_interval_hours >= 1 AND sync_interval_hours <= 168",
    )
    op.create_foreign_key(
        "fk_collection_sources_created_by_user",
        "collection_sources",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_collection_sources_created_by_user", "collection_sources", type_="foreignkey"
    )
    op.drop_constraint(
        "valid_collection_sync_interval", "collection_sources", type_="check"
    )
    op.drop_column("collection_sources", "last_attempt_at")
    op.drop_column("collection_sources", "next_sync_at")
    op.drop_column("collection_sources", "sync_interval_hours")
    op.drop_column("collection_sources", "created_by_user_id")
