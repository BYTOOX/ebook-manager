from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    id: UUID
    username: str
    display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SetupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=10, max_length=256)
    display_name: str | None = Field(default=None, max_length=120)
    setup_token: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=256)


class AuthStatus(BaseModel):
    ok: bool
    user: UserRead | None = None


class LoginResponse(BaseModel):
    ok: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
