from __future__ import annotations

import os
import shutil
import uuid
import zipfile
from decimal import Decimal
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

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: F401, E402
from app.models.metadata import MetadataProviderResult  # noqa: E402
from app.models.reading import Bookmark  # noqa: E402
from app.services.metadata_service import MetadataService  # noqa: E402


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


def test_reading_settings_are_persisted_and_validated() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    current = client.get("/api/v1/settings/reading")
    assert current.status_code == 200
    assert current.json()["reading_mode"] == "paged"

    updated = client.put(
        "/api/v1/settings/reading",
        json={
            "font_family": "Georgia",
            "font_size": 20,
            "line_height": "1.75",
            "margin_size": 32,
            "reading_mode": "scroll",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["font_family"] == "Georgia"
    assert updated.json()["font_size"] == 20
    assert updated.json()["line_height"] == "1.75"
    assert updated.json()["margin_size"] == 32
    assert updated.json()["reading_mode"] == "scroll"
    assert updated.json()["updated_at"]

    invalid = client.put("/api/v1/settings/reading", json={"reading_mode": "sideways"})
    assert invalid.status_code == 400


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


def test_progress_endpoint_and_sync_event_update_reading_progress() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("progress.epub", make_test_epub(), "application/epub+zip")},
    )
    assert upload.status_code == 201
    book_id = upload.json()["book_id"]

    update = client.put(
        f"/api/v1/books/{book_id}/progress",
        json={
            "cfi": "epubcfi(/6/2!/4/2/1:0)",
            "progress_percent": 12.5,
            "chapter_label": "Start",
            "chapter_href": "chapter.xhtml",
            "location_json": {"location": 4},
            "device_id": "test-device",
            "client_updated_at": "2026-04-26T12:00:00Z",
        },
    )
    assert update.status_code == 200
    assert update.json()["resolved"] == "client_won"
    assert update.json()["progress"]["progress_percent"] == 12.5

    progress = client.get(f"/api/v1/books/{book_id}/progress")
    assert progress.status_code == 200
    assert progress.json()["cfi"] == "epubcfi(/6/2!/4/2/1:0)"

    sync = client.post(
        "/api/v1/sync/events",
        json={
            "device_id": "test-device",
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "type": "progress.updated",
                    "client_created_at": "2026-04-26T12:10:00Z",
                    "payload": {
                        "book_id": book_id,
                        "cfi": "epubcfi(/6/2!/4/2/3:0)",
                        "progress_percent": 64,
                        "chapter_label": "Middle",
                        "chapter_href": "chapter.xhtml",
                        "location_json": {"location": 40},
                        "client_updated_at": "2026-04-26T12:10:00Z",
                    },
                }
            ],
        },
    )
    assert sync.status_code == 200
    assert sync.json()["processed"] == 1

    updated = client.get(f"/api/v1/books/{book_id}/progress")
    assert updated.status_code == 200
    assert updated.json()["progress_percent"] == 64
    assert updated.json()["chapter_label"] == "Middle"

    books = client.get("/api/v1/books")
    assert books.status_code == 200
    assert books.json()["items"][0]["status"] == "in_progress"
    assert books.json()["items"][0]["progress_percent"] == 64


def test_sync_progress_returns_server_winner_for_stale_event() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("progress-conflict.epub", make_test_epub(), "application/epub+zip")},
    )
    assert upload.status_code == 201
    book_id = upload.json()["book_id"]

    current = client.put(
        f"/api/v1/books/{book_id}/progress",
        json={
            "cfi": "epubcfi(/6/2!/4/2/9:0)",
            "progress_percent": 80,
            "client_updated_at": "2026-04-26T12:20:00Z",
        },
    )
    assert current.status_code == 200

    stale = client.post(
        "/api/v1/sync/events",
        json={
            "device_id": "old-device",
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "type": "progress.updated",
                    "client_created_at": "2026-04-26T12:00:00Z",
                    "payload": {
                        "book_id": book_id,
                        "cfi": "epubcfi(/6/2!/4/2/1:0)",
                        "progress_percent": 10,
                        "client_updated_at": "2026-04-26T12:00:00Z",
                    },
                }
            ],
        },
    )
    assert stale.status_code == 200
    payload = stale.json()
    assert payload["processed"] == 1
    assert payload["results"][0]["resolved"] == "server_won"
    assert payload["results"][0]["progress"]["progress_percent"] == 80

    progress = client.get(f"/api/v1/books/{book_id}/progress")
    assert progress.status_code == 200
    assert progress.json()["progress_percent"] == 80


