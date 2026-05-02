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
    min_score: float = Field(default=0.85, ge=0, le=1)
    review_margin: float = Field(default=0.04, ge=0, le=1)


MetadataAutoApplyStatus = Literal["applied", "needs_review", "no_match"]


class MetadataAutoApplyResponse(BaseModel):
    status: MetadataAutoApplyStatus
    message: str
    candidate: MetadataCandidate | None = None
    items: list[MetadataCandidate] = Field(default_factory=list)
    total: int = 0
    applied_fields: list[MetadataApplyField] = Field(default_factory=list)
    book: BookDetail | None = None
