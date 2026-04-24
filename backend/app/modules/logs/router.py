from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Broker, Project, ProjectLog
from app.db.session import get_db
from app.modules.common import ok
from app.modules.logs.schemas import ProjectLogCreatePayload, ProjectLogUpdatePayload

router = APIRouter(prefix="/projects", tags=["logs"])
history_router = APIRouter(prefix="/history", tags=["history"])


@history_router.get("/logs")
def list_history_logs(
    broker_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    keyword: str = Query(default=""),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict:
    query = (
        db.query(ProjectLog, Project, Broker)
        .join(Project, ProjectLog.project_id == Project.id)
        .join(Broker, Project.broker_id == Broker.id)
    )

    if broker_id is not None:
        query = query.filter(Broker.id == broker_id)

    if project_id is not None:
        query = query.filter(Project.id == project_id)

    if start_date is not None:
        query = query.filter(ProjectLog.log_date >= datetime.combine(start_date, time.min))

    if end_date is not None:
        query = query.filter(ProjectLog.log_date <= datetime.combine(end_date, time.max))

    if keyword.strip():
        fuzzy = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Broker.name.like(fuzzy),
                Project.name.like(fuzzy),
                ProjectLog.content.like(fuzzy),
                ProjectLog.next_action.like(fuzzy),
            )
        )

    rows = query.order_by(ProjectLog.log_date.desc()).limit(limit).all()

    return ok(
        [
            {
                "id": log.id,
                "brokerId": broker.id,
                "brokerName": broker.name,
                "projectId": project.id,
                "projectName": project.name,
                "projectType": project.project_type,
                "logDate": log.log_date.strftime("%Y-%m-%d %H:%M"),
                "content": log.content,
                "nextAction": log.next_action,
            }
            for log, project, broker in rows
        ]
    )


@router.post("/{project_id}/logs")
def create_project_log(
    project_id: int,
    payload: ProjectLogCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    log = ProjectLog(
        project_id=project.id,
        log_date=datetime.now(),
        content=payload.content,
        next_action=payload.next_action,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return ok(
        {
            "id": log.id,
            "logDate": log.log_date.strftime("%Y-%m-%d %H:%M"),
            "content": log.content,
            "nextAction": log.next_action,
        }
    )


@router.put("/logs/{log_id}")
def update_project_log(
    log_id: int,
    payload: ProjectLogUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    log = db.query(ProjectLog).filter(ProjectLog.id == log_id).first()
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")

    log.content = payload.content
    log.next_action = payload.next_action
    db.add(log)
    db.commit()
    db.refresh(log)
    return ok(
        {
            "id": log.id,
            "logDate": log.log_date.strftime("%Y-%m-%d %H:%M"),
            "content": log.content,
            "nextAction": log.next_action,
        }
    )


@router.delete("/logs/{log_id}")
def delete_project_log(log_id: int, db: Session = Depends(get_db)) -> dict:
    log = db.query(ProjectLog).filter(ProjectLog.id == log_id).first()
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")

    db.delete(log)
    db.commit()
    return ok({"id": log_id, "deleted": True})
