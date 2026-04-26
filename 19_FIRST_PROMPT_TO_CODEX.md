# Premier prompt à donner à GPT Codex

Tu vas travailler sur le projet Aurelia.

Aurelia est une application web/PWA auto-hébergée de bibliothèque EPUB personnelle, mobile-first, pensée pour Android, avec lecture intégrée, offline-first, synchronisation de progression au retour réseau, et une interface premium dark cyber luxury noir/jaune-or.

Lis tous les fichiers de cadrage fournis dans le dossier :
- 00_MASTER_PROMPT_CODEX.md
- 01_PRODUCT_REQUIREMENTS.md
- 02_UX_UI_SPEC.md
- 03_ARCHITECTURE.md
- 04_DATABASE_MODEL.md
- 05_API_SPEC.md
- 06_FRONTEND_SPEC.md
- 07_BACKEND_SPEC.md
- 08_OFFLINE_SYNC_SPEC.md
- 09_METADATA_SPEC.md
- 10_BACKLOG.md
- 11_ACCEPTANCE_CRITERIA.md
- 17_CODEX_GUARDRAILS.md

Ta première mission n’est PAS de coder.

Tu dois d’abord :
1. inspecter le repo existant,
2. dire s’il est vide ou non,
3. proposer la structure finale du projet,
4. confirmer la stack technique,
5. proposer le plan d’implémentation de la Phase 1,
6. lister précisément les fichiers que tu vas créer ou modifier,
7. identifier les risques techniques,
8. signaler les décisions ambiguës éventuelles,
9. attendre ma validation avant toute implémentation.

Rappels critiques :
- EPUB uniquement en V1.
- Android/PWA prioritaire.
- Offline-first obligatoire.
- Sync au retour réseau obligatoire.
- IndexedDB obligatoire côté client pour offline/progression/bookmarks/sync_queue.
- PostgreSQL obligatoire côté serveur.
- Design premium dark cyber luxury, noir/jaune-or.
- Simplicité Apple + richesse Netflix + puissance Linux.
- Pas de hors scope.
- Pas de dashboard admin générique.
- Pas de microservices.
- Pas d’application mobile native en V1.
- Pas de PDF, MOBI, AZW3, CBZ/CBR, audiobook, DRM ou IA en V1.

Commence par ton audit et ton plan. Ne code rien tant que je n’ai pas validé.
