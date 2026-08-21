from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, status

from app.modules.auth.authorization import require_organization_access
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.organizations.repository import list_user_organizations
from app.modules.organizations.schemas import (
    MeResponse,
    OrganizationCreate,
    OrganizationResponse,
    UserOrganizationResponse,
)
from app.modules.organizations.service import create_organization

router = APIRouter(prefix="/api/v1", tags=["tenant-core"])


@router.get("/me", response_model=MeResponse)
def get_me(session: DatabaseSession, user: CurrentUser) -> MeResponse:
    organizations = [
        UserOrganizationResponse(id=organization.id, name=organization.name, role=membership.role)
        for organization, membership in list_user_organizations(session, user.id)
    ]
    return MeResponse(id=user.id, email=user.email, name=user.name, organizations=organizations)


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_organization(
    payload: Annotated[OrganizationCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> OrganizationResponse:
    return OrganizationResponse.model_validate(create_organization(session, user, payload))


@router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> OrganizationResponse:
    organization, _membership = require_organization_access(session, user, organization_id)
    return OrganizationResponse.model_validate(organization)
