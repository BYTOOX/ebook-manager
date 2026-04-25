# ebook-manager

Stack minimal:
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite
- **Orchestration**: Docker Compose

Données persistées:
- `data/db/` pour SQLite
- `data/library/` pour les ebooks importés

## Démarrage (3 commandes)

```bash
docker compose build
```

```bash
docker compose up -d
```

```bash
open http://localhost:5173
```
