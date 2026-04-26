# Backlog Aurelia

## Phase 0 - Cadrage
- Valider architecture
- Valider stack
- Valider modèle DB
- Valider endpoints
- Valider UX principale
- Créer structure repo

## Phase 1 - Socle backend/frontend
- Setup FastAPI
- Setup PostgreSQL
- Setup SQLAlchemy/Alembic
- Setup config env
- Setup auth mono-utilisateur
- Setup models DB initiaux
- Setup migrations
- Setup tests backend
- Setup frontend TypeScript
- Setup thème dark/gold minimal
- Setup Podman Compose

Critères :
- API démarre.
- DB connectée.
- Migration initiale OK.
- User admin créable.
- Auth fonctionne.
- Frontend démarre.

## Phase 2 - Import EPUB
- Upload EPUB
- Validation format
- Hash fichier
- Détection doublon exact
- Extraction metadata EPUB
- Extraction cover
- Stockage fichier par book_id
- Création book en DB
- Import jobs
- Scan dossier incoming

## Phase 3 - Bibliothèque frontend premium
- AppShell
- Bottom navigation
- Home page
- Library page
- Book cards
- Book detail
- Upload page simple
- Design premium dark/gold

## Phase 4 - Reader EPUB online
- Intégrer renderer EPUB
- Ouvrir EPUB depuis API
- Afficher contenu
- Mode paginé
- Mode scroll
- Table des matières
- Progression calculée
- Sauvegarde progression serveur
- Reprise CFI

## Phase 5 - Offline PWA
- Manifest PWA
- Service worker
- IndexedDB
- Télécharger EPUB offline
- Charger EPUB offline
- Sauvegarder progression locale
- État offline visible

## Phase 6 - Sync
- Sync queue IndexedDB
- Sync progress.updated
- Retry au retour réseau
- Conflict newest wins
- Sync bookmarks
- UI synced/syncing/offline

## Phase 7 - Organisation
- Tags
- Collections
- Séries
- Statuts
- Rating étoiles
- Filtres
- Tri

## Phase 8 - Metadata providers
- Open Library provider
- Google Books provider
- Search metadata endpoint
- Normalize results
- Apply selected fields
- Cover download

## Phase 9 - Polish
- Empty states
- Loading skeletons
- Error states
- Responsive QA
- Dark/gold theme polish
- Settings lecture
- Cache management
- Logs import
- Documentation déploiement

## Phase 10 - Déploiement
- Podman Compose
- Docker Compose compatible
- Volumes
- README
- Backup docs
- Reverse proxy notes
