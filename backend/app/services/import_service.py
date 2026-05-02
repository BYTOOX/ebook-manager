from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.book import Author, Book, BookAuthor
from app.models.import_job import ImportJob
from app.services.epub_service import EpubService
from app.services.metadata_enrichment_service import (
    DEFAULT_AUTO_METADATA_FIELDS,
    MetadataEnrichmentService,
)
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage = StorageService(settings)
        self.epub = EpubService()

    def import_epub(
        self,
        db: Session,
        source_path: Path,
        *,
        source: str,
        original_filename: str | None = None,
        remove_source: bool = False,
    ) -> ImportJob:
        self.storage.ensure_layout()
        job = ImportJob(
            source=source,
            status="running",
            filename=original_filename or source_path.name,
            file_path=str(source_path),
            started_at=datetime.now(UTC),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            file_hash = self.storage.hash_file(source_path)
            existing = db.scalar(
                select(Book).where(Book.file_hash == file_hash, Book.deleted_at.is_(None))
            )
            if existing is not None:
                job.status = "warning"
                job.error_message = "Exact duplicate detected by SHA-256 hash"
                job.result_book_id = existing.id
                job.finished_at = datetime.now(UTC)
                db.add(job)
                db.commit()
                db.refresh(job)
                return job

            metadata = self.epub.extract_metadata(source_path)
            book_id = uuid.uuid4()
            epub_path = self.storage.copy_original_epub(source_path, book_id)
            cover_path = self.storage.save_cover_jpeg(metadata.cover_bytes, book_id)
            self.storage.save_metadata_snapshot(
                {
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "language": metadata.language,
                    "isbn": metadata.isbn,
                    "publisher": metadata.publisher,
                    "published_date": metadata.published_date,
                    "description": metadata.description,
                    "subjects": metadata.subjects,
                    "contributors": metadata.contributors,
                    "source": "epub",
                    "raw": metadata.raw,
                },
                book_id,
            )

            book = Book(
                id=book_id,
                title=metadata.title,
                description=metadata.description,
                language=metadata.language,
                isbn=metadata.isbn,
                publisher=metadata.publisher,
                published_date=metadata.published_date,
                original_filename=original_filename or source_path.name,
                file_path=str(epub_path),
                file_size=epub_path.stat().st_size,
                file_hash=file_hash,
                cover_path=str(cover_path) if cover_path else None,
                metadata_source="epub",
            )
            db.add(book)
            db.flush()

            for position, author_name in enumerate(metadata.authors):
                author = self._get_or_create_author(db, author_name)
                db.add(BookAuthor(book_id=book.id, author_id=author.id, position=position))

            job.status = "success"
            job.result_book_id = book.id
            job.finished_at = datetime.now(UTC)
            db.add(job)
            db.commit()
            db.refresh(job)
            if self.settings.METADATA_AUTO_ENRICH_ON_IMPORT:
                try:
                    db.refresh(book)
                    MetadataEnrichmentService(self.settings).auto_enrich_book(
                        db,
                        book,
                        fields=DEFAULT_AUTO_METADATA_FIELDS,
                    )
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    logger.warning("metadata enrichment during import failed for %s: %s", source_path, exc)
                db.refresh(job)
            return job
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.now(UTC)
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        finally:
            if remove_source:
                source_path.unlink(missing_ok=True)

    def scan_incoming(self, db: Session, path: Path | None = None) -> list[ImportJob]:
        self.storage.ensure_layout()
        scan_path = self.storage.assert_inside_library(path or self.storage.incoming_path)
        if not scan_path.exists():
            scan_path.mkdir(parents=True, exist_ok=True)
            return []
        if not scan_path.is_dir():
            raise ValueError("Scan path must be a directory")

        jobs: list[ImportJob] = []
        for epub_path in self._iter_epub_files(scan_path):
            jobs.append(
                self.import_epub(
                    db,
                    epub_path,
                    source="scan",
                    original_filename=epub_path.relative_to(scan_path).as_posix(),
                    remove_source=False,
                )
            )
        return jobs

    def _iter_epub_files(self, scan_path: Path) -> list[Path]:
        library_path = self.storage.library_path.resolve()
        ignored_library_roots = {"books", "tmp", "exports"}
        epub_files: list[Path] = []

        for candidate in scan_path.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() != ".epub":
                continue

            resolved = candidate.resolve()
            try:
                relative_to_library = resolved.relative_to(library_path)
            except ValueError:
                relative_to_library = None

            if relative_to_library and relative_to_library.parts:
                if relative_to_library.parts[0] in ignored_library_roots:
                    continue

            epub_files.append(candidate)

        return sorted(epub_files, key=lambda path: path.relative_to(scan_path).as_posix().casefold())

    def _get_or_create_author(self, db: Session, name: str) -> Author:
        clean_name = name.strip()
        author = db.scalar(select(Author).where(Author.name == clean_name))
        if author is not None:
            return author

        author = Author(name=clean_name)
        db.add(author)
        db.flush()
        return author
