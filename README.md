# Aurelia

![Release](https://img.shields.io/badge/release-v1.0.0-f5c542?style=for-the-badge&labelColor=050505)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20Android-f5c542?style=for-the-badge&labelColor=050505)
![EPUB](https://img.shields.io/badge/EPUB-reader-f5c542?style=for-the-badge&labelColor=050505)

**Aurelia est une bibliotheque EPUB personnelle auto-hebergee, avec PWA web, lecteur Android natif, lecture offline et synchronisation de progression.**

## Ce qui est inclus

- Web app React mobile-first pour importer, organiser et lire les EPUB.
- Backend FastAPI avec auth Bearer JWT, metadonnees, couvertures et sync.
- Android Reader natif Kotlin/Compose + Readium.
- Lecture Android au choix : streaming/cache temporaire ou telechargement hors ligne.
- Progression locale puis sync serveur.
- APK publie via GitHub Releases.

## Liens utiles

- Web local : [http://localhost:3000](http://localhost:3000)
- API locale : [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- OpenAPI : [http://localhost:8000/docs](http://localhost:8000/docs)
- APK Android : [GitHub Releases](https://github.com/BYTOOX/ebook-manager/releases)
- Specs Android : [aurelia-android-reader-docs/](aurelia-android-reader-docs/)
- Specs produit : [design/](design/)

## Stack

| Surface | Tech |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, JWT |
| Frontend | React, Vite, TypeScript, TanStack Query, Dexie, epub.js |
| Android | Kotlin, Compose, Room, WorkManager, Readium |
| Infra | Docker Compose, GitHub Actions |

## Demarrage rapide

```bash
cp .env.example .env
docker compose up --build
```

Sur Windows PowerShell :

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Identifiants de test de la base dev :

```txt
username: admin
password: PasswordAdmin123
```

Pour une base neuve, utiliser l'ecran de setup web ou `POST /api/v1/auth/setup`.

## Android

Build local :

```powershell
cd android-reader
.\gradlew.bat assembleDebug
```

APK local :

```txt
android-reader/app/build/outputs/apk/debug/app-debug.apk
```

Installation ADB :

```powershell
adb install -r android-reader/app/build/outputs/apk/debug/app-debug.apk
```

Publication GitHub :

- Le workflow `.github/workflows/android-reader-release.yml` build l'APK.
- Un tag `android-reader-v*` cree ou met a jour une Release.
- L'asset publie s'appelle `AureliaReader-debug.apk`.

## Commandes dev

Backend :

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend :

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
```

Android :

```powershell
cd android-reader
.\gradlew.bat assembleDebug
```

## API

Base URL :

```txt
http://localhost:8000/api/v1
```

Auth :

```http
Authorization: Bearer <access_token>
```

Endpoints principaux :

- `POST /auth/setup`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /books`
- `GET /books/{id}`
- `GET /books/{id}/download`
- `POST /sync/events`

## Repo

```txt
backend/                     FastAPI, DB, services, tests
frontend/                    PWA React
android-reader/              App Android native
aurelia-android-reader-docs/ Specs Android
design/                      Specs produit
compose.yaml                 Stack locale
```

## Statut V1

- Backend auth tests : OK
- Frontend typecheck : OK
- Android debug build : OK
- Test telephone via ADB : OK
- APK Release workflow : actif
