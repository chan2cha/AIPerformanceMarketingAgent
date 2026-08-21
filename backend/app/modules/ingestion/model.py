from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CollectionSource(Base):
    __tablename__ = "collection_sources"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_collection_sources_id_organization"),
        ForeignKeyConstraint(
            ["brand_id", "organization_id"],
            ["brands.id", "brands.organization_id"],
            name="fk_collection_sources_brand_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["competitor_id", "brand_id", "organization_id"],
            ["competitors.id", "competitors.brand_id", "competitors.organization_id"],
            name="fk_collection_sources_competitor_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "platform IN ('meta_ad_library', 'tiktok_creative_center')",
            name="valid_collection_platform",
        ),
        CheckConstraint("scope IN ('competitor', 'industry')", name="valid_collection_scope"),
        CheckConstraint("status IN ('active', 'paused')", name="valid_collection_status"),
        CheckConstraint(
            "sync_interval_hours >= 1 AND sync_interval_hours <= 168",
            name="valid_collection_sync_interval",
        ),
        Index("ix_collection_sources_organization_id", "organization_id"),
        Index("ix_collection_sources_brand_id", "brand_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    brand_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    competitor_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    external_identifier: Mapped[str | None] = mapped_column(String(500))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(10))
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    sync_interval_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="24"
    )
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
