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


class BookSeriesInfo(BaseModel):
    name: str
    index: float | None = None
    source: str


class BookUpdate(BaseModel):
    title: str | None = None
    authors: list[str] | None = None
    series_name: str | None = None
    series_index: float | None = None
    tags: list[str] | None = None
    status: str | None = None
    rating: int | None = None
    favorite: bool | None = None


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
    series: BookSeriesInfo | None = None
    related_books: list[BookListItem] = []
    subjects: list[str] = []
    contributors: list[str] = []
    characters: list[str] = []
    tags: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class ReadingProgressPayload(BaseModel):
    cfi: str | None = None
    progress_percent: float | None = None
    chapter_label: str | None = None
    chapter_href: str | None = None
    location_json: dict | None = None
    device_id: str | None = None
    client_updated_at: datetime | None = None


class ReadingProgressOut(BaseModel):
    cfi: str | None = None
    progress_percent: float | None = None
    chapter_label: str | None = None
    chapter_href: str | None = None
    location_json: dict | None = None
    device_id: str | None = None
    updated_at: datetime | None = None


class ReadingProgressResponse(BaseModel):
    ok: bool
    resolved: str
    progress: ReadingProgressOut
