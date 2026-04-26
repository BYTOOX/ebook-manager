from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookAuthor(Base):
    __tablename__ = "book_authors"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    book = relationship("Book", back_populates="book_authors")
    author = relationship("Author", back_populates="book_authors")


class BookTag(Base):
    __tablename__ = "book_tags"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    book = relationship("Book", back_populates="book_tags")
    tag = relationship("Tag", back_populates="book_tags")


class BookSeries(Base):
    __tablename__ = "book_series"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    series_index: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    series_label: Mapped[str | None] = mapped_column(String(80))

    book = relationship("Book", back_populates="book_series")
    series = relationship("Series", back_populates="book_series")


class CollectionBook(Base):
    __tablename__ = "collection_books"

    collection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    collection = relationship("Collection", back_populates="collection_books")
    book = relationship("Book", back_populates="collection_books")


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_books_rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(20))
    isbn: Mapped[str | None] = mapped_column(String(40), index=True)
    publisher: Mapped[str | None] = mapped_column(String(255))
    published_date: Mapped[str | None] = mapped_column(String(40))
    original_filename: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    file_hash: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    cover_path: Mapped[str | None] = mapped_column(Text)
    metadata_source: Mapped[str | None] = mapped_column(String(80))
    metadata_provider_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="unread", nullable=False, index=True)
    rating: Mapped[int | None] = mapped_column(Integer, index=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    book_authors = relationship(
        "BookAuthor", back_populates="book", cascade="all, delete-orphan", order_by="BookAuthor.position"
    )
    book_tags = relationship("BookTag", back_populates="book", cascade="all, delete-orphan")
    book_series = relationship(
        "BookSeries", back_populates="book", cascade="all, delete-orphan", uselist=False
    )
    collection_books = relationship(
        "CollectionBook", back_populates="book", cascade="all, delete-orphan"
    )


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    sort_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    book_authors = relationship("BookAuthor", back_populates="author", cascade="all, delete-orphan")


class Series(Base):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    book_series = relationship("BookSeries", back_populates="series", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    color: Mapped[str | None] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    book_tags = relationship("BookTag", back_populates="tag", cascade="all, delete-orphan")


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    cover_book_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("books.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    collection_books = relationship(
        "CollectionBook", back_populates="collection", cascade="all, delete-orphan"
    )
