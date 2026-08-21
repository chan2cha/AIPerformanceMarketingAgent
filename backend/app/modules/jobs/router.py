from uuid import UUID

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.jobs.schemas import JobResponse
from app.modules.jobs.service import get_authorized_job

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, session: DatabaseSession, user: CurrentUser) -> JobResponse:
    return JobResponse.model_validate(get_authorized_job(session, user, job_id))
