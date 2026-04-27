# MASTER PROMPT CODEX — Aurelia Android Reader

## Contexte

Le projet existant s'appelle Aurelia.

Aurelia est une bibliothèque EPUB personnelle auto-hébergée composée actuellement de :

- Backend FastAPI
- PostgreSQL
- Frontend React/Vite/TypeScript
- Reader web EPUB basé sur epub.js
- Offline-first côté web via IndexedDB/Dexie
- Synchronisation de progression
- Import EPUB
- Metadata providers Open Library / Google Books

Le nouveau développement consiste à ajouter un vrai client Android natif nommé :

Aurelia Reader

Cette application Android doit se connecter au serveur Aurelia existant, télécharger les EPUB, les lire localement avec Readium Kotlin Toolkit, sauvegarder la progression localement, puis synchroniser la progression avec le serveur.

## Objectif global

Créer un écosystème :

Aurelia Server = bibliothèque, stockage, metadata, progression serveur  
Aurelia Web = administration/import/gestion bibliothèque  
Aurelia Reader Android = application de lecture native confortable

Le but n'est PAS de recréer toute l'application web sur Android.

Le but est de créer un reader Android simple, rapide, confortable et fiable.

## Priorité produit

L'objectif principal est le confort de lecture, proche de Lithium Reader sur Android :

- plein écran propre
- mode paginé ou scroll
- tap zones gauche/droite/centre
- swipe fluide
- réglages simples
- reprise exacte de lecture
- offline fiable
- sync progression

Les annotations, highlights, notes, statistiques, TTS, OPDS, PDF, MOBI, CBZ et fonctionnalités avancées sont hors scope V1.

## Règles strictes

Ne pas sortir du périmètre demandé.

Ne pas ajouter de fonctionnalités non demandées.

Ne pas réécrire le backend sauf dans les phases où c'est explicitement demandé.

Ne pas introduire React Native, Flutter, Capacitor ou une PWA wrapper.

L'application Android doit être native Kotlin.

Le moteur de lecture EPUB cible est Readium Kotlin Toolkit.

L'interface Android doit utiliser Jetpack Compose.

Le stockage local doit être propre et maintenable.

Chaque phase doit être livrée avec :

- code fonctionnel
- build vérifié
- tests ou vérifications manuelles documentées
- résumé des fichiers modifiés
- risques connus
- TODO restants

## Stack Android cible

- Kotlin
- Gradle Kotlin DSL si possible
- Jetpack Compose
- Material 3
- Readium Kotlin Toolkit
- OkHttp ou Retrofit
- Kotlin Serialization ou Moshi
- Room
- DataStore
- WorkManager
- Coil pour couvertures
- AndroidX Security pour stockage token si disponible et raisonnable

## Méthode de travail attendue

Avant de coder une phase :

1. Lire les documents de specs fournis.
2. Inspecter le repo existant.
3. Identifier les fichiers concernés.
4. Proposer brièvement le plan d'action.
5. Implémenter uniquement la phase demandée.
6. Exécuter les tests/builds disponibles.
7. Corriger les erreurs.
8. Ne pas passer à la phase suivante sans instruction explicite.

## Commandes attendues

Pour le backend :

```bash
cd backend
python -m pytest
```

Pour le frontend web :

```bash
cd frontend
npm run build
npm run typecheck
```

Pour Android :

```bash
cd android-reader
./gradlew assembleDebug
```

Adapter les commandes si la structure finale diffère, mais documenter le changement.

## Interdictions

Ne pas supprimer les fonctionnalités existantes.

Ne pas changer les routes API existantes sauf demande explicite.

Ne pas casser le frontend web.

Ne pas introduire de dépendances lourdes sans justification.

Ne pas stocker de secrets en dur.

Ne pas ajouter de télémétrie.

Ne pas ajouter de compte cloud externe.

Ne pas dépendre de Google Drive.

Ne pas implémenter annotations/highlights en V1.

Ne pas implémenter PDF/MOBI/CBZ en V1.

## Définition de terminé

Une phase est terminée si :

- le code compile
- les tests concernés passent ou les limitations sont documentées
- le comportement demandé fonctionne
- les erreurs connues sont listées
- aucun scope creep n'a été ajouté
