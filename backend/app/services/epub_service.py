from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

import ebooklib
from ebooklib import epub


@dataclass
class ExtractedEpubMetadata:
    title: str
    authors: list[str] = field(default_factory=list)
    language: str | None = None
    isbn: str | None = None
    publisher: str | None = None
    published_date: str | None = None
    description: str | None = None
    subjects: list[str] = field(default_factory=list)
    contributors: list[str] = field(default_factory=list)
    cover_bytes: bytes | None = None
    raw: dict[str, object] = field(default_factory=dict)


class EpubValidationError(ValueError):
    pass


class EpubService:
    def validate_epub(self, path: Path) -> None:
        if path.suffix.lower() != ".epub":
            raise EpubValidationError("Only EPUB files are supported")
        if not zipfile.is_zipfile(path):
            raise EpubValidationError("File is not a valid EPUB archive")

        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "mimetype" not in names or "META-INF/container.xml" not in names:
                raise EpubValidationError("EPUB archive is missing required files")
            mimetype = archive.read("mimetype").decode("utf-8", errors="ignore").strip()
            if mimetype != "application/epub+zip":
                raise EpubValidationError("Invalid EPUB mimetype")

    def extract_metadata(self, path: Path) -> ExtractedEpubMetadata:
        self.validate_epub(path)
        book = epub.read_epub(str(path))

        title = self._first_metadata(book, "DC", "title") or path.stem
        authors = self._all_metadata(book, "DC", "creator")
        identifiers = self._all_metadata(book, "DC", "identifier")

        metadata = ExtractedEpubMetadata(
            title=title.strip() or path.stem,
            authors=[author.strip() for author in authors if author.strip()],
            language=self._first_metadata(book, "DC", "language"),
            isbn=self._find_isbn(identifiers),
            publisher=self._first_metadata(book, "DC", "publisher"),
            published_date=self._first_metadata(book, "DC", "date"),
            description=clean_metadata_text(self._first_metadata(book, "DC", "description")),
            subjects=self._clean_list(self._all_metadata(book, "DC", "subject")),
            contributors=self._clean_list(self._all_metadata(book, "DC", "contributor")),
            cover_bytes=self._extract_cover(book),
            raw={
                "titles": self._all_metadata(book, "DC", "title"),
                "creators": authors,
                "contributors": self._all_metadata(book, "DC", "contributor"),
                "identifiers": identifiers,
                "subjects": self._all_metadata(book, "DC", "subject"),
            },
        )
        return metadata

    def _first_metadata(self, book: epub.EpubBook, namespace: str, name: str) -> str | None:
        values = self._all_metadata(book, namespace, name)
        return values[0] if values else None

    def _all_metadata(self, book: epub.EpubBook, namespace: str, name: str) -> list[str]:
        values: list[str] = []
        for entry in book.get_metadata(namespace, name):
            if entry and entry[0]:
                values.append(str(entry[0]))
        return values

    def _clean_list(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        cleaned: list[str] = []
        for value in values:
            text = clean_metadata_text(value)
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        return cleaned

    def _find_isbn(self, identifiers: list[str]) -> str | None:
        for value in identifiers:
            compact = value.replace("-", "").replace(" ", "")
            if compact.upper().startswith("ISBN"):
                compact = compact[4:].lstrip(":")
            if len(compact) in {10, 13} and compact[:-1].isdigit():
                return compact
        return None

    def _extract_cover(self, book: epub.EpubBook) -> bytes | None:
        cover_meta = book.get_metadata("OPF", "cover")
        for _, attributes in cover_meta:
            cover_id = attributes.get("content") if isinstance(attributes, dict) else None
            if cover_id:
                item = book.get_item_with_id(cover_id)
                if item is not None:
                    return item.get_content()

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER:
                return item.get_content()

        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            name = item.get_name().lower()
            if "cover" in name:
                return item.get_content()
        return None


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def clean_metadata_text(value: str | None) -> str | None:
    if value is None:
        return None

    parser = _TextHTMLParser()
    parser.feed(value)
    text = " ".join(parser.parts) if parser.parts else value
    text = " ".join(text.split())
    return text or None
