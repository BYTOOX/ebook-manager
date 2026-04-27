# PLAN — Phases de développement Aurelia Android Reader

## Important

Chaque phase doit être faite séparément.

Ne jamais commencer la phase suivante sans validation humaine.

Chaque phase doit finir par :

- résumé
- fichiers modifiés
- commandes exécutées
- résultats tests/build
- risques restants

---

# Phase 1 — Migration Bearer Auth

## Objectif

Migrer Aurelia Server + Aurelia Web de cookie auth vers Bearer auth.

## Scope

Backend :

- modifier login pour retourner access_token
- modifier setup pour retourner access_token
- modifier get_current_user pour lire Authorization Bearer
- logout stateless
- tests adaptés

Frontend :

- stocker token
- envoyer Authorization header
- retirer dépendance cookie
- gérer 401
- build OK

Docs :

- README auth mis à jour
- .env si nécessaire

## Hors scope

- Android
- refresh token
- révocation serveur
- modification des features livres/import/reader

## Acceptance

- backend tests pass
- frontend build pass
- login web fonctionne
- refresh page conserve session
- routes protégées refusent sans token

---

# Phase 2 — Création projet Android skeleton

## Objectif

Créer l'application Android native Aurelia Reader.

## Scope

- projet `android-reader`
- Kotlin
- Jetpack Compose
- Material 3
- navigation
- thème Aurelia
- écrans placeholder :
  - setup serveur
  - login
  - home
  - library
  - book detail
  - reader
  - settings
- build debug OK

## Hors scope

- API réelle
- Readium
- downloads
- sync

## Acceptance

- `./gradlew assembleDebug` OK
- app lance sur émulateur/device
- navigation basique OK

---

# Phase 3 — API client + auth Android

## Objectif

Connecter l'app Android au serveur Aurelia.

## Scope

- stockage URL serveur
- health check
- login Bearer
- stockage token sécurisé ou DataStore
- AuthInterceptor
- GET /auth/me
- logout

## Acceptance

- URL serveur sauvegardée
- login fonctionne
- token envoyé sur requêtes
- logout supprime token
- erreurs affichées

---

# Phase 4 — Bibliothèque Android

## Objectif

Afficher les livres du serveur dans l'app Android.

## Scope

- GET /books
- pagination simple
- recherche simple
- GET /books/{id}
- affichage couvertures avec Coil
- fiche livre

## Acceptance

- liste visible
- recherche fonctionne
- détail livre visible
- erreurs réseau propres

---

# Phase 5 — Téléchargement offline

## Objectif

Télécharger EPUB + cover localement.

## Scope

- GET /books/{id}/file
- stockage `files/books/<id>.epub`
- stockage cover local
- Room entities pour books/downloads
- état downloaded
- suppression offline

## Acceptance

- téléchargement fonctionne
- fichier existe localement
- suppression offline fonctionne
- lecture non encore nécessaire

---

# Phase 6 — Readium reader minimal

## Objectif

Ouvrir un EPUB local avec Readium.

## Scope

- intégrer Readium Kotlin Toolkit
- ouvrir fichier local téléchargé
- afficher contenu EPUB
- mode paginé
- navigation page suivante/précédente
- retour fiche livre

## Acceptance

- EPUB local s'ouvre
- page suivante/précédente fonctionne
- pas de crash sur retour app

---

# Phase 7 — Confort reader Lithium-like

## Objectif

Ajouter les réglages essentiels et l'UX de lecture.

## Scope

- plein écran
- tap centre overlay
- tap gauche/droite
- swipe
- panneau réglages
- flow auto/paged/scrolled
- brightness
- thèmes
- text size
- align
- margin
- line spacing
- font
- préférences persistées

## Acceptance

- réglages changent rendu
- réglages persistés
- UI discrète
- expérience tactile correcte sur device réel

---

# Phase 8 — Progression locale

## Objectif

Sauvegarder et restaurer la position de lecture.

## Scope

- mapper locator Readium vers stockage local
- sauvegarde régulière
- sauvegarde onPause/onStop
- restauration à l'ouverture
- afficher progression

## Acceptance

- fermeture/réouverture reprend au bon endroit
- changement de réglage ne détruit pas position
- progression visible en bibliothèque

---

# Phase 9 — Sync progression serveur

## Objectif

Synchroniser la progression avec Aurelia Server.

## Scope

- PUT /books/{id}/progress online
- queue locale offline
- POST /sync/events
- WorkManager
- états sync

## Acceptance

- progression envoyée serveur
- offline puis retour réseau sync correctement
- pas de perte de progression locale
- coalescing des événements

---

# Phase 10 — Polish V1

## Objectif

Stabiliser la V1.

## Scope

- tests device réel
- gestion erreurs EPUB
- loaders
- empty states
- amélioration performance
- README Android
- instructions build APK

## Acceptance

- APK debug installable
- scénario complet validé :
  - login
  - liste livres
  - download
  - lecture offline
  - progression
  - sync
- bugs bloquants corrigés
