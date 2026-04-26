from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.book import Book
from app.models.reading import ReadingProgress
from app.schemas.book import BookDetail, BookListItem, BookListResponse

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


@router.get("/{book_id}", response_model=BookDetail)
def get_book(book_id: str, current_user: CurrentUser, db: DbSession) -> BookDetail:
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
