from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.book import Book
from app.models.sync import SyncEvent
from app.schemas.sync import SyncEventsRequest, SyncEventsResponse
from app.services.progress_service import apply_reading_progress, progress_payload_from_sync

router = APIRouter()


@router.post("/events", response_model=SyncEventsResponse)
def receive_sync_events(
    payload: SyncEventsRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SyncEventsResponse:
    processed = 0
    now = datetime.now(timezone.utc)
    for event in payload.events:
        status = "received"
        processed_at = None
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
                apply_reading_progress(
                    db,
                    user_id=current_user.id,
                    book=book,
                    payload=progress_payload,
                )
                processed += 1
                status = "processed"
                processed_at = now

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
    db.commit()
    return SyncEventsResponse(ok=True, accepted=len(payload.events), processed=processed)
