from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Broker
from app.db.session import get_db
from app.modules.brokers.schemas import BrokerCreatePayload, BrokerUpdatePayload
from app.modules.common import ok

router = APIRouter(prefix="/brokers", tags=["brokers"])


def serialize_broker(broker: Broker) -> dict:
    projects = broker.projects
    next_project = min(projects, key=lambda item: item.planned_date) if projects else None
    return {
        "id": broker.id,
        "name": broker.name,
        "shortName": broker.short_name,
        "currentProjects": len(projects),
        "activeProjects": len([project for project in projects if project.status in ["执行中", "准备中"]]),
        "nextMilestone": (
            f"{next_project.planned_date.month}/{next_project.planned_date.day} {next_project.name}"
            if next_project is not None
            else "-"
        ),
        "riskCount": sum(len(project.risks) for project in projects),
        "overdueCount": sum(
            len([task for task in project.tasks if task.status == "已逾期"])
            for project in projects
        ),
    }


@router.post("")
def create_broker(payload: BrokerCreatePayload, db: Session = Depends(get_db)) -> dict:
    broker = Broker(
        name=payload.name,
        short_name=payload.short_name,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        status=payload.status,
        note=payload.note,
    )
    db.add(broker)
    db.commit()
    db.refresh(broker)

    return ok(serialize_broker(broker))


@router.put("/{broker_id}")
def update_broker(
    broker_id: int,
    payload: BrokerUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    broker.name = payload.name
    broker.short_name = payload.short_name
    broker.contact_name = payload.contact_name
    broker.contact_phone = payload.contact_phone
    broker.status = payload.status
    broker.note = payload.note
    db.add(broker)
    db.commit()
    db.refresh(broker)
    return ok(serialize_broker(broker))


@router.delete("/{broker_id}")
def delete_broker(broker_id: int, db: Session = Depends(get_db)) -> dict:
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    db.delete(broker)
    db.commit()
    return ok({"id": broker_id, "deleted": True})


@router.get("")
def list_brokers(db: Session = Depends(get_db)) -> dict:
    brokers = db.query(Broker).all()
    return ok([serialize_broker(broker) for broker in brokers])
