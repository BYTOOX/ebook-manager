# Product Requirements Document - Aurelia Ebook Library

Nom de travail : Aurelia

## Vision

Aurelia est une bibliothèque EPUB personnelle auto-hébergée, pensée mobile-first, avec une expérience premium proche d’une app native.

L’objectif est de remplacer l’usage actuel d’une app comme Lithium Pro par un système personnel tout-en-un :
- import des EPUB,
- bibliothèque visuelle,
- lecture intégrée,
- lecture hors ligne,
- synchronisation de progression,
- enrichissement des métadonnées,
- interface luxueuse, simple et rapide.

## Positionnement

Aurelia doit être :
- plus élégant qu’un outil admin,
- plus personnel qu’un Calibre-Web,
- plus simple qu’une usine à gaz,
- plus puissant qu’un simple lecteur EPUB local.

L’expérience doit rappeler :
- Netflix pour la navigation média,
- Apple Books pour la sobriété,
- une marque de luxe tech pour l’ambiance,
- Linux pour la puissance sous le capot.

## Public cible

V1 :
- un seul utilisateur,
- usage personnel,
- lecture principalement sur Android,
- PWA installable.

## Fonctionnalités V1

### Bibliothèque

- Import EPUB par upload web.
- Import EPUB par scan d’un dossier.
- Extraction automatique des métadonnées EPUB : titre, auteur(s), couverture, langue, description si présente, ISBN si présent, date de publication si présente, éditeur si présent.
- Affichage des livres en grille premium.
- Affichage alternatif en liste dense.
- Recherche par titre, auteur, tag, série.
- Filtres : tous, non lus, en cours, terminés, téléchargés hors ligne, favoris.
- Tri : date d’ajout, dernière lecture, titre, auteur, progression, note, série.

### Métadonnées

- Édition manuelle complète : titre, sous-titre, auteur(s), description, couverture, langue, ISBN, éditeur, date de publication, série, numéro dans la série, tags, collections.
- Détection de doublons avec avertissement, pas blocage strict.
- Recherche de métadonnées en ligne via providers.
- Providers V1 : Open Library, Google Books.
- Ne jamais écraser les métadonnées sans validation utilisateur.

### Séries et collections

- Gérer les séries.
- Chaque livre peut appartenir à une série.
- Chaque livre peut avoir un numéro dans la série.
- Collections manuelles.
- Un livre peut appartenir à plusieurs collections.
- Exemples : À lire bientôt, Technique, Roman détente, Favoris, Série à finir.

### Notation et statuts

- Système d’étoiles de 0 à 5, étoiles entières en V1.
- La note est personnelle et sert au tri/filtre.
- Statuts : à lire, en cours, terminé, abandonné, favori.
- Le statut “en cours” peut être déduit de la progression, mais doit rester modifiable.

### Lecture EPUB

- Lecteur EPUB intégré.
- Mode paginé.
- Mode scroll vertical.
- Choix du mode par l’utilisateur.
- Table des matières.
- Progression visible.
- Reprise à la dernière position.
- Sauvegarde automatique.
- Plein écran ou mode focus.
- Réglages : taille de police, police, interligne, marges, thème, largeur de colonne si applicable.

### Thèmes de lecture

Thèmes minimum :
- automatique selon système,
- clair,
- sombre,
- sépia,
- noir/jaune-or.

Le thème noir/jaune-or est important :
- fond noir profond,
- texte jaune chaud,
- contraste élevé,
- confortable pour les yeux.

### Offline-first

La lecture hors ligne est obligatoire.

L’application doit permettre :
- de télécharger un EPUB localement dans la PWA,
- de lire ce livre sans connexion,
- de sauvegarder la progression localement,
- de synchroniser automatiquement dès que la connexion revient.

Stockage local :
- IndexedDB pour EPUB offline,
- IndexedDB pour progression locale,
- IndexedDB pour bookmarks,
- IndexedDB pour file d’attente de sync.

### Synchronisation

Pour chaque livre :
- position EPUB CFI,
- pourcentage,
- chapitre actuel,
- date de dernière lecture,
- timestamp de mise à jour,
- device_id optionnel.

Règle de conflit V1 :
- la progression la plus récente gagne.

### Bookmarks

V1 :
- ajouter un bookmark,
- supprimer un bookmark,
- lister les bookmarks d’un livre,
- synchroniser les bookmarks.

V2 :
- surlignage,
- notes sur passage,
- export Markdown.

### Page d’accueil

La page d’accueil doit être centrée sur la reprise de lecture.

Sections :
1. Continuer la lecture
2. Téléchargés hors ligne
3. Récemment ajoutés
4. Collections ou séries optionnelles

Le premier élément doit être une grande carte “Continuer la lecture”.

### Navigation

Navigation mobile en bas :
- Home
- Library
- Search
- Collections
- Settings

Les actions avancées doivent être cachées dans des menus contextuels ou une section Gestion.

### Administration

Interface admin discrète.

Fonctions :
- uploader un EPUB,
- lancer un scan,
- voir erreurs d’import,
- voir doublons potentiels,
- modifier métadonnées,
- supprimer un livre,
- gérer collections,
- gérer tags,
- voir état offline si pertinent,
- exporter métadonnées.

Ne pas afficher l’admin comme interface principale.

## Fonctionnalités V2

- OPDS pour liseuses.
- WebDAV optionnel.
- Export EPUB propre.
- Surlignage.
- Notes sur passages.
- Export notes Markdown.
- Recherche dans le contenu du livre.
- Statistiques de lecture.
- Support liseuse Android amélioré.
- Import automatique depuis dossier surveillé plus avancé.

## Hors scope

- DRM.
- Contournement DRM.
- Marketplace.
- Téléchargement automatisé depuis sources externes non autorisées.
- Support multi-user.
- Application native Android/iOS.
- Audiobooks.
- PDF.
- IA générative.
- Social features.
