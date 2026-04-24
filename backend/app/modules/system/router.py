from __future__ import annotations

from fastapi import APIRouter

from app.db.session import reset_demo_database
from app.modules.common import ok

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/reset-demo")
def reset_demo_data() -> dict:
    reset_demo_database()
    return ok({"reset": True})
