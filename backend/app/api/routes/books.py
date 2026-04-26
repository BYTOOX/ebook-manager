from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.book import Book
from app.models.reading import ReadingProgress
from app.schemas.book import BookDetail, BookListItem, BookListResponse
from app.schemas.imports import UploadBookResponse
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


@router.get("", response_model=BookListResponse)
def list_books(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BookListResponse:
    del current_user
    total = db.scalar(select(func.count()).select_from(Book).where(Book.deleted_at.is_(None))) or 0
    books = db.scalars(
        select(Book)
        .where(Book.deleted_at.is_(None))
        .order_by(Book.added_at.desc())
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
    item = serialize_book(
        book,
        float(progress.progress_percent) if progress and progress.progress_percent is not None else None,
    )
    return BookDetail(
        **item.model_dump(),
        subtitle=book.subtitle,
        description=book.description,
        language=book.language,
        isbn=book.isbn,
        publisher=book.publisher,
        published_date=book.published_date,
        original_filename=book.original_filename,
        file_size=book.file_size,
        metadata_source=book.metadata_source,
    )
