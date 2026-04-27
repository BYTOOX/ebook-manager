# SPEC — Reader EPUB Readium

## Objectif

Implémenter un lecteur EPUB Android confortable avec Readium Kotlin Toolkit.

Le benchmark de confort est Lithium Reader, mais seulement sur les sensations de lecture :

- simplicité
- fluidité
- plein écran
- réglages essentiels
- reprise fiable

## Scope V1

Le reader doit supporter :

- ouverture EPUB local
- mode paginé
- mode scroll
- thème clair
- thème gris
- thème noir
- thème sépia
- thème Aurelia
- taille texte
- alignement gauche / justifié
- marges
- interligne
- police
- luminosité dans le reader
- tap zones
- swipe
- sauvegarde locator/progression
- reprise au locator sauvegardé

## Hors scope V1

- annotations
- highlights
- notes
- recherche plein texte
- TTS
- OPDS
- fixed-layout avancé
- PDF/MOBI/CBZ

## Interaction tactile

### Tap centre

Affiche ou masque l'overlay UI :

- top bar
- bottom bar
- bouton réglages
- progression

### Tap droite

Page suivante en mode paginé.

### Tap gauche

Page précédente en mode paginé.

### Swipe horizontal

Page suivante/précédente.

### Mode scroll

En mode scroll, swipe vertical natif.

## UI reader

### État normal

- contenu plein écran
- aucune barre intrusive
- status bar et nav bar masquées si possible
- progression discrète optionnelle

### Overlay visible

Top bar :

- retour
- titre court
- bouton réglages

Bottom bar :

- progression
- chapitre
- bouton page/position si utile

## Réglages V1

Le panneau réglages doit être simple, proche de Lithium.

```txt
Flow
[ Auto ] [ Paged ] [ Scrolled ]

Brightness
────────●────────

Theme
○ White  ○ Gray  ● Black  ○ Sepia  ○ Aurelia

Text size
120%                    −     +

Text align
Justify                 Left  Justify

Margin
5%                      −     +

Line spacing
1.6                     −     +

Font
[ System Serif        ▼ ]
```

## Préférences à persister

Stocker globalement :

- flow
- theme
- font size
- font family
- line height
- margins
- text align
- brightness
- publisher styles on/off si implémenté

Stocker par livre :

- locator Readium
- progression %
- chapitre
- date dernière lecture

## Thème Aurelia

Valeurs recommandées :

```txt
background: #050505
surface: #111111
readerBackground: #0B0B08
text: #C9A227
accent: #F5C542
muted: #8A7A3A
```

Le but : noir profond + or doux lisible.

## Gestion position

La position doit être sauvegardée :

- régulièrement pendant lecture
- quand l'app passe en arrière-plan
- quand le reader est quitté
- avant changement important de préférences si possible

La restauration doit se faire au locator le plus précis disponible.

## Critères d'acceptation

- un EPUB téléchargé s'ouvre
- la page suivante/précédente fonctionne
- le mode scroll fonctionne ou est explicitement désactivé si Readium bloque temporairement
- les réglages modifient le rendu sans crash
- la position ne revient pas au début après fermeture app
- la position ne saute pas violemment après changement de taille texte
- le reader reste utilisable offline
