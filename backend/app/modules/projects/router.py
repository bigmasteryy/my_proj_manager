from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Broker, Project
from app.db.session import get_db
from app.modules.common import ok
from app.modules.projects.schemas import ProjectCreatePayload, ProjectUpdatePayload
from app.modules.projects.utils import calculate_project_progress

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(
    broker_id: Optional[int] = None,
    status: str = Query(default=""),
    keyword: str = Query(default=""),
    owner_name: str = Query(default=""),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Project).join(Broker)

    if broker_id is not None:
        query = query.filter(Project.broker_id == broker_id)

    if status.strip():
        query = query.filter(Project.status == status.strip())

    if owner_name.strip():
        query = query.filter(Project.owner_name.like(f"%{owner_name.strip()}%"))

    if keyword.strip():
        fuzzy = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Project.name.like(fuzzy),
                Project.project_type.like(fuzzy),
                Broker.name.like(fuzzy),
                Project.description.like(fuzzy),
            )
        )

    projects = query.order_by(Project.planned_date.asc()).all()

    return ok(
        [
            {
                "id": project.id,
                "brokerId": project.broker.id,
                "brokerName": project.broker.name,
                "projectName": project.name,
                "projectType": project.project_type,
                "ownerName": project.owner_name,
                "plannedDate": project.planned_date.isoformat(),
                "progressPercent": calculate_project_progress(project),
                "riskCount": len(project.risks),
                "overdueCount": len([task for task in project.tasks if task.status == "已逾期"]),
                "status": project.status,
            }
            for project in projects
        ]
    )


@router.post("")
def create_project(payload: ProjectCreatePayload, db: Session = Depends(get_db)) -> dict:
    broker = db.query(Broker).filter(Broker.id == payload.broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    project = Project(
        broker_id=payload.broker_id,
        name=payload.name,
        project_type=payload.project_type,
        owner_name=payload.owner_name,
        planned_date=payload.planned_date,
        status=payload.status,
        progress_percent=0,
        description=payload.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ok(
        {
            "id": project.id,
            "brokerName": broker.name,
            "projectName": project.name,
            "projectType": project.project_type,
            "ownerName": project.owner_name,
            "plannedDate": project.planned_date.isoformat(),
            "progressPercent": project.progress_percent,
            "riskCount": 0,
            "overdueCount": 0,
            "status": project.status,
        }
    )


@router.put("/{project_id}")
def update_project(
    project_id: int,
    payload: ProjectUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    broker = db.query(Broker).filter(Broker.id == payload.broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    project.broker_id = payload.broker_id
    project.name = payload.name
    project.project_type = payload.project_type
    project.owner_name = payload.owner_name
    project.planned_date = payload.planned_date
    project.status = payload.status
    project.description = payload.description
    db.add(project)
    db.commit()
    db.refresh(project)

    return ok(
        {
            "id": project.id,
            "brokerName": broker.name,
            "projectName": project.name,
            "projectType": project.project_type,
            "ownerName": project.owner_name,
            "plannedDate": project.planned_date.isoformat(),
            "progressPercent": calculate_project_progress(project),
            "riskCount": len(project.risks),
            "overdueCount": len([task for task in project.tasks if task.status == "已逾期"]),
            "status": project.status,
        }
    )


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return ok({"id": project_id, "deleted": True})


@router.get("/{project_id}")
def get_project_detail(project_id: int, db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ok(
        {
            "id": project.id,
            "brokerId": project.broker.id,
            "brokerName": project.broker.name,
            "name": project.name,
            "projectType": project.project_type,
            "ownerName": project.owner_name,
            "plannedDate": project.planned_date.isoformat(),
            "status": project.status,
            "progressPercent": calculate_project_progress(project),
            "overdueCount": len([task for task in project.tasks if task.status == "已逾期"]),
            "description": project.description,
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "ownerName": task.owner_name,
                    "plannedContent": task.planned_content,
                    "plannedDate": task.planned_date.isoformat(),
                    "actualAction": task.actual_action or "",
                    "completionResult": task.completion_result or "",
                    "status": task.status,
                }
                for task in project.tasks
            ],
            "risks": [
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
                for risk in project.risks
            ],
            "logs": [
                {
                    "id": log.id,
                    "logDate": log.log_date.strftime("%Y-%m-%d %H:%M"),
                    "content": log.content,
                    "nextAction": log.next_action,
                }
                for log in project.logs
            ],
        }
    )
