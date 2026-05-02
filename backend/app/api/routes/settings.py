from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models.settings import ReadingSettings
from app.schemas.settings import (
    AppSettingsRead,
    AppSettingsUpdate,
    ReadingSettingsRead,
    ReadingSettingsUpdate,
    SystemSettingsRead,
)
from app.services.settings_service import read_app_settings, read_system_settings, update_app_settings

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
    if payload.reading_mode is not None and payload.reading_mode not in {"paged", "scroll"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reading mode")
    settings = get_or_create_reading_settings(db, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return ReadingSettingsRead.model_validate(settings)


@router.get("/app", response_model=AppSettingsRead)
def app_settings(current_user: CurrentUser, db: DbSession) -> AppSettingsRead:
    del current_user
    return read_app_settings(db)


@router.put("/app", response_model=AppSettingsRead)
def update_app_settings_route(
    payload: AppSettingsUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> AppSettingsRead:
    del current_user
    return update_app_settings(db, payload)


@router.get("/system", response_model=SystemSettingsRead)
def system_settings(current_user: CurrentUser) -> SystemSettingsRead:
    del current_user
    return read_system_settings()
