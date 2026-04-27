# Architecture Technique - Aurelia

## Vue d’ensemble

Aurelia est une application web/PWA auto-hébergée composée de :
- Frontend Next.js/React TypeScript
- Backend FastAPI
- PostgreSQL
- Stockage fichiers local
- Service Worker PWA
- IndexedDB côté client pour offline
- Workers backend pour import, extraction metadata et scan

## Frontend

Responsabilités :
- UI mobile-first
- bibliothèque
- lecteur EPUB
- offline cache
- sync queue
- PWA installable
- gestion thème
- appels API

Technos :
- React/Next.js
- TypeScript
- TanStack Query ou équivalent
- Zustand ou équivalent pour état local UI
- IndexedDB via Dexie.js ou wrapper similaire
- epub.js ou alternative pour rendu EPUB
- Service Worker via Workbox ou configuration custom

## Backend

Responsabilités :
- API REST
- auth locale
- gestion livres
- stockage métadonnées
- upload EPUB
- scan dossier
- extraction EPUB
- providers metadata
- sync progression
- bookmarks
- collections/tags/séries
- logs d’import

Technos :
- FastAPI
- SQLAlchemy 2.x ou SQLModel
- Alembic
- Pydantic v2
- PostgreSQL
- ebooklib ou lib équivalente pour EPUB
- Pillow pour covers si nécessaire
- httpx pour providers metadata

## Database

PostgreSQL.

Contient :
- utilisateur local
- livres
- auteurs
- tags
- collections
- séries
- progression
- bookmarks
- import jobs
- metadata provider results

## Storage

Structure recommandée :

```txt
/data/library/
  incoming/
  books/
    <book_id>/
      original.epub
      cover.jpg
      metadata.json
  tmp/
  exports/
```

Règle :
- Le fichier EPUB importé est copié dans la structure interne.
- Le chemin stable repose sur book_id.
- Ne pas dépendre du nom original.
- Garder le nom original en DB.

## Offline

Côté client :
- EPUB stocké dans IndexedDB.
- Progression locale stockée dans IndexedDB.
- Bookmarks locaux stockés dans IndexedDB.
- Queue de sync stockée dans IndexedDB.

Règles :
- Le livre téléchargé doit être lisible sans réseau.
- La progression doit être sauvegardée localement.
- La sync se déclenche au retour réseau, au lancement de l’app, périodiquement si online, et après changement significatif de progression.

## Sync

Le client maintient une sync queue.

Événements :
- progress.updated
- bookmark.created
- bookmark.deleted
- book.offline.downloaded
- book.offline.removed

Chaque événement contient :
- event_id UUID
- type
- payload
- created_at
- retry_count
- status

Règle de conflit progression :
- updated_at le plus récent gagne.

## Authentification

V1 :
- utilisateur unique local.
- login/password.
- session cookie httpOnly recommandé.
- JWT acceptable si proprement sécurisé.

Recommandation :
- session cookie httpOnly + CSRF si frontend/backend même domaine.
- JWT uniquement si architecture séparée stricte.

Fonctions :
- login,
- logout,
- me,
- change password.

Pas de multi-user en V1.

## Import EPUB

Flux upload :
1. Upload fichier EPUB.
2. Sauvegarde temporaire.
3. Validation format.
4. Calcul hash fichier.
5. Détection doublon par hash.
6. Extraction metadata.
7. Extraction cover.
8. Copie vers /data/library/books/<book_id>/original.epub.
9. Création entrée DB.
10. Génération résultat import.

Flux scan :
1. Scanner /data/library/incoming ou chemin configuré.
2. Détecter EPUB non importés.
3. Appliquer même pipeline que upload.
4. Marquer erreurs si échec.

## Metadata Providers

Providers V1 :
- Open Library
- Google Books

Architecture :
- interface provider commune.
- recherche par ISBN.
- fallback titre + auteur.
- normalisation des résultats.
- stockage temporaire des propositions.
- validation utilisateur avant application.

Ne jamais écraser automatiquement les métadonnées.

## EPUB Reader

Le frontend utilise un renderer EPUB.

Données nécessaires :
- book_id
- EPUB blob local ou URL streaming
- progression CFI
- settings de lecture
- bookmarks

Online :
- le reader peut charger EPUB depuis API sécurisée.

Offline :
- le reader charge EPUB depuis IndexedDB.

## Déploiement

Podman Compose :
- backend
- frontend
- postgres
- optional reverse proxy non obligatoire

Volumes :
- postgres_data
- library_data

Variables :
- DATABASE_URL
- SECRET_KEY
- LIBRARY_PATH
- CORS_ORIGINS
- APP_URL
- METADATA_PROVIDERS_ENABLED

## Observabilité

Logs :
- backend stdout
- import jobs en DB
- erreurs metadata provider
- erreurs scan

Page admin V1 :
- voir derniers imports
- voir erreurs
- relancer scan

## Sauvegarde

À sauvegarder :
- PostgreSQL
- `/data/library/books`
- config
- éventuellement export metadata JSON
