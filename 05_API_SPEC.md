# API Specification - Aurelia

Base path : `/api/v1`

## Auth

### POST /auth/login
Body :
```json
{ "username": "admin", "password": "password" }
```

### POST /auth/logout
Response :
```json
{ "ok": true }
```

### GET /auth/me
Response :
```json
{ "id": "uuid", "username": "admin", "display_name": "Arnaud" }
```

## Books

### GET /books
Query params :
- q
- status
- tag
- collection_id
- series_id
- downloaded
- favorite
- sort
- order
- limit
- offset

Response :
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "The Whispering Light",
      "authors": ["Elian Vale"],
      "cover_url": "/api/v1/books/uuid/cover",
      "status": "in_progress",
      "rating": 4,
      "favorite": false,
      "progress_percent": 42,
      "is_offline_available": false,
      "added_at": "2026-04-26T10:00:00Z",
      "last_opened_at": "2026-04-26T12:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /books/upload
Multipart :
- file EPUB

Response :
```json
{ "job_id": "uuid", "book_id": "uuid", "status": "success" }
```

### GET /books/{book_id}
Retourne la fiche complète livre, auteurs, description, série, tags, collections, statut, note et progression.

### PATCH /books/{book_id}
Modifie métadonnées, statut, note, favori.

### DELETE /books/{book_id}
Soft delete préféré.

### GET /books/{book_id}/file
Returns EPUB file.

### GET /books/{book_id}/cover
Returns cover image.

## Progress

### GET /books/{book_id}/progress

### PUT /books/{book_id}/progress
Body :
```json
{
  "cfi": "epubcfi(...)",
  "progress_percent": 42,
  "chapter_label": "Chapter 4",
  "chapter_href": "chapter4.xhtml",
  "location_json": {},
  "device_id": "android-pwa",
  "client_updated_at": "2026-04-26T12:00:00Z"
}
```

Response :
```json
{
  "ok": true,
  "resolved": "client_won",
  "progress": {
    "cfi": "epubcfi(...)",
    "progress_percent": 42,
    "updated_at": "2026-04-26T12:00:01Z"
  }
}
```

Conflict policy V1 :
- newest updated_at wins.

## Bookmarks

### GET /books/{book_id}/bookmarks
### POST /books/{book_id}/bookmarks
### DELETE /bookmarks/{bookmark_id}

## Tags

### GET /tags
### POST /tags
### POST /books/{book_id}/tags

## Collections

### GET /collections
### POST /collections
### GET /collections/{collection_id}
### POST /collections/{collection_id}/books
### DELETE /collections/{collection_id}/books/{book_id}

## Series

### GET /series
### POST /series
### PATCH /books/{book_id}/series

## Metadata Providers

### POST /books/{book_id}/metadata/search
Body :
```json
{ "providers": ["openlibrary", "googlebooks"], "query": null, "isbn": null }
```

### POST /books/{book_id}/metadata/apply
Application uniquement après validation utilisateur.

## Import / Scan

### POST /library/scan
Body :
```json
{ "path": "/data/library/incoming" }
```

### GET /import-jobs
### GET /import-jobs/{job_id}

## Settings

### GET /settings/reading
### PUT /settings/reading

## Sync

### POST /sync/events
Body :
```json
{
  "device_id": "android-pwa",
  "events": [
    {
      "event_id": "uuid",
      "type": "progress.updated",
      "client_created_at": "...",
      "payload": {}
    }
  ]
}
```
