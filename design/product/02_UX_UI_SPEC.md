# UX/UI Specification - Aurelia

## Direction artistique

Aurelia doit avoir une esthétique :
- dark cyber,
- luxueuse,
- sobre,
- Apple-like,
- média façon Netflix,
- noire avec accents jaune-or,
- premium sans être bling-bling.

Le design doit éviter :
- dashboard admin générique,
- Bootstrap brut,
- SaaS enterprise,
- surcharge de boutons,
- couleurs trop vives,
- cards trop carrées,
- interface de gestion comptable.

## Palette recommandée

Base :
- Noir profond : #050505
- Noir secondaire : #0B0B0D
- Charcoal : #121216
- Surface : #18181D
- Surface glass : rgba(255, 255, 255, 0.04)

Accents :
- Or principal : #F5C542
- Or doux : #D8A936
- Jaune lecture : #FFD966
- Texte principal sombre : #F5F1E8
- Texte secondaire : #B8B0A0
- Texte discret : #7C766A

États :
- Succès/offline OK : #6FD08C
- Warning : #F2B84B
- Erreur : #FF5C5C

## Thèmes

L’application doit supporter :
- thème automatique selon système,
- thème clair,
- thème sombre,
- thème noir/jaune-or.

Le thème noir/jaune-or est prioritaire pour la lecture.

## Typographie

Objectif :
- élégance,
- lisibilité,
- contraste,
- confort mobile.

Recommandations :
- UI : Inter, SF Pro alternative, system-ui.
- Titres premium : option serif élégante, par exemple Playfair Display ou Cormorant Garamond, mais à utiliser avec modération.
- Lecture : police configurable.
- Fournir au minimum : serif, sans-serif, dyslexic-friendly option si simple, system default.

## Principes UX

- Mobile-first.
- Une action principale claire par écran.
- Les fonctions avancées sont cachées dans un menu.
- Les écrans doivent respirer.
- Les couvertures sont centrales.
- Les boutons doivent être rares mais évidents.
- La lecture doit être immersive.
- La progression doit être visible sans envahir.
- L’offline doit être rassurant, visible mais discret.

## Écran Home

Objectif :
Permettre à l’utilisateur de reprendre sa lecture en un geste.

Structure :
- Header avec logo/nom Aurelia.
- Petite icône profil ou settings.
- Grande carte “Continue Reading”.
- Section “Downloaded”.
- Section “Recently Added”.
- Bottom navigation.

Carte “Continue Reading” :
- Couverture du livre.
- Label “Continuer la lecture”.
- Titre.
- Auteur.
- Progression en pourcentage.
- Barre de progression.
- Bouton principal “Lire”.
- Badge offline si téléchargé.

Si aucun livre en cours :
- afficher “Choisis ton prochain livre”
- suggestions récemment ajoutées.

## Écran Library

Objectif :
Parcourir, filtrer et gérer la bibliothèque.

Structure :
- Header “Library”.
- Icône recherche.
- Toggle Grid/List.
- Filtres horizontaux : All, Unread, In Progress, Finished, Downloaded, Favorites.
- Bouton Sort.
- Grille de couvertures.

Card livre en grille :
- Couverture.
- Titre.
- Auteur ou série selon espace.
- Étoiles.
- Progression.
- Badge offline.
- Badge favori/bookmark si applicable.

Mode liste :
- Plus dense.
- Couverture miniature.
- Titre.
- Auteur.
- Série.
- Progression.
- Statut.
- Note.
- Bouton menu.

## Écran Book Detail

Structure :
- Grande couverture.
- Titre.
- Auteur.
- Étoiles.
- Statut.
- Progression.
- Bouton principal “Lire”.
- Bouton secondaire “Télécharger offline” ou “Disponible offline”.
- Résumé.
- Série.
- Tags.
- Collections.
- Métadonnées.
- Menu avancé.

Menu avancé :
- Modifier métadonnées.
- Rechercher métadonnées en ligne.
- Changer couverture.
- Marquer comme terminé.
- Ajouter à collection.
- Supprimer téléchargement offline.
- Supprimer livre.

## Écran Reader

Objectif :
Lecture immersive, confortable, premium.

Structure :
- Top bar minimal : retour, titre livre, menu.
- Indication offline si disponible.
- Zone de lecture.
- Progression basse.
- Contrôles discrets : Aa, bookmark, thème, table des matières.
- Bottom sheet pour réglages.

Modes :
- Paginé.
- Scroll vertical.

Réglages :
- Taille police.
- Police.
- Interligne.
- Marges.
- Thème.
- Mode paginé/scroll.
- Luminosité CSS optionnelle.

Le reader doit masquer la bottom navigation standard.

## Écran Settings

Sections :
- Apparence : thème automatique, clair, sombre, noir/jaune-or.
- Lecture : mode par défaut, police, taille, marges.
- Offline : livres téléchargés, taille cache, vider cache.
- Bibliothèque : scan dossier, import, metadata providers.
- Avancé : logs, export metadata, version app.

## Animation et ressenti

Animations :
- transitions douces,
- pas d’effets gadgets,
- pas d’animation lente,
- feedback immédiat.

Exemples :
- hover/tap subtil sur cartes,
- apparition légère des bottom sheets,
- skeleton loaders élégants,
- progress bars fluides.

## Accessibilité

- Contraste fort.
- Taille de police réglable.
- Boutons assez grands pour mobile.
- Navigation utilisable à une main.
- Respect prefers-reduced-motion.
- Labels accessibles pour icônes.
