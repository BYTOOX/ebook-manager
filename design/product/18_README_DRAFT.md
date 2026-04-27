# Aurelia

Aurelia est une bibliothèque EPUB personnelle auto-hébergée, mobile-first, avec lecture intégrée, offline-first et synchronisation de progression.

## Objectifs

- Importer des EPUB.
- Organiser une bibliothèque personnelle.
- Lire directement dans l’application.
- Lire hors ligne sur Android via PWA.
- Synchroniser la progression au retour réseau.
- Offrir une interface premium dark/cyber/luxury avec accents jaune-or.

## Stack

Backend :
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic

Frontend :
- React/Next.js
- TypeScript
- PWA
- IndexedDB

Déploiement :
- Podman Compose
- Volumes persistants

## Fonctionnalités V1

- EPUB uniquement.
- Upload web.
- Scan dossier.
- Extraction métadonnées.
- Extraction couverture.
- Bibliothèque visuelle.
- Lecture EPUB intégrée.
- Progression sauvegardée.
- Offline-first.
- Sync automatique.
- Tags.
- Collections.
- Séries.
- Étoiles.
- Metadata providers Open Library / Google Books.

## Hors scope V1

- PDF.
- MOBI/AZW3.
- DRM.
- Audiobooks.
- Multi-user.
- App mobile native.
- IA.
- Recommandations.

## Développement

À compléter par Codex lors de l’implémentation.

Commandes attendues :
- démarrage backend
- démarrage frontend
- migrations
- tests
- podman compose up

## Données persistantes

À sauvegarder :
- PostgreSQL
- `/data/library`
- configuration `.env`

## Licence

Projet personnel.
