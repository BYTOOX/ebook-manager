from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.book import BookDetail


MetadataProvider = Literal["openlibrary", "googlebooks"]
MetadataApplyField = Literal[
    "association",
    "title",
    "subtitle",
    "authors",
    "description",
    "language",
    "isbn",
    "publisher",
    "published_date",
    "cover",
]


class MetadataSearchPayload(BaseModel):
    providers: list[MetadataProvider] = Field(
        default_factory=lambda: ["googlebooks"]
    )
    query: str | None = None
    isbn: str | None = None


class MetadataCandidate(BaseModel):
    id: UUID
    provider: MetadataProvider
    provider_item_id: str | None = None
    score: float = 0
    title: str
    subtitle: str | None = None
    authors: list[str] = Field(default_factory=list)
    description: str | None = None
    language: str | None = None
    isbn: str | None = None
    publisher: str | None = None
    published_date: str | None = None
    cover_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class MetadataSearchResponse(BaseModel):
    items: list[MetadataCandidate] = Field(default_factory=list)
    total: int


class MetadataApplyPayload(BaseModel):
    result_id: UUID
    fields: list[MetadataApplyField] = Field(default_factory=list)


class MetadataAutoApplyPayload(BaseModel):
    providers: list[MetadataProvider] = Field(default_factory=lambda: ["googlebooks"])
    query: str | None = None
    isbn: str | None = None
    fields: list[MetadataApplyField] = Field(
        default_factory=lambda: [
            "association",
            "title",
            "subtitle",
            "authors",
            "description",
            "language",
            "isbn",
            "publisher",
            "published_date",
            "cover",
        ]
    )
    min_score: float = Field(default=0.75, ge=0, le=1)
    review_margin: float = Field(default=0, ge=0, le=1)


MetadataAutoApplyStatus = Literal["applied", "needs_review", "no_match"]
MetadataLibraryAutoApplyStatus = Literal["applied", "needs_review", "no_match", "skipped", "error"]


class MetadataAutoApplyResponse(BaseModel):
    status: MetadataAutoApplyStatus
    message: str
    candidate: MetadataCandidate | None = None
    items: list[MetadataCandidate] = Field(default_factory=list)
    total: int = 0
    applied_fields: list[MetadataApplyField] = Field(default_factory=list)
    book: BookDetail | None = None


class MetadataLibraryAutoApplyPayload(BaseModel):
    providers: list[MetadataProvider] = Field(default_factory=lambda: ["googlebooks"])
    fields: list[MetadataApplyField] = Field(
        default_factory=lambda: [
            "association",
            "title",
            "subtitle",
            "authors",
            "description",
            "language",
            "isbn",
            "publisher",
            "published_date",
            "cover",
        ]
    )
    min_score: float = Field(default=0.75, ge=0, le=1)
    review_margin: float = Field(default=0, ge=0, le=1)
    only_missing_provider: bool = True
    limit: int | None = Field(default=None, ge=1, le=5000)


class MetadataLibraryAutoApplyItem(BaseModel):
    book_id: UUID
    title: str
    status: MetadataLibraryAutoApplyStatus
    message: str
    candidate_title: str | None = None
    candidate_provider_id: str | None = None
    score: float | None = None
    applied_fields: list[MetadataApplyField] = Field(default_factory=list)


class MetadataLibraryAutoApplyResponse(BaseModel):
    scanned: int
    applied: int
    needs_review: int
    no_match: int
    skipped: int
    errors: int
    items: list[MetadataLibraryAutoApplyItem] = Field(default_factory=list)


class MetadataPendingBook(BaseModel):
    id: UUID
    title: str
    authors: list[str] = Field(default_factory=list)


class MetadataPendingBooksResponse(BaseModel):
    items: list[MetadataPendingBook] = Field(default_factory=list)
    total: int
