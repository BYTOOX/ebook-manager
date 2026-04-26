from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.api.routes.books import _series_from_filename, book_cover_url, serialize_book
from app.models.book import Book, BookAuthor, BookSeries, BookTag, Collection, CollectionBook, Series, Tag
from app.schemas.organization import (
    CollectionBooksPayload,
    CollectionDetail,
    CollectionListResponse,
    CollectionPayload,
    CollectionSummary,
    SeriesDetail,
    SeriesListResponse,
    SeriesPayload,
    SeriesSummary,
    TagListResponse,
    TagPayload,
    TagSummary,
)

router = APIRouter()


def _clean_text(value: str | None) -> str:
    return value.strip() if value else ""


def _get_collection_or_404(db: DbSession, collection_id: UUID) -> Collection:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection


def _get_series_or_404(db: DbSession, series_id: UUID) -> Series:
    series = db.get(Series, series_id)
    if series is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    return series


def _get_tag_or_404(db: DbSession, tag_id: UUID) -> Tag:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


def _collection_books(db: DbSession, collection: Collection) -> list[Book]:
    return list(
        db.scalars(
            select(Book)
            .join(CollectionBook, CollectionBook.book_id == Book.id)
            .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
            .where(CollectionBook.collection_id == collection.id, Book.deleted_at.is_(None))
            .order_by(CollectionBook.position.asc(), func.lower(Book.title))
        ).unique()
    )


def _series_books(db: DbSession, series: Series) -> list[Book]:
    return list(
        db.scalars(
            select(Book)
            .join(BookSeries, BookSeries.book_id == Book.id)
            .options(selectinload(Book.book_authors).selectinload(BookAuthor.author))
            .where(BookSeries.series_id == series.id, Book.deleted_at.is_(None))
            .order_by(BookSeries.series_index.asc().nulls_last(), func.lower(Book.title))
        ).unique()
    )


def _cover_url(book: Book | None) -> str | None:
    return book_cover_url(book) if book else None


