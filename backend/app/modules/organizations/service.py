from sqlalchemy.orm import Session

from app.modules.organizations.model import Membership, Organization
from app.modules.organizations.schemas import OrganizationCreate
from app.modules.users.model import User


def create_organization(session: Session, user: User, payload: OrganizationCreate) -> Organization:
    organization = Organization(name=payload.name)
    try:
        session.add(organization)
        session.flush()
        session.add(Membership(organization_id=organization.id, user_id=user.id, role="owner"))
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(organization)
    return organization
