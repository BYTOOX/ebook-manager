# PRD — Aurelia Reader Android

## Résumé

Aurelia Reader est une application Android native de lecture EPUB connectée au serveur Aurelia.

Elle permet à l'utilisateur de :

- se connecter à son serveur Aurelia
- consulter sa bibliothèque EPUB
- télécharger des livres pour lecture offline
- lire les EPUB avec un confort proche de Lithium Reader
- sauvegarder la progression localement
- synchroniser la progression avec le serveur

## Utilisateur cible

Utilisateur principal :

- personne possédant un serveur Aurelia auto-hébergé
- lit principalement sur Android
- veut une expérience plus propre qu'une PWA
- veut une lecture fluide, plein écran, offline
- veut reprendre la lecture entre appareils

## Objectifs V1

### Objectif 1 : Connexion serveur

L'utilisateur peut configurer l'URL de son serveur Aurelia et se connecter avec son compte.

### Objectif 2 : Bibliothèque

L'utilisateur peut voir la liste des livres disponibles sur le serveur.

### Objectif 3 : Téléchargement offline

L'utilisateur peut télécharger un EPUB localement.

### Objectif 4 : Lecture confortable

L'utilisateur peut lire un EPUB local avec Readium.

### Objectif 5 : Progression

L'application sauvegarde immédiatement la progression localement et la synchronise avec le serveur.

### Objectif 6 : Réglages essentiels

L'utilisateur peut régler :

- flow : auto, paged, scrolled
- thème : clair, gris, noir, sépia, Aurelia
- taille texte
- alignement
- marges
- interligne
- police
- luminosité reader

## Hors scope V1

Les fonctionnalités suivantes ne doivent pas être développées en V1 :

- annotations
- highlights
- notes
- export markdown
- statistiques de lecture
- TTS
- OPDS
- PDF
- MOBI
- CBZ
- gestion avancée collections/tags
- édition metadata
- import EPUB depuis Android
- multi-utilisateur avancé côté app
- recommandations IA

## Expérience cible

L'expérience doit être simple :

1. L'utilisateur ouvre l'app.
2. Il arrive sur "Continuer la lecture" ou "Bibliothèque".
3. Il télécharge un livre si nécessaire.
4. Il lit en plein écran.
5. Il quitte.
6. Il revient plus tard exactement au même endroit.

## Benchmark UX

Le benchmark de confort est Lithium Reader sur Android, non pas en nombre de fonctionnalités, mais en sensation de lecture :

- peu de réglages
- réglages accessibles rapidement
- interface discrète
- texte lisible
- tactile fiable
- pas de barre de navigateur
- pas de latence gênante
- pas de perte de position

## Écrans V1

### Setup serveur

- champ URL serveur
- bouton tester connexion
- message état serveur
- bouton continuer vers login

### Login

- username
- password
- bouton connexion
- erreur claire

### Home

- continuer la lecture
- livres téléchargés
- accès bibliothèque serveur

### Bibliothèque

- liste livres
- recherche simple
- état téléchargé / non téléchargé
- couverture, titre, auteur, progression

### Fiche livre

- couverture
- titre
- auteurs
- description si disponible
- progression
- bouton lire
- bouton télécharger
- bouton supprimer offline

### Reader

- rendu EPUB
- plein écran
- tap centre affiche/masque UI
- tap droite page suivante
- tap gauche page précédente
- swipe horizontal
- panneau réglages
- indicateur progression discret

### Paramètres

- URL serveur
- compte connecté
- logout
- thème app
- purge cache offline
- informations version

## Critères d'acceptation V1

- l'app Android compile en debug
- l'utilisateur peut se connecter au serveur
- l'utilisateur peut lister les livres
- l'utilisateur peut télécharger un EPUB
- l'utilisateur peut lire un EPUB localement
- le reader fonctionne sans réseau après téléchargement
- la progression est sauvegardée localement
- la progression est envoyée au serveur
- à la réouverture, le livre reprend au bon endroit
- les réglages de lecture sont persistés
