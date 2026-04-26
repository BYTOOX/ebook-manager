from __future__ import annotations

import os
import shutil
import zipfile
from html import escape
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

    detail = client.get(f"/api/v1/books/{payload['book_id']}")
    assert detail.status_code == 200
    assert detail.json()["original_filename"] == "phase-two.epub"

    duplicate = client.post(
        "/api/v1/books/upload",
        files={"file": ("phase-two-copy.epub", epub_bytes, "application/epub+zip")},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["status"] == "warning"
    assert duplicate.json()["book_id"] == payload["book_id"]


def test_scan_imports_epubs_recursively_from_series_folders() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    series_dir = TEST_LIBRARY_PATH / "incoming" / "Nom de la serie"
    series_dir.mkdir(parents=True)
    (series_dir / "Tome1-aurelia.epub").write_bytes(make_test_epub())

    scan = client.post("/api/v1/library/scan", json={})
    assert scan.status_code == 200
    payload = scan.json()
    assert payload["scanned"] == 1
    assert payload["imported"] == 1
    assert payload["jobs"][0]["filename"] == "Nom de la serie/Tome1-aurelia.epub"

    books = client.get("/api/v1/books")
    assert books.status_code == 200
    assert books.json()["total"] == 1
    assert books.json()["items"][0]["title"] == "Aurelia Phase Two"


def test_scan_imports_every_epub_recursively_regardless_of_naming() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    incoming = TEST_LIBRARY_PATH / "incoming"
    files = {
        incoming / "Loose Book.EPUB": make_test_epub("Loose Book", "9780000000101"),
        incoming / "Auteurs divers" / "Anthologie bizarre.epub": make_test_epub(
            "Anthologie bizarre", "9780000000102"
        ),
        incoming / "Serie X" / "Sous-cycle" / "vol_003-final.epub": make_test_epub(
            "Volume Final", "9780000000103"
        ),
    }
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    scan = client.post("/api/v1/library/scan", json={})
    assert scan.status_code == 200
    payload = scan.json()
    assert payload["scanned"] == 3
    assert payload["imported"] == 3
    assert {job["filename"] for job in payload["jobs"]} == {
        "Loose Book.EPUB",
        "Auteurs divers/Anthologie bizarre.epub",
        "Serie X/Sous-cycle/vol_003-final.epub",
    }

    books = client.get("/api/v1/books")
    assert books.status_code == 200
    assert books.json()["total"] == 3
    assert {book["title"] for book in books.json()["items"]} == {
        "Loose Book",
        "Anthologie bizarre",
        "Volume Final",
    }


def test_book_search_matches_nested_original_filename() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    cherub_dir = TEST_LIBRARY_PATH / "incoming" / "CHERUB"
    cherub_dir.mkdir(parents=True)
    (cherub_dir / "100 jours en enfer.epub").write_bytes(
        make_test_epub("100 jours en enfer", "9780000000201")
    )

    scan = client.post("/api/v1/library/scan", json={})
    assert scan.status_code == 200
    assert scan.json()["imported"] == 1

    search = client.get("/api/v1/books?q=cherub")
    assert search.status_code == 200
    payload = search.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "100 jours en enfer"


def test_book_detail_cleans_description_and_lists_series_books() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    cherub_dir = TEST_LIBRARY_PATH / "incoming" / "CHERUB"
    cherub_dir.mkdir(parents=True)
    (cherub_dir / "CHERUB 01.epub").write_bytes(
        make_test_epub(
            "100 jours en enfer",
            "9780000000301",
            '<h3><span class="Apple-style-span">James rejoint Cherub.</span></h3>',
        )
    )
    (cherub_dir / "CHERUB 02.epub").write_bytes(
        make_test_epub("Trafic", "9780000000302", "Deuxieme mission.")
    )

    scan = client.post("/api/v1/library/scan", json={})
    assert scan.status_code == 200
    first_book_id = next(
        job["result_book_id"] for job in scan.json()["jobs"] if job["filename"] == "CHERUB/CHERUB 01.epub"
    )

    detail = client.get(f"/api/v1/books/{first_book_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["description"] == "James rejoint Cherub."
    assert payload["series"]["name"] == "CHERUB"
    assert payload["series"]["index"] == 1.0
    assert [book["title"] for book in payload["related_books"]] == ["Trafic"]


def test_series_index_does_not_treat_title_number_as_volume() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    cherub_dir = TEST_LIBRARY_PATH / "incoming" / "CHERUB"
    cherub_dir.mkdir(parents=True)
    (cherub_dir / "100 jours en enfer.epub").write_bytes(
        make_test_epub("100 jours en enfer", "9780000000401")
    )

    scan = client.post("/api/v1/library/scan", json={})
    assert scan.status_code == 200
    book_id = scan.json()["jobs"][0]["result_book_id"]

    detail = client.get(f"/api/v1/books/{book_id}")
    assert detail.status_code == 200
    assert detail.json()["series"]["name"] == "CHERUB"
    assert detail.json()["series"]["index"] is None


def make_test_epub(
    title: str = "Aurelia Phase Two",
    isbn: str = "9780000000002",
    description: str = "EPUB synthetique pour test.",
) -> bytes:
    cover_buffer = BytesIO()
    Image.new("RGB", (2, 2), (245, 197, 66)).save(cover_buffer, "PNG")
    png_cover = cover_buffer.getvalue()
    buffer = BytesIO()
    escaped_description = escape(description)
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
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="book-id" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{isbn}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>Codex Tester</dc:creator>
    <dc:language>fr</dc:language>
    <dc:publisher>Aurelia Lab</dc:publisher>
    <dc:date>2026-04-26</dc:date>
    <dc:description>{escaped_description}</dc:description>
    <dc:subject>Bibliotheque personnelle</dc:subject>
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
