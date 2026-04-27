from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization:
        raise authentication_error()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise authentication_error()

    user_id = decode_access_token(token)
    if user_id is None:
        raise authentication_error()

    user = db.get(User, user_id)
    if user is None:
        raise authentication_error()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
