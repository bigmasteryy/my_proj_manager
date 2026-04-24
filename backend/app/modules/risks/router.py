from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Project, Risk
from app.db.session import get_db
from app.modules.common import ok
from app.modules.projects.utils import close_reminders_for_item, create_risk_reminder_if_needed
from app.modules.risks.schemas import RiskCreatePayload, RiskStatusUpdatePayload, RiskUpdatePayload

router = APIRouter(tags=["risks"])


@router.post("/projects/{project_id}/risks")
def create_risk(
    project_id: int,
    payload: RiskCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    risk = Risk(
        project_id=project.id,
        title=payload.title,
        level=payload.level,
        affects_milestone=payload.affects_milestone,
        owner_name=payload.owner_name,
        planned_resolve_date=payload.planned_resolve_date,
        status=payload.status,
        action_plan=payload.action_plan,
    )
    db.add(risk)
    db.flush()

    create_risk_reminder_if_needed(db, project, risk)
    db.commit()
    db.refresh(risk)

    return ok(
        {
            "id": risk.id,
            "title": risk.title,
            "level": risk.level,
            "affectsMilestone": risk.affects_milestone,
            "ownerName": risk.owner_name,
            "plannedResolveDate": risk.planned_resolve_date.isoformat(),
            "status": risk.status,
            "actionPlan": risk.action_plan,
        }
    )


@router.put("/risks/{risk_id}")
def update_risk(
    risk_id: int,
    payload: RiskUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None:
        raise HTTPException(status_code=404, detail="Risk not found")

    project = risk.project
    close_reminders_for_item(db, project, risk.title)

    risk.title = payload.title
    risk.level = payload.level
    risk.affects_milestone = payload.affects_milestone
    risk.owner_name = payload.owner_name
    risk.planned_resolve_date = payload.planned_resolve_date
    risk.status = payload.status
    risk.action_plan = payload.action_plan
    db.add(risk)

    if risk.status != "已解除":
        create_risk_reminder_if_needed(db, project, risk)

    db.commit()
    db.refresh(risk)

    return ok(
        {
            "id": risk.id,
            "title": risk.title,
            "level": risk.level,
            "affectsMilestone": risk.affects_milestone,
            "ownerName": risk.owner_name,
            "plannedResolveDate": risk.planned_resolve_date.isoformat(),
            "status": risk.status,
            "actionPlan": risk.action_plan,
        }
    )


@router.post("/risks/{risk_id}/status")
def update_risk_status(
    risk_id: int,
    payload: RiskStatusUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None:
        raise HTTPException(status_code=404, detail="Risk not found")

    risk.status = payload.status
    risk.action_plan = payload.action_plan
    db.add(risk)

    if risk.status == "已解除":
        close_reminders_for_item(db, risk.project, risk.title)
    else:
        create_risk_reminder_if_needed(db, risk.project, risk)

    db.commit()
    db.refresh(risk)

    return ok(
        {
            "id": risk.id,
            "title": risk.title,
            "level": risk.level,
            "affectsMilestone": risk.affects_milestone,
            "ownerName": risk.owner_name,
            "plannedResolveDate": risk.planned_resolve_date.isoformat(),
            "status": risk.status,
            "actionPlan": risk.action_plan,
        }
    )


@router.delete("/risks/{risk_id}")
def delete_risk(risk_id: int, db: Session = Depends(get_db)) -> dict:
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None:
        raise HTTPException(status_code=404, detail="Risk not found")

    close_reminders_for_item(db, risk.project, risk.title)
    db.delete(risk)
    db.commit()
    return ok({"id": risk_id, "deleted": True})
