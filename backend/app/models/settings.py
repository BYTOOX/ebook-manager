from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReadingSettings(Base):
    __tablename__ = "reading_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    theme: Mapped[str] = mapped_column(String(40), default="system", nullable=False)
    reader_theme: Mapped[str] = mapped_column(String(40), default="black_gold", nullable=False)
    font_family: Mapped[str | None] = mapped_column(String(120))
    font_size: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    line_height: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("1.60"), nullable=False)
    margin_size: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    reading_mode: Mapped[str] = mapped_column(String(20), default="paged", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="reading_settings")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value_json: Mapped[object] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
