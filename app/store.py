from __future__ import annotations

from dataclasses import dataclass, field

from app.models import Book


@dataclass
class InMemoryStore:
    books: dict[str, Book] = field(default_factory=dict)

    def upsert_book(self, book: Book) -> Book:
        self.books[book.id] = book
        return book

    def get_book(self, book_id: str) -> Book | None:
        return self.books.get(book_id)

    def list_books(self) -> list[Book]:
        return list(self.books.values())


store = InMemoryStore()