def test_sync_bookmark_create_conflict_and_delete() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("bookmark.epub", make_test_epub(), "application/epub+zip")},
    )
    assert upload.status_code == 201
    book_id = upload.json()["book_id"]
    bookmark_id = str(uuid.uuid4())

    created = client.post(
        "/api/v1/sync/events",
        json={
            "device_id": "bookmark-device",
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "type": "bookmark.created",
                    "client_created_at": "2026-04-26T12:00:00Z",
                    "payload": {
                        "id": bookmark_id,
                        "book_id": book_id,
                        "cfi": "epubcfi(/6/2!/4/2/1:0)",
                        "progress_percent": 18,
                        "chapter_label": "Start",
                        "created_at": "2026-04-26T12:00:00Z",
                        "updated_at": "2026-04-26T12:00:00Z",
                    },
                }
            ],
        },
    )
    assert created.status_code == 200
    assert created.json()["processed"] == 1
    assert created.json()["results"][0]["bookmark"]["cfi"] == "epubcfi(/6/2!/4/2/1:0)"

    listed = client.get(f"/api/v1/books/{book_id}/bookmarks")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == bookmark_id
    assert listed.json()["items"][0]["progress_percent"] == 18

    with SessionLocal() as db:
        bookmark = db.get(Bookmark, uuid.UUID(bookmark_id))
        assert bookmark is not None
        assert bookmark.chapter_label == "Start"

    stale = client.post(
        "/api/v1/sync/events",
        json={
            "device_id": "bookmark-device",
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "type": "bookmark.created",
                    "client_created_at": "2026-04-26T11:50:00Z",
                    "payload": {
                        "id": bookmark_id,
                        "book_id": book_id,
                        "cfi": "epubcfi(/6/2!/4/2/0:0)",
                        "updated_at": "2026-04-26T11:50:00Z",
                    },
                }
            ],
        },
    )
    assert stale.status_code == 200
    assert stale.json()["results"][0]["resolved"] == "server_won"
    assert stale.json()["results"][0]["bookmark"]["cfi"] == "epubcfi(/6/2!/4/2/1:0)"

    deleted = client.post(
        "/api/v1/sync/events",
        json={
            "device_id": "bookmark-device",
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "type": "bookmark.deleted",
                    "client_created_at": "2026-04-26T12:10:00Z",
                    "payload": {
                        "id": bookmark_id,
                        "updated_at": "2026-04-26T12:10:00Z",
                    },
                }
            ],
        },
    )
    assert deleted.status_code == 200
    assert deleted.json()["processed"] == 1
    assert deleted.json()["results"][0]["bookmark"]["deleted_at"] is not None

    with SessionLocal() as db:
        bookmark = db.get(Bookmark, uuid.UUID(bookmark_id))
        assert bookmark is not None
        assert bookmark.deleted_at is not None

    listed_after_delete = client.get(f"/api/v1/books/{book_id}/bookmarks")
    assert listed_after_delete.status_code == 200
    assert listed_after_delete.json() == {"items": [], "total": 0}


def test_book_patch_updates_metadata_authors_and_series() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("metadata.epub", make_test_epub(), "application/epub+zip")},
    )
    assert upload.status_code == 201
    book_id = upload.json()["book_id"]

    update = client.patch(
        f"/api/v1/books/{book_id}",
        json={
            "title": "Aurelia Metadata",
            "authors": ["Elian Vale", "Codex Tester"],
            "series_name": "Aurelia Cycle",
            "series_index": 1.5,
            "tags": ["Fantasy", "Aventure"],
            "status": "in_progress",
            "rating": 4,
            "favorite": True,
        },
    )
    assert update.status_code == 200
    payload = update.json()
    assert payload["title"] == "Aurelia Metadata"
    assert payload["authors"] == ["Elian Vale", "Codex Tester"]
    assert payload["series"] == {"name": "Aurelia Cycle", "index": 1.5, "source": "manual"}
    assert payload["tags"] == ["Aventure", "Fantasy"]
    assert payload["status"] == "in_progress"
    assert payload["rating"] == 4
    assert payload["favorite"] is True

    tagged = client.get("/api/v1/books?tag=Fantasy")
    assert tagged.status_code == 200
    assert tagged.json()["total"] == 1
    assert tagged.json()["items"][0]["title"] == "Aurelia Metadata"


