# Backend Specification - Aurelia

## Stack

- FastAPI
- Python 3.12+
- PostgreSQL
- SQLAlchemy 2.x ou SQLModel
- Alembic
- Pydantic v2
- httpx
- ebooklib ou alternative EPUB
- Pillow pour images/covers
- passlib/argon2 ou bcrypt pour password hashing

## Structure recommandée

```txt
backend/
  app/
    main.py
    core/
      config.py
      security.py
      logging.py
      database.py
    models/
      user.py
      book.py
      author.py
      series.py
      tag.py
      collection.py
      progress.py
      bookmark.py
      import_job.py
      metadata.py
    schemas/
      auth.py
      book.py
      progress.py
      bookmark.py
      collection.py
      metadata.py
      settings.py
    api/
      deps.py
      routes/
        auth.py
        books.py
        progress.py
        bookmarks.py
        tags.py
        collections.py
        series.py
        metadata.py
        imports.py
        settings.py
        sync.py
    services/
      epub_service.py
      import_service.py
      scan_service.py
      cover_service.py
      metadata/
        base.py
        openlibrary.py
        googlebooks.py
      sync_service.py
      storage_service.py
    workers/
      import_worker.py
    tests/
  alembic/
  pyproject.toml
```

## Configuration

```env
APP_NAME=Aurelia
APP_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
DATABASE_URL=postgresql+psycopg://aurelia:aurelia@postgres:5432/aurelia
SECRET_KEY=change-me
LIBRARY_PATH=/data/library
INCOMING_PATH=/data/library/incoming
CORS_ORIGINS=http://localhost:3000
METADATA_OPENLIBRARY_ENABLED=true
METADATA_GOOGLEBOOKS_ENABLED=true
```

## StorageService

Responsabilités :
- créer dossier book_id,
- copier original.epub,
- enregistrer cover.jpg,
- lire fichier EPUB,
- retourner chemins,
- supprimer livre,
- calculer hash.

## EpubService

Responsabilités :
- valider EPUB,
- extraire metadata,
- extraire cover,
- extraire table des matières si utile,
- fournir infos pour lecteur.

Extraction minimum :
- title,
- authors,
- language,
- identifier/isbn,
- publisher,
- date,
- description,
- cover.

## ImportService

Responsabilités :
- pipeline upload/scan,
- créer import_job,
- valider fichier,
- hash,
- détecter doublon,
- extraire metadata,
- créer book,
- créer authors,
- créer cover,
- copier fichier,
- mettre à jour job.

Politique doublon :
- si hash identique, avertir et ne pas créer doublon exact par défaut.
- si titre/auteur similaire, créer mais signaler possible doublon.

## Metadata provider system

Interface :

```python
class MetadataProvider:
    name: str

    async def search_by_isbn(self, isbn: str) -> list[MetadataCandidate]:
        ...

    async def search_by_title_author(self, title: str, author: str | None) -> list[MetadataCandidate]:
        ...
```

Normalized candidate :
- provider
- provider_item_id
- title
- subtitle
- authors
- description
- language
- isbn
- publisher
- published_date
- cover_url
- score
- raw

Providers :
- Open Library
- Google Books

Important :
- timeout court.
- erreurs non bloquantes.
- logs propres.
- jamais d’application automatique sans endpoint apply.

## SyncService

Responsabilités :
- recevoir événements client,
- appliquer progression,
- appliquer bookmarks,
- gérer conflit updated_at,
- retourner état serveur.

Progress conflict :
- si client_updated_at > server_updated_at, client gagne.
- sinon serveur gagne.
- retourner décision.

## Auth

V1 mono-utilisateur mais auth obligatoire.

Au premier lancement :
- prévoir commande ou endpoint setup pour créer admin si aucun utilisateur.
- ne pas créer admin/password hardcodé en production.

Endpoints :
- login
- logout
- me
- change password

## Tests backend

Tests minimum :
- upload EPUB valide
- refus fichier non EPUB
- extraction metadata
- création book
- update progress
- conflict progress newest wins
- bookmarks CRUD
- collections CRUD
- tags CRUD
- metadata provider normalization avec mocks
