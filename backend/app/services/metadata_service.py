from __future__ import annotations

import logging
import re
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.book import Book
from app.models.metadata import MetadataProviderResult
from app.schemas.metadata import MetadataCandidate, MetadataProvider, MetadataSearchPayload
from app.services.epub_service import clean_metadata_text

logger = logging.getLogger(__name__)


class MetadataService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def search_candidates(
        self,
        db: Session,
        book: Book,
        payload: MetadataSearchPayload,
    ) -> list[MetadataCandidate]:
        query = self._query_for(book, payload)
        isbn = _clean_isbn(payload.isbn or book.isbn)
        providers = payload.providers or ["openlibrary", "googlebooks"]
        normalized: list[dict[str, Any]] = []

        with httpx.Client(timeout=8, follow_redirects=True) as client:
            if "openlibrary" in providers and self.settings.METADATA_OPENLIBRARY_ENABLED:
                normalized.extend(self._safe_search_provider("openlibrary", client, query, isbn))
            if "googlebooks" in providers and self.settings.METADATA_GOOGLEBOOKS_ENABLED:
                normalized.extend(self._safe_search_provider("googlebooks", client, query, isbn))

        candidates: list[MetadataCandidate] = []
        for item in normalized:
            score = self._score_candidate(book, item, isbn)
            item["score"] = score
            result = MetadataProviderResult(
                book_id=book.id,
                provider=item["provider"],
                provider_item_id=item.get("provider_item_id"),
                query=query,
                raw_json=item.get("raw") if isinstance(item.get("raw"), dict) else {},
                normalized_json={key: value for key, value in item.items() if key != "raw"},
                score=Decimal(str(score)),
            )
            db.add(result)
            db.flush()
            candidates.append(MetadataCandidate(id=result.id, **item))

        return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)[:12]

    def download_cover(self, cover_url: str | None) -> bytes | None:
        if not cover_url or not cover_url.startswith(("https://", "http://")):
            return None
        try:
            with httpx.Client(timeout=8, follow_redirects=True) as client:
                response = client.get(cover_url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("metadata cover download failed: %s", exc)
            return None

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/") or len(response.content) > 10 * 1024 * 1024:
            return None
        return response.content

    def _safe_search_provider(
        self,
        provider: MetadataProvider,
        client: httpx.Client,
        query: str,
        isbn: str | None,
    ) -> list[dict[str, Any]]:
        try:
            if provider == "openlibrary":
                return self._search_openlibrary(client, query, isbn)
            return self._search_googlebooks(client, query, isbn)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("%s metadata search failed: %s", provider, exc)
            return []

    def _search_openlibrary(
        self,
        client: httpx.Client,
        query: str,
        isbn: str | None,
    ) -> list[dict[str, Any]]:
        params = {
            "limit": "8",
            "fields": ",".join(
                [
                    "key",
                    "title",
                    "subtitle",
                    "author_name",
                    "first_publish_year",
                    "publisher",
                    "isbn",
                    "language",
                    "cover_i",
                    "edition_key",
                ]
            ),
        }
        if isbn:
            params["isbn"] = isbn
        else:
            params["q"] = query

        response = client.get("https://openlibrary.org/search.json", params=params)
        response.raise_for_status()
        payload = response.json()
        docs = payload.get("docs") if isinstance(payload, dict) else []
        return [self._normalize_openlibrary(doc) for doc in docs if isinstance(doc, dict)]

    def _search_googlebooks(
        self,
        client: httpx.Client,
        query: str,
        isbn: str | None,
    ) -> list[dict[str, Any]]:
        response = client.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": f"isbn:{isbn}" if isbn else query, "maxResults": "8", "printType": "books"},
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items") if isinstance(payload, dict) else []
        return [self._normalize_googlebook(item) for item in items if isinstance(item, dict)]

    def _normalize_openlibrary(self, doc: dict[str, Any]) -> dict[str, Any]:
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
        isbn = _first_isbn(doc.get("isbn"))
        return {
            "provider": "openlibrary",
            "provider_item_id": _first_string(doc.get("edition_key")) or _string_or_none(doc.get("key")),
            "title": _string_or_none(doc.get("title")) or "Titre inconnu",
            "subtitle": _string_or_none(doc.get("subtitle")),
            "authors": _clean_list(doc.get("author_name")),
            "description": None,
            "language": _first_string(doc.get("language")),
            "isbn": isbn,
            "publisher": _first_string(doc.get("publisher")),
            "published_date": _string_or_none(doc.get("first_publish_year")),
            "cover_url": cover_url,
            "raw": doc,
        }

    def _normalize_googlebook(self, item: dict[str, Any]) -> dict[str, Any]:
        info = item.get("volumeInfo") if isinstance(item.get("volumeInfo"), dict) else {}
        image_links = info.get("imageLinks") if isinstance(info.get("imageLinks"), dict) else {}
        cover_url = _string_or_none(image_links.get("thumbnail") or image_links.get("smallThumbnail"))
        if cover_url:
            cover_url = cover_url.replace("http://", "https://", 1)
        return {
            "provider": "googlebooks",
            "provider_item_id": _string_or_none(item.get("id")),
            "title": _string_or_none(info.get("title")) or "Titre inconnu",
            "subtitle": _string_or_none(info.get("subtitle")),
            "authors": _clean_list(info.get("authors")),
            "description": clean_metadata_text(_string_or_none(info.get("description"))),
            "language": _string_or_none(info.get("language")),
            "isbn": _first_google_isbn(info.get("industryIdentifiers")),
            "publisher": _string_or_none(info.get("publisher")),
            "published_date": _string_or_none(info.get("publishedDate")),
            "cover_url": cover_url,
            "raw": item,
        }

    def _query_for(self, book: Book, payload: MetadataSearchPayload) -> str:
        clean_query = payload.query.strip() if payload.query else ""
        if clean_query:
            return clean_query
        authors = " ".join(link.author.name for link in book.book_authors[:2])
        return " ".join(part for part in [book.title, authors] if part).strip()

    def _score_candidate(self, book: Book, candidate: dict[str, Any], requested_isbn: str | None) -> float:
        score = 0.0
        book_isbn = _clean_isbn(book.isbn)
        candidate_isbn = _clean_isbn(_string_or_none(candidate.get("isbn")))
        if candidate_isbn and candidate_isbn in {book_isbn, requested_isbn}:
            score += 0.45

        score += 0.3 * _ratio(book.title, _string_or_none(candidate.get("title")))
        score += 0.1 * _author_score(
            [link.author.name for link in book.book_authors],
            candidate.get("authors") if isinstance(candidate.get("authors"), list) else [],
        )
        if candidate.get("cover_url"):
            score += 0.05
        if candidate.get("description"):
            score += 0.05
        if book.language and candidate.get("language") == book.language:
            score += 0.05
        return round(min(score, 1.0), 3)


def _clean_isbn(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", value)
    return cleaned.upper() or None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_string(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            text = _string_or_none(item)
            if text:
                return text
        return None
    return _string_or_none(value)


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = clean_metadata_text(_string_or_none(item))
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _first_isbn(value: Any) -> str | None:
    values = value if isinstance(value, list) else [value]
    cleaned = [_clean_isbn(_string_or_none(item)) for item in values]
    isbn13 = next((item for item in cleaned if item and len(item) == 13), None)
    return isbn13 or next((item for item in cleaned if item), None)


def _first_google_isbn(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    identifiers = [
        item for item in value if isinstance(item, dict) and _string_or_none(item.get("identifier"))
    ]
    isbn13 = next(
        (
            _clean_isbn(item.get("identifier"))
            for item in identifiers
            if item.get("type") == "ISBN_13"
        ),
        None,
    )
    return isbn13 or _first_isbn([item.get("identifier") for item in identifiers])


def _normal(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").casefold().strip()


def _ratio(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, _normal(left), _normal(right)).ratio()


def _author_score(book_authors: list[str], candidate_authors: list[Any]) -> float:
    if not book_authors or not candidate_authors:
        return 0.0
    ratios = [
        _ratio(book_author, _string_or_none(candidate_author))
        for book_author in book_authors
        for candidate_author in candidate_authors
    ]
    return max(ratios, default=0.0)
