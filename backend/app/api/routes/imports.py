from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.import_job import ImportJob
from app.schemas.imports import ImportJobRead, ImportJobsResponse, ScanRequest, ScanResponse
from app.services.import_service import ImportService

router = APIRouter()


@router.get("/import-jobs", response_model=ImportJobsResponse)
def list_import_jobs(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ImportJobsResponse:
    del current_user
    total = db.scalar(select(func.count()).select_from(ImportJob)) or 0
    jobs = db.scalars(
        select(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit).offset(offset)
    )
    return ImportJobsResponse(
        items=[ImportJobRead.model_validate(job) for job in jobs],
        total=total,
    )


@router.get("/import-jobs/{job_id}", response_model=ImportJobRead)
def get_import_job(job_id: str, current_user: CurrentUser, db: DbSession) -> ImportJobRead:
    del current_user
    job = db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return ImportJobRead.model_validate(job)


@router.post("/library/scan", response_model=ScanResponse)
def scan_library(
    payload: ScanRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ScanResponse:
    del current_user
    try:
        jobs = ImportService(get_settings()).scan_incoming(
            db,
            Path(payload.path) if payload.path else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ScanResponse(
        scanned=len(jobs),
        imported=sum(1 for job in jobs if job.status == "success"),
        warnings=sum(1 for job in jobs if job.status == "warning"),
        failed=sum(1 for job in jobs if job.status == "failed"),
        jobs=[ImportJobRead.model_validate(job) for job in jobs],
    )
