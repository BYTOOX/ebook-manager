from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Lock, Thread
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.models.import_job import ImportBatch, ImportJob
from app.schemas.imports import ImportBatchRead
from app.services.import_service import ImportService
from app.services.settings_service import get_runtime_settings
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

TERMINAL_JOB_STATUSES = {"success", "warning", "failed", "canceled"}
TERMINAL_BATCH_STATUSES = {"success", "warning", "failed", "canceled"}
_worker_lock = Lock()
_worker_started = False
_worker_stop = Event()


def serialize_import_batch(batch: ImportBatch) -> ImportBatchRead:
    return ImportBatchRead.model_validate(batch)


class ImportQueueService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage = StorageService(settings)

    async def create_upload_batch(
        self,
        db: Session,
        files: list[UploadFile],
        *,
        relative_paths: list[str] | None = None,
    ) -> ImportBatch:
        if not files:
            raise ValueError("At least one EPUB is required")
        max_files = getattr(self.settings, "IMPORT_MAX_FILES_PER_BATCH", 100)
        if len(files) > max_files:
            raise ValueError(f"Batch is limited to {max_files} EPUB files")

        names = [self._safe_relative_path(file, relative_paths, index) for index, file in enumerate(files)]
        for name in names:
            if not name.lower().endswith(".epub"):
                raise ValueError("Only EPUB files are supported")

        self.storage.ensure_layout()
        batch = ImportBatch(status="pending", total_items=len(files), message="Queued upload")
        db.add(batch)
        db.commit()
        db.refresh(batch)

        saved_paths: list[Path] = []
        try:
            for index, file in enumerate(files):
                tmp_path = await self.storage.save_upload_to_tmp(file)
                saved_paths.append(tmp_path)
                db.add(
                    ImportJob(
                        batch_id=batch.id,
                        sort_order=index,
                        source="queued_upload",
                        status="pending",
                        filename=names[index],
                        file_path=str(tmp_path),
                    )
                )
            db.commit()
            db.refresh(batch)
            update_batch_counts(db, batch.id)
            return batch
        except Exception:
            for path in saved_paths:
                path.unlink(missing_ok=True)
            db.delete(batch)
            db.commit()
            raise

    def _safe_relative_path(
        self,
        file: UploadFile,
        relative_paths: list[str] | None,
        index: int,
    ) -> str:
        candidate = relative_paths[index] if relative_paths and index < len(relative_paths) else file.filename
        name = (candidate or file.filename or f"book-{index + 1}.epub").replace("\\", "/").strip("/")
        parts = [part for part in name.split("/") if part and part not in {".", ".."}]
        return "/".join(parts) or f"book-{index + 1}.epub"

    def cancel_batch(self, db: Session, batch_id: UUID) -> ImportBatch:
        batch = _batch_or_raise(db, batch_id)
        if batch.status in TERMINAL_BATCH_STATUSES:
            return batch
        batch.status = "canceled"
        batch.finished_at = datetime.now(UTC)
        batch.message = "Canceled"
        for job in batch.jobs:
            if job.status in {"pending", "running"}:
                job.status = "canceled"
                job.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(batch)
        update_batch_counts(db, batch.id)
        return batch

    def retry_batch(self, db: Session, batch_id: UUID) -> ImportBatch:
        batch = _batch_or_raise(db, batch_id)
        retryable = 0
        for job in batch.jobs:
            if job.status in {"failed", "canceled"} and job.file_path and Path(job.file_path).exists():
                job.status = "pending"
                job.error_message = None
                job.started_at = None
                job.finished_at = None
                retryable += 1
        if retryable == 0:
            raise ValueError("No retryable import item remains")
        batch.status = "pending"
        batch.finished_at = None
        batch.message = "Retry queued"
        db.commit()
        db.refresh(batch)
        update_batch_counts(db, batch.id)
        return batch

    def reset_running(self, db: Session) -> None:
        for job in db.scalars(select(ImportJob).where(ImportJob.status == "running")):
            job.status = "pending"
            job.error_message = "Resumed after backend restart"
            db.add(job)
        for batch in db.scalars(select(ImportBatch).where(ImportBatch.status == "running")):
            batch.status = "pending"
            batch.message = "Resumed after backend restart"
            db.add(batch)
        db.commit()


