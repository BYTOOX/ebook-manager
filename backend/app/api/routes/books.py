from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.book import Author, Book, BookAuthor, BookSeries, BookTag, Series, Tag
from app.models.metadata import MetadataProviderResult
from app.models.reading import ReadingProgress
from app.schemas.book import (
    BookDetail,
    BookListItem,
    BookListResponse,
    BookSeriesInfo,
    BookUpdate,
    ReadingProgressOut,
    ReadingProgressPayload,
    ReadingProgressResponse,
)
from app.schemas.imports import UploadBookResponse
from app.schemas.metadata import MetadataApplyPayload, MetadataSearchPayload, MetadataSearchResponse
from app.services.epub_service import EpubService, clean_metadata_text
from app.services.import_service import ImportService
from app.services.metadata_service import MetadataService
from app.services.progress_service import apply_reading_progress, serialize_progress
from app.services.storage_service import StorageService

router = APIRouter()


def book_cover_url(book: Book) -> str | None:
    if not book.cover_path:
        return None
    version_source = book.updated_at or book.added_at
    version = int(version_source.timestamp() * 1000) if version_source else 0
    return f"/api/v1/books/{book.id}/cover?v={version}"


def serialize_book(book: Book, progress_percent: float | None = None) -> BookListItem:
    authors = [link.author.name for link in book.book_authors]
    return BookListItem(
        id=book.id,
        title=book.title,
        authors=authors,
        cover_url=book_cover_url(book),
        status=book.status,
        rating=book.rating,
        favorite=book.favorite,
        progress_percent=progress_percent,
        is_offline_available=False,
        added_at=book.added_at,
        last_opened_at=book.last_opened_at,
    )


