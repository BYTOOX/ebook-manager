"""Add import queue and application settings.

Revision ID: 202605020002
Revises: 202605020001
Create Date: 2026-05-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202605020002"
down_revision = "202605020001"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value_json", json_type, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("total_items", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed_items", sa.Integer(), server_default="0", nullable=False),
        sa.Column("success_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("warning_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("canceled_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("progress_percent", sa.Numeric(6, 3), server_default="0", nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_batches_status", "import_batches", ["status"])
    op.add_column("import_jobs", sa.Column("batch_id", sa.Uuid(), nullable=True))
    op.add_column("import_jobs", sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False))
    op.add_column("import_jobs", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_import_jobs_batch_id", "import_jobs", ["batch_id"])
    op.create_foreign_key(
        "fk_import_jobs_batch_id_import_batches",
        "import_jobs",
        "import_batches",
        ["batch_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_import_jobs_batch_id_import_batches", "import_jobs", type_="foreignkey")
    op.drop_index("ix_import_jobs_batch_id", table_name="import_jobs")
    op.drop_column("import_jobs", "updated_at")
    op.drop_column("import_jobs", "sort_order")
    op.drop_column("import_jobs", "batch_id")
    op.drop_index("ix_import_batches_status", table_name="import_batches")
    op.drop_table("import_batches")
    op.drop_table("app_settings")
