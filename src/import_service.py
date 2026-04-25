from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZipFile

SUPPORTED_EXTENSIONS = {".epub", ".pdf"}


@dataclass
class ImportFileResult:
    source_path: str
    hash: str
    extension: str
    duplicate: bool
    stored_as: str | None = None


class ImportService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.books_dir = self.data_dir / "books"
        self.logs_dir = self.data_dir / "logs"
        self.index_path = self.data_dir / "library_index.json"
        self.progress_path = self.data_dir / "progress.json"
        self.log_file = self.logs_dir / "import.log"

        self.books_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._configure_logger()

    def _configure_logger(self) -> None:
        self.logger = logging.getLogger("ebook_import")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _list_supported_files(self, root: Path) -> list[Path]:
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    def _load_index(self) -> dict[str, dict[str, Any]]:
        items = self._read_json(self.index_path, default=[])
        index: dict[str, dict[str, Any]] = {}
        for item in items:
            file_hash = item.get("hash")
            if file_hash:
                index[file_hash] = item
        return index

    def preview_source(self, source_type: str, source_path: str) -> dict[str, Any]:
        temp_dir: Path | None = None
        try:
            files, temp_dir = self._resolve_source_files(source_type, source_path)
            hash_index = self._load_index()

            result: list[ImportFileResult] = []
            for item in files:
                file_hash = self._hash_file(item)
                result.append(
                    ImportFileResult(
                        source_path=str(item),
                        hash=file_hash,
                        extension=item.suffix.lower(),
                        duplicate=file_hash in hash_index,
                    )
                )

            return {
                "sourceType": source_type,
                "sourcePath": source_path,
                "total": len(result),
                "duplicates": sum(1 for r in result if r.duplicate),
                "files": [r.__dict__ for r in result],
            }
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Preview failed for %s (%s)", source_path, source_type)
            raise ValueError(str(exc)) from exc
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def import_source(self, source_type: str, source_path: str) -> dict[str, Any]:
        temp_dir: Path | None = None
        try:
            files, temp_dir = self._resolve_source_files(source_type, source_path)
            hash_index = self._load_index()
            imported: list[ImportFileResult] = []

            for src in files:
                file_hash = self._hash_file(src)
                duplicate = file_hash in hash_index
                if duplicate:
                    imported.append(
                        ImportFileResult(
                            source_path=str(src),
                            hash=file_hash,
                            extension=src.suffix.lower(),
                            duplicate=True,
                        )
                    )
                    continue

                target_name = f"{file_hash}{src.suffix.lower()}"
                target_path = self.books_dir / target_name
                try:
                    shutil.copy2(src, target_path)
                    entry = {
                        "hash": file_hash,
                        "extension": src.suffix.lower(),
                        "storedPath": str(target_path.relative_to(self.project_root)),
                        "sourcePath": str(src),
                        "importedAt": datetime.now(timezone.utc).isoformat(),
                    }
                    hash_index[file_hash] = entry

                    imported.append(
                        ImportFileResult(
                            source_path=str(src),
                            hash=file_hash,
                            extension=src.suffix.lower(),
                            duplicate=False,
                            stored_as=str(target_path),
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    self.logger.exception("Import failed for %s", src)
                    raise ValueError(f"Impossible d'importer {src}: {exc}") from exc

            self._write_json(self.index_path, list(hash_index.values()))

            return {
                "total": len(imported),
                "imported": sum(1 for item in imported if not item.duplicate),
                "duplicates": sum(1 for item in imported if item.duplicate),
                "files": [item.__dict__ for item in imported],
            }
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def import_progress(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("formatVersion") != 1:
            raise ValueError("formatVersion doit être égal à 1")

        books = payload.get("books")
        if not isinstance(books, list):
            raise ValueError("Le champ 'books' doit être une liste")

        existing = self._read_json(self.progress_path, default={"formatVersion": 1, "books": []})
        indexed = {book.get("bookId"): book for book in existing.get("books", []) if book.get("bookId")}

        imported_count = 0
        for book in books:
            book_id = book.get("bookId")
            progress = book.get("progress")
            bookmarks = book.get("bookmarks")
            updated_at = book.get("updatedAt")

            if not book_id or not isinstance(progress, (int, float)) or not isinstance(bookmarks, list) or not updated_at:
                raise ValueError("Entrée de progression invalide; voir docs/sync-format.md")

            indexed[book_id] = {
                "bookId": book_id,
                "progress": float(progress),
                "bookmarks": bookmarks,
                "updatedAt": updated_at,
            }
            imported_count += 1

        merged = {"formatVersion": 1, "books": list(indexed.values())}
        self._write_json(self.progress_path, merged)
        return {"imported": imported_count, "total": len(books)}

    def _resolve_source_files(self, source_type: str, source_path: str) -> tuple[list[Path], Path | None]:
        path = Path(source_path).expanduser().resolve()
        if source_type == "directory":
            if not path.exists() or not path.is_dir():
                raise ValueError("Le dossier source est introuvable")
            return self._list_supported_files(path), None

        if source_type == "zip":
            if not path.exists() or not path.is_file():
                raise ValueError("Le fichier ZIP est introuvable")

            temp_dir = Path(tempfile.mkdtemp(prefix="ebook-import-"))
            with ZipFile(path, "r") as zf:
                zf.extractall(temp_dir)
            return self._list_supported_files(temp_dir), temp_dir

        raise ValueError("sourceType invalide. Utilisez 'directory' ou 'zip'")
