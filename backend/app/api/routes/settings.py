from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.settings import ReadingSettings
from app.schemas.settings import ReadingSettingsRead, ReadingSettingsUpdate

router = APIRouter()


def get_or_create_reading_settings(db: DbSession, user_id) -> ReadingSettings:
    settings = db.query(ReadingSettings).filter(ReadingSettings.user_id == user_id).one_or_none()
    if settings is None:
        settings = ReadingSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/reading", response_model=ReadingSettingsRead)
def read_settings(current_user: CurrentUser, db: DbSession) -> ReadingSettingsRead:
    return ReadingSettingsRead.model_validate(get_or_create_reading_settings(db, current_user.id))


@router.put("/reading", response_model=ReadingSettingsRead)
def update_settings(
    payload: ReadingSettingsUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ReadingSettingsRead:
    settings = get_or_create_reading_settings(db, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return ReadingSettingsRead.model_validate(settings)
