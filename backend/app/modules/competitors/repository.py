from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.modules.competitors.model import Competitor
from app.modules.organizations.model import Membership
from app.modules.users.model import User


def get_authorized_competitor(session: Session, user: User, competitor_id: UUID) -> Competitor:
    competitor = session.scalar(
        select(Competitor)
        .join(Membership, Membership.organization_id == Competitor.organization_id)
        .where(Competitor.id == competitor_id, Membership.user_id == user.id)
    )
    if competitor is None:
        raise ResourceNotFoundError(
            code="COMPETITOR_NOT_FOUND",
            message="Competitor를 찾을 수 없습니다.",
        )
    return competitor


def list_brand_competitors(session: Session, brand_id: UUID) -> list[Competitor]:
    return list(
        session.scalars(
            select(Competitor)
            .where(Competitor.brand_id == brand_id)
            .order_by(Competitor.created_at, Competitor.id)
        )
    )
