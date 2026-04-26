from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image

from app.core.config import Settings


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def library_path(self) -> Path:
        return self.settings.LIBRARY_PATH

    @property
    def incoming_path(self) -> Path:
        return self.settings.INCOMING_PATH

    def ensure_layout(self) -> None:
        for path in [
            self.library_path,
            self.incoming_path,
            self.library_path / "books",
            self.library_path / "tmp",
            self.library_path / "exports",
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def book_dir(self, book_id: uuid.UUID) -> Path:
        return self.library_path / "books" / str(book_id)

    def original_epub_path(self, book_id: uuid.UUID) -> Path:
        return self.book_dir(book_id) / "original.epub"

    def cover_path(self, book_id: uuid.UUID) -> Path:
        return self.book_dir(book_id) / "cover.jpg"

    def metadata_path(self, book_id: uuid.UUID) -> Path:
        return self.book_dir(book_id) / "metadata.json"

    def ensure_book_dir(self, book_id: uuid.UUID) -> Path:
        path = self.book_dir(book_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def assert_inside_library(self, path: Path) -> Path:
        resolved = path.resolve()
        library = self.library_path.resolve()
        if resolved != library and library not in resolved.parents:
            raise ValueError("Scan path must stay inside LIBRARY_PATH")
        return resolved

    def hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    async def save_upload_to_tmp(self, upload: UploadFile) -> Path:
        self.ensure_layout()
        tmp_path = self.library_path / "tmp" / f"{uuid.uuid4()}.epub"
        max_size = self.settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        written = 0

        with tmp_path.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                written += len(chunk)
                if written > max_size:
                    target.close()
                    tmp_path.unlink(missing_ok=True)
                    raise ValueError(f"EPUB is larger than {self.settings.MAX_UPLOAD_SIZE_MB} MB")
                target.write(chunk)

        return tmp_path

    def copy_original_epub(self, source: Path, book_id: uuid.UUID) -> Path:
        self.ensure_book_dir(book_id)
        destination = self.original_epub_path(book_id)
        shutil.copy2(source, destination)
        return destination

    def save_cover_jpeg(self, cover_bytes: bytes | None, book_id: uuid.UUID) -> Path | None:
        if not cover_bytes:
            return None

        self.ensure_book_dir(book_id)
        destination = self.cover_path(book_id)
        try:
            from io import BytesIO

            with Image.open(BytesIO(cover_bytes)) as image:
                image.convert("RGB").save(destination, "JPEG", quality=90, optimize=True)
        except Exception:
            return None
        return destination

    def save_metadata_snapshot(self, metadata: dict[str, Any], book_id: uuid.UUID) -> Path:
        self.ensure_book_dir(book_id)
        destination = self.metadata_path(book_id)
        destination.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return destination
