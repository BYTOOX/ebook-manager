from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse, PasswordChangeRequest, SetupRequest, UserRead
from app.services.user_service import (
    authenticate_user,
    create_user,
    has_any_user,
    update_password,
)

router = APIRouter()


def build_login_response(user) -> LoginResponse:
    settings = get_settings()
    return LoginResponse(
        ok=True,
        access_token=create_access_token(user.id),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.post("/setup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def setup_first_user(payload: SetupRequest, db: DbSession) -> LoginResponse:
    settings = get_settings()
    if has_any_user(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setup already completed")
    if settings.FIRST_USER_SETUP_TOKEN and payload.setup_token != settings.FIRST_USER_SETUP_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid setup token")

    user = create_user(db, payload.username, payload.password, payload.display_name)
    return build_login_response(user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: DbSession) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return build_login_response(user)


@router.post("/logout")
def logout() -> dict[str, bool]:
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/change-password")
def change_password(payload: PasswordChangeRequest, current_user: CurrentUser, db: DbSession) -> dict[str, bool]:
    if not update_password(db, current_user, payload.current_password, payload.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current password")
    return {"ok": True}
