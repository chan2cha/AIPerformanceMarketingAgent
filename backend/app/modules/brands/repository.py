from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.modules.brands.model import Brand
from app.modules.organizations.model import Membership
from app.modules.users.model import User


def get_authorized_brand(session: Session, user: User, brand_id: UUID) -> Brand:
    brand = session.scalar(
        select(Brand)
        .join(Membership, Membership.organization_id == Brand.organization_id)
        .where(Brand.id == brand_id, Membership.user_id == user.id)
    )
    if brand is None:
        raise ResourceNotFoundError(code="BRAND_NOT_FOUND", message="Brand를 찾을 수 없습니다.")
    return brand


def list_organization_brands(
    session: Session, organization_id: UUID, offset: int, limit: int
) -> list[Brand]:
    return list(
        session.scalars(
            select(Brand)
            .where(Brand.organization_id == organization_id)
            .order_by(Brand.created_at, Brand.id)
            .offset(offset)
            .limit(limit)
        )
    )
