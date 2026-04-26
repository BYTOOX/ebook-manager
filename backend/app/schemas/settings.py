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
