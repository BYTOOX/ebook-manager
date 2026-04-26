from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.book import ReadingProgressOut


class SyncEventIn(BaseModel):
    event_id: UUID
    type: str
    client_created_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncEventsRequest(BaseModel):
    device_id: str | None = None
    events: list[SyncEventIn]


class SyncBookmarkOut(BaseModel):
    id: UUID
    book_id: UUID
    cfi: str
    progress_percent: float | None = None
    chapter_label: str | None = None
    excerpt: str | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class SyncEventResult(BaseModel):
    event_id: UUID
    type: str
    status: str
    resolved: str | None = None
    book_id: UUID | None = None
    progress: ReadingProgressOut | None = None
    bookmark: SyncBookmarkOut | None = None
    error: str | None = None


class SyncEventsResponse(BaseModel):
    ok: bool
    accepted: int
    processed: int
    results: list[SyncEventResult] = Field(default_factory=list)
