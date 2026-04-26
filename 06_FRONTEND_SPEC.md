# Frontend Specification - Aurelia

## Stack

- React ou Next.js
- TypeScript
- PWA
- IndexedDB via Dexie.js
- TanStack Query recommandé
- Zustand recommandé pour UI state
- epub.js ou alternative pour EPUB rendering
- CSS Modules, Tailwind ou design system maison

L’interface doit être mobile-first.

## Routes

- `/` : Home
- `/library` : Bibliothèque
- `/search` : Recherche
- `/collections` : Collections et séries
- `/books/:id` : Fiche livre
- `/reader/:id` : Lecteur EPUB
- `/settings` : Paramètres
- `/settings/advanced` : Gestion avancée
- `/import` : Upload et scan

## AppShell

Contient :
- ThemeProvider
- AuthProvider
- SyncProvider
- OfflineProvider
- BottomNavigation
- Toast system
- Modal/BottomSheet system

BottomNavigation visible sur :
- Home
- Library
- Search
- Collections
- Settings

BottomNavigation cachée sur :
- Reader
- Login
- certains modals plein écran

## PWA

Exigences :
- manifest.json
- service worker
- installable Android
- icônes
- theme_color noir
- background_color noir
- standalone display mode

## IndexedDB

DB locale : `aurelia_local`

Stores :
- offline_books
- reading_progress
- bookmarks
- sync_queue
- settings_cache

### offline_books
- book_id
- title
- authors
- cover_blob
- epub_blob
- downloaded_at
- file_size
- version_hash

### reading_progress
- book_id
- cfi
- progress_percent
- chapter_label
- chapter_href
- location_json
- updated_at
- dirty

### bookmarks
- id
- book_id
- cfi
- progress_percent
- chapter_label
- excerpt
- note
- created_at
- updated_at
- dirty
- deleted

### sync_queue
- event_id
- type
- payload
- created_at
- retry_count
- status

## Offline behavior

Quand l’utilisateur télécharge un livre :
1. Récupérer EPUB via API.
2. Stocker Blob dans IndexedDB.
3. Stocker cover.
4. Marquer comme offline.
5. Afficher badge offline.

Quand l’utilisateur ouvre un livre :
1. Si EPUB offline existe, charger IndexedDB.
2. Sinon charger API.
3. Si aucun réseau et pas offline, afficher erreur claire.

Sauvegarde progression :
- En local immédiatement.
- Ajouter event dans sync_queue.
- Si online, tenter sync.
- Si offline, attendre retour réseau.

## SyncProvider

Responsabilités :
- écouter online/offline.
- pousser sync_queue quand online.
- gérer retry.
- éviter doublons.
- exposer état sync : synced, syncing, offline, error.

## Theme

CSS variables obligatoires :

```css
:root {
  --color-bg: #050505;
  --color-bg-soft: #0B0B0D;
  --color-surface: #121216;
  --color-surface-elevated: #18181D;
  --color-text: #F5F1E8;
  --color-text-muted: #B8B0A0;
  --color-accent: #F5C542;
  --color-accent-soft: #D8A936;
  --color-reader-text: #FFD966;
}
```

## Qualité attendue

- Pas de page blanche brute.
- Pas de layout desktop forcé.
- Pas de boutons minuscules.
- Pas de composants admin visibles sur Home.
- Pas d’UX de CRUD brut.
- Animations sobres.
- Loading states soignés.
- Empty states propres.
- Error states compréhensibles.
