"""Initial Aurelia schema.

Revision ID: 202604260001
Revises:
Create Date: 2026-04-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202604260001"
down_revision = None
branch_labels = None
depends_on = None

jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("isbn", sa.String(length=40), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("published_date", sa.String(length=40), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("cover_path", sa.Text(), nullable=True),
        sa.Column("metadata_source", sa.String(length=80), nullable=True),
        sa.Column("metadata_provider_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="unread", nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("favorite", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_books_rating"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_hash"),
    )
    op.create_index("ix_books_added_at", "books", ["added_at"])
    op.create_index("ix_books_deleted_at", "books", ["deleted_at"])
    op.create_index("ix_books_file_hash", "books", ["file_hash"])
    op.create_index("ix_books_isbn", "books", ["isbn"])
    op.create_index("ix_books_last_opened_at", "books", ["last_opened_at"])
    op.create_index("ix_books_rating", "books", ["rating"])
    op.create_index("ix_books_status", "books", ["status"])
    op.create_index("ix_books_title", "books", ["title"])

    op.create_table(
        "authors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sort_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_authors_name", "authors", ["name"])

    op.create_table(
        "series",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_series_name", "series", ["name"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("color", sa.String(length=24), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "collections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_book_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cover_book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_collections_name", "collections", ["name"])

    op.create_table(
        "book_authors",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("book_id", "author_id"),
    )

    op.create_table(
        "book_tags",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("book_id", "tag_id"),
    )

    op.create_table(
        "book_series",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("series_id", sa.Uuid(), nullable=False),
        sa.Column("series_index", sa.Numeric(8, 2), nullable=True),
        sa.Column("series_label", sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("book_id"),
    )
    op.create_index("ix_book_series_series_id", "book_series", ["series_id"])

    op.create_table(
        "collection_books",
        sa.Column("collection_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("collection_id", "book_id"),
    )

    op.create_table(
        "reading_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("cfi", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.Numeric(6, 3), nullable=True),
        sa.Column("chapter_label", sa.String(length=500), nullable=True),
        sa.Column("chapter_href", sa.String(length=1000), nullable=True),
        sa.Column("location_json", jsonb, nullable=True),
        sa.Column("device_id", sa.String(length=120), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100)",
            name="ck_reading_progress_percent",
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "book_id", name="uq_reading_progress_user_book"),
    )
    op.create_index("ix_reading_progress_book_id", "reading_progress", ["book_id"])
    op.create_index("ix_reading_progress_updated_at", "reading_progress", ["updated_at"])
    op.create_index("ix_reading_progress_user_id", "reading_progress", ["user_id"])

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("cfi", sa.Text(), nullable=False),
        sa.Column("progress_percent", sa.Numeric(6, 3), nullable=True),
        sa.Column("chapter_label", sa.String(length=500), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookmarks_book_id", "bookmarks", ["book_id"])
    op.create_index("ix_bookmarks_deleted_at", "bookmarks", ["deleted_at"])
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"])

    op.create_table(
        "reading_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("theme", sa.String(length=40), server_default="system", nullable=False),
        sa.Column("reader_theme", sa.String(length=40), server_default="black_gold", nullable=False),
        sa.Column("font_family", sa.String(length=120), nullable=True),
        sa.Column("font_size", sa.Integer(), server_default="18", nullable=False),
        sa.Column("line_height", sa.Numeric(3, 2), server_default="1.60", nullable=False),
        sa.Column("margin_size", sa.Integer(), server_default="24", nullable=False),
        sa.Column("reading_mode", sa.String(length=20), server_default="paged", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_book_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["result_book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_jobs_source", "import_jobs", ["source"])
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])

    op.create_table(
        "metadata_provider_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_item_id", sa.String(length=255), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("raw_json", jsonb, nullable=True),
        sa.Column("normalized_json", jsonb, nullable=True),
        sa.Column("score", sa.Numeric(6, 3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metadata_provider_results_provider", "metadata_provider_results", ["provider"])

    op.create_table(
        "sync_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.String(length=120), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("payload", jsonb, nullable=False),
        sa.Column("client_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="received", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_events_device_id", "sync_events", ["device_id"])
    op.create_index("ix_sync_events_event_type", "sync_events", ["event_type"])
    op.create_index("ix_sync_events_status", "sync_events", ["status"])
    op.create_index("ix_sync_events_user_id", "sync_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("sync_events")
    op.drop_table("metadata_provider_results")
    op.drop_table("import_jobs")
    op.drop_table("reading_settings")
    op.drop_table("bookmarks")
    op.drop_table("reading_progress")
    op.drop_table("collection_books")
    op.drop_table("book_series")
    op.drop_table("book_tags")
    op.drop_table("book_authors")
    op.drop_table("collections")
    op.drop_table("tags")
    op.drop_table("series")
    op.drop_table("authors")
    op.drop_table("books")
    op.drop_table("users")
