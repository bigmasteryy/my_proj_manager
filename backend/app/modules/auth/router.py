from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import User, UserSession
from app.db.session import get_db
from app.modules.auth.deps import get_current_session, get_current_user
from app.modules.auth.schemas import LoginPayload
from app.modules.auth.utils import generate_session_token, session_expiry_from_now, verify_password
from app.modules.common import ok

router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "role": user.role,
        "status": user.status,
        "createdAt": user.created_at.strftime("%Y-%m-%d %H:%M"),
        "lastLoginAt": user.last_login_at.strftime("%Y-%m-%d %H:%M") if user.last_login_at else "",
    }


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已停用，请联系管理员")

    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token=token,
        created_at=datetime.now(),
        expires_at=session_expiry_from_now(),
    )
    user.last_login_at = datetime.now()
    db.add(session)
    db.add(user)
    db.commit()
    db.refresh(user)

    return ok(
        {
            "token": token,
            "user": serialize_user(user),
        }
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return ok(serialize_user(user))


@router.post("/logout")
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)) -> dict:
    db.delete(session)
    db.commit()
    return ok({"logout": True})
