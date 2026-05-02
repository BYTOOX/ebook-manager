from __future__ import annotations

from app.core.config import Settings
from app.models.book import Author, Book, BookAuthor
from app.schemas.metadata import MetadataSearchPayload
from app.services.metadata_service import MetadataService, _is_french_candidate


def make_book() -> Book:
    book = Book(
        title="Tome 10 - Le grand jeu",
        language="fr",
        original_filename="CHERUB/Tome 10 - Le grand jeu.epub",
        file_path="library/cherub-10.epub",
    )
    book.book_authors.append(BookAuthor(author=Author(name="Robert Muchamore"), position=0))
    return book


def test_google_queries_include_series_and_volume_context() -> None:
    service = MetadataService(Settings())
    context = service._context_for(
        make_book(),
        MetadataSearchPayload(query="Tome 10 - Le grand jeu Robert Muchamore"),
    )

    queries = service._google_queries(context)

    assert context.series_name == "CHERUB"
    assert context.series_index == 10
    assert "CHERUB Tome 10 Le grand jeu Robert Muchamore" in queries
    assert "CHERUB Mission 10 Le grand jeu Robert Muchamore" in queries
    assert "Tome 10 - Le grand jeu Robert Muchamore" in queries


def test_score_prefers_matching_french_series_volume() -> None:
    service = MetadataService(Settings())
    book = make_book()
    context = service._context_for(book, MetadataSearchPayload())

    good = {
        "title": "Cherub (Mission 10) - Le grand jeu",
        "authors": ["Robert Muchamore"],
        "language": "fr",
        "cover_url": "https://example.test/cover.jpg",
        "description": "Un roman CHERUB.",
        "publisher": "Casterman",
    }
    wrong_volume = {
        "title": "Cherub (Mission 13) - Le clan Aramov",
        "authors": ["Robert Muchamore"],
        "language": "fr",
        "cover_url": "https://example.test/cover.jpg",
        "description": "Un roman CHERUB.",
        "publisher": "Casterman",
    }

    assert service._score_candidate(book, good, None, context) > 0.85
    assert service._score_candidate(book, good, None, context) > service._score_candidate(
        book, wrong_volume, None, context
    )


def test_score_trusts_exact_french_title_without_author_or_isbn() -> None:
    service = MetadataService(Settings())
    book = Book(
        title="Harry Potter a l'ecole des sorciers",
        language="fr",
        original_filename="Harry Potter a l'ecole des sorciers.epub",
        file_path="library/hp-1.epub",
    )
    context = service._context_for(book, MetadataSearchPayload())

    candidate = {
        "title": "HARRY POTTER A L'ECOLE DES SORCIERS",
        "authors": [],
        "language": "fr",
    }

    assert service._score_candidate(book, candidate, None, context) >= 0.75


def test_noisy_parenthetical_editions_are_cleaned_for_search_and_score() -> None:
    service = MetadataService(Settings())
    book = Book(
        title="Harry Potter et le Prisonnier d'Azkaban (Serpentard)",
        language="fr",
        original_filename="Harry Potter/Harry Potter 3.epub",
        file_path="library/hp-3.epub",
    )
    context = service._context_for(book, MetadataSearchPayload())

    assert context.title_search == "Harry Potter et le Prisonnier d'Azkaban"
    assert context.query == "Harry Potter et le Prisonnier d'Azkaban"
    assert all("Serpentard" not in query for query in service._google_queries(context)[:3])

    candidate = {
        "title": "HARRY POTTER ET LE PRISONNIER D'AZKABAN (SERPENTARD)",
        "authors": [],
        "language": "fr",
        "cover_url": "https://example.test/cover.jpg",
        "publisher": "Gallimard",
    }

    assert service._score_candidate(book, candidate, None, context) >= 0.75


def test_non_french_candidates_are_filtered() -> None:
    assert _is_french_candidate({"language": "fr"})
    assert _is_french_candidate({"language": None})
    assert not _is_french_candidate({"language": "en"})
