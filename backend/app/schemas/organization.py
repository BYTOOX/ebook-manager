from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.book import BookListItem


class CollectionPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CollectionBooksPayload(BaseModel):
    book_ids: list[UUID] = Field(default_factory=list)


class CollectionSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    book_count: int
    cover_book_id: UUID | None = None
    cover_url: str | None = None
    created_at: datetime
    updated_at: datetime


class CollectionDetail(CollectionSummary):
    books: list[BookListItem] = Field(default_factory=list)


class CollectionListResponse(BaseModel):
    items: list[CollectionSummary]
    total: int


class SeriesPayload(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class SeriesSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    book_count: int
    cover_book_id: UUID | None = None
    cover_url: str | None = None
    created_at: datetime
    updated_at: datetime


class SeriesDetail(SeriesSummary):
    books: list[BookListItem] = Field(default_factory=list)


class SeriesListResponse(BaseModel):
    items: list[SeriesSummary]
    total: int


class TagPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=24)


class TagSummary(BaseModel):
    id: UUID
    name: str
    color: str | None = None
    book_count: int
    created_at: datetime


class TagListResponse(BaseModel):
    items: list[TagSummary]
    total: int
