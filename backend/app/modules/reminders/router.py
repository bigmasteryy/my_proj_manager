from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Reminder
from app.db.session import get_db
from app.modules.common import ok
from app.modules.reminders.schemas import ReminderActionPayload

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("")
def list_reminders(db: Session = Depends(get_db)) -> dict:
    reminders = db.query(Reminder).order_by(Reminder.deadline.asc()).all()
    return ok(
        [
            {
                "id": item.id,
                "type": item.type,
                "brokerName": item.broker_name,
                "projectName": item.project_name,
                "itemName": item.item_name,
                "level": item.level,
                "deadline": item.deadline.isoformat(),
                "status": item.status,
                "description": item.description,
            }
            for item in reminders
        ]
    )


@router.post("/{reminder_id}/handle")
def handle_reminder(
    reminder_id: int,
    _: ReminderActionPayload,
    db: Session = Depends(get_db),
) -> dict:
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.status = "已处理"
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return ok({"id": reminder.id, "status": reminder.status})


@router.post("/{reminder_id}/ignore")
def ignore_reminder(
    reminder_id: int,
    _: ReminderActionPayload,
    db: Session = Depends(get_db),
) -> dict:
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.status = "已忽略"
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return ok({"id": reminder.id, "status": reminder.status})
