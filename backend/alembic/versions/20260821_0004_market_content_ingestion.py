"""Add automated market-content collection sources.

Revision ID: 20260821_0004
Revises: 20260810_0003
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260821_0004"
down_revision: str | Sequence[str] | None = "20260810_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collection_sources",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("brand_id", sa.UUID(), nullable=False),
        sa.Column("competitor_id", sa.UUID(), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("external_identifier", sa.String(length=500), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=True),
        sa.Column(
            "keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "platform IN ('meta_ad_library', 'tiktok_creative_center')",
            name="valid_collection_platform",
        ),
        sa.CheckConstraint("scope IN ('competitor', 'industry')", name="valid_collection_scope"),
        sa.CheckConstraint("status IN ('active', 'paused')", name="valid_collection_status"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["brand_id", "organization_id"],
            ["brands.id", "brands.organization_id"],
            name="fk_collection_sources_brand_tenant",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["competitor_id", "brand_id", "organization_id"],
            ["competitors.id", "competitors.brand_id", "competitors.organization_id"],
            name="fk_collection_sources_competitor_tenant",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_collection_sources_id_organization"),
    )
    op.create_index(
        "ix_collection_sources_organization_id", "collection_sources", ["organization_id"]
    )
    op.create_index("ix_collection_sources_brand_id", "collection_sources", ["brand_id"])
    op.create_index(
        "uq_creatives_tenant_source_external",
        "creatives",
        ["organization_id", "source", "source_external_id"],
        unique=True,
        postgresql_where=sa.text("source_external_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_creatives_tenant_source_external", table_name="creatives")
    op.drop_index("ix_collection_sources_brand_id", table_name="collection_sources")
    op.drop_index("ix_collection_sources_organization_id", table_name="collection_sources")
    op.drop_table("collection_sources")
