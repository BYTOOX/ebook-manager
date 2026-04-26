from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


MetadataProvider = Literal["openlibrary", "googlebooks"]
MetadataApplyField = Literal[
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
        default_factory=lambda: ["openlibrary", "googlebooks"]
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
