# Aurelia

![Version](https://img.shields.io/badge/version-1.0.0-f5c542?style=for-the-badge&labelColor=050505)
![EPUB](https://img.shields.io/badge/EPUB-only-f5c542?style=for-the-badge&labelColor=050505)
![PWA](https://img.shields.io/badge/PWA-offline--first-f5c542?style=for-the-badge&labelColor=050505)
![Stack](https://img.shields.io/badge/FastAPI%20%2B%20React%20%2B%20PostgreSQL-111111?style=for-the-badge&labelColor=050505)

**Aurelia est une bibliotheque EPUB personnelle auto-hebergee, mobile-first, offline-first, avec lecteur integre et synchronisation de progression.**

V1.0 cible un usage personnel solide : importer, organiser, enrichir, lire, telecharger offline, reprendre la lecture, et synchroniser au retour reseau. L'application privilégie une experience PWA Android premium, noire et jaune-or, sans interface admin lourde.

---

## Statut

**Release actuelle : 1.0.0**

La V1 a passe la RC locale :

- Backend tests : `19 passed`
- Frontend build PWA : OK
- Docker Compose stack : OK
- Reader online/offline : OK
- Progression locale IndexedDB : OK
- Sync queue retour reseau : OK
- Manifest PWA + service worker : OK
- OpenAPI : OK

## Sommaire

- [Fonctionnalites](#fonctionnalites)
- [Architecture](#architecture)
- [Stack](#stack)
- [Demarrage rapide](#demarrage-rapide)
- [Identifiants de test](#identifiants-de-test)
- [Import EPUB](#import-epub)
- [Lecture et offline](#lecture-et-offline)
- [Metadata providers](#metadata-providers)
- [Organisation](#organisation)
- [Maintenance avancee](#maintenance-avancee)
- [Commandes de developpement](#commandes-de-developpement)
- [API](#api)
- [Donnees persistantes](#donnees-persistantes)
- [Tests RC](#tests-rc)
- [Limites V1](#limites-v1)
- [Roadmap](#roadmap)

## Fonctionnalites

### Bibliotheque

- Import EPUB par upload web.
- Scan recursif du dossier `library-import/`.
- Detection de doublons exacts par hash fichier.
- Extraction automatique des metadonnees EPUB.
- Extraction et stockage local des couvertures.
- Recherche par titre, auteur, ISBN, editeur et nom de fichier original.
- Home centree sur la reprise de lecture.
- Grilles, rails horizontaux et fiches livre mobile-first.

### Reader EPUB

- Route reader dediee : `/reader/:bookId`.
- Rendu EPUB avec `epub.js`.
- Mode pagine.
- Mode scroll.
- Table des matieres.
- Progression visible.
- Sauvegarde CFI.
- Reprise automatique.
- Bookmarks locaux et synchronisables.
- Reglages lecture : mode, police, taille, interligne, marges.

### Offline-first

- Telechargement EPUB en Blob IndexedDB.
- Telechargement couverture en Blob IndexedDB.
- Snapshot metadata local.
- Ouverture reader prioritaire depuis IndexedDB.
- Erreur claire si le livre n'est pas disponible offline.
- Progression locale immediate.
- Queue de sync locale.
- Retry automatique au retour reseau.

### Synchronisation

- Events `progress.updated`, `bookmark.created`, `bookmark.deleted`.
- Coalescing des progressions par livre pour eviter les queues inutiles.
- Politique de conflit V1 : l'update le plus recent gagne.
- Etat sync visible : synced, syncing, pending, offline, error.

### Enrichissement metadata

- Providers V1 :
  - Open Library
  - Google Books
- Recherche par titre, auteur ou ISBN.
- Comparaison des propositions.
- Application champ par champ.
- Remplacement de couverture provider avec stockage local backend.
- Pas d'ecrasement automatique sans validation utilisateur.

### Organisation

- Collections manuelles.
- Series detectees depuis les dossiers d'import puis materialisables.
- Tags avec couleur.
- Statuts : unread, in_progress, finished, abandoned.
- Favoris.
- Note personnelle de 0 a 5.

## Architecture

```mermaid
flowchart LR
  Android["Android / Browser PWA"] --> Frontend["React + Vite + TypeScript"]
  Frontend --> Dexie["IndexedDB / Dexie"]
  Frontend --> API["FastAPI /api/v1"]
  API --> Postgres["PostgreSQL"]
  API --> Library["/data/library"]
  API --> Providers["Open Library / Google Books"]

  Dexie --> OfflineBooks["offline_books"]
  Dexie --> Progress["reading_progress"]
  Dexie --> Queue["sync_queue"]
  Dexie --> Settings["settings_cache"]
```

### Structure du repo

```txt
ebookmanager/
  backend/
    app/
      api/routes/
      models/
      schemas/
      services/
    alembic/
    tests/
  frontend/
    src/
      components/
      lib/
      pages/
      providers/
      stores/
      styles/
  library-import/
  compose.yaml
  README.md
```

## Stack

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16
- Pydantic v2
- HTTP-only session cookie
- Pillow
- EbookLib

### Frontend

- React 18
- Vite
- TypeScript
- TanStack Query
- Zustand
- Dexie / IndexedDB
- epub.js
- vite-plugin-pwa
- lucide-react

### Runtime

- Docker Compose ou Podman Compose
- Backend : port `8000`
- Frontend : port `3000`
- PostgreSQL via volume Docker
- Bibliotheque EPUB via volume Docker

## Demarrage rapide

### 1. Configuration

```bash
cp .env.example .env
```

Sur Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

### 2. Lancement complet

```bash
docker compose up --build
```

Ou avec Podman :

```bash
podman compose up --build
```

### 3. URLs

- Frontend : [http://localhost:3000](http://localhost:3000)
- Backend API : [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- OpenAPI : [http://localhost:8000/docs](http://localhost:8000/docs)
- Health : [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

## Identifiants de test

Pour la base de developpement actuelle :

```txt
username: admin
password: PasswordAdmin123
```

Pour une base neuve, utiliser l'ecran de setup dans la PWA ou appeler :

```bash
curl -X POST http://localhost:8000/api/v1/auth/setup ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"very-secure-password\",\"display_name\":\"Aurelia\"}"
```

Si `FIRST_USER_SETUP_TOKEN` est defini, ajouter `setup_token` dans le JSON.

## Import EPUB

### Upload web

Aller sur :

```txt
/import
```

Puis selectionner un fichier `.epub`.

### Scan dossier

Avec Compose, placer les EPUB dans :

```txt
library-import/
```

Exemple :

```txt
library-import/
  CHERUB/
    01 - 100 jours en enfer.epub
    02 - Trafic.epub
  Robin Hood/
    Tome 3.epub
```

Le backend monte ce dossier en lecture seule dans :

```txt
/data/library/incoming
```

Le scan importe les fichiers `.epub` recursivement.

## Lecture et offline

### Priorite de chargement du reader

1. EPUB local IndexedDB si disponible.
2. API backend si le reseau est disponible.
3. Message d'erreur clair si offline et EPUB absent.

### Stores IndexedDB

```txt
aurelia_local
  offline_books
  reading_progress
  bookmarks
  sync_queue
  settings_cache
```

### Flux offline

```mermaid
sequenceDiagram
  participant User as Utilisateur
  participant PWA as PWA React
  participant IDB as IndexedDB
  participant API as FastAPI

  User->>PWA: Telecharger offline
  PWA->>API: GET /books/{id}/file
  API-->>PWA: EPUB blob
  PWA->>API: GET /books/{id}/cover
  API-->>PWA: Cover blob
  PWA->>IDB: Sauvegarde EPUB + cover + metadata
  User->>PWA: Ouvrir reader hors reseau
  PWA->>IDB: Charge EPUB local
  PWA->>IDB: Sauvegarde progression
  PWA->>IDB: Queue progress.updated
  PWA->>API: Sync au retour reseau
```

## Metadata providers

Aurelia peut enrichir un livre via :

- Open Library
- Google Books

Champs applicables :

- titre
- sous-titre
- auteurs
- description
- langue
- ISBN
- editeur
- date de publication
- couverture

La couverture provider est telechargee cote backend, validee, puis stockee localement. Aurelia ne depend pas d'un hotlink externe pour afficher une couverture appliquee.

## Organisation

La page Collections regroupe :

- Collections
- Series
- Tags

Les livres peuvent etre selectionnes dans une collection. Les series peuvent etre detectees depuis les dossiers d'import et affichees dans les fiches livre.

## Maintenance avancee

Route :

```txt
/settings/advanced
```

Fonctions disponibles :

- Sante API.
- Etat reseau.
- Etat sync.
- Sync manuelle.
- Derniers imports.
- Scan incoming.
- Etat IndexedDB.
- Taille offline approximative.
- Liste des livres offline.
- Retrait d'un livre offline.
- Purge des EPUB offline sans supprimer progressions, bookmarks ou queue sync.

## Commandes de developpement

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests et build

Backend :

```bash
cd backend
.venv\Scripts\python.exe -m pytest
```

Frontend :

```bash
cd frontend
npm.cmd run build
```

Stack :

```bash
docker compose ps
docker compose logs --tail=120 backend frontend
```

## API

Base URL :

```txt
http://localhost:8000/api/v1
```

Endpoints principaux :

```txt
GET    /health
POST   /auth/setup
POST   /auth/login
GET    /auth/me
POST   /auth/logout

GET    /books
GET    /books/{book_id}
PATCH  /books/{book_id}
POST   /books/upload
GET    /books/{book_id}/file
GET    /books/{book_id}/cover
GET    /books/{book_id}/progress
PUT    /books/{book_id}/progress
GET    /books/{book_id}/bookmarks

POST   /books/{book_id}/metadata/search
POST   /books/{book_id}/metadata/apply

GET    /organization/collections
POST   /organization/collections
PATCH  /organization/collections/{collection_id}
DELETE /organization/collections/{collection_id}
PUT    /organization/collections/{collection_id}/books

GET    /organization/series
GET    /organization/tags
POST   /organization/tags
PATCH  /organization/tags/{tag_id}
DELETE /organization/tags/{tag_id}

POST   /library/scan
GET    /import-jobs

GET    /settings/reading
PUT    /settings/reading

POST   /sync/events
```

Documentation interactive :

```txt
http://localhost:8000/docs
```

## Donnees persistantes

Sauvegarder :

- Volume PostgreSQL : `postgres_data`
- Volume bibliotheque : `library_data`
- Fichier `.env`
- Dossier `library-import/` si vous y conservez les EPUB source

Dans le conteneur backend :

```txt
/data/library
  books/
  incoming/
```

## Variables d'environnement

Variables principales :

```txt
APP_NAME=Aurelia
APP_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
DATABASE_URL=postgresql+psycopg://aurelia:aurelia@postgres:5432/aurelia
SECRET_KEY=change-me-generate-a-long-random-secret
LIBRARY_PATH=/data/library
INCOMING_PATH=/data/library/incoming
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
SESSION_COOKIE_SECURE=false
MAX_UPLOAD_SIZE_MB=200
METADATA_OPENLIBRARY_ENABLED=true
METADATA_GOOGLEBOOKS_ENABLED=true
```

En production, remplacer `SECRET_KEY`, adapter `APP_URL`, `API_URL`, `CORS_ORIGINS`, et activer `SESSION_COOKIE_SECURE=true` derriere HTTPS.

## Tests RC

Derniere passe RC realisee :

```txt
Backend pytest          PASS
Frontend build          PASS
Docker stack            PASS
Health API              PASS
OpenAPI                 PASS
PWA manifest            PASS
Service worker          PASS
Auth                    PASS
Library/Search          PASS
Book detail cover       PASS
Reader online           PASS
Reader offline          PASS
IndexedDB offline EPUB  PASS
Progress local          PASS
Sync queue return       PASS
```

Scenario critique valide :

```txt
telecharger offline -> couper reseau -> lire -> sauvegarder progression locale
-> retablir reseau -> sync -> queue vide -> progression serveur mise a jour
```

## Limites V1

Aurelia 1.0 ne gere pas :

- PDF
- MOBI / AZW3
- CBZ
- audiobooks
- DRM
- multi-utilisateur
- OPDS / WebDAV
- application mobile native
- recommandations IA
- annotations avancees et surlignages

## Roadmap

### V1.x

- Edition manuelle complete des champs metadata avances.
- Suppression serveur d'un livre depuis l'app.
- Export/import de sauvegarde plus guide.
- QA Android PWA sur plusieurs appareils.
- Amelioration des etats d'erreur EPUB corrompu/cache plein.

### V2

- OPDS.
- WebDAV optionnel.
- Recherche plein texte dans les EPUB.
- Surlignages et notes.
- Export Markdown des notes.
- Statistiques de lecture.
- Integrations liseuses Android.

## Philosophie produit

Aurelia n'est pas un dashboard admin. C'est une bibliotheque personnelle qui doit rester rapide, lisible, belle, et fiable hors ligne.

Le coeur V1 :

```txt
Importer. Lire. Reprendre. Offline. Synchroniser.
```

## Licence

Projet personnel.
