# Critères d’acceptation globaux - Aurelia

## Produit

L’application est acceptée si :
- L’utilisateur peut importer un EPUB.
- Le livre apparaît dans la bibliothèque.
- La couverture et les métadonnées sont extraites.
- L’utilisateur peut modifier les métadonnées.
- L’utilisateur peut lire le livre dans l’app.
- La progression est sauvegardée.
- La progression est restaurée à la réouverture.
- Le livre peut être téléchargé offline.
- Le livre reste lisible sans réseau.
- La progression offline se synchronise au retour réseau.
- La page Home permet de reprendre la lecture directement.
- L’interface est mobile-first.
- Le thème noir/jaune-or existe.
- Les fonctions avancées ne polluent pas l’interface principale.

## UX

L’application est refusée si :
- Elle ressemble à un dashboard admin générique.
- La Home ne met pas “Continuer la lecture” en priorité.
- Le reader est inconfortable sur téléphone.
- Le mode sombre est gris fade au lieu de noir profond.
- Les actions principales sont cachées.
- Les fonctions admin sont trop visibles.
- La navigation mobile est pénible.

## Technique

L’application est acceptée si :
- Backend démarre avec une commande documentée.
- Frontend démarre avec une commande documentée.
- DB migrée via Alembic.
- Podman Compose fonctionne.
- Volumes persistants configurés.
- Tests essentiels passent.
- OpenAPI disponible.
- Pas de données critiques uniquement dans localStorage.
- IndexedDB utilisé pour offline.
- PostgreSQL utilisé comme DB principale.

## Offline

Scénario obligatoire :
1. Importer un EPUB.
2. Ouvrir fiche livre.
3. Télécharger offline.
4. Ouvrir reader.
5. Couper réseau.
6. Lire plusieurs pages.
7. Fermer l’app.
8. Rouvrir l’app hors réseau.
9. Retrouver la progression locale.
10. Rétablir réseau.
11. Vérifier sync serveur.

## Sync

- Pas de perte de progression.
- Dernier update gagne.
- Les erreurs réseau ne bloquent pas la lecture.
- La queue retry automatiquement.

## Sécurité

- Auth requise.
- Pas de mot de passe hardcodé en prod.
- Cookies/JWT sécurisés selon architecture.
- Upload limité aux EPUB.
- Validation fichier.
- Pas d’exposition libre du dossier `/data`.
