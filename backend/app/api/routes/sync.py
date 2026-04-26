from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.book import Book
from app.models.sync import SyncEvent
from app.schemas.sync import SyncEventResult, SyncEventsRequest, SyncEventsResponse
from app.services.bookmark_service import (
    apply_bookmark_created,
    apply_bookmark_deleted,
    serialize_bookmark,
)
from app.services.progress_service import (
    apply_reading_progress,
    progress_payload_from_sync,
    serialize_progress,
)

router = APIRouter()


@router.post("/events", response_model=SyncEventsResponse)
def receive_sync_events(
    payload: SyncEventsRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SyncEventsResponse:
    processed = 0
    results: list[SyncEventResult] = []
    now = datetime.now(timezone.utc)
    for event in payload.events:
        status = "ignored"
        resolved = None
        processed_at = None
        progress = None
        bookmark = None
        error = None
        book_uuid = None
        if event.type == "progress.updated":
            book_id = event.payload.get("book_id")
            try:
                book_uuid = UUID(str(book_id))
            except (TypeError, ValueError):
                book_uuid = None

            book = db.get(Book, book_uuid) if book_uuid is not None else None
            if book is not None and book.deleted_at is None:
                progress_payload = progress_payload_from_sync(
                    {**event.payload, "device_id": payload.device_id or event.payload.get("device_id")}
                )
                resolved, reading_progress = apply_reading_progress(
                    db,
                    user_id=current_user.id,
                    book=book,
                    payload=progress_payload,
                )
                progress = serialize_progress(reading_progress)
                processed += 1
                status = "processed"
                processed_at = now
            else:
                error = "Book not found"
        elif event.type == "bookmark.created":
            book_id = event.payload.get("book_id")
            try:
                book_uuid = UUID(str(book_id))
            except (TypeError, ValueError):
                book_uuid = None

            book = db.get(Book, book_uuid) if book_uuid is not None else None
            if book is not None and book.deleted_at is None:
                try:
                    resolved, stored_bookmark = apply_bookmark_created(
                        db,
                        user_id=current_user.id,
                        book=book,
                        payload=event.payload,
                        client_created_at=event.client_created_at,
                    )
                    bookmark = serialize_bookmark(stored_bookmark)
                    processed += 1
                    status = "processed"
                    processed_at = now
                except ValueError as exc:
                    error = str(exc)
            else:
                error = "Book not found"
        elif event.type == "bookmark.deleted":
            try:
                resolved, stored_bookmark = apply_bookmark_deleted(
                    db,
                    user_id=current_user.id,
                    payload=event.payload,
                    client_created_at=event.client_created_at,
                )
                bookmark = serialize_bookmark(stored_bookmark)
                if stored_bookmark is not None:
                    book_uuid = stored_bookmark.book_id
                    processed += 1
                    status = "processed"
                    processed_at = now
                else:
                    status = "ignored"
                    error = "Bookmark not found"
            except ValueError as exc:
                error = str(exc)
        else:
            error = "Unsupported event type"

        db.merge(
            SyncEvent(
                id=event.event_id,
                user_id=current_user.id,
                device_id=payload.device_id,
                event_type=event.type,
                payload=event.payload,
                client_created_at=event.client_created_at,
                processed_at=processed_at,
                status=status,
            )
        )
        results.append(
            SyncEventResult(
                event_id=event.event_id,
                type=event.type,
                status=status,
                resolved=resolved,
                book_id=book_uuid,
                progress=progress,
                bookmark=bookmark,
                error=error,
            )
        )
    db.commit()
    return SyncEventsResponse(ok=True, accepted=len(payload.events), processed=processed, results=results)
