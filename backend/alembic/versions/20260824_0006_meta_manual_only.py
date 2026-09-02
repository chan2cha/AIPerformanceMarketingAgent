"""Disable legacy Meta collection sources.

Revision ID: 20260824_0006
Revises: 20260821_0005
Create Date: 2026-08-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260824_0006"
down_revision: str | Sequence[str] | None = "20260821_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE collection_sources
        SET status = 'paused',
            next_sync_at = NULL,
            last_error_code = 'PLATFORM_MANUAL_ONLY'
        WHERE platform = 'meta_ad_library'
        """
    )


def downgrade() -> None:
    # A prior active/paused state cannot be reconstructed safely. Keep legacy
    # sources paused and only remove the policy marker.
    op.execute(
        """
        UPDATE collection_sources
        SET last_error_code = NULL
        WHERE platform = 'meta_ad_library'
          AND last_error_code = 'PLATFORM_MANUAL_ONLY'
        """
    )
