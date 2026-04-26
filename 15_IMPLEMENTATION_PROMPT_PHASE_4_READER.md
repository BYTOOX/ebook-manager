# Prompt Codex - Phase 4 Reader EPUB

Tu vas implémenter le lecteur EPUB intégré.

Objectif :
Permettre de lire un EPUB dans l’application, sauvegarder la progression, et reprendre au bon endroit.

Fonctions :
- route `/reader/:bookId`
- chargement EPUB depuis API
- rendu EPUB
- mode paginé
- mode scroll si possible
- table des matières
- progression %
- CFI courant
- sauvegarde progression serveur
- reprise progression
- bookmark simple
- réglages lecture : thème, font size, line height, margins, font family

Design :
- reader immersif
- bottom navigation masquée
- top bar minimal
- thème noir/jaune-or prioritaire
- texte confortable
- contrôles discrets

Contraintes :
- Ne pas faire offline dans cette phase.
- Ne pas faire annotations/surlignages.
- Ne pas faire recherche texte V1.

Avant de coder :
- Vérifie la librairie EPUB utilisée.
- Explique comment CFI/progression est calculée.
- Liste risques techniques.
- Attends validation.
