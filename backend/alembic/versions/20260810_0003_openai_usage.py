"""Track cached input usage for real provider cost calculation.

Revision ID: 20260810_0003
Revises: 20260810_0002
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0003"
down_revision: str | Sequence[str] | None = "20260810_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "api_usage",
        sa.Column("cached_input_units", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("api_usage", "cached_input_units")
