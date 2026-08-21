from typing import Protocol
from uuid import UUID


class JobDispatcher(Protocol):
    def dispatch_creative_analysis(self, job_id: UUID) -> None: ...

    def dispatch_market_content_sync(self, job_id: UUID) -> None: ...


class CeleryJobDispatcher:
    def dispatch_creative_analysis(self, job_id: UUID) -> None:
        from worker.tasks.creative_analysis import analyze_creative_job

        analyze_creative_job.delay(str(job_id))

    def dispatch_market_content_sync(self, job_id: UUID) -> None:
        from worker.tasks.market_content_sync import sync_market_content_job

        sync_market_content_job.delay(str(job_id))


def get_job_dispatcher() -> JobDispatcher:
    return CeleryJobDispatcher()
