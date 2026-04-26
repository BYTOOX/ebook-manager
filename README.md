# Aurelia

Aurelia is a self-hosted, mobile-first EPUB library and reader PWA.

V1 is intentionally focused: EPUB only, one local user, PostgreSQL on the server,
IndexedDB for offline state, and a premium dark black/gold interface.

## Current Capabilities

- Local authentication with an HTTP-only session cookie.
- EPUB upload and recursive incoming-folder scan.
- Exact duplicate detection by file hash.
- EPUB metadata and cover extraction.
- Library, search, home resume, book detail, collections, series, tags, ratings, favorites, and reading statuses.
- Integrated EPUB reader with paged mode, scroll mode, table of contents, bookmarks, reading settings, CFI resume, and progress tracking.
- Offline download with EPUB and cover stored in IndexedDB.
- Offline reader path that prefers the local EPUB blob when available.
- Local progress/bookmark queue with automatic sync retry when the network returns.
- Newest-update-wins progress conflict policy.
- Metadata enrichment via Open Library and Google Books with field-by-field user approval.
- Provider cover replacement stored locally by the backend.
- Advanced maintenance page for API health, import jobs, incoming scan, IndexedDB/offline state, sync state, and offline cache cleanup.

## Out Of Scope For V1

- PDF, MOBI, AZW3, CBZ, audiobooks.
- DRM handling or DRM bypass.
- Multi-user accounts.
- Native mobile app.
- AI recommendations or generated metadata.
- OPDS/WebDAV and ebook-device integrations.

## Stack

Backend:

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic v2

Frontend:

- React 18
- Vite
- TypeScript
- TanStack Query
- Zustand
- Dexie / IndexedDB
- epub.js
- vite-plugin-pwa
- lucide-react

## Local Development

Copy the environment file:

```bash
cp .env.example .env
```

Start the full stack:

```bash
docker compose up --build
```

Podman Compose also works:

```bash
podman compose up --build
```

URLs:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- OpenAPI: http://localhost:8000/docs

## Test Login

For the current development database:

- username: `admin`
- password: `PasswordAdmin123`

For a fresh database, use the setup screen in the PWA or call:

```bash
curl -X POST http://localhost:8000/api/v1/auth/setup ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"very-secure-password\",\"display_name\":\"Aurelia\"}"
```

If `FIRST_USER_SETUP_TOKEN` is set, include `setup_token` in the JSON body.

## Bulk Import

With Compose, place EPUB files under `library-import/`.

The backend mounts this folder read-only at `/data/library/incoming`, and the scan action imports every `.epub` file recursively.

Example:

```txt
library-import/
  Series Name/
    Tome1.epub
    Tome2.epub
```

## Development Commands

Backend only:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend only:

```bash
cd frontend
npm install
npm run dev
```

Tests and checks:

```bash
cd backend
.venv\Scripts\python.exe -m pytest

cd ../frontend
npm.cmd run build
```

## Persistent Data

Back up these items:

- PostgreSQL volume `postgres_data`.
- Library volume `library_data`.
- Project `.env` file.
- Optional import staging folder `library-import/` if you keep source EPUBs there.

Inside the backend container, the library volume is mounted at `/data/library`.
