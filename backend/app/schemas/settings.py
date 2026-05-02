from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReadingSettingsRead(BaseModel):
    id: UUID
    theme: str
    reader_theme: str
    font_family: str | None = None
    font_size: int
    line_height: Decimal
    margin_size: int
    reading_mode: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadingSettingsUpdate(BaseModel):
    theme: str | None = None
    reader_theme: str | None = None
    font_family: str | None = None
    font_size: int | None = Field(default=None, ge=12, le=36)
    line_height: Decimal | None = Field(default=None, ge=Decimal("1.00"), le=Decimal("2.50"))
    margin_size: int | None = Field(default=None, ge=0, le=80)
    reading_mode: str | None = None


class AppSettingsValues(BaseModel):
    max_upload_size_mb: int = Field(ge=1, le=2048)
    import_max_files_per_batch: int = Field(ge=1, le=500)
    import_worker_concurrency: int = Field(ge=1, le=8)
    metadata_openlibrary_enabled: bool
    metadata_googlebooks_enabled: bool
    metadata_auto_enrich_on_import: bool
    trash_retention_hours: int = Field(ge=1, le=720)
    trash_auto_purge_enabled: bool
    default_theme: str = Field(max_length=40)
    default_reader_theme: str = Field(max_length=40)


class AppSettingsUpdate(BaseModel):
    max_upload_size_mb: int | None = Field(default=None, ge=1, le=2048)
    import_max_files_per_batch: int | None = Field(default=None, ge=1, le=500)
    import_worker_concurrency: int | None = Field(default=None, ge=1, le=8)
    metadata_openlibrary_enabled: bool | None = None
    metadata_googlebooks_enabled: bool | None = None
    metadata_auto_enrich_on_import: bool | None = None
    trash_retention_hours: int | None = Field(default=None, ge=1, le=720)
    trash_auto_purge_enabled: bool | None = None
    default_theme: str | None = Field(default=None, max_length=40)
    default_reader_theme: str | None = Field(default=None, max_length=40)


class AppSettingsRead(BaseModel):
    values: AppSettingsValues
    defaults: AppSettingsValues
    overrides: dict[str, object]
    updated_at: datetime | None = None


class SystemSettingsRead(BaseModel):
    app_env: str
    app_url: str
    api_url: str
    library_path: str
    incoming_path: str
    cors_origins: list[str]
    database_url_configured: bool
    secret_key_configured: bool
    setup_token_configured: bool
