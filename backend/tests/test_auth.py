from __future__ import annotations

import os
import shutil
import zipfile
from io import BytesIO
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-with-at-least-thirty-two-bytes"
TEST_LIBRARY_PATH = Path(__file__).parent / ".test-library"
os.environ["LIBRARY_PATH"] = str(TEST_LIBRARY_PATH)
os.environ["INCOMING_PATH"] = str(TEST_LIBRARY_PATH / "incoming")

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: F401, E402


def setup_function() -> None:
    shutil.rmtree(TEST_LIBRARY_PATH, ignore_errors=True)
    Base.metadata.create_all(bind=engine)


def teardown_function() -> None:
    Base.metadata.drop_all(bind=engine)
    shutil.rmtree(TEST_LIBRARY_PATH, ignore_errors=True)


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_first_user_setup_login_and_me() -> None:
    client = TestClient(app)
    setup = client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )
    assert setup.status_code == 201
    assert setup.json()["user"]["username"] == "admin"

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["display_name"] == "Aurelia"

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "very-secure-password"},
    )
    assert login.status_code == 200
    assert login.json()["ok"] is True


def test_epub_upload_extracts_book_and_detects_duplicate() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    epub_bytes = make_test_epub()
    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("phase-two.epub", epub_bytes, "application/epub+zip")},
    )
    assert upload.status_code == 201
    payload = upload.json()
    assert payload["status"] == "success"
    assert payload["book_id"]

    books = client.get("/api/v1/books")
    assert books.status_code == 200
    assert books.json()["items"][0]["title"] == "Aurelia Phase Two"
    assert books.json()["items"][0]["authors"] == ["Codex Tester"]

    cover = client.get(f"/api/v1/books/{payload['book_id']}/cover")
    assert cover.status_code == 200
    assert cover.headers["content-type"] == "image/jpeg"

    file_response = client.get(f"/api/v1/books/{payload['book_id']}/file")
    assert file_response.status_code == 200
    assert file_response.headers["content-type"].startswith("application/epub+zip")

    duplicate = client.post(
        "/api/v1/books/upload",
        files={"file": ("phase-two-copy.epub", epub_bytes, "application/epub+zip")},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["status"] == "warning"
    assert duplicate.json()["book_id"] == payload["book_id"]


def make_test_epub() -> bytes:
    cover_buffer = BytesIO()
    Image.new("RGB", (2, 2), (245, 197, 66)).save(cover_buffer, "PNG")
    png_cover = cover_buffer.getvalue()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="book-id" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">9780000000002</dc:identifier>
    <dc:title>Aurelia Phase Two</dc:title>
    <dc:creator>Codex Tester</dc:creator>
    <dc:language>fr</dc:language>
    <dc:publisher>Aurelia Lab</dc:publisher>
    <dc:date>2026-04-26</dc:date>
    <dc:description>EPUB synthetique pour test.</dc:description>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/>
    <item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image"/>
  </manifest>
  <spine>
    <itemref idref="chapter"/>
  </spine>
</package>""",
        )
        archive.writestr(
            "OEBPS/chapter.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Start</title></head>
<body><h1>Aurelia</h1><p>Phase Two test EPUB.</p></body></html>""",
        )
        archive.writestr("OEBPS/cover.png", png_cover)
    return buffer.getvalue()
