"""restore Meta sources for Apify automation

Revision ID: 20260824_0007
Revises: 20260824_0006
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260824_0007"
down_revision: str | None = "20260824_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE collection_sources
        SET status = 'active', next_sync_at = NOW(), last_error_code = NULL
        WHERE platform = 'meta_ad_library'
          AND last_error_code = 'PLATFORM_MANUAL_ONLY'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE collection_sources
        SET status = 'paused', next_sync_at = NULL,
            last_error_code = 'PLATFORM_MANUAL_ONLY'
        WHERE platform = 'meta_ad_library'
        """
    )