def test_book_list_rating_sort_keeps_unrated_books_last() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    low = client.post(
        "/api/v1/books/upload",
        files={"file": ("rated-low.epub", make_test_epub("Rated Low", "9780000000701"), "application/epub+zip")},
    )
    high = client.post(
        "/api/v1/books/upload",
        files={"file": ("rated-high.epub", make_test_epub("Rated High", "9780000000702"), "application/epub+zip")},
    )
    unrated = client.post(
        "/api/v1/books/upload",
        files={"file": ("unrated.epub", make_test_epub("Unrated", "9780000000703"), "application/epub+zip")},
    )
    assert low.status_code == 201
    assert high.status_code == 201
    assert unrated.status_code == 201

    assert client.patch(f"/api/v1/books/{low.json()['book_id']}", json={"rating": 2}).status_code == 200
    assert client.patch(f"/api/v1/books/{high.json()['book_id']}", json={"rating": 5}).status_code == 200

    desc = client.get("/api/v1/books?sort=rating&order=desc")
    assert desc.status_code == 200
    assert [book["title"] for book in desc.json()["items"]] == ["Rated High", "Rated Low", "Unrated"]

    asc = client.get("/api/v1/books?sort=rating&order=asc")
    assert asc.status_code == 200
    assert [book["title"] for book in asc.json()["items"]] == ["Rated Low", "Rated High", "Unrated"]


def test_metadata_apply_updates_selected_fields_from_provider_result() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("metadata-provider.epub", make_test_epub(), "application/epub+zip")},
    )
    assert upload.status_code == 201
    book_id = upload.json()["book_id"]

    with SessionLocal() as db:
        result = MetadataProviderResult(
            book_id=uuid.UUID(book_id),
            provider="googlebooks",
            provider_item_id="gb-test",
            query="Aurelia provider",
            raw_json={},
            normalized_json={
                "provider": "googlebooks",
                "provider_item_id": "gb-test",
                "title": "Aurelia Provider Edition",
                "subtitle": "The curated one",
                "authors": ["Elian Vale"],
                "description": "<p>Clean provider description.</p>",
                "language": "fr",
                "isbn": "9780000000801",
                "publisher": "Aurelia Press",
                "published_date": "2026-04-26",
            },
            score=Decimal("0.920"),
        )
        db.add(result)
        db.commit()
        result_id = str(result.id)

    apply = client.post(
        f"/api/v1/books/{book_id}/metadata/apply",
        json={
            "result_id": result_id,
            "fields": [
                "title",
                "subtitle",
                "authors",
                "description",
                "language",
                "isbn",
                "publisher",
                "published_date",
            ],
        },
    )
    assert apply.status_code == 200
    payload = apply.json()
    assert payload["title"] == "Aurelia Provider Edition"
    assert payload["subtitle"] == "The curated one"
    assert payload["authors"] == ["Elian Vale"]
    assert payload["description"] == "Clean provider description."
    assert payload["language"] == "fr"
    assert payload["isbn"] == "9780000000801"
    assert payload["publisher"] == "Aurelia Press"
    assert payload["published_date"] == "2026-04-26"
    assert payload["metadata_source"] == "googlebooks"


def test_metadata_apply_cover_replaces_file_and_bumps_cover_url(monkeypatch) -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    upload = client.post(
        "/api/v1/books/upload",
        files={"file": ("provider-cover.epub", make_test_epub(), "application/epub+zip")},
    )
    assert upload.status_code == 201
    book_id = upload.json()["book_id"]
    before = client.get(f"/api/v1/books/{book_id}")
    assert before.status_code == 200
    before_cover_url = before.json()["cover_url"]

    cover_buffer = BytesIO()
    Image.new("RGB", (4, 4), (20, 40, 220)).save(cover_buffer, "PNG")

    def fake_download_cover(self: MetadataService, cover_url: str) -> bytes:
        assert cover_url == "https://example.test/cover.jpg"
        return cover_buffer.getvalue()

    monkeypatch.setattr(MetadataService, "download_cover", fake_download_cover)

    with SessionLocal() as db:
        result = MetadataProviderResult(
            book_id=uuid.UUID(book_id),
            provider="openlibrary",
            provider_item_id="ol-cover",
            query="Aurelia cover",
            raw_json={},
            normalized_json={
                "provider": "openlibrary",
                "provider_item_id": "ol-cover",
                "title": "Aurelia Phase Two",
                "authors": ["Codex Tester"],
                "cover_url": "https://example.test/cover.jpg",
            },
            score=Decimal("0.800"),
        )
        db.add(result)
        db.commit()
        result_id = str(result.id)

    apply = client.post(
        f"/api/v1/books/{book_id}/metadata/apply",
        json={"result_id": result_id, "fields": ["cover"]},
    )
    assert apply.status_code == 200
    after_cover_url = apply.json()["cover_url"]
    assert after_cover_url != before_cover_url

    cover_response = client.get(after_cover_url)
    assert cover_response.status_code == 200
    with Image.open(BytesIO(cover_response.content)) as image:
        red, _green, blue = image.convert("RGB").getpixel((0, 0))
    assert blue > red