def _get_book_or_404(db: Session, book_id: UUID) -> Book:
    book = db.get(Book, book_id)
    if book is None or book.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def _metadata_snapshot(book: Book) -> dict[str, object]:
    metadata_path = Path(book.file_path).with_name("metadata.json")
    if not metadata_path.exists():
        return {}
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _list_from_metadata(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = clean_metadata_text(str(item)) if item is not None else None
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _clean_candidate_text(value: object) -> str | None:
    if value is None:
        return None
    return clean_metadata_text(str(value))


def _epub_metadata_lists(book: Book) -> tuple[list[str], list[str]]:
    path = Path(book.file_path)
    if not path.exists():
        return [], []
    try:
        metadata = EpubService().extract_metadata(path)
    except Exception:
        return [], []
    return metadata.subjects, metadata.contributors


def _series_from_filename(filename: str | None) -> tuple[str | None, float | None]:
    if not filename:
        return None, None
    parts = Path(filename).parts
    if len(parts) < 2:
        return None, None

    series_name = parts[0].strip()
    if not series_name:
        return None, None

    name = Path(parts[-1]).stem
    match = re.search(r"\b(?:tome|vol(?:ume)?|livre)\s*0*([0-9]{1,3})\b", name, re.IGNORECASE)
    if not match:
        match = re.search(r"\b[A-Za-z][A-Za-z _-]+0*([0-9]{1,3})\b", name)
    if not match:
        match = re.search(r"^0*([0-9]{1,3})(?:\s*[-_.]|$)", name)
    return series_name, float(match.group(1)) if match else None


def _related_books_for_series(db: Session, book: Book, series_name: str | None) -> list[BookListItem]:
    if not series_name:
        return []

    books = db.scalars(
        select(Book)
        .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
        .where(
            Book.deleted_at.is_(None),
            Book.id != book.id,
            Book.original_filename.ilike(f"{series_name}/%"),
        )
        .order_by(func.lower(Book.original_filename), Book.added_at.desc())
        .limit(24)
    ).unique()
    return [serialize_book(related) for related in books]


def _related_books_for_stored_series(db: Session, book: Book) -> list[BookListItem]:
    if not book.book_series:
        return []
    books = db.scalars(
        select(Book)
        .join(BookSeries, BookSeries.book_id == Book.id)
        .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
        .where(
            Book.deleted_at.is_(None),
            Book.id != book.id,
            BookSeries.series_id == book.book_series.series_id,
        )
        .order_by(BookSeries.series_index.asc().nulls_last(), func.lower(Book.title))
        .limit(24)
    ).unique()
    return [serialize_book(related) for related in books]


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


def _set_book_series(
    db: Session,
    book: Book,
    series_name: str | None,
    series_index: float | None,
) -> None:
    clean_name = series_name.strip() if series_name else ""
    if not clean_name:
        book.book_series = None
        return

    series = db.scalar(select(Series).where(func.lower(Series.name) == clean_name.lower()))
    if series is None:
        series = Series(name=clean_name)
        db.add(series)
        db.flush()

    if book.book_series is None:
        book.book_series = BookSeries(book_id=book.id)
    book.book_series.series_id = series.id
    book.book_series.series_index = (
        Decimal(str(series_index)) if series_index is not None else None
    )
    book.book_series.series_label = "manual"


def _set_book_tags(db: Session, book: Book, tag_names: list[str]) -> None:
    cleaned: list[str] = []
    seen: set[str] = set()
    for name in tag_names:
        clean_name = name.strip()
        if not clean_name:
            continue
        key = clean_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(clean_name[:80])

    book.book_tags.clear()
    for name in cleaned:
        tag = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        book.book_tags.append(BookTag(tag=tag))


def _book_series_info(book: Book) -> BookSeriesInfo | None:
    if book.book_series and book.book_series.series:
        return BookSeriesInfo(
            name=book.book_series.series.name,
            index=float(book.book_series.series_index)
            if book.book_series.series_index is not None
            else None,
            source=book.book_series.series_label or "manual",
        )

    series_name, series_index = _series_from_filename(book.original_filename)
    return (
        BookSeriesInfo(name=series_name, index=series_index, source="import_path")
        if series_name
        else None
    )


@router.get("", response_model=BookListResponse)
def list_books(
    current_user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None),
    book_status: str | None = Query(default=None, alias="status"),
    favorite: bool | None = Query(default=None),
    tag: str | None = Query(default=None),
    sort: str = Query(default="added_at"),
    order: str = Query(default="desc"),
    limit: int = Query(default=24, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> BookListResponse:
    order = order.lower()
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order")

    sort_columns = {
        "added_at": Book.added_at,
        "title": func.lower(Book.title),
        "last_opened_at": Book.last_opened_at,
        "rating": Book.rating,
    }
    sort_column = sort_columns.get(sort)
    if sort_column is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort")

    conditions = [Book.deleted_at.is_(None)]
    if book_status:
        conditions.append(Book.status == book_status)
    if favorite is not None:
        conditions.append(Book.favorite == favorite)
    clean_tag = tag.strip() if tag else ""
    if clean_tag:
        conditions.append(Book.book_tags.any(BookTag.tag.has(func.lower(Tag.name) == clean_tag.lower())))

    clean_query = q.strip() if q else ""
    if clean_query:
        pattern = f"%{clean_query}%"
        conditions.append(
            or_(
                Book.title.ilike(pattern),
                Book.subtitle.ilike(pattern),
                Book.original_filename.ilike(pattern),
                Book.isbn.ilike(pattern),
                Book.publisher.ilike(pattern),
                Book.book_authors.any(BookAuthor.author.has(Author.name.ilike(pattern))),
            )
        )

    total = db.scalar(select(func.count()).select_from(Book).where(*conditions)) or 0
    sort_expression = sort_column.asc() if order == "asc" else sort_column.desc()
    if sort in {"last_opened_at", "rating"}:
        sort_expression = sort_expression.nulls_last()
    books = list(
        db.scalars(
            select(Book)
            .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
            .where(*conditions)
            .order_by(sort_expression, Book.added_at.desc())
            .limit(limit)
            .offset(offset)
        ).unique()
    )
    progress_by_book: dict[UUID, float] = {}
    if books:
        progress_rows = db.scalars(
            select(ReadingProgress).where(
                ReadingProgress.user_id == current_user.id,
                ReadingProgress.book_id.in_([book.id for book in books]),
            )
        )
        progress_by_book = {
            row.book_id: float(row.progress_percent)
            for row in progress_rows
            if row.progress_percent is not None
        }

    return BookListResponse(
        items=[serialize_book(book, progress_by_book.get(book.id)) for book in books],
        total=total,
    )


@router.get("/{book_id}/progress", response_model=ReadingProgressOut)
def get_book_progress(
    book_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ReadingProgressOut:
    _get_book_or_404(db, book_id)
    reading_progress = db.scalar(
        select(ReadingProgress).where(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.book_id == book_id,
        )
    )
    return serialize_progress(reading_progress)


@router.put("/{book_id}/progress", response_model=ReadingProgressResponse)
def put_book_progress(
    book_id: UUID,
    payload: ReadingProgressPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> ReadingProgressResponse:
    book = _get_book_or_404(db, book_id)
    resolved, progress = apply_reading_progress(
        db,
        user_id=current_user.id,
        book=book,
        payload=payload,
    )
    db.commit()
    db.refresh(progress)
    return ReadingProgressResponse(ok=True, resolved=resolved, progress=serialize_progress(progress))


@router.patch("/{book_id}", response_model=BookDetail)
def update_book(
    book_id: UUID,
    payload: BookUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> BookDetail:
    book = _get_book_or_404(db, book_id)
    fields = payload.model_fields_set

    if "title" in fields:
        title = (payload.title or "").strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
        book.title = title
    if "authors" in fields:
        _set_book_authors(db, book, payload.authors or [])
    if "series_name" in fields or "series_index" in fields:
        current_name = book.book_series.series.name if book.book_series and book.book_series.series else None
        current_index = (
            float(book.book_series.series_index)
            if book.book_series and book.book_series.series_index is not None
            else None
        )
        _set_book_series(
            db,
            book,
            payload.series_name if "series_name" in fields else current_name,
            payload.series_index if "series_index" in fields else current_index,
        )
    if "tags" in fields:
        _set_book_tags(db, book, payload.tags or [])
    if "status" in fields:
        if payload.status not in {"unread", "in_progress", "finished", "abandoned"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        book.status = payload.status
    if "rating" in fields:
        if payload.rating is not None and not 0 <= payload.rating <= 5:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rating")
        book.rating = payload.rating
    if "favorite" in fields:
        book.favorite = bool(payload.favorite)

    db.commit()
    db.refresh(book)
    return get_book(book_id, current_user, db)


@router.post("/upload", response_model=UploadBookResponse, status_code=status.HTTP_201_CREATED)
async def upload_book(
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession,
) -> UploadBookResponse:
    del current_user
    if not file.filename or not file.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only EPUB files are supported")

    service = ImportService(get_settings())
    try:
        tmp_path = await service.storage.save_upload_to_tmp(file)
        job = service.import_epub(
            db,
            tmp_path,
            source="upload",
            original_filename=file.filename,
            remove_source=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UploadBookResponse(
        job_id=job.id,
        book_id=job.result_book_id,
        status=job.status,
        warning=job.error_message if job.status == "warning" else None,
    )


@router.post("/{book_id}/metadata/search", response_model=MetadataSearchResponse)
def search_book_metadata(
    book_id: UUID,
    payload: MetadataSearchPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> MetadataSearchResponse:
    del current_user
    book = _get_book_or_404(db, book_id)
    service = MetadataService(get_settings())
    candidates = service.search_candidates(db, book, payload)
    db.commit()
    return MetadataSearchResponse(items=candidates, total=len(candidates))


@router.post("/{book_id}/metadata/apply", response_model=BookDetail)
def apply_book_metadata(
    book_id: UUID,
    payload: MetadataApplyPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> BookDetail:
    book = _get_book_or_404(db, book_id)
    fields = set(payload.fields)
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No metadata fields selected")

    result = db.get(MetadataProviderResult, payload.result_id)
    if result is None or result.book_id != book.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metadata result not found")
    candidate = result.normalized_json if isinstance(result.normalized_json, dict) else {}

    if "title" in fields:
        title = _clean_candidate_text(candidate.get("title"))
        if title:
            book.title = title
    if "subtitle" in fields:
        book.subtitle = _clean_candidate_text(candidate.get("subtitle"))
    if "authors" in fields:
        authors = candidate.get("authors") if isinstance(candidate.get("authors"), list) else []
        _set_book_authors(db, book, [str(author) for author in authors])
    if "description" in fields:
        book.description = clean_metadata_text(_clean_candidate_text(candidate.get("description")))
    if "language" in fields:
        book.language = _clean_candidate_text(candidate.get("language"))
    if "isbn" in fields:
        book.isbn = _clean_candidate_text(candidate.get("isbn"))
    if "publisher" in fields:
        book.publisher = _clean_candidate_text(candidate.get("publisher"))
    if "published_date" in fields:
        book.published_date = _clean_candidate_text(candidate.get("published_date"))
    if "cover" in fields:
        cover_url = _clean_candidate_text(candidate.get("cover_url"))
        if not cover_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider cover not available")
        cover_bytes = MetadataService(get_settings()).download_cover(cover_url)
        if not cover_bytes:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Provider cover download failed")
        cover_path = StorageService(get_settings()).save_cover_jpeg(cover_bytes, book.id)
        if not cover_path:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Provider cover could not be saved")
        book.cover_path = str(cover_path)
        book.updated_at = datetime.now(timezone.utc)

    book.metadata_source = result.provider
    book.metadata_provider_id = result.provider_item_id
    db.commit()
    db.refresh(book)
    return get_book(book_id, current_user, db)


@router.get("/{book_id}", response_model=BookDetail)
def get_book(book_id: UUID, current_user: CurrentUser, db: DbSession) -> BookDetail:
    book = _get_book_or_404(db, book_id)

    progress = db.scalar(
        select(ReadingProgress).where(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.book_id == book.id,
        )
    )
    item = serialize_book(
        book,
        float(progress.progress_percent) if progress and progress.progress_percent is not None else None,
    )
    snapshot = _metadata_snapshot(book)
    subjects = _list_from_metadata(snapshot.get("subjects"))
    contributors = _list_from_metadata(snapshot.get("contributors"))
    if not subjects and not contributors:
        subjects, contributors = _epub_metadata_lists(book)

    series = _book_series_info(book)
    related_books = (
        _related_books_for_stored_series(db, book)
        if series and series.source == "manual"
        else _related_books_for_series(db, book, series.name if series else None)
    )

    return BookDetail(
        **item.model_dump(),
        subtitle=book.subtitle,
        description=clean_metadata_text(book.description),
        language=book.language,
        isbn=book.isbn,
        publisher=book.publisher,
        published_date=book.published_date,
        original_filename=book.original_filename,
        file_size=book.file_size,
        metadata_source=book.metadata_source,
        series=series,
        related_books=related_books,
        subjects=subjects,
        contributors=contributors,
        characters=[],
        tags=sorted(link.tag.name for link in book.book_tags),
    )


@router.get("/{book_id}/file")
def get_book_file(book_id: UUID, current_user: CurrentUser, db: DbSession) -> FileResponse:
    del current_user
    book = _get_book_or_404(db, book_id)

    path = Path(book.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPUB file not found")

    filename = book.original_filename or f"{book.id}.epub"
    return FileResponse(path, media_type="application/epub+zip", filename=filename)


@router.get("/{book_id}/cover")
def get_book_cover(book_id: UUID, current_user: CurrentUser, db: DbSession) -> FileResponse:
    del current_user
    book = _get_book_or_404(db, book_id)
    if not book.cover_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")

    path = Path(book.cover_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")

    return FileResponse(path, media_type="image/jpeg")
