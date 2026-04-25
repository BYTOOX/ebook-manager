# Format interne de synchronisation

Ce document décrit le payload attendu par `POST /api/import/progress`.

## Schéma JSON

```json
{
  "formatVersion": 1,
  "books": [
    {
      "bookId": "sha256:ab12...",
      "progress": 63.5,
      "bookmarks": [
        {
          "cfi": "epubcfi(/6/14[xchapter]!/4/2/8)",
          "label": "Chapitre 4",
          "createdAt": "2026-04-24T19:22:00Z"
        }
      ],
      "updatedAt": "2026-04-25T12:00:00Z"
    }
  ]
}
```

## Règles de validation

- `formatVersion` doit être `1`.
- `books` doit être une liste.
- Chaque entrée doit contenir:
  - `bookId` (string non vide)
  - `progress` (nombre)
  - `bookmarks` (liste)
  - `updatedAt` (date ISO-8601 string)

## Comportement d'import

- Les entrées sont fusionnées par `bookId`.
- Si un `bookId` existe déjà, il est remplacé par la version importée.
- Le fichier fusionné est sauvegardé dans `data/progress.json`.
