# SPEC — UI/UX Aurelia Reader

## Direction produit

L'app doit être sobre, sombre, rapide et confortable.

Inspiration :

- Lithium Reader pour le confort de lecture
- Aurelia Web pour l'identité noir/or
- Material 3 pour les composants Android

## Ton visuel

- premium
- dark
- minimal
- noir profond
- jaune-or en accent
- pas d'interface admin lourde

## Palette recommandée

```txt
Black: #050505
Surface: #111111
Surface 2: #1A1A1A
Gold: #F5C542
Muted Gold: #A8892A
Text: #F6F1DF
Muted Text: #A7A7A7
Error: #FF6B6B
```

## Écran Setup serveur

Objectif : connecter l'app à une instance Aurelia.

Champs :

- URL serveur
- bouton Tester
- bouton Continuer

Comportement :

- normaliser URL
- refuser URL vide
- afficher état health
- sauvegarder URL si health OK

## Écran Login

Champs :

- username
- password

Actions :

- login
- afficher erreur claire
- sauvegarder token si succès
- naviguer Home

## Home

Sections :

- Continuer la lecture
- Téléchargés
- Bibliothèque serveur

Si aucun livre téléchargé :

- message simple
- bouton Bibliothèque

## Bibliothèque

Liste mobile-first :

- couverture
- titre
- auteur
- progression
- icône downloaded/pas downloaded

Recherche simple en haut.

Pagination ou chargement progressif.

## Fiche livre

Éléments :

- grande couverture
- titre
- auteurs
- description
- progression
- bouton Lire
- bouton Télécharger
- bouton Supprimer offline si downloaded

Règle :

- si pas téléchargé, le bouton Lire peut télécharger puis ouvrir, ou demander confirmation.
- V1 recommandée : bouton Télécharger séparé + Lire actif uniquement si downloaded.

## Reader

Le reader doit être prioritaire sur tout le reste.

En lecture :

- pas de barre de navigation applicative permanente
- overlay masqué par défaut
- tap centre pour afficher overlay
- top/bottom bars semi-transparentes ou surface sombre

## Panneau réglages

Doit être accessible depuis le reader.

Il doit contenir seulement :

- Flow
- Brightness
- Theme
- Text size
- Text align
- Margin
- Line spacing
- Font

Ne pas ajouter de réglages avancés en V1.

## États d'erreur

Messages courts :

- serveur indisponible
- session expirée
- téléchargement impossible
- fichier local absent
- EPUB illisible
- sync en attente

## Accessibilité minimale

- zones tactiles assez grandes
- contraste suffisant
- texte lisible
- boutons avec labels
- ne pas dépendre uniquement de la couleur

## Critères d'acceptation UX

- l'app est utilisable à une main
- le reader ne montre pas d'UI parasite
- les réglages sont modifiables rapidement
- le retour arrière Android est prévisible
- les erreurs sont compréhensibles
