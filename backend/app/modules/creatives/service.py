from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.modules.brands.repository import get_authorized_brand
from app.modules.competitors.model import Competitor
from app.modules.creatives.model import Creative
from app.modules.creatives.schemas import CreativeCreate
from app.modules.users.model import User


def create_creative(
    session: Session,
    user: User,
    brand_id: UUID,
    payload: CreativeCreate,
) -> Creative:
    brand = get_authorized_brand(session, user, brand_id)
    if payload.competitor_id is not None:
        competitor = session.scalar(
            select(Competitor).where(
                Competitor.id == payload.competitor_id,
                Competitor.brand_id == brand.id,
                Competitor.organization_id == brand.organization_id,
            )
        )
        if competitor is None:
            raise ResourceNotFoundError(
                code="COMPETITOR_NOT_FOUND", message="Competitor를 찾을 수 없습니다."
            )

    creative = Creative(
        organization_id=brand.organization_id,
        brand_id=brand.id,
        competitor_id=payload.competitor_id,
        ownership_type=payload.ownership_type,
        source=payload.source,
        source_external_id=payload.source_external_id,
        source_url=str(payload.source_url) if payload.source_url else None,
        media_type=payload.media_type,
        title=payload.title,
        body=payload.body,
        first_seen_at=payload.first_seen_at,
        last_seen_at=payload.last_seen_at,
        raw_payload=payload.raw_payload,
    )
    session.add(creative)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(creative)
    return creative
