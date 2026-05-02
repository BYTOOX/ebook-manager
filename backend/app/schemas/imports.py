from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportJobRead(BaseModel):
    id: UUID
    source: str
    status: str
    filename: str | None = None
    file_path: str | None = None
    error_message: str | None = None
    result_book_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ImportJobsResponse(BaseModel):
    items: list[ImportJobRead]
    total: int


class UploadBookResponse(BaseModel):
    job_id: UUID
    book_id: UUID | None = None
    status: str
    warning: str | None = None


class ImportBatchRead(BaseModel):
    id: UUID
    status: str
    total_items: int
    processed_items: int
    success_count: int
    warning_count: int
    failed_count: int
    canceled_count: int
    progress_percent: float
    message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    updated_at: datetime
    finished_at: datetime | None = None
    jobs: list[ImportJobRead] = []

    model_config = ConfigDict(from_attributes=True)


class ImportBatchListResponse(BaseModel):
    items: list[ImportBatchRead]
    total: int


class QueuedUploadResponse(BaseModel):
    job_id: UUID
    total: int
