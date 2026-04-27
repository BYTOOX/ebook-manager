# API CONTRACT — Aurelia Server pour Android Reader

## Base URL

L'utilisateur configure l'URL serveur, par exemple :

```txt
https://aurelia.example.com
```

L'API est disponible sous :

```txt
/api/v1
```

## Auth

Toutes les routes protégées utilisent :

```http
Authorization: Bearer <access_token>
```

## Endpoints nécessaires V1

### Health

```http
GET /api/v1/health
```

Utilisé pour tester l'URL serveur.

Réponse attendue :

```json
{
  "status": "ok",
  "app": "Aurelia"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json
```

Body :

```json
{
  "username": "admin",
  "password": "password"
}
```

Réponse :

```json
{
  "ok": true,
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 2592000,
  "user": {
    "id": "...",
    "username": "admin",
    "display_name": "Aurelia"
  }
}
```

### Current user

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Liste livres

```http
GET /api/v1/books?limit=50&offset=0&sort=last_opened_at&order=desc
Authorization: Bearer <token>
```

L'app Android doit supporter :

- pagination
- recherche via `q`
- tri simple

### Détail livre

```http
GET /api/v1/books/{book_id}
Authorization: Bearer <token>
```

Utilisé pour fiche livre et metadata offline.

### Fichier EPUB

```http
GET /api/v1/books/{book_id}/file
Authorization: Bearer <token>
```

L'app télécharge le fichier dans le stockage local privé Android.

### Couverture

```http
GET /api/v1/books/{book_id}/cover
Authorization: Bearer <token>
```

L'app peut aussi utiliser `cover_url` fourni par les réponses livres.

### Progression

Récupération :

```http
GET /api/v1/books/{book_id}/progress
Authorization: Bearer <token>
```

Mise à jour simple :

```http
PUT /api/v1/books/{book_id}/progress
Authorization: Bearer <token>
Content-Type: application/json
```

Body recommandé :

```json
{
  "cfi": "...",
  "progress_percent": 42.5,
  "chapter_label": "Chapitre 4",
  "chapter_href": "...",
  "location_json": {},
  "client_updated_at": "2026-04-27T10:00:00Z",
  "device_id": "android-reader"
}
```

### Sync events

```http
POST /api/v1/sync/events
Authorization: Bearer <token>
Content-Type: application/json
```

Body :

```json
{
  "device_id": "android-reader",
  "events": [
    {
      "event_id": "uuid",
      "type": "progress.updated",
      "payload": {
        "book_id": "uuid",
        "cfi": "...",
        "progress_percent": 42.5,
        "chapter_label": "Chapitre 4",
        "chapter_href": "...",
        "location_json": {},
        "client_updated_at": "2026-04-27T10:00:00Z",
        "device_id": "android-reader"
      },
      "client_created_at": "2026-04-27T10:00:00Z"
    }
  ]
}
```

## V1 recommandation

Pour simplifier V1 Android :

- utiliser `PUT /books/{id}/progress` quand online
- garder une queue locale si offline
- flush via `POST /sync/events` au retour réseau

## Erreurs attendues

### 401

Token absent ou invalide.

Action app :

- retour login
- suppression token local si token invalide confirmé

### 404

Livre/fichier/couverture absent.

Action app :

- afficher erreur claire
- supprimer état offline si fichier local absent

### 5xx

Serveur indisponible.

Action app :

- continuer lecture offline si EPUB déjà local
- mettre sync en attente
