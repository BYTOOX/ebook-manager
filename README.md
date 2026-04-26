# Aurelia

Aurelia is a self-hosted, mobile-first EPUB library and PWA. V1 is intentionally narrow:
EPUB only, PostgreSQL as the server database, IndexedDB for offline client state, and a
premium dark black/gold interface.

## Repository State

The repository started with product and architecture specifications only. Phase 1 adds the
application foundation:

- `backend/`: FastAPI, SQLAlchemy 2.x, Alembic, mono-user auth, initial PostgreSQL schema.
- `frontend/`: React + Vite + TypeScript, PWA shell, dark/gold UI, IndexedDB stores.
- `compose.yaml`: Podman Compose / Docker Compose compatible local stack.

## Stack

Backend:

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic v2
- HTTP-only session cookie backed by a signed token

Frontend:

- React 18
- TypeScript strict
- Vite
- TanStack Query
- Zustand
- Dexie / IndexedDB
- vite-plugin-pwa
- lucide-react icons

## Local Development

Copy the environment file:

```bash
cp .env.example .env
```

Start the full stack:

```bash
podman compose up --build
```

Docker Compose also works:

```bash
docker compose up --build
```

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

URLs:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- OpenAPI: http://localhost:8000/docs

## First Login

Use the setup screen in the PWA, or call:

```bash
curl -X POST http://localhost:8000/api/v1/auth/setup ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"very-secure-password\",\"display_name\":\"Aurelia\"}"
```

If `FIRST_USER_SETUP_TOKEN` is set, include `setup_token` in the JSON body.

## Phase 1 Scope

Implemented now:

- API health endpoint.
- First-user setup, login, logout, `me`, password change.
- Initial schema for users, books, authors, series, tags, collections, reading progress,
  bookmarks, reading settings, import jobs, metadata results, and sync events.
- Alembic initial migration.
- Minimal books listing/detail API for the frontend shell.
- Minimal sync event intake endpoint.
- PWA shell, mobile navigation, login/setup UI, Home, Library, Search, Collections,
  Settings, Import placeholder, Book detail, Reader placeholder.
- IndexedDB stores required by the offline-first architecture.

Next phases:

- Phase 2: EPUB upload, validation, hashing, metadata and cover extraction, storage.
- Phase 3: premium library UI with real imported content.
- Phase 4: integrated EPUB reader.
- Phase 5: offline EPUB download/read path.
- Phase 6: full sync conflict handling and bookmarks sync.
