from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('inactive', 'trialing', 'active', 'past_due', 'cancelled')",
            name="valid_subscription_status",
        ),
        UniqueConstraint("organization_id", name="uq_subscriptions_organization"),
        UniqueConstraint(
            "billing_provider", "external_subscription_id", name="uq_subscriptions_external"
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
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pilot_40")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="inactive")
    billing_provider: Mapped[str] = mapped_column(String(30), nullable=False)
    external_customer_id: Mapped[str | None] = mapped_column(String(255))
    external_subscription_id: Mapped[str | None] = mapped_column(String(255))
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('grant', 'reservation', 'settlement', 'release', 'adjustment')",
            name="valid_credit_entry_type",
        ),
        UniqueConstraint(
            "organization_id", "idempotency_key", name="uq_credit_ledger_tenant_idempotency"
        ),
        Index("ix_credit_ledger_organization_created", "organization_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL")
    )
    job_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL")
    )
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(14, 8), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    entry_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
