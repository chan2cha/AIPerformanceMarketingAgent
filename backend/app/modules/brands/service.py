from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.authorization import require_organization_access
from app.modules.billing.service import ensure_plan_resource_allowed
from app.modules.brands.model import Brand
from app.modules.brands.repository import get_authorized_brand
from app.modules.brands.schemas import BrandCreate, BrandUpdate
from app.modules.users.model import User


def create_brand(
    session: Session,
    user: User,
    organization_id: UUID,
    payload: BrandCreate,
) -> Brand:
    require_organization_access(session, user, organization_id)
    ensure_plan_resource_allowed(session, organization_id, "brand")
    brand = Brand(
        organization_id=organization_id,
        name=payload.name,
        website=str(payload.website) if payload.website else None,
        industry=payload.industry,
        description=payload.description,
        target_customer=payload.target_customer,
        brand_tone=payload.brand_tone,
    )
    session.add(brand)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(brand)
    return brand


def update_brand(
    session: Session,
    user: User,
    brand_id: UUID,
    payload: BrandUpdate,
) -> Brand:
    brand = get_authorized_brand(session, user, brand_id)
    for field, value in payload.persistence_values().items():
        setattr(brand, field, value)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(brand)
    return brand
