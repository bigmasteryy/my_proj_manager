from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.deps import get_current_user, require_admin
from app.modules.auth.router import serialize_user
from app.modules.auth.utils import hash_password
from app.modules.common import ok
from app.modules.users.schemas import UserCreatePayload, UserResetPasswordPayload, UserUpdatePayload

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("")
def list_users(db: Session = Depends(get_db)) -> dict:
    users = db.query(User).order_by(User.created_at.asc()).all()
    return ok([serialize_user(user) for user in users])


@router.post("")
def create_user(payload: UserCreatePayload, db: Session = Depends(get_db)) -> dict:
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=payload.username,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        status=payload.status,
        created_at=datetime.now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(serialize_user(user))


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdatePayload, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.display_name = payload.display_name
    user.role = payload.role
    user.status = payload.status
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(serialize_user(user))


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: UserResetPasswordPayload,
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(serialize_user(user))


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")

    db.delete(user)
    db.commit()
    return ok({"id": user_id, "deleted": True})
