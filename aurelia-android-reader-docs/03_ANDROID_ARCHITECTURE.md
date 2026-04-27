# ARCHITECTURE — Aurelia Reader Android

## Objectif

Créer une application Android native minimaliste, confortable et maintenable pour lire les EPUB servis par Aurelia Server.

## Stack

- Kotlin
- Jetpack Compose
- Material 3
- Readium Kotlin Toolkit
- OkHttp ou Retrofit
- Kotlin Serialization ou Moshi
- Room
- DataStore
- WorkManager
- Coil
- AndroidX Security si pertinent

## Structure projet proposée

```txt
android-reader/
  app/
    src/main/java/ch/bytoox/aureliareader/
      MainActivity.kt
      AureliaReaderApp.kt

      core/
        network/
          ApiClient.kt
          AuthInterceptor.kt
          AureliaApi.kt
          NetworkModels.kt
        storage/
          TokenStore.kt
          ServerSettingsStore.kt
          ReaderPreferencesStore.kt
        files/
          BookFileStore.kt

      data/
        db/
          AppDatabase.kt
          BookEntity.kt
          ProgressEntity.kt
          DownloadEntity.kt
          SyncEventEntity.kt
        repositories/
          AuthRepository.kt
          LibraryRepository.kt
          DownloadRepository.kt
          ReaderRepository.kt
          SyncRepository.kt

      ui/
        navigation/
          AppNavGraph.kt
          Routes.kt
        screens/
          setup/
          login/
          home/
          library/
          bookdetail/
          reader/
          settings/
        theme/
          Color.kt
          Theme.kt
          Typography.kt

      reader/
        ReadiumModule.kt
        ReadiumReaderController.kt
        ReaderSettings.kt
        ReaderLocatorMapper.kt

      sync/
        ProgressSyncWorker.kt
```

## Principes

### Séparation serveur / lecteur

Le serveur gère :

- livres
- fichiers EPUB
- couvertures
- metadata
- progression serveur

L'app Android gère :

- lecture locale
- cache des livres
- progression locale
- sync
- réglages de lecture

### Offline par défaut pour la lecture

Un EPUB doit être téléchargé localement avant lecture.

V1 ne fait pas de streaming EPUB depuis le serveur.

### Source de vérité

Pour le fichier EPUB :

- serveur = source de vérité
- app = cache offline

Pour la progression :

- app = source immédiate
- serveur = source synchronisée

### UI minimaliste

Pas de duplication complète de l'app web.

L'app Android doit rester centrée sur la lecture.

## Modules applicatifs

### AuthRepository

Responsabilités :

- login
- logout
- stockage token
- récupération utilisateur courant

### LibraryRepository

Responsabilités :

- récupérer liste des livres
- récupérer détail livre
- cache local des metadata utiles

### DownloadRepository

Responsabilités :

- télécharger EPUB
- télécharger cover
- stocker localement
- supprimer offline
- indiquer état download

### ReaderRepository

Responsabilités :

- ouvrir un fichier EPUB local
- lire/sauver la progression locale
- fournir les préférences reader

### SyncRepository

Responsabilités :

- envoyer progression au serveur
- gérer retry
- exposer état sync

## Navigation V1

```txt
SetupServer
Login
Home
Library
BookDetail
Reader
Settings
```

## Critères techniques

- pas de logique réseau directement dans les Composables
- pas de stockage token en dur
- pas d'API call bloquant sur main thread
- downloads annulables
- erreurs réseau lisibles
- builds reproductibles
