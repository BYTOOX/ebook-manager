# Metadata Enrichment Specification - Aurelia

## Objectif

Permettre d’enrichir les métadonnées EPUB via des providers externes, comme un équivalent “TMDB du livre”, tout en gardant le contrôle utilisateur.

## Providers V1

- Open Library
- Google Books

## Principe critique

Ne jamais écraser automatiquement les métadonnées existantes sans validation.

L’utilisateur doit pouvoir :
- lancer une recherche,
- comparer les propositions,
- choisir une proposition,
- choisir quels champs appliquer.

## Pipeline

À l’import :
1. Extraire metadata locale EPUB.
2. Si ISBN présent, proposer recherche par ISBN.
3. Sinon proposer recherche titre + auteur.
4. Stocker les propositions.
5. Afficher dans UI.
6. Appliquer uniquement après validation.

## Champs normalisés

```ts
type MetadataCandidate = {
  provider: "openlibrary" | "googlebooks";
  provider_item_id: string;
  score: number;
  title: string;
  subtitle?: string;
  authors: string[];
  description?: string;
  language?: string;
  isbn?: string;
  publisher?: string;
  published_date?: string;
  cover_url?: string;
  raw: unknown;
};
```

## Scoring

Le score doit prendre en compte :
- ISBN exact,
- similarité titre,
- similarité auteur,
- présence couverture,
- présence description,
- langue.

Priorité :
1. ISBN exact.
2. Titre + auteur très proche.
3. Titre proche.
4. Fallback.

## UI metadata

Écran “Rechercher métadonnées” :
- liste des résultats,
- provider visible,
- score ou indicateur de confiance,
- titre,
- auteur,
- couverture,
- date,
- description courte.

Écran “Appliquer” :
- checkboxes par champ :
  - titre,
  - sous-titre,
  - auteurs,
  - description,
  - couverture,
  - ISBN,
  - éditeur,
  - date,
  - langue.
- preview avant/après.

## Gestion covers

Si provider fournit cover_url :
- télécharger côté backend,
- valider image,
- stocker localement,
- ne pas hotlinker en permanence.

## Erreurs

Si provider indisponible :
- ne pas bloquer l’app.
- afficher “Provider indisponible”.
- logger erreur.
- permettre recherche locale/manuelle.
