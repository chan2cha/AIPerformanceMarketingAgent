"""Add subscription billing and provider credit ledger.

Revision ID: 20260826_0008
Revises: 20260824_0007
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260826_0008"
down_revision: str | Sequence[str] | None = "20260824_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("plan_code", sa.String(length=50), server_default="pilot_40", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="inactive", nullable=False),
        sa.Column("billing_provider", sa.String(length=30), nullable=False),
        sa.Column("external_customer_id", sa.String(length=255), nullable=True),
        sa.Column("external_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('inactive', 'trialing', 'active', 'past_due', 'cancelled')",
            name="valid_subscription_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_subscriptions_organization"),
        sa.UniqueConstraint(
            "billing_provider", "external_subscription_id", name="uq_subscriptions_external"
        ),
    )
    op.create_table(
        "credit_ledger",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=True),
        sa.Column("job_id", sa.UUID(), nullable=True),
        sa.Column("entry_type", sa.String(length=30), nullable=False),
        sa.Column("amount_usd", sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "entry_type IN ('grant', 'reservation', 'settlement', 'release', 'adjustment')",
            name="valid_credit_entry_type",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "idempotency_key", name="uq_credit_ledger_tenant_idempotency"
        ),
    )
    op.create_index(
        "ix_credit_ledger_organization_created",
        "credit_ledger",
        ["organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_credit_ledger_organization_created", table_name="credit_ledger")
    op.drop_table("credit_ledger")
    op.drop_table("subscriptions")
