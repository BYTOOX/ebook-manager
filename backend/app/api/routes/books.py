from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.book import Author, Book, BookAuthor
from app.models.reading import ReadingProgress
from app.schemas.book import BookDetail, BookListItem, BookListResponse, BookSeriesInfo
from app.schemas.imports import UploadBookResponse
from app.services.epub_service import EpubService, clean_metadata_text
from app.services.import_service import ImportService

router = APIRouter()


def serialize_book(book: Book, progress_percent: float | None = None) -> BookListItem:
    authors = [link.author.name for link in book.book_authors]
    return BookListItem(
        id=book.id,
        title=book.title,
        authors=authors,
        cover_url=f"/api/v1/books/{book.id}/cover" if book.cover_path else None,
        status=book.status,
        rating=book.rating,
        favorite=book.favorite,
        progress_percent=progress_percent,
        is_offline_available=False,
        added_at=book.added_at,
        last_opened_at=book.last_opened_at,
    )


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


@router.get("", response_model=BookListResponse)
def list_books(
    current_user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None),
    book_status: str | None = Query(default=None, alias="status"),
    favorite: bool | None = Query(default=None),
    sort: str = Query(default="added_at"),
    order: str = Query(default="desc"),
    limit: int = Query(default=24, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> BookListResponse:
    del current_user
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
    books = db.scalars(
        select(Book)
        .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
        .where(*conditions)
        .order_by(sort_expression, Book.added_at.desc())
        .limit(limit)
        .offset(offset)
    ).unique()
    return BookListResponse(items=[serialize_book(book) for book in books], total=total)


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


@router.get("/{book_id}", response_model=BookDetail)
def get_book(book_id: UUID, current_user: CurrentUser, db: DbSession) -> BookDetail:
    book = db.get(Book, book_id)
    if book is None or book.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

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

    series_name, series_index = _series_from_filename(book.original_filename)
    related_books = _related_books_for_series(db, book, series_name)

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
        series=BookSeriesInfo(name=series_name, index=series_index, source="import_path")
        if series_name
        else None,
        related_books=related_books,
        subjects=subjects,
        contributors=contributors,
        characters=[],
    )


@router.get("/{book_id}/file")
def get_book_file(book_id: UUID, current_user: CurrentUser, db: DbSession) -> FileResponse:
    del current_user
    book = db.get(Book, book_id)
    if book is None or book.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    path = Path(book.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EPUB file not found")

    filename = book.original_filename or f"{book.id}.epub"
    return FileResponse(path, media_type="application/epub+zip", filename=filename)


@router.get("/{book_id}/cover")
def get_book_cover(book_id: UUID, current_user: CurrentUser, db: DbSession) -> FileResponse:
    del current_user
    book = db.get(Book, book_id)
    if book is None or book.deleted_at is not None or not book.cover_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")

    path = Path(book.cover_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")

    return FileResponse(path, media_type="image/jpeg")
