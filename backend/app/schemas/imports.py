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

    model_config = ConfigDict(from_attributes=True)


class ImportJobsResponse(BaseModel):
    items: list[ImportJobRead]
    total: int


class UploadBookResponse(BaseModel):
    job_id: UUID
    book_id: UUID | None = None
    status: str
    warning: str | None = None


class ScanRequest(BaseModel):
    path: str | None = None


class ScanResponse(BaseModel):
    scanned: int
    imported: int
    warnings: int
    failed: int
    jobs: list[ImportJobRead]
