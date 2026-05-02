"""Add library trash support.

Revision ID: 202605020001
Revises: 202604260001
Create Date: 2026-05-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605020001"
down_revision = "202604260001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("trash_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_books_trash_expires_at", "books", ["trash_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_books_trash_expires_at", table_name="books")
    op.drop_column("books", "trash_expires_at")
