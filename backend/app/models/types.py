from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects import postgresql

jsonb_type = JSON().with_variant(postgresql.JSONB(), "postgresql")
