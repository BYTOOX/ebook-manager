# Guardrails Codex - Aurelia

## Règles absolues

Tu dois respecter strictement le scope validé.

Tu ne dois pas :
- ajouter PDF,
- ajouter audiobooks,
- ajouter IA,
- ajouter multi-user,
- ajouter app native,
- ajouter DRM,
- ajouter recommandations,
- ajouter microservices,
- remplacer la stack,
- refaire tout le repo sans raison,
- créer une UI admin comme interface principale.

## Quand tu hésites

Si un choix impacte :
- architecture,
- DB,
- UX principale,
- offline,
- sync,
- sécurité,
- stockage,

Alors tu dois :
1. expliquer le choix,
2. proposer 2 ou 3 options,
3. recommander une option,
4. attendre validation.

## Style de code

- TypeScript strict côté frontend.
- Types Pydantic côté backend.
- Fonctions courtes.
- Services séparés.
- Pas de logique métier énorme dans les routes.
- Pas de composants React géants.
- Pas de duplication inutile.
- Noms explicites.
- Tests pour logique critique.

## Documentation

À chaque phase :
- mettre à jour README si commandes changent.
- documenter les variables d’environnement.
- documenter les migrations.
- documenter les endpoints ajoutés.

## UX

Chaque écran doit être pensé mobile-first.

Priorité :
1. Lire
2. Reprendre
3. Télécharger offline
4. Organiser
5. Administrer

L’admin ne doit jamais dominer l’expérience.

## Performance

- Lazy load covers.
- Paginer bibliothèque.
- Ne pas charger tous les EPUB.
- Ne pas stocker gros blobs en mémoire inutilement.
- Debounce progression.
- Éviter re-render reader excessif.

## Sécurité

- Valider upload EPUB.
- Limiter taille fichier configurable.
- Ne pas exposer chemins fichiers.
- Auth obligatoire.
- Pas de secret hardcodé.
- Headers sécurité si possible.
