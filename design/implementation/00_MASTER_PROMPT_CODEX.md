# Mission Codex - Développement application Ebook Library

Tu es un agent de développement senior chargé de concevoir puis développer une application web/PWA auto-hébergée de bibliothèque EPUB personnelle.

## Objectif produit

Créer une application personnelle de bibliothèque EPUB, mobile-first, premium, installable en PWA sur Android, avec lecture intégrée, lecture hors ligne, synchronisation automatique de progression, import hybride et gestion propre des métadonnées.

L’application doit offrir :
- la simplicité d’une app Apple,
- la richesse visuelle d’une médiathèque type Netflix,
- la puissance et la maîtrise d’un système Linux,
- une expérience sombre élégante, dark cyber luxury, avec accents noir/jaune-or,
- une base technique propre, maintenable, auto-hébergée.

## Utilisateur cible

Utilisateur unique, usage personnel.

Appareil principal :
- Téléphone Android

Application actuelle de référence :
- Lithium Pro

Usage :
- Lecture de 1 ou 2 livres maximum en parallèle
- Lecture hors ligne obligatoire
- Synchronisation automatique dès que la connexion revient
- Projet futur d’achat d’une liseuse, donc prévoir à terme OPDS/WebDAV/export EPUB, mais pas en V1

## Formats supportés

V1 :
- EPUB uniquement

Hors scope V1 :
- PDF
- MOBI
- AZW3
- CBZ/CBR
- Audiobooks
- DRM
- conversion de formats

## Stack souhaitée

Backend :
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x ou SQLModel
- Alembic pour migrations
- JWT ou session sécurisée
- API REST documentée OpenAPI

Frontend :
- Next.js ou React moderne
- TypeScript obligatoire
- PWA installable
- Mobile-first
- IndexedDB pour offline
- Service Worker

Déploiement :
- Podman Compose en priorité
- Docker Compose compatible si simple
- Volumes persistants
- Reverse proxy compatible

Stockage :
- EPUB stockés dans `/data/library/books/<book_id>/original.epub`
- Covers dans `/data/library/books/<book_id>/cover.jpg`
- Métadonnées principales en PostgreSQL
- Optionnel : metadata snapshot JSON local par livre

## Méthode de travail obligatoire

Tu ne dois pas coder immédiatement.

Première étape :
1. Inspecter le repo existant si présent.
2. Résumer l’état initial.
3. Proposer l’architecture finale.
4. Proposer la structure des dossiers.
5. Proposer le modèle de données.
6. Proposer les endpoints API.
7. Proposer les écrans frontend.
8. Lister les risques techniques.
9. Attendre validation avant implémentation.

Pendant le développement :
- Avancer étape par étape.
- Ne jamais modifier massivement sans expliquer.
- Ne pas ajouter de fonctionnalités hors scope.
- Ne pas créer de microservices inutiles.
- Ne pas remplacer la stack sans justification.
- Signaler les choix ambigus.
- Proposer plusieurs options quand une décision impacte l’architecture.
- Garder une documentation à jour.
- Fournir des commandes de test.
- Vérifier que le projet démarre localement.

## Interdictions

Ne pas faire :
- Application mobile native V1
- Microservices
- SQLite comme DB principale
- Auth complexe type Keycloak
- SSO en V1
- Recommandations IA
- OCR
- Scraping illégal
- Gestion DRM
- Conversion EPUB vers autres formats
- Support PDF
- Audiobooks
- Interface admin omniprésente
- Dashboard générique façon SaaS B2B
- Design Bootstrap standard
- Stockage de progression uniquement côté navigateur
- Dépendance obligatoire à un service cloud externe

## Priorités absolues

1. Expérience mobile Android premium
2. Lecture EPUB intégrée confortable
3. Offline-first
4. Sync fiable de progression
5. Import EPUB propre
6. Métadonnées propres et modifiables
7. Design sombre noir/jaune-or élégant
8. Code maintenable
