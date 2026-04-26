# Prompt Codex - Phase 2

Tu vas implémenter la Phase 2 : Import EPUB.

Préconditions :
- Phase 1 terminée.
- Backend fonctionne.
- DB fonctionne.
- Frontend minimal fonctionne.

Objectif :
Permettre d’importer un fichier EPUB, d’extraire ses métadonnées, sa couverture, et de créer une entrée livre en DB.

Fonctions à implémenter :
- POST /api/v1/books/upload
- validation fichier EPUB
- calcul hash
- détection doublon exact
- extraction metadata EPUB
- extraction cover
- stockage dans `/data/library/books/<book_id>/original.epub`
- stockage cover dans `/data/library/books/<book_id>/cover.jpg`
- création book/authors en DB
- GET /api/v1/books
- GET /api/v1/books/{book_id}
- GET /api/v1/books/{book_id}/cover
- GET /api/v1/books/{book_id}/file
- import_jobs simples

Frontend :
- page import simple
- drag & drop EPUB
- affichage résultat import
- affichage bibliothèque minimale

Contraintes :
- EPUB uniquement.
- Ne pas gérer PDF.
- Ne pas gérer metadata online dans cette phase.
- Ne pas faire l’offline dans cette phase.

Avant de coder :
- Inspecte l’existant.
- Propose le plan d’implémentation.
- Liste les fichiers à modifier.
- Attends validation.
