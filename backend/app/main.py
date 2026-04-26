from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, books, health, imports, organization, settings, sync
from app.core.config import get_settings


def create_app() -> FastAPI:
    app_settings = get_settings()
    app = FastAPI(
        title=app_settings.APP_NAME,
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api/v1")
    api.include_router(health.router, tags=["health"])
    api.include_router(auth.router, prefix="/auth", tags=["auth"])
    api.include_router(books.router, prefix="/books", tags=["books"])
    api.include_router(organization.router, prefix="/organization", tags=["organization"])
    api.include_router(imports.router, tags=["imports"])
    api.include_router(settings.router, prefix="/settings", tags=["settings"])
    api.include_router(sync.router, prefix="/sync", tags=["sync"])
    app.include_router(api)

    @app.get("/health", tags=["health"])
    def root_health() -> dict[str, str]:
        return {"status": "ok", "app": app_settings.APP_NAME}

    return app


app = create_app()
