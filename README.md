# Ebook Manager

API + interface web minimale pour importer et lire des ebooks EPUB/PDF.

## Lancer

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Interface:
- Bibliothèque: `http://localhost:8000/ui/library`

Endpoints:
- `POST /books/import`
- `GET /books`
- `GET /books/{id}`
