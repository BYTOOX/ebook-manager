# SPEC — Offline, downloads et sync progression

## Objectif

Permettre à Aurelia Reader Android de lire sans réseau après téléchargement, puis de synchroniser la progression quand le réseau revient.

## Principe

Un EPUB doit être téléchargé localement avant lecture.

Le stockage local Android est le cache offline.

Le serveur Aurelia reste la source de vérité pour la bibliothèque.

## Stockage fichiers

Utiliser le stockage privé de l'application :

```txt
files/books/<book_id>.epub
files/covers/<book_id>.jpg
```

Ne pas demander de permission stockage externe pour la V1.

## Base locale

Utiliser Room pour stocker :

### BookEntity

- id
- title
- authors
- coverUrl
- localCoverPath
- localFilePath
- isDownloaded
- fileSize
- progressPercent
- lastOpenedAt
- metadataJson
- updatedAt

### ProgressEntity

- bookId
- locatorJson
- cfi si disponible
- progressPercent
- chapterLabel
- chapterHref
- updatedAt
- dirty

### SyncEventEntity

- eventId
- type
- payloadJson
- createdAt
- retryCount
- status

### DownloadEntity

- bookId
- status
- progress
- error
- updatedAt

## Download EPUB

Flux :

1. utilisateur clique télécharger
2. app appelle `GET /books/{id}/file`
3. écrit le fichier dans `files/books`
4. vérifie taille > 0
5. marque `isDownloaded = true`
6. télécharge cover si disponible
7. met à jour la fiche livre

## Lecture offline

Si le fichier local existe :

- ouvrir directement le fichier local
- ne pas bloquer sur le réseau

Si le fichier local n'existe pas :

- proposer téléchargement
- afficher erreur claire si offline

## Progression locale

À chaque changement de position significatif :

- sauvegarder ProgressEntity
- marquer dirty = true
- créer ou coalescer un event `progress.updated`

Coalescing recommandé :

- un seul événement pending par livre
- remplacer payload par la position la plus récente

## Sync online

Quand réseau disponible :

- envoyer événements pending/failed
- batch max 25
- si succès, supprimer events résolus
- marquer ProgressEntity dirty=false si serveur accepte
- si erreur réseau, retry plus tard

## WorkManager

Créer un worker :

```txt
ProgressSyncWorker
```

Déclencheurs :

- réseau disponible
- app startup
- sortie reader
- intervalle périodique raisonnable si nécessaire

## Conflit V1

Politique simple :

- l'update la plus récente gagne
- se baser sur timestamp client et/ou serveur
- si doute, préserver local et retenter

## Critères d'acceptation

- un livre téléchargé reste lisible sans réseau
- la progression est sauvegardée sans réseau
- la progression est sync au retour réseau
- plusieurs changements rapides ne créent pas 200 événements
- une erreur serveur ne supprime pas la progression locale
- l'utilisateur voit un état sync simple : synced, pending, error
