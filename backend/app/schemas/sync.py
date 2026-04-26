from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SyncEventIn(BaseModel):
    event_id: UUID
    type: str
    client_created_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncEventsRequest(BaseModel):
    device_id: str | None = None
    events: list[SyncEventIn]


class SyncEventsResponse(BaseModel):
    ok: bool
    accepted: int
    processed: int
