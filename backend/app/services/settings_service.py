from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.settings import AppSetting
from app.schemas.settings import (
    AppSettingsRead,
    AppSettingsUpdate,
    AppSettingsValues,
    SystemSettingsRead,
)


def default_app_settings(settings: Settings | None = None) -> AppSettingsValues:
    settings = settings or get_settings()
    return AppSettingsValues(
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        import_max_files_per_batch=100,
        import_worker_concurrency=1,
        metadata_openlibrary_enabled=settings.METADATA_OPENLIBRARY_ENABLED,
        metadata_googlebooks_enabled=settings.METADATA_GOOGLEBOOKS_ENABLED,
        metadata_auto_enrich_on_import=settings.METADATA_AUTO_ENRICH_ON_IMPORT,
        trash_retention_hours=24,
        trash_auto_purge_enabled=True,
        default_theme="system",
        default_reader_theme="black_gold",
    )


def _settings_rows(db: Session) -> list[AppSetting]:
    return list(db.scalars(select(AppSetting).order_by(AppSetting.key.asc())))


def _overrides(db: Session) -> dict[str, Any]:
    return {row.key: row.value_json for row in _settings_rows(db)}


def get_app_settings_values(db: Session) -> AppSettingsValues:
    defaults = default_app_settings()
    values = defaults.model_dump()
    values.update(_overrides(db))
    return AppSettingsValues.model_validate(values)


def read_app_settings(db: Session) -> AppSettingsRead:
    defaults = default_app_settings()
    rows = _settings_rows(db)
    overrides = {row.key: row.value_json for row in rows}
    values = defaults.model_dump()
    values.update(overrides)
    updated_at: datetime | None = max((row.updated_at for row in rows), default=None)
    return AppSettingsRead(
        values=AppSettingsValues.model_validate(values),
        defaults=defaults,
        overrides=overrides,
        updated_at=updated_at,
    )


def update_app_settings(db: Session, payload: AppSettingsUpdate) -> AppSettingsRead:
    defaults = default_app_settings()
    candidate = defaults.model_dump()
    candidate.update(_overrides(db))
    candidate.update(payload.model_dump(exclude_unset=True, exclude_none=True))
    validated = AppSettingsValues.model_validate(candidate)

    for key, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        row = db.get(AppSetting, key)
        if row is None:
            row = AppSetting(key=key, value_json=value)
        else:
            row.value_json = value
        db.add(row)

    db.commit()
    return read_app_settings(db)


class RuntimeSettings:
    def __init__(self, base: Settings, values: AppSettingsValues) -> None:
        self._base = base
        self.MAX_UPLOAD_SIZE_MB = values.max_upload_size_mb
        self.METADATA_OPENLIBRARY_ENABLED = values.metadata_openlibrary_enabled
        self.METADATA_GOOGLEBOOKS_ENABLED = values.metadata_googlebooks_enabled
        self.METADATA_AUTO_ENRICH_ON_IMPORT = values.metadata_auto_enrich_on_import
        self.IMPORT_MAX_FILES_PER_BATCH = values.import_max_files_per_batch
        self.IMPORT_WORKER_CONCURRENCY = values.import_worker_concurrency
        self.TRASH_RETENTION_HOURS = values.trash_retention_hours
        self.TRASH_AUTO_PURGE_ENABLED = values.trash_auto_purge_enabled

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)


def get_runtime_settings(db: Session) -> RuntimeSettings:
    return RuntimeSettings(get_settings(), get_app_settings_values(db))


def read_system_settings() -> SystemSettingsRead:
    settings = get_settings()
    return SystemSettingsRead(
        app_env=settings.APP_ENV,
        app_url=settings.APP_URL,
        api_url=settings.API_URL,
        library_path=str(settings.LIBRARY_PATH),
        incoming_path=str(settings.INCOMING_PATH),
        cors_origins=settings.cors_origins,
        database_url_configured=bool(settings.DATABASE_URL),
        secret_key_configured=bool(settings.SECRET_KEY and not settings.SECRET_KEY.startswith("change-me")),
        setup_token_configured=bool(settings.FIRST_USER_SETUP_TOKEN),
    )
