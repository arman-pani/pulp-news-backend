from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_db_session, require_internal_token
from app.schemas import JobResponse
from app.services.jobs import run_cleanup_job, run_notification_job, run_scrape_job

router = APIRouter(prefix="/internal/jobs", tags=["internal"])


class ScrapeJobRequest(BaseModel):
    schedule_name: str | None = None


class CleanupJobRequest(BaseModel):
    days_old: int | None = None


class NotificationJobRequest(BaseModel):
    minutes_back: int | None = None


@router.post("/scrape", response_model=JobResponse, dependencies=[Depends(require_internal_token)])
def scrape_articles_job(
    payload: ScrapeJobRequest,
    session: Session = Depends(get_db_session),
) -> JobResponse:
    result = run_scrape_job(session, schedule_name=payload.schedule_name)
    return JobResponse(status="completed", detail="Scrape job finished", data=result)


@router.post("/cleanup", response_model=JobResponse, dependencies=[Depends(require_internal_token)])
def cleanup_articles_job(
    payload: CleanupJobRequest,
    session: Session = Depends(get_db_session),
) -> JobResponse:
    result = run_cleanup_job(session, days_old=payload.days_old)
    return JobResponse(status="completed", detail="Cleanup job finished", data=result)


@router.post(
    "/notifications",
    response_model=JobResponse,
    dependencies=[Depends(require_internal_token)],
)
def notification_job(
    payload: NotificationJobRequest,
    session: Session = Depends(get_db_session),
) -> JobResponse:
    result = run_notification_job(session, minutes_back=payload.minutes_back)
    return JobResponse(status="completed", detail="Notification job finished", data=result)
