# Ebook Manager Sync Prototype

Ce dépôt contient une implémentation minimale de la synchronisation de lecture:

- `POST /sync/progress`
- `POST /sync/bookmarks`
- `GET /sync/books/:book_id`

Le serveur applique une logique **last-write-wins** basée sur `updated_at`.

## Lancement

```bash
node server.js
```

Le frontend de démonstration est servi sur `http://localhost:3000`.

## Sécurité (clé API)

Le serveur vérifie une clé API simple par utilisateur/appareil avec les en-têtes:

- `x-user-id`
- `x-device-id`
- `x-api-key`

Configuration via variable d'environnement:

```bash
SYNC_API_KEYS="alice:kindle-1:secret1,bob:iphone-2:secret2"
```

Sans cette variable, des clés de démonstration sont actives (voir `server.js`).
