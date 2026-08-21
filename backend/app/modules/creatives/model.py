from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Creative(Base):
    __tablename__ = "creatives"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_creatives_id_organization"),
        ForeignKeyConstraint(
            ["brand_id", "organization_id"],
            ["brands.id", "brands.organization_id"],
            name="fk_creatives_brand_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["competitor_id", "brand_id", "organization_id"],
            ["competitors.id", "competitors.brand_id", "competitors.organization_id"],
            name="fk_creatives_competitor_tenant",
        ),
        CheckConstraint(
            "ownership_type IN ('own', 'competitor', 'market')", name="valid_ownership_type"
        ),
        CheckConstraint(
            "media_type IN ('image', 'video', 'carousel', 'text')", name="valid_media_type"
        ),
        Index("ix_creatives_organization_created", "organization_id", "created_at"),
        Index("ix_creatives_brand_created", "brand_id", "created_at"),
        Index(
            "uq_creatives_tenant_source_external",
            "organization_id",
            "source",
            "source_external_id",
            unique=True,
            postgresql_where=text("source_external_id IS NOT NULL"),
        ),
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
    ownership_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="manual")
    source_external_id: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CreativeAsset(Base):
    __tablename__ = "creative_assets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["creative_id", "organization_id"],
            ["creatives.id", "creatives.organization_id"],
            name="fk_creative_assets_creative_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_creative_assets_organization_id", "organization_id"),
        Index("ix_creative_assets_creative_id", "creative_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    creative_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(128))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CreativeAnalysis(Base):
    __tablename__ = "creative_analyses"
    __table_args__ = (
        ForeignKeyConstraint(
            ["creative_id", "organization_id"],
            ["creatives.id", "creatives.organization_id"],
            name="fk_creative_analyses_creative_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint("status IN ('completed', 'superseded')", name="valid_status"),
        UniqueConstraint("job_id", name="uq_creative_analyses_job_id"),
        Index("ix_creative_analyses_organization_id", "organization_id"),
        Index("ix_creative_analyses_creative_created", "creative_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    creative_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    job_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="completed")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    hook: Mapped[str | None] = mapped_column(Text)
    offer: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(String(500))
    angle: Mapped[str | None] = mapped_column(String(500))
    emotional_triggers: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    visual_elements: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
