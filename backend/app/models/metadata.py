from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import jsonb_type


class MetadataProviderResult(Base):
    __tablename__ = "metadata_provider_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("books.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    provider_item_id: Mapped[str | None] = mapped_column(String(255))
    query: Mapped[str | None] = mapped_column(Text)
    raw_json: Mapped[dict | None] = mapped_column(jsonb_type)
    normalized_json: Mapped[dict | None] = mapped_column(jsonb_type)
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
