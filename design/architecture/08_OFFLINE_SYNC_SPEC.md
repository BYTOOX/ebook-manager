# Offline & Sync Specification - Aurelia

## Objectif

L’utilisateur doit pouvoir lire sur Android sans connexion, puis retrouver sa progression synchronisée quand la connexion revient.

La lecture hors ligne est une exigence V1.

## Principes

- Le serveur est la source de vérité finale.
- Le client conserve une copie locale exploitable hors ligne.
- Les actions faites offline sont mises dans une queue.
- La queue est synchronisée automatiquement au retour réseau.
- La progression la plus récente gagne.

## Données locales

IndexedDB stores :
- offline_books
- reading_progress
- bookmarks
- sync_queue
- settings_cache

## Téléchargement offline

Quand l’utilisateur appuie sur “Télécharger offline” :
1. GET `/books/{book_id}/file`
2. Stocker EPUB blob dans IndexedDB.
3. GET `/books/{book_id}/cover`
4. Stocker cover blob dans IndexedDB.
5. Stocker metadata snapshot.
6. Marquer livre disponible offline.
7. Afficher badge offline.

## Ouverture du reader

Priorité :
1. EPUB IndexedDB si présent.
2. API serveur si online.
3. Erreur si offline et EPUB absent.

## Sauvegarde progression

À chaque changement significatif :
- sauvegarder en IndexedDB immédiatement,
- debounce en arrière-plan,
- ajouter ou mettre à jour événement sync queue.

Éviter de créer 200 événements pour 200 pages :
- coalescer les progress.updated par book_id.
- garder uniquement le dernier event non envoyé pour ce livre.

## Sync queue event

```ts
type SyncEvent = {
  event_id: string;
  type: "progress.updated" | "bookmark.created" | "bookmark.deleted";
  payload: unknown;
  created_at: string;
  retry_count: number;
  status: "pending" | "syncing" | "failed";
};
```

## Progress event payload

```json
{
  "book_id": "uuid",
  "cfi": "epubcfi(...)",
  "progress_percent": 42,
  "chapter_label": "Chapter 4",
  "chapter_href": "chapter4.xhtml",
  "location_json": {},
  "device_id": "android-pwa",
  "client_updated_at": "2026-04-26T12:00:00Z"
}
```

## Sync triggers

Déclencher sync :
- quand `navigator.onLine` repasse true,
- au lancement de l’app,
- à intervalle raisonnable si online,
- quand l’utilisateur quitte le reader,
- après modification bookmark.

## Conflict policy

V1 :
- updated_at le plus récent gagne.

Si serveur gagne :
- mettre à jour IndexedDB local avec serveur.
- prévenir discrètement si nécessaire.

Si client gagne :
- serveur mis à jour.
- local marqué synced.

## UI states

Afficher état discret :
- Offline
- Syncing
- Synced
- Sync error

Ne pas bloquer la lecture en cas d’erreur sync.

## Cache management

Settings offline :
- afficher livres téléchargés.
- afficher taille approximative.
- supprimer un livre offline.
- vider cache offline.

## Edge cases

Gérer :
- fermeture brutale navigateur,
- retour réseau instable,
- upload sync échoué,
- livre supprimé serveur mais présent offline,
- EPUB local corrompu,
- cache navigateur plein.

En cas de cache plein :
- afficher erreur claire.
- proposer suppression offline.
