from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-with-at-least-thirty-two-bytes"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: F401, E402


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)


def teardown_function() -> None:
    Base.metadata.drop_all(bind=engine)


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_first_user_setup_login_and_me() -> None:
    client = TestClient(app)
    setup = client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "very-secure-password", "display_name": "Aurelia"},
    )
    assert setup.status_code == 201
    assert setup.json()["user"]["username"] == "admin"

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["display_name"] == "Aurelia"

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "very-secure-password"},
    )
    assert login.status_code == 200
    assert login.json()["ok"] is True
