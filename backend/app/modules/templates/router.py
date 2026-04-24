from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Broker, Project, Risk, Task, Template, TemplateRisk, TemplateTask
from app.db.session import get_db
from app.modules.common import ok
from app.modules.projects.utils import create_risk_reminder_if_needed, create_task_reminder_if_needed
from app.modules.templates.schemas import (
    ProjectSaveAsTemplatePayload,
    TemplateCreatePayload,
    TemplateGenerateProjectPayload,
    TemplateUpdatePayload,
)

router = APIRouter(prefix="/templates", tags=["templates"])


def serialize_template(item: Template) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "templateType": item.template_type,
        "scene": item.scene,
        "taskCount": len(item.tasks),
        "riskCount": len(item.risks),
        "recentUseCount": item.recent_use_count,
    }


@router.get("")
def list_templates(db: Session = Depends(get_db)) -> dict:
    templates = db.query(Template).all()
    return ok([serialize_template(item) for item in templates])


@router.get("/{template_id}")
def get_template_detail(template_id: int, db: Session = Depends(get_db)) -> dict:
    template = db.query(Template).filter(Template.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    return ok(
        {
            **serialize_template(template),
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "plannedContent": task.planned_content,
                    "defaultOwnerName": task.default_owner_name or "",
                    "offsetDays": task.offset_days,
                }
                for task in template.tasks
            ],
            "risks": [
                {
                    "id": risk.id,
                    "title": risk.title,
                    "level": risk.level,
                    "affectsMilestone": risk.affects_milestone,
                    "actionPlan": risk.action_plan,
                    "offsetDays": risk.offset_days,
                }
                for risk in template.risks
            ],
        }
    )


@router.post("")
def create_template(payload: TemplateCreatePayload, db: Session = Depends(get_db)) -> dict:
    template = Template(
        name=payload.name,
        template_type=payload.template_type,
        scene=payload.scene,
        task_count=len(payload.tasks),
        risk_count=len(payload.risks),
        recent_use_count=0,
    )
    db.add(template)
    db.flush()

    db.add_all(
        [
            TemplateTask(
                template_id=template.id,
                name=task.name,
                planned_content=task.planned_content,
                default_owner_name=task.default_owner_name,
                offset_days=task.offset_days,
            )
            for task in payload.tasks
        ]
    )
    db.add_all(
        [
            TemplateRisk(
                template_id=template.id,
                title=risk.title,
                level=risk.level,
                affects_milestone=risk.affects_milestone,
                action_plan=risk.action_plan,
                offset_days=risk.offset_days,
            )
            for risk in payload.risks
        ]
    )
    db.commit()
    db.refresh(template)
    return ok(serialize_template(template))


@router.put("/{template_id}")
def update_template(
    template_id: int,
    payload: TemplateUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    template = db.query(Template).filter(Template.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    template.name = payload.name
    template.template_type = payload.template_type
    template.scene = payload.scene
    template.task_count = len(payload.tasks)
    template.risk_count = len(payload.risks)
    db.add(template)
    db.flush()

    db.query(TemplateTask).filter(TemplateTask.template_id == template.id).delete()
    db.query(TemplateRisk).filter(TemplateRisk.template_id == template.id).delete()

    db.add_all(
        [
            TemplateTask(
                template_id=template.id,
                name=task.name,
                planned_content=task.planned_content,
                default_owner_name=task.default_owner_name,
                offset_days=task.offset_days,
            )
            for task in payload.tasks
        ]
    )
    db.add_all(
        [
            TemplateRisk(
                template_id=template.id,
                title=risk.title,
                level=risk.level,
                affects_milestone=risk.affects_milestone,
                action_plan=risk.action_plan,
                offset_days=risk.offset_days,
            )
            for risk in payload.risks
        ]
    )
    db.commit()
    db.refresh(template)
    return ok(serialize_template(template))


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)) -> dict:
    template = db.query(Template).filter(Template.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(template)
    db.commit()
    return ok({"id": template_id, "deleted": True})


@router.post("/{template_id}/generate-project")
def generate_project_from_template(
    template_id: int,
    payload: TemplateGenerateProjectPayload,
    db: Session = Depends(get_db),
) -> dict:
    template = db.query(Template).filter(Template.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    broker = db.query(Broker).filter(Broker.id == payload.broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    project = Project(
        broker_id=broker.id,
        name=payload.name,
        project_type=template.template_type,
        owner_name=payload.owner_name,
        planned_date=payload.planned_date,
        status=payload.status,
        progress_percent=0,
        description=payload.description or f"基于模板“{template.name}”生成",
    )


@router.post("/projects/{project_id}/save-as-template")
def save_project_as_template(
    project_id: int,
    payload: ProjectSaveAsTemplatePayload,
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    template = Template(
        name=payload.name,
        template_type=project.project_type,
        scene=payload.scene,
        task_count=len(project.tasks),
        risk_count=len(project.risks),
        recent_use_count=0,
    )
    db.add(template)
    db.flush()

    db.add_all(
        [
            TemplateTask(
                template_id=template.id,
                name=task.name,
                planned_content=task.planned_content,
                default_owner_name=task.owner_name,
                offset_days=0,
            )
            for task in project.tasks
        ]
    )
    db.add_all(
        [
            TemplateRisk(
                template_id=template.id,
                title=risk.title,
                level=risk.level,
                affects_milestone=risk.affects_milestone,
                action_plan=risk.action_plan,
                offset_days=0,
            )
            for risk in project.risks
        ]
    )
    db.commit()
    db.refresh(template)
    return ok(serialize_template(template))
    db.add(project)
    db.flush()

    for task_tpl in template.tasks:
        task = Task(
            project_id=project.id,
            name=task_tpl.name,
            owner_name=task_tpl.default_owner_name or payload.owner_name,
            planned_content=task_tpl.planned_content,
            planned_date=payload.planned_date + timedelta(days=task_tpl.offset_days),
            actual_action="",
            completion_result="",
            status="未开始",
        )
        db.add(task)
        db.flush()
        create_task_reminder_if_needed(db, project, task)

    for risk_tpl in template.risks:
        risk = Risk(
            project_id=project.id,
            title=risk_tpl.title,
            level=risk_tpl.level,
            affects_milestone=risk_tpl.affects_milestone,
            owner_name=payload.owner_name,
            planned_resolve_date=payload.planned_date + timedelta(days=risk_tpl.offset_days),
            status="待处理",
            action_plan=risk_tpl.action_plan,
        )
        db.add(risk)
        db.flush()
        create_risk_reminder_if_needed(db, project, risk)

    template.recent_use_count += 1
    db.add(template)
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
            "riskCount": len(project.risks),
            "overdueCount": len([task for task in project.tasks if task.status == "已逾期"]),
            "status": project.status,
        }
    )
