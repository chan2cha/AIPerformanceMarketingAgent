from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.model import Membership, Organization


def list_user_organizations(
    session: Session, user_id: UUID
) -> list[tuple[Organization, Membership]]:
    rows = session.execute(
        select(Organization, Membership)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user_id)
        .order_by(Organization.created_at, Organization.id)
    )
    return list(rows.tuples())
