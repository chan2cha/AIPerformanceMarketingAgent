from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ResourceNotFoundError
from app.modules.ingestion.model import CollectionSource
from app.modules.organizations.model import Membership
from app.modules.users.model import User


def get_authorized_collection_source(
    session: Session, user: User, source_id: UUID
) -> CollectionSource:
    source = session.scalar(
        select(CollectionSource)
        .join(Membership, Membership.organization_id == CollectionSource.organization_id)
        .where(CollectionSource.id == source_id, Membership.user_id == user.id)
    )
    if source is None:
        raise ResourceNotFoundError(
            code="COLLECTION_SOURCE_NOT_FOUND",
            message="수집 소스를 찾을 수 없습니다.",
        )
    return source


def list_brand_collection_sources(
    session: Session, organization_id: UUID, brand_id: UUID
) -> list[CollectionSource]:
    return list(
        session.scalars(
            select(CollectionSource)
            .where(
                CollectionSource.organization_id == organization_id,
                CollectionSource.brand_id == brand_id,
            )
            .order_by(CollectionSource.created_at, CollectionSource.id)
        )
    )
