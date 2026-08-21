from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.brands.model import Brand
from app.modules.competitors.model import Competitor
from app.modules.competitors.repository import get_authorized_competitor
from app.modules.competitors.schemas import CompetitorCreate
from app.modules.users.model import User


def create_competitor(
    session: Session,
    brand: Brand,
    payload: CompetitorCreate,
) -> Competitor:
    competitor = Competitor(
        organization_id=brand.organization_id,
        brand_id=brand.id,
        name=payload.name,
        website=str(payload.website) if payload.website else None,
        instagram_url=str(payload.instagram_url) if payload.instagram_url else None,
        meta_page_id=payload.meta_page_id,
        tiktok_url=str(payload.tiktok_url) if payload.tiktok_url else None,
        extra_metadata=payload.metadata,
    )
    session.add(competitor)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(competitor)
    return competitor


def delete_competitor(session: Session, user: User, competitor_id: UUID) -> None:
    competitor = get_authorized_competitor(session, user, competitor_id)
    session.delete(competitor)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
