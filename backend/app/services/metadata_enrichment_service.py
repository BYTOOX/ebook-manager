from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.book import Author, Book, BookAuthor, BookSeries, BookTag, Tag
from app.models.metadata import MetadataProviderResult
from app.schemas.metadata import (
    MetadataApplyField,
    MetadataAutoApplyResponse,
    MetadataCandidate,
    MetadataLibraryAutoApplyItem,
    MetadataLibraryAutoApplyResponse,
    MetadataPendingBook,
    MetadataPendingBooksResponse,
    MetadataProvider,
    MetadataSearchPayload,
)
from app.services.epub_service import clean_metadata_text
from app.services.metadata_service import MetadataService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

DEFAULT_AUTO_METADATA_FIELDS: list[MetadataApplyField] = [
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
METADATA_ENRICHED_TAG = "metadonnees-enrichies"
METADATA_ENRICHED_TAG_COLOR = "#f5c542"


@dataclass
class AutoEnrichmentResult:
    status: str
    message: str
    candidate: MetadataCandidate | None = None
    items: list[MetadataCandidate] = field(default_factory=list)
    total: int = 0
    applied_fields: list[MetadataApplyField] = field(default_factory=list)


class MetadataEnrichmentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.metadata = MetadataService(settings)
        self.storage = StorageService(settings)

    def auto_enrich_book(
        self,
        db: Session,
        book: Book,
        *,
        providers: list[MetadataProvider] | None = None,
        query: str | None = None,
        isbn: str | None = None,
        fields: list[MetadataApplyField] | None = None,
        min_score: float = 0.75,
        review_margin: float = 0,
    ) -> AutoEnrichmentResult:
        requested_fields = fields or DEFAULT_AUTO_METADATA_FIELDS
        candidates = self.metadata.search_candidates(
            db,
            book,
            MetadataSearchPayload(
                providers=providers or ["googlebooks"],
                query=query,
                isbn=isbn,
            ),
        )
        if not candidates:
            return AutoEnrichmentResult(status="no_match", message="Aucune proposition trouvee")

        best = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None
        if best.score < min_score:
            return AutoEnrichmentResult(
                status="needs_review",
                message=f"Meilleur score trop bas ({round(best.score * 100)}%)",
                candidate=best,
                items=candidates,
                total=len(candidates),
            )
        if review_margin > 0 and second and best.score - second.score < review_margin:
            return AutoEnrichmentResult(
                status="needs_review",
                message="Plusieurs propositions proches, verification conseillee",
                candidate=best,
                items=candidates,
                total=len(candidates),
            )

        result = db.get(MetadataProviderResult, best.id)
        if result is None or result.book_id != book.id:
            return AutoEnrichmentResult(
                status="needs_review",
                message="La proposition selectionnee n'est plus disponible",
                candidate=best,
                items=candidates,
                total=len(candidates),
            )

        candidate = result.normalized_json if isinstance(result.normalized_json, dict) else {}
        available_fields = _available_metadata_fields(candidate, requested_fields)
        if not available_fields:
            return AutoEnrichmentResult(
                status="needs_review",
                message="La proposition ne contient aucun champ applicable",
                candidate=best,
                items=candidates,
                total=len(candidates),
            )

        applied = self.apply_metadata_candidate(db, book, result, set(available_fields))
        return AutoEnrichmentResult(
            status="applied",
            message=f"Association appliquee automatiquement ({round(best.score * 100)}%)",
            candidate=best,
            items=candidates,
            total=len(candidates),
            applied_fields=applied,
        )

    def auto_enrich_library(
        self,
        db: Session,
        *,
        providers: list[MetadataProvider] | None = None,
        fields: list[MetadataApplyField] | None = None,
        min_score: float = 0.75,
        review_margin: float = 0,
        only_missing_provider: bool = True,
        limit: int | None = None,
    ) -> MetadataLibraryAutoApplyResponse:
        conditions = [Book.deleted_at.is_(None)]
        if only_missing_provider:
            conditions.append(Book.metadata_provider_id.is_(None))
        conditions.append(_book_lacks_enriched_tag())
        query = (
            select(Book)
            .options(
                selectinload(Book.book_authors).selectinload(BookAuthor.author),
                selectinload(Book.book_series).selectinload(BookSeries.series),
            )
            .where(*conditions)
            .order_by(Book.added_at.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        books = list(db.scalars(query).unique())
        items: list[MetadataLibraryAutoApplyItem] = []
        applied = 0
        needs_review = 0
        no_match = 0
        skipped = 0
        errors = 0

        for book in books:
            if only_missing_provider and book.metadata_provider_id:
                skipped += 1
                items.append(
                    MetadataLibraryAutoApplyItem(
                        book_id=book.id,
                        title=book.title,
                        status="skipped",
                        message="Deja associe",
                    )
                )
                continue

            try:
                result = self.auto_enrich_book(
                    db,
                    book,
                    providers=providers,
                    fields=fields,
                    min_score=min_score,
                    review_margin=review_margin,
                )
                db.commit()
                if result.status == "applied":
                    applied += 1
                elif result.status == "needs_review":
                    needs_review += 1
                else:
                    no_match += 1
                items.append(_library_item_from_result(book.id, book.title, result))
            except Exception as exc:
                db.rollback()
                logger.warning("library metadata enrichment failed for %s: %s", book.id, exc)
                errors += 1
                items.append(
                    MetadataLibraryAutoApplyItem(
                        book_id=book.id,
                        title=book.title,
                        status="error",
                        message=str(exc),
                    )
                )

        return MetadataLibraryAutoApplyResponse(
            scanned=len(books),
            applied=applied,
            needs_review=needs_review,
            no_match=no_match,
            skipped=skipped,
            errors=errors,
            items=items,
        )

    def pending_books(
        self,
        db: Session,
        *,
        limit: int = 5000,
    ) -> MetadataPendingBooksResponse:
        conditions = [
            Book.deleted_at.is_(None),
            Book.metadata_provider_id.is_(None),
            _book_lacks_enriched_tag(),
        ]
        total = db.scalar(select(func.count()).select_from(Book).where(*conditions)) or 0
        books = list(
            db.scalars(
                select(Book)
                .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
                .where(*conditions)
                .order_by(Book.added_at.asc())
                .limit(limit)
            ).unique()
        )
        return MetadataPendingBooksResponse(
            items=[
                MetadataPendingBook(
                    id=book.id,
                    title=book.title,
                    authors=[link.author.name for link in book.book_authors if link.author],
                )
                for book in books
            ],
            total=total,
        )

    def apply_metadata_candidate(
        self,
        db: Session,
        book: Book,
        result: MetadataProviderResult,
        fields: set[MetadataApplyField],
    ) -> list[MetadataApplyField]:
        candidate = result.normalized_json if isinstance(result.normalized_json, dict) else {}
        applied: list[MetadataApplyField] = []

        if "title" in fields:
            title = _clean_candidate_text(candidate.get("title"))
            if title:
                book.title = title
                applied.append("title")
        if "subtitle" in fields:
            book.subtitle = _clean_candidate_text(candidate.get("subtitle"))
            applied.append("subtitle")
        if "authors" in fields:
            authors = candidate.get("authors") if isinstance(candidate.get("authors"), list) else []
            if authors:
                _set_book_authors(db, book, [str(author) for author in authors])
                applied.append("authors")
        if "description" in fields:
            description = clean_metadata_text(_clean_candidate_text(candidate.get("description")))
            if description:
                book.description = description
                applied.append("description")
        if "language" in fields:
            language = _clean_candidate_text(candidate.get("language"))
            if language:
                book.language = language
                applied.append("language")
        if "isbn" in fields:
            isbn = _clean_candidate_text(candidate.get("isbn"))
            if isbn:
                book.isbn = isbn
                applied.append("isbn")
        if "publisher" in fields:
            publisher = _clean_candidate_text(candidate.get("publisher"))
            if publisher:
                book.publisher = publisher
                applied.append("publisher")
        if "published_date" in fields:
            published_date = _clean_candidate_text(candidate.get("published_date"))
            if published_date:
                book.published_date = published_date
                applied.append("published_date")
        if "cover" in fields:
            cover_url = _clean_candidate_text(candidate.get("cover_url"))
            if cover_url:
                cover_bytes = self.metadata.download_cover(cover_url)
                cover_path = self.storage.save_cover_jpeg(cover_bytes, book.id) if cover_bytes else None
                if cover_path:
                    book.cover_path = str(cover_path)
                    book.updated_at = datetime.now(timezone.utc)
                    applied.append("cover")

        if "association" in fields or applied:
            book.metadata_source = result.provider
            book.metadata_provider_id = result.provider_item_id
            if "association" in fields:
                applied.insert(0, "association")
            mark_book_metadata_enriched(db, book)

        return applied


def auto_result_to_response(
    result: AutoEnrichmentResult,
    *,
    book=None,
) -> MetadataAutoApplyResponse:
    return MetadataAutoApplyResponse(
        status=result.status,
        message=result.message,
        candidate=result.candidate,
        items=result.items,
        total=result.total,
        applied_fields=result.applied_fields,
        book=book,
    )


def _library_item_from_result(
    book_id: UUID,
    title: str,
    result: AutoEnrichmentResult,
) -> MetadataLibraryAutoApplyItem:
    return MetadataLibraryAutoApplyItem(
        book_id=book_id,
        title=title,
        status=result.status,
        message=result.message,
        candidate_title=result.candidate.title if result.candidate else None,
        candidate_provider_id=result.candidate.provider_item_id if result.candidate else None,
        score=result.candidate.score if result.candidate else None,
        applied_fields=result.applied_fields,
    )


def _clean_candidate_text(value: object) -> str | None:
    if value is None:
        return None
    return clean_metadata_text(str(value))


def _candidate_has_field(candidate: dict[str, object], field: MetadataApplyField) -> bool:
    if field == "association":
        return True
    if field == "authors":
        authors = candidate.get("authors")
        return isinstance(authors, list) and any(str(author).strip() for author in authors)
    if field == "cover":
        return bool(_clean_candidate_text(candidate.get("cover_url")))
    return bool(_clean_candidate_text(candidate.get(field)))


def _available_metadata_fields(
    candidate: dict[str, object],
    requested_fields: list[MetadataApplyField],
) -> list[MetadataApplyField]:
    return [field for field in requested_fields if _candidate_has_field(candidate, field)]


def _set_book_authors(db: Session, book: Book, author_names: list[str]) -> None:
    cleaned: list[str] = []
    seen: set[str] = set()
    for name in author_names:
        clean_name = name.strip()
        if not clean_name:
            continue
        key = clean_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(clean_name)

    book.book_authors.clear()
    for position, name in enumerate(cleaned):
        author = db.scalar(select(Author).where(func.lower(Author.name) == name.lower()))
        if author is None:
            author = Author(name=name)
            db.add(author)
            db.flush()
        book.book_authors.append(BookAuthor(author=author, position=position))


def _book_lacks_enriched_tag():
    return ~Book.book_tags.any(
        BookTag.tag.has(func.lower(Tag.name) == METADATA_ENRICHED_TAG.lower())
    )


def mark_book_metadata_enriched(db: Session, book: Book) -> None:
    if any(
        link.tag and link.tag.name.casefold() == METADATA_ENRICHED_TAG.casefold()
        for link in book.book_tags
    ):
        return

    tag = db.scalar(select(Tag).where(func.lower(Tag.name) == METADATA_ENRICHED_TAG.lower()))
    if tag is None:
        tag = Tag(name=METADATA_ENRICHED_TAG, color=METADATA_ENRICHED_TAG_COLOR)
        db.add(tag)
        db.flush()

    book.book_tags.append(BookTag(tag=tag))
