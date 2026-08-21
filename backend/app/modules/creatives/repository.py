from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.modules.creatives.model import Creative, CreativeAnalysis
from app.modules.organizations.model import Membership
from app.modules.users.model import User


def get_authorized_creative(session: Session, user: User, creative_id: UUID) -> Creative:
    creative = session.scalar(
        select(Creative)
        .join(Membership, Membership.organization_id == Creative.organization_id)
        .where(Creative.id == creative_id, Membership.user_id == user.id)
    )
    if creative is None:
        raise ResourceNotFoundError(
            code="CREATIVE_NOT_FOUND", message="Creative을 찾을 수 없습니다."
        )
    return creative


def list_brand_creatives(
    session: Session,
    organization_id: UUID,
    brand_id: UUID,
    competitor_id: UUID | None,
    ownership_type: str | None,
    media_type: str | None,
    analyzed: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
    offset: int,
    limit: int,
) -> list[Creative]:
    analysis_exists = exists(
        select(CreativeAnalysis.id).where(
            CreativeAnalysis.creative_id == Creative.id,
            CreativeAnalysis.organization_id == Creative.organization_id,
            CreativeAnalysis.status == "completed",
        )
    )
    statement = select(Creative).where(
        Creative.organization_id == organization_id,
        Creative.brand_id == brand_id,
    )
    if competitor_id is not None:
        statement = statement.where(Creative.competitor_id == competitor_id)
    if ownership_type is not None:
        statement = statement.where(Creative.ownership_type == ownership_type)
    if media_type is not None:
        statement = statement.where(Creative.media_type == media_type)
    if analyzed is not None:
        statement = statement.where(analysis_exists if analyzed else ~analysis_exists)
    if created_from is not None:
        statement = statement.where(Creative.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(Creative.created_at <= created_to)
    return list(
        session.scalars(
            statement.order_by(Creative.created_at.desc(), Creative.id).offset(offset).limit(limit)
        )
    )


def list_creative_analyses(
    session: Session, creative_id: UUID, organization_id: UUID
) -> list[CreativeAnalysis]:
    return list(
        session.scalars(
            select(CreativeAnalysis)
            .where(
                CreativeAnalysis.creative_id == creative_id,
                CreativeAnalysis.organization_id == organization_id,
            )
            .order_by(CreativeAnalysis.created_at.desc(), CreativeAnalysis.id.desc())
        )
    )
