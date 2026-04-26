from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.reading import ReadingProgress
from app.schemas.book import ReadingProgressOut, ReadingProgressPayload


def _aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def serialize_progress(progress: ReadingProgress | None) -> ReadingProgressOut:
    if progress is None:
        return ReadingProgressOut()
    return ReadingProgressOut(
        cfi=progress.cfi,
        progress_percent=float(progress.progress_percent)
        if progress.progress_percent is not None
        else None,
        chapter_label=progress.chapter_label,
        chapter_href=progress.chapter_href,
        location_json=progress.location_json,
        device_id=progress.device_id,
        updated_at=progress.updated_at,
    )


def progress_payload_from_sync(payload: dict[str, Any]) -> ReadingProgressPayload:
    client_updated_at = payload.get("client_updated_at")
    if isinstance(client_updated_at, str):
        try:
            client_updated_at = datetime.fromisoformat(client_updated_at.replace("Z", "+00:00"))
        except ValueError:
            client_updated_at = None
    elif not isinstance(client_updated_at, datetime):
        client_updated_at = None

    progress_percent = payload.get("progress_percent")
    if isinstance(progress_percent, str):
        try:
            progress_percent = float(progress_percent)
        except ValueError:
            progress_percent = None
    elif not isinstance(progress_percent, (int, float)) or isinstance(progress_percent, bool):
        progress_percent = None

    location_json = payload.get("location_json")
    return ReadingProgressPayload(
        cfi=payload.get("cfi") if isinstance(payload.get("cfi"), str) else None,
        progress_percent=progress_percent,
        chapter_label=payload.get("chapter_label")
        if isinstance(payload.get("chapter_label"), str)
        else None,
        chapter_href=payload.get("chapter_href")
        if isinstance(payload.get("chapter_href"), str)
        else None,
        location_json=location_json if isinstance(location_json, dict) else None,
        device_id=payload.get("device_id") if isinstance(payload.get("device_id"), str) else None,
        client_updated_at=client_updated_at,
    )


def apply_reading_progress(
    db: Session,
    *,
    user_id: uuid.UUID,
    book: Book,
    payload: ReadingProgressPayload,
) -> tuple[str, ReadingProgress]:
    client_updated_at = _aware_datetime(payload.client_updated_at) or datetime.now(timezone.utc)
    progress = (
        db.query(ReadingProgress)
        .filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book.id,
        )
        .one_or_none()
    )

    if progress is not None:
        server_updated_at = _aware_datetime(progress.updated_at)
        if server_updated_at is not None and server_updated_at > client_updated_at:
            return "server_won", progress
    else:
        progress = ReadingProgress(user_id=user_id, book_id=book.id)
        db.add(progress)

    progress.cfi = payload.cfi
    progress.progress_percent = (
        Decimal(str(round(max(0.0, min(100.0, payload.progress_percent)), 3)))
        if payload.progress_percent is not None
        else None
    )
    progress.chapter_label = payload.chapter_label
    progress.chapter_href = payload.chapter_href
    progress.location_json = payload.location_json
    progress.device_id = payload.device_id
    progress.updated_at = client_updated_at

    book.last_opened_at = client_updated_at
    if payload.progress_percent is not None:
        if payload.progress_percent >= 99:
            book.status = "finished"
        elif book.status == "unread":
            book.status = "in_progress"

    db.flush()
    return "client_won", progress
