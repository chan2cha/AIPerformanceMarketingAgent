from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Response, status

from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.brands.repository import get_authorized_brand
from app.modules.competitors.repository import list_brand_competitors
from app.modules.competitors.schemas import CompetitorCreate, CompetitorResponse
from app.modules.competitors.service import create_competitor, delete_competitor

router = APIRouter(prefix="/api/v1", tags=["competitors"])


@router.post(
    "/brands/{brand_id}/competitors",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_competitor(
    brand_id: UUID,
    payload: Annotated[CompetitorCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> CompetitorResponse:
    brand = get_authorized_brand(session, user, brand_id)
    return CompetitorResponse.model_validate(create_competitor(session, brand, payload))


@router.get("/brands/{brand_id}/competitors", response_model=list[CompetitorResponse])
def get_competitors(
    brand_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> list[CompetitorResponse]:
    get_authorized_brand(session, user, brand_id)
    return [
        CompetitorResponse.model_validate(competitor)
        for competitor in list_brand_competitors(session, brand_id)
    ]


@router.delete("/competitors/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_competitor(
    competitor_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> Response:
    delete_competitor(session, user, competitor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
