from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.models import User, UserSession
from app.db.session import get_db


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Unauthorized")


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise _unauthorized()
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise _unauthorized()
    token = authorization[len(prefix):].strip()
    if not token:
        raise _unauthorized()
    return token


def get_current_session(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> UserSession:
    token = _extract_token(authorization)
    session = (
        db.query(UserSession)
        .join(User)
        .filter(UserSession.token == token)
        .first()
    )
    if session is None:
        raise _unauthorized()
    if session.expires_at < datetime.now():
        db.delete(session)
        db.commit()
        raise _unauthorized()
    if session.user.status != "active":
        raise _unauthorized()
    return session


def get_current_user(session: UserSession = Depends(get_current_session)) -> User:
    return session.user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
