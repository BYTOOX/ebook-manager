from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.book import Book
from app.models.metadata import MetadataProviderResult
from app.schemas.metadata import MetadataCandidate, MetadataProvider, MetadataSearchPayload
from app.services.epub_service import clean_metadata_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchContext:
    query: str
    title: str
    title_core: str
    authors: list[str]
    series_name: str | None
    series_index: float | None
    language: str | None


class MetadataService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def search_candidates(
        self,
        db: Session,
        book: Book,
        payload: MetadataSearchPayload,
    ) -> list[MetadataCandidate]:
        context = self._context_for(book, payload)
        query = context.query
        isbn = _clean_isbn(payload.isbn or book.isbn)
        providers = payload.providers or ["googlebooks"]
        normalized: list[dict[str, Any]] = []

        with httpx.Client(timeout=8, follow_redirects=True) as client:
            if "googlebooks" in providers and self.settings.METADATA_GOOGLEBOOKS_ENABLED:
                normalized.extend(self._safe_search_provider("googlebooks", client, context, isbn))

        candidates: list[MetadataCandidate] = []
        for item in _dedupe_candidates(normalized):
            if not _is_french_candidate(item):
                continue
            score = self._score_candidate(book, item, isbn, context)
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
        context: SearchContext,
        isbn: str | None,
    ) -> list[dict[str, Any]]:
        try:
            if provider == "openlibrary":
                return self._search_openlibrary(client, context.query, isbn)
            return self._search_googlebooks(client, context, isbn)
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
        context: SearchContext,
        isbn: str | None,
    ) -> list[dict[str, Any]]:
        queries = [f"isbn:{isbn}"] if isbn else []
        queries.extend(self._google_queries(context))
        candidates: list[dict[str, Any]] = []

        for query in _dedupe_text(queries):
            try:
                response = client.get(
                    "https://www.googleapis.com/books/v1/volumes",
                    params={
                        "q": query,
                        "maxResults": "10",
                        "printType": "books",
                        "langRestrict": "fr",
                        "orderBy": "relevance",
                    },
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError as exc:
                logger.warning("googlebooks metadata query failed for %r: %s", query, exc)
                continue

            items = payload.get("items") if isinstance(payload, dict) else []
            candidates.extend(
                self._normalize_googlebook(item) for item in items if isinstance(item, dict)
            )

        return candidates

    def _normalize_openlibrary(self, doc: dict[str, Any]) -> dict[str, Any]:
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
        isbn = _first_isbn(doc.get("isbn"))
        return {
            "provider": "openlibrary",
            "provider_item_id": _first_string(doc.get("edition_key"))
            or _string_or_none(doc.get("key")),
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
        cover_url = _first_string(
            [
                image_links.get("extraLarge"),
                image_links.get("large"),
                image_links.get("medium"),
                image_links.get("thumbnail"),
                image_links.get("smallThumbnail"),
            ]
        )
        if cover_url:
            cover_url = _upgrade_google_cover_url(cover_url.replace("http://", "https://", 1))
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

    def _context_for(self, book: Book, payload: MetadataSearchPayload) -> SearchContext:
        clean_query = payload.query.strip() if payload.query else ""
        authors = [
            link.author.name.strip()
            for link in book.book_authors[:2]
            if link.author and link.author.name.strip()
        ]
        series_name, series_index = _series_from_book(book)
        title = book.title.strip()
        title_core = _title_core(title)
        fallback_query = " ".join(part for part in [title, " ".join(authors)] if part).strip()
        return SearchContext(
            query=clean_query or fallback_query,
            title=title,
            title_core=title_core,
            authors=authors,
            series_name=series_name,
            series_index=series_index,
            language=book.language,
        )

    def _google_queries(self, context: SearchContext) -> list[str]:
        title = context.title
        core = context.title_core or title
        author_text = " ".join(context.authors)
        primary_author = context.authors[0] if context.authors else ""
        series = context.series_name
        index = _format_series_index(context.series_index)
        queries: list[str] = []

        def add(*parts: str | None) -> None:
            query = " ".join(part.strip() for part in parts if part and part.strip())
            if query:
                queries.append(query)

        if series and index:
            add(series, f"Tome {index}", core, author_text)
            add(series, f"Mission {index}", core, author_text)
            add(series, index, core, author_text)
        if series:
            add(series, core, author_text)
            if context.query and not _contains_normalized(context.query, series):
                query_author = (
                    None
                    if author_text and _contains_normalized(context.query, author_text)
                    else author_text
                )
                add(series, context.query, query_author)

        add(context.query)
        if author_text and not _contains_normalized(context.query, author_text):
            add(context.query, author_text)
        if core != title:
            add(title, author_text)
        add(core, author_text)
        if core and primary_author:
            add(f'intitle:"{core}"', f'inauthor:"{primary_author}"')

        return _dedupe_text(queries)

    def _score_candidate(
        self,
        book: Book,
        candidate: dict[str, Any],
        requested_isbn: str | None,
        context: SearchContext,
    ) -> float:
        score = 0.0
        book_isbn = _clean_isbn(book.isbn)
        candidate_isbn = _clean_isbn(_string_or_none(candidate.get("isbn")))
        if candidate_isbn and candidate_isbn in {book_isbn, requested_isbn}:
            score += 0.45

        candidate_title = _string_or_none(candidate.get("title"))
        candidate_subtitle = _string_or_none(candidate.get("subtitle"))
        candidate_heading = " ".join(part for part in [candidate_title, candidate_subtitle] if part)
        candidate_core = _title_core(candidate_heading)
        title_score = max(
            _ratio(context.title, candidate_heading),
            _ratio(context.title_core, candidate_heading),
            _ratio(context.title_core, candidate_core),
        )
        score += 0.35 * title_score
        score += 0.15 * _author_score(
            [link.author.name for link in book.book_authors],
            candidate.get("authors") if isinstance(candidate.get("authors"), list) else [],
        )
        if context.series_name:
            if _contains_normalized(candidate_heading, context.series_name):
                score += 0.12
            elif _contains_normalized(context.query, context.series_name):
                score -= 0.04
        if context.series_index is not None:
            if _volume_matches(candidate_heading, context.series_index):
                score += 0.1
            elif _volume_candidates(candidate_heading):
                score -= 0.12

        candidate_language = _string_or_none(candidate.get("language"))
        if candidate_language == "fr":
            score += 0.12
        elif candidate_language:
            score -= 0.2

        if candidate.get("cover_url"):
            score += 0.03
        if candidate.get("description"):
            score += 0.03
        if candidate.get("publisher"):
            score += 0.02
        return round(max(0.0, min(score, 1.0)), 3)


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


def _dedupe_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        provider = _string_or_none(item.get("provider")) or ""
        provider_id = _string_or_none(item.get("provider_item_id"))
        key = (
            f"{provider}:{provider_id}"
            if provider_id
            else ":".join(
                [
                    provider,
                    _normal(_string_or_none(item.get("title"))),
                    _normal(" ".join(item.get("authors") or [])),
                    _normal(_string_or_none(item.get("published_date"))),
                ]
            )
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _dedupe_text(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = re.sub(r"\s+", " ", value).strip()
        if not text:
            continue
        key = _normal(text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(text)
    return deduped


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
    text = (value or "").translate(
        {
            ord("\u0153"): "oe",
            ord("\u0152"): "Oe",
            ord("\u2019"): "'",
        }
    )
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"'", " ", text)
    text = re.sub(r"[^0-9A-Za-z]+", " ", text)
    return re.sub(r"\s+", " ", text).casefold().strip()


def _contains_normalized(haystack: str | None, needle: str | None) -> bool:
    clean_haystack = _normal(haystack)
    clean_needle = _normal(needle)
    return bool(clean_haystack and clean_needle and clean_needle in clean_haystack)


def _format_series_index(value: float | None) -> str | None:
    if value is None:
        return None
    if float(value).is_integer():
        return str(int(value))
    return str(value).rstrip("0").rstrip(".")


def _series_from_book(book: Book) -> tuple[str | None, float | None]:
    if book.book_series and book.book_series.series:
        index = (
            float(book.book_series.series_index)
            if book.book_series.series_index is not None
            else None
        )
        return book.book_series.series.name, index
    return _series_from_filename(book.original_filename)


def _series_from_filename(filename: str | None) -> tuple[str | None, float | None]:
    if not filename:
        return None, None
    parts = re.split(r"[\\/]+", filename)
    if len(parts) < 2:
        return None, None

    series_name = parts[0].strip()
    if not series_name:
        return None, None

    name = re.sub(r"\.[^.]+$", "", parts[-1])
    volume_pattern = r"\b(?:tome|vol(?:ume)?|livre|mission|t)\s*0*([0-9]{1,3})\b"
    match = re.search(volume_pattern, name, re.IGNORECASE)
    if not match:
        match = re.search(r"\b[A-Za-z][A-Za-z _-]+0*([0-9]{1,3})\b", name)
    if not match:
        match = re.search(r"^0*([0-9]{1,3})(?:\s*[-_.]|$)", name)
    return series_name, float(match.group(1)) if match else None


def _title_core(title: str | None) -> str:
    text = re.sub(r"\s+", " ", title or "").strip()
    if not text:
        return ""

    patterns = [
        r"^\s*[\[(]?\s*(?:tome|vol(?:ume)?|livre|mission|t)\s*0*[0-9]{1,3}\s*[\])]?[\s\-:_.]*",
        r"^\s*0*[0-9]{1,3}\s*[\-:_.]\s*",
        (
            r"^\s*[^-:]+?\s*[\[(]\s*(?:tome|vol(?:ume)?|livre|mission|t)"
            r"\s*0*[0-9]{1,3}\s*[\])]\s*[\-:_.]*"
        ),
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return text or (title or "").strip()


def _volume_candidates(text: str | None) -> set[int]:
    normal_text = _normal(text)
    volume_pattern = r"\b(?:tome|vol(?:ume)?|livre|mission|t)\s*0*([0-9]{1,3})\b"
    values = {
        int(match.group(1))
        for match in re.finditer(volume_pattern, normal_text)
    }
    values.update(
        int(match.group(1))
        for match in re.finditer(r"[\[(]\s*0*([0-9]{1,3})\s*[\])]", normal_text)
    )
    return values


def _volume_matches(text: str | None, expected: float | None) -> bool:
    if expected is None:
        return False
    if not float(expected).is_integer():
        return False
    return int(expected) in _volume_candidates(text)


def _is_french_candidate(candidate: dict[str, Any]) -> bool:
    language = _string_or_none(candidate.get("language"))
    return language in {None, "", "fr"}


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


def _upgrade_google_cover_url(url: str) -> str:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if parsed.netloc.endswith("google.com") and parsed.path.startswith("/books/content"):
        query["zoom"] = "0"
        query.pop("edge", None)
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )
