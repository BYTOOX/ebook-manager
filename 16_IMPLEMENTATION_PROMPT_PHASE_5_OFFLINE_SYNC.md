# Prompt Codex - Phase 5 Offline & Sync

Tu vas implémenter l’offline-first et la synchronisation.

Objectif :
Un EPUB téléchargé doit être lisible hors ligne, avec progression locale synchronisée au retour réseau.

Fonctions :
- IndexedDB via Dexie.js
- stockage EPUB blob local
- stockage cover blob local
- stockage progression locale
- sync_queue
- détection online/offline
- retry sync
- conflict newest wins
- badge offline
- settings offline cache

Stores IndexedDB :
- offline_books
- reading_progress
- bookmarks
- sync_queue
- settings_cache

Reader :
- charger EPUB local si disponible
- fallback API si online
- erreur claire si offline et non téléchargé

Progression :
- sauvegarde locale immédiate
- event progress.updated coalescé
- sync au retour online
- PUT serveur
- résolution conflit

Contraintes :
- Ne pas utiliser localStorage pour EPUB/progression.
- Ne pas bloquer la lecture si sync échoue.
- Ne pas perdre progression.
- Ne pas créer 200 events inutiles.

Avant de coder :
- Explique le modèle IndexedDB.
- Explique le flux offline.
- Explique la stratégie de conflit.
- Attends validation.
