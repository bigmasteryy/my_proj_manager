from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Project, Task
from app.db.session import get_db
from app.modules.common import ok
from app.modules.projects.utils import (
    close_reminders_for_item,
    create_task_reminder_if_needed,
    sync_project_progress,
)
from app.modules.tasks.schemas import TaskCreatePayload, TaskStatusUpdatePayload, TaskUpdatePayload

router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks")
def create_task(
    project_id: int,
    payload: TaskCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(
        project_id=project.id,
        name=payload.name,
        owner_name=payload.owner_name,
        planned_content=payload.planned_content,
        planned_date=payload.planned_date,
        actual_action=payload.actual_action,
        completion_result=payload.completion_result,
        status=payload.status,
    )
    db.add(task)
    db.flush()

    create_task_reminder_if_needed(db, project, task)
    db.refresh(project)
    sync_project_progress(db, project)
    db.commit()
    db.refresh(task)

    return ok(
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
    )


@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    payload: TaskUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    project = task.project
    close_reminders_for_item(db, project, task.name)

    task.name = payload.name
    task.owner_name = payload.owner_name
    task.planned_content = payload.planned_content
    task.planned_date = payload.planned_date
    task.actual_action = payload.actual_action
    task.completion_result = payload.completion_result
    task.status = payload.status
    db.add(task)

    if task.status != "已完成":
        create_task_reminder_if_needed(db, project, task)

    sync_project_progress(db, project)
    db.commit()
    db.refresh(task)

    return ok(
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
    )


@router.post("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    project = task.project
    task.status = payload.status
    if payload.actual_action is not None:
        task.actual_action = payload.actual_action
    if payload.completion_result is not None:
        task.completion_result = payload.completion_result
    elif payload.status == "已完成" and not task.completion_result:
        task.completion_result = "完成"

    db.add(task)

    if task.status == "已完成":
        close_reminders_for_item(db, project, task.name)
    else:
        create_task_reminder_if_needed(db, project, task)

    sync_project_progress(db, project)
    db.commit()
    db.refresh(task)

    return ok(
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
    )


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    project = task.project
    close_reminders_for_item(db, project, task.name)
    db.delete(task)
    sync_project_progress(db, project)
    db.commit()
    return ok({"id": task_id, "deleted": True})
