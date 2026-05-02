from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.import_job import ImportBatch
from app.models.import_job import ImportJob
from app.schemas.imports import (
    ImportBatchListResponse,
    ImportBatchRead,
    ImportJobRead,
    ImportJobsResponse,
    QueuedUploadResponse,
)
from app.services.import_queue_service import (
    ImportQueueService,
    import_batch_total,
    process_import_batch,
    serialize_import_batch,
)
from app.services.settings_service import get_runtime_settings

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


@router.post("/imports/upload", response_model=QueuedUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_imports(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
    files: list[UploadFile] = File(...),
    relative_paths: list[str] | None = Form(default=None),
) -> QueuedUploadResponse:
    del current_user
    try:
        batch = await ImportQueueService(get_runtime_settings(db)).create_upload_batch(
            db,
            files,
            relative_paths=relative_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    background_tasks.add_task(process_import_batch, batch.id)
    return QueuedUploadResponse(job_id=batch.id, total=batch.total_items)


@router.get("/jobs", response_model=ImportBatchListResponse)
def list_jobs(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ImportBatchListResponse:
    del current_user
    batches = list(
        db.scalars(
            select(ImportBatch)
            .options(selectinload(ImportBatch.jobs))
            .order_by(ImportBatch.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).unique()
    )
    return ImportBatchListResponse(
        items=[serialize_import_batch(batch) for batch in batches],
        total=import_batch_total(db),
    )


@router.get("/jobs/{job_id}", response_model=ImportBatchRead)
def get_job(job_id: UUID, current_user: CurrentUser, db: DbSession) -> ImportBatchRead:
    del current_user
    batch = db.get(ImportBatch, job_id, options=[selectinload(ImportBatch.jobs)])
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return serialize_import_batch(batch)


@router.post("/jobs/{job_id}/cancel", response_model=ImportBatchRead)
def cancel_job(job_id: UUID, current_user: CurrentUser, db: DbSession) -> ImportBatchRead:
    del current_user
    try:
        batch = ImportQueueService(get_runtime_settings(db)).cancel_batch(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return serialize_import_batch(batch)


@router.post("/jobs/{job_id}/retry", response_model=ImportBatchRead)
def retry_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
) -> ImportBatchRead:
    del current_user
    try:
        batch = ImportQueueService(get_runtime_settings(db)).retry_batch(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background_tasks.add_task(process_import_batch, batch.id)
    return serialize_import_batch(batch)
