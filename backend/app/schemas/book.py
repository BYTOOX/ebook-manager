from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookListItem(BaseModel):
    id: UUID
    title: str
    authors: list[str] = []
    cover_url: str | None = None
    status: str
    rating: int | None = None
    favorite: bool
    progress_percent: float | None = None
    is_offline_available: bool = False
    added_at: datetime
    last_opened_at: datetime | None = None


class BookListResponse(BaseModel):
    items: list[BookListItem]
    total: int


class BookDetail(BookListItem):
    subtitle: str | None = None
    description: str | None = None
    language: str | None = None
    isbn: str | None = None
    publisher: str | None = None
    published_date: str | None = None
    original_filename: str | None = None
    file_size: int | None = None
    metadata_source: str | None = None

    model_config = ConfigDict(from_attributes=True)
