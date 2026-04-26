from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.sync import SyncEvent
from app.schemas.sync import SyncEventsRequest, SyncEventsResponse

router = APIRouter()


@router.post("/events", response_model=SyncEventsResponse)
def receive_sync_events(
    payload: SyncEventsRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SyncEventsResponse:
    for event in payload.events:
        db.merge(
            SyncEvent(
                id=event.event_id,
                user_id=current_user.id,
                device_id=payload.device_id,
                event_type=event.type,
                payload=event.payload,
                client_created_at=event.client_created_at,
                status="received",
            )
        )
    db.commit()
    return SyncEventsResponse(ok=True, accepted=len(payload.events), processed=0)
