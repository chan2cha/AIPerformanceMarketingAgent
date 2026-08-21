from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Query, status

from app.modules.auth.authorization import require_organization_access
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.brands.repository import get_authorized_brand, list_organization_brands
from app.modules.brands.schemas import BrandCreate, BrandResponse, BrandUpdate
from app.modules.brands.service import create_brand, update_brand

router = APIRouter(prefix="/api/v1", tags=["brands"])


@router.post(
    "/organizations/{organization_id}/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_brand(
    organization_id: UUID,
    payload: Annotated[BrandCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> BrandResponse:
    return BrandResponse.model_validate(create_brand(session, user, organization_id, payload))


@router.get("/organizations/{organization_id}/brands", response_model=list[BrandResponse])
def get_brands(
    organization_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[BrandResponse]:
    require_organization_access(session, user, organization_id)
    return [
        BrandResponse.model_validate(brand)
        for brand in list_organization_brands(session, organization_id, offset, limit)
    ]


@router.get("/brands/{brand_id}", response_model=BrandResponse)
def get_brand(brand_id: UUID, session: DatabaseSession, user: CurrentUser) -> BrandResponse:
    return BrandResponse.model_validate(get_authorized_brand(session, user, brand_id))


@router.patch("/brands/{brand_id}", response_model=BrandResponse)
def patch_brand(
    brand_id: UUID,
    payload: Annotated[BrandUpdate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> BrandResponse:
    return BrandResponse.model_validate(update_brand(session, user, brand_id, payload))
