from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.modules.organizations.model import Membership, Organization
from app.modules.users.model import User


def require_organization_access(
    session: Session, user: User, organization_id: UUID
) -> tuple[Organization, Membership]:
    result = session.execute(
        select(Organization, Membership)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(
            Organization.id == organization_id,
            Membership.user_id == user.id,
        )
    ).one_or_none()
    if result is None:
        raise ResourceNotFoundError(
            code="ORGANIZATION_NOT_FOUND",
            message="Organization을 찾을 수 없습니다.",
        )
    return result
