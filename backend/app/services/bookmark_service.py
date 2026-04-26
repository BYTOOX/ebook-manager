from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.reading import Bookmark
from app.schemas.sync import SyncBookmarkOut


def _aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _payload_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _aware_datetime(value)
    if isinstance(value, str):
        try:
            return _aware_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def _payload_uuid(value: Any) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _payload_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _payload_progress(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return None
    if not isinstance(value, (int, float)):
        return None
    return Decimal(str(round(max(0.0, min(100.0, float(value))), 3)))


def serialize_bookmark(bookmark: Bookmark | None) -> SyncBookmarkOut | None:
    if bookmark is None:
        return None
    return SyncBookmarkOut(
        id=bookmark.id,
        book_id=bookmark.book_id,
        cfi=bookmark.cfi,
        progress_percent=float(bookmark.progress_percent)
        if bookmark.progress_percent is not None
        else None,
        chapter_label=bookmark.chapter_label,
        excerpt=bookmark.excerpt,
        note=bookmark.note,
        created_at=bookmark.created_at,
        updated_at=bookmark.updated_at,
        deleted_at=bookmark.deleted_at,
    )


def apply_bookmark_created(
    db: Session,
    *,
    user_id: uuid.UUID,
    book: Book,
    payload: dict[str, Any],
    client_created_at: datetime | None = None,
) -> tuple[str, Bookmark]:
    bookmark_id = _payload_uuid(payload.get("id") or payload.get("bookmark_id"))
    if bookmark_id is None:
        raise ValueError("Bookmark id is required")

    client_updated_at = (
        _payload_datetime(payload.get("updated_at"))
        or _payload_datetime(payload.get("client_updated_at"))
        or _aware_datetime(client_created_at)
        or datetime.now(timezone.utc)
    )
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is not None:
        if bookmark.user_id != user_id or bookmark.book_id != book.id:
            raise ValueError("Bookmark belongs to another scope")
        server_updated_at = _aware_datetime(bookmark.updated_at)
        if server_updated_at is not None and server_updated_at > client_updated_at:
            return "server_won", bookmark
    else:
        cfi = _payload_string(payload.get("cfi"))
        if cfi is None:
            raise ValueError("Bookmark cfi is required")
        bookmark = Bookmark(id=bookmark_id, user_id=user_id, book_id=book.id, cfi=cfi)
        created_at = _payload_datetime(payload.get("created_at")) or _aware_datetime(client_created_at)
        if created_at is not None:
            bookmark.created_at = created_at
        db.add(bookmark)

    cfi = _payload_string(payload.get("cfi"))
    if cfi is not None:
        bookmark.cfi = cfi
    bookmark.progress_percent = _payload_progress(payload.get("progress_percent"))
    bookmark.chapter_label = _payload_string(payload.get("chapter_label"))
    bookmark.excerpt = _payload_string(payload.get("excerpt"))
    bookmark.note = _payload_string(payload.get("note"))
    bookmark.updated_at = client_updated_at
    bookmark.deleted_at = None

    db.flush()
    return "client_won", bookmark


def apply_bookmark_deleted(
    db: Session,
    *,
    user_id: uuid.UUID,
    payload: dict[str, Any],
    client_created_at: datetime | None = None,
) -> tuple[str, Bookmark | None]:
    bookmark_id = _payload_uuid(payload.get("id") or payload.get("bookmark_id"))
    if bookmark_id is None:
        raise ValueError("Bookmark id is required")

    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None or bookmark.user_id != user_id:
        return "ignored", None

    client_updated_at = (
        _payload_datetime(payload.get("updated_at"))
        or _payload_datetime(payload.get("client_updated_at"))
        or _aware_datetime(client_created_at)
        or datetime.now(timezone.utc)
    )
    server_updated_at = _aware_datetime(bookmark.updated_at)
    deleted_at = _aware_datetime(bookmark.deleted_at)
    if deleted_at is not None and (server_updated_at is None or deleted_at > server_updated_at):
        server_updated_at = deleted_at
    if server_updated_at is not None and server_updated_at > client_updated_at:
        return "server_won", bookmark

    bookmark.updated_at = client_updated_at
    bookmark.deleted_at = client_updated_at
    db.flush()
    return "client_won", bookmark