def _batch_or_raise(db: Session, batch_id: UUID) -> ImportBatch:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise ValueError("Import job not found")
    return batch


def update_batch_counts(db: Session, batch_id: UUID) -> ImportBatch:
    batch = _batch_or_raise(db, batch_id)
    jobs = list(batch.jobs)
    batch.total_items = len(jobs)
    batch.success_count = sum(1 for job in jobs if job.status == "success")
    batch.warning_count = sum(1 for job in jobs if job.status == "warning")
    batch.failed_count = sum(1 for job in jobs if job.status == "failed")
    batch.canceled_count = sum(1 for job in jobs if job.status == "canceled")
    batch.processed_items = sum(1 for job in jobs if job.status in TERMINAL_JOB_STATUSES)
    batch.progress_percent = (
        round((batch.processed_items / batch.total_items) * 100, 3) if batch.total_items else 0
    )
    if batch.processed_items == batch.total_items and batch.total_items > 0:
        batch.finished_at = batch.finished_at or datetime.now(UTC)
        if batch.failed_count:
            batch.status = "failed"
            batch.message = f"{batch.failed_count} import(s) failed"
        elif batch.canceled_count and not (batch.success_count or batch.warning_count):
            batch.status = "canceled"
            batch.message = "Canceled"
        elif batch.warning_count:
            batch.status = "warning"
            batch.message = f"{batch.warning_count} warning(s)"
        else:
            batch.status = "success"
            batch.message = "Import complete"
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def process_import_batch(batch_id: UUID) -> None:
    with SessionLocal() as db:
        batch = db.get(
            ImportBatch,
            batch_id,
            options=[selectinload(ImportBatch.jobs)],
        )
        if batch is None or batch.status in TERMINAL_BATCH_STATUSES:
            return
        batch.status = "running"
        batch.started_at = batch.started_at or datetime.now(UTC)
        batch.message = "Import running"
        db.commit()

        settings = get_runtime_settings(db)
        service = ImportService(settings)
        jobs = list(
            db.scalars(
                select(ImportJob)
                .where(ImportJob.batch_id == batch_id)
                .order_by(ImportJob.sort_order.asc(), ImportJob.created_at.asc())
            )
        )
        for job in jobs:
            db.refresh(batch)
            if batch.status == "canceled":
                if job.status == "pending":
                    job.status = "canceled"
                    job.finished_at = datetime.now(UTC)
                    db.add(job)
                    db.commit()
                continue
            if job.status != "pending":
                continue
            try:
                path = Path(job.file_path or "")
                service.run_import_job(
                    db,
                    job,
                    path,
                    original_filename=job.filename,
                    remove_source=False,
                )
                if job.status in {"success", "warning"}:
                    path.unlink(missing_ok=True)
            except Exception as exc:
                db.rollback()
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.now(UTC)
                db.add(job)
                db.commit()
            update_batch_counts(db, batch_id)
        update_batch_counts(db, batch_id)


def process_next_pending_batch() -> bool:
    with SessionLocal() as db:
        batch_id = db.scalar(
            select(ImportBatch.id)
            .where(ImportBatch.status == "pending")
            .order_by(ImportBatch.created_at.asc())
            .limit(1)
        )
    if batch_id is None:
        return False
    process_import_batch(batch_id)
    return True


def start_import_worker() -> None:
    global _worker_started
    settings = get_settings()
    if settings.DATABASE_URL.startswith("sqlite"):
        return
    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True
        Thread(target=_worker_loop, name="aurelia-import-worker", daemon=True).start()


def _worker_loop() -> None:
    while not _worker_stop.wait(2.0):
        try:
            process_next_pending_batch()
        except Exception as exc:
            logger.warning("import worker iteration failed: %s", exc)


def import_batch_total(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(ImportBatch)) or 0