def test_google_books_cover_url_prefers_high_resolution_without_page_curl() -> None:
    service = MetadataService(get_settings())
    normalized = service._normalize_googlebook(
        {
            "id": "gb-cover",
            "volumeInfo": {
                "title": "Cover test",
                "imageLinks": {
                    "extraLarge": "http://books.google.com/books/content?id=abc&printsec=frontcover&img=1&zoom=3",
                    "thumbnail": (
                        "http://books.google.com/books/content?id=tiny&printsec=frontcover"
                        "&img=1&zoom=1&edge=curl&source=gbs_api"
                    )
                },
            },
        }
    )

    assert normalized["cover_url"].startswith("https://books.google.com/books/content")
    assert "id=abc" in normalized["cover_url"]
    assert "zoom=0" in normalized["cover_url"]
    assert "edge=curl" not in normalized["cover_url"]


def test_organization_collections_series_and_tags() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    first = client.post(
        "/api/v1/books/upload",
        files={"file": ("org-one.epub", make_test_epub("Org One", "9780000000501"), "application/epub+zip")},
    )
    second = client.post(
        "/api/v1/books/upload",
        files={"file": ("org-two.epub", make_test_epub("Org Two", "9780000000502"), "application/epub+zip")},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    first_id = first.json()["book_id"]
    second_id = second.json()["book_id"]

    update_series = client.patch(
        f"/api/v1/books/{first_id}",
        json={"series_name": "Organisation Cycle", "series_index": 2, "tags": ["Cycle"]},
    )
    assert update_series.status_code == 200
    update_second_series = client.patch(
        f"/api/v1/books/{second_id}",
        json={"series_name": "Organisation Cycle", "series_index": 1, "tags": ["Cycle", "Favori"]},
    )
    assert update_second_series.status_code == 200

    collection = client.post(
        "/api/v1/organization/collections",
        json={"name": "Pile prioritaire", "description": "A lire bientot"},
    )
    assert collection.status_code == 201
    collection_id = collection.json()["id"]
    assert collection.json()["book_count"] == 0

    set_books = client.put(
        f"/api/v1/organization/collections/{collection_id}/books",
        json={"book_ids": [first_id, second_id]},
    )
    assert set_books.status_code == 200
    payload = set_books.json()
    assert payload["book_count"] == 2
    assert [book["title"] for book in payload["books"]] == ["Org One", "Org Two"]

    collections = client.get("/api/v1/organization/collections")
    assert collections.status_code == 200
    assert collections.json()["total"] == 1
    assert collections.json()["items"][0]["name"] == "Pile prioritaire"

    series = client.get("/api/v1/organization/series")
    assert series.status_code == 200
    assert series.json()["total"] == 1
    assert series.json()["items"][0]["name"] == "Organisation Cycle"

    series_detail = client.get(f"/api/v1/organization/series/{series.json()['items'][0]['id']}")
    assert series_detail.status_code == 200
    assert [book["title"] for book in series_detail.json()["books"]] == ["Org Two", "Org One"]

    tags = client.get("/api/v1/organization/tags")
    assert tags.status_code == 200
    assert {tag["name"] for tag in tags.json()["items"]} == {"Cycle", "Favori"}

    create_tag = client.post("/api/v1/organization/tags", json={"name": "Archive", "color": "#f5c542"})
    assert create_tag.status_code == 201
    assert create_tag.json()["name"] == "Archive"


def test_organization_series_materializes_import_path_series() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )

    series_dir = TEST_LIBRARY_PATH / "incoming" / "CHERUB"
    series_dir.mkdir(parents=True)
    (series_dir / "CHERUB 01.epub").write_bytes(make_test_epub("100 jours en enfer", "9780000000601"))
    (series_dir / "CHERUB 02.epub").write_bytes(make_test_epub("Trafic", "9780000000602"))

    scan = client.post("/api/v1/library/scan", json={})
    assert scan.status_code == 200
    assert scan.json()["imported"] == 2

    series = client.get("/api/v1/organization/series")
    assert series.status_code == 200
    payload = series.json()
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "CHERUB"
    assert payload["items"][0]["book_count"] == 2

    detail = client.get(f"/api/v1/organization/series/{payload['items'][0]['id']}")
    assert detail.status_code == 200
    assert [book["title"] for book in detail.json()["books"]] == ["100 jours en enfer", "Trafic"]

    book_detail = client.get(f"/api/v1/books/{detail.json()['books'][0]['id']}")
    assert book_detail.status_code == 200
    assert book_detail.json()["series"]["source"] == "import_path"


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