def _collection_summary(db: DbSession, collection: Collection) -> CollectionSummary:
    books = _collection_books(db, collection)
    cover_book = next((book for book in books if book.id == collection.cover_book_id), books[0] if books else None)
    return CollectionSummary(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        book_count=len(books),
        cover_book_id=cover_book.id if cover_book else None,
        cover_url=_cover_url(cover_book),
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


def _collection_detail(db: DbSession, collection: Collection) -> CollectionDetail:
    summary = _collection_summary(db, collection)
    return CollectionDetail(**summary.model_dump(), books=[serialize_book(book) for book in _collection_books(db, collection)])


def _series_summary(db: DbSession, series: Series) -> SeriesSummary:
    books = _series_books(db, series)
    cover_book = books[0] if books else None
    return SeriesSummary(
        id=series.id,
        name=series.name,
        description=series.description,
        book_count=len(books),
        cover_book_id=cover_book.id if cover_book else None,
        cover_url=_cover_url(cover_book),
        created_at=series.created_at,
        updated_at=series.updated_at,
    )


def _series_detail(db: DbSession, series: Series) -> SeriesDetail:
    summary = _series_summary(db, series)
    return SeriesDetail(**summary.model_dump(), books=[serialize_book(book) for book in _series_books(db, series)])


def _tag_summary(db: DbSession, tag: Tag) -> TagSummary:
    book_count = db.scalar(
        select(func.count())
        .select_from(BookTag)
        .join(Book, Book.id == BookTag.book_id)
        .where(BookTag.tag_id == tag.id, Book.deleted_at.is_(None))
    ) or 0
    return TagSummary(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        book_count=book_count,
        created_at=tag.created_at,
    )


def _materialize_import_path_series(db: DbSession) -> None:
    changed = False
    books = list(
        db.scalars(
            select(Book)
            .options(selectinload(Book.book_series))
            .where(Book.deleted_at.is_(None), Book.original_filename.is_not(None))
        ).unique()
    )
    for book in books:
        if book.book_series is not None:
            continue
        series_name, series_index = _series_from_filename(book.original_filename)
        if not series_name:
            continue

        series = db.scalar(select(Series).where(func.lower(Series.name) == series_name.lower()))
        if series is None:
            series = Series(name=series_name)
            db.add(series)
            db.flush()
        book.book_series = BookSeries(
            book_id=book.id,
            series_id=series.id,
            series_index=series_index,
            series_label="import_path",
        )
        changed = True

    if changed:
        db.commit()


@router.get("/collections", response_model=CollectionListResponse)
def list_collections(current_user: CurrentUser, db: DbSession) -> CollectionListResponse:
    del current_user
    collections = list(db.scalars(select(Collection).order_by(func.lower(Collection.name))).unique())
    return CollectionListResponse(
        items=[_collection_summary(db, collection) for collection in collections],
        total=len(collections),
    )


@router.post("/collections", response_model=CollectionDetail, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> CollectionDetail:
    del current_user
    name = _clean_text(payload.name)
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name is required")
    existing = db.scalar(select(Collection).where(func.lower(Collection.name) == name.lower()))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Collection already exists")

    collection = Collection(name=name, description=_clean_text(payload.description) or None)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return _collection_detail(db, collection)


@router.get("/collections/{collection_id}", response_model=CollectionDetail)
def get_collection(
    collection_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> CollectionDetail:
    del current_user
    return _collection_detail(db, _get_collection_or_404(db, collection_id))


@router.patch("/collections/{collection_id}", response_model=CollectionDetail)
def update_collection(
    collection_id: UUID,
    payload: CollectionPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> CollectionDetail:
    del current_user
    collection = _get_collection_or_404(db, collection_id)
    name = _clean_text(payload.name)
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name is required")
    existing = db.scalar(
        select(Collection).where(func.lower(Collection.name) == name.lower(), Collection.id != collection.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Collection already exists")

    collection.name = name
    collection.description = _clean_text(payload.description) or None
    db.commit()
    db.refresh(collection)
    return _collection_detail(db, collection)


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: UUID, current_user: CurrentUser, db: DbSession) -> Response:
    del current_user
    collection = _get_collection_or_404(db, collection_id)
    db.delete(collection)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/collections/{collection_id}/books", response_model=CollectionDetail)
def set_collection_books(
    collection_id: UUID,
    payload: CollectionBooksPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> CollectionDetail:
    del current_user
    collection = _get_collection_or_404(db, collection_id)

    book_ids: list[UUID] = []
    seen: set[UUID] = set()
    for book_id in payload.book_ids:
        if book_id not in seen:
            seen.add(book_id)
            book_ids.append(book_id)

    books = (
        list(
            db.scalars(
                select(Book).where(Book.deleted_at.is_(None), Book.id.in_(book_ids))
            ).unique()
        )
        if book_ids
        else []
    )
    if len(books) != len(book_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some books were not found")

    by_id = {book.id: book for book in books}
    collection.collection_books.clear()
    for position, book_id in enumerate(book_ids):
        collection.collection_books.append(CollectionBook(book=by_id[book_id], position=position))
    collection.cover_book_id = book_ids[0] if book_ids else None
    db.commit()
    db.refresh(collection)
    return _collection_detail(db, collection)


@router.get("/series", response_model=SeriesListResponse)
def list_series(current_user: CurrentUser, db: DbSession) -> SeriesListResponse:
    del current_user
    _materialize_import_path_series(db)
    series_items = list(db.scalars(select(Series).order_by(func.lower(Series.name))).unique())
    summaries = [_series_summary(db, series) for series in series_items]
    summaries = [summary for summary in summaries if summary.book_count > 0]
    return SeriesListResponse(items=summaries, total=len(summaries))


@router.get("/series/{series_id}", response_model=SeriesDetail)
def get_series(series_id: UUID, current_user: CurrentUser, db: DbSession) -> SeriesDetail:
    del current_user
    _materialize_import_path_series(db)
    return _series_detail(db, _get_series_or_404(db, series_id))


@router.patch("/series/{series_id}", response_model=SeriesDetail)
def update_series(
    series_id: UUID,
    payload: SeriesPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> SeriesDetail:
    del current_user
    series = _get_series_or_404(db, series_id)
    if payload.name is not None:
        name = _clean_text(payload.name)
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Series name is required")
        existing = db.scalar(select(Series).where(func.lower(Series.name) == name.lower(), Series.id != series.id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Series already exists")
        series.name = name
    if "description" in payload.model_fields_set:
        series.description = _clean_text(payload.description) or None
    db.commit()
    db.refresh(series)
    return _series_detail(db, series)


@router.get("/tags", response_model=TagListResponse)
def list_tags(current_user: CurrentUser, db: DbSession) -> TagListResponse:
    del current_user
    tags = list(db.scalars(select(Tag).order_by(func.lower(Tag.name))).unique())
    return TagListResponse(items=[_tag_summary(db, tag) for tag in tags], total=len(tags))


@router.post("/tags", response_model=TagSummary, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagPayload, current_user: CurrentUser, db: DbSession) -> TagSummary:
    del current_user
    name = _clean_text(payload.name)
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name is required")
    existing = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")

    tag = Tag(name=name, color=_clean_text(payload.color) or None)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return _tag_summary(db, tag)


@router.patch("/tags/{tag_id}", response_model=TagSummary)
def update_tag(
    tag_id: UUID,
    payload: TagPayload,
    current_user: CurrentUser,
    db: DbSession,
) -> TagSummary:
    del current_user
    tag = _get_tag_or_404(db, tag_id)
    name = _clean_text(payload.name)
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name is required")
    existing = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower(), Tag.id != tag.id))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")

    tag.name = name
    tag.color = _clean_text(payload.color) or None
    db.commit()
    db.refresh(tag)
    return _tag_summary(db, tag)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: UUID, current_user: CurrentUser, db: DbSession) -> Response:
    del current_user
    tag = _get_tag_or_404(db, tag_id)
    db.delete(tag)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
