from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Author(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str


class Series(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    index_in_series: float | None = None


class Bookmark(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    book_id: str
    location: str
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReadingProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    book_id: str
    current_location: str
    percent: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: Literal["phone", "tablet", "desktop", "ereader"]
    last_sync_at: datetime | None = None


class Book(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str | None = None
    authors: list[Author] = Field(default_factory=list)
    series: Series | None = None
    tags: list[str] = Field(default_factory=list)
    format: Literal["epub", "pdf"]
    file_path: str
    cover_path: str | None = None
    bookmarks: list[Bookmark] = Field(default_factory=list)
    reading_progress: ReadingProgress | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
