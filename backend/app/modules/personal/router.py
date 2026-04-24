from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import PersonalTask, User
from app.db.session import get_db
from app.modules.auth.deps import get_current_user
from app.modules.common import ok
from app.modules.personal.schemas import (
    PersonalTaskCompletePayload,
    PersonalTaskCreatePayload,
    PersonalTaskSortPayload,
    PersonalTaskUpdatePayload,
)

router = APIRouter(prefix="/personal", tags=["personal"])


def serialize_task(task: PersonalTask) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "category": task.category,
        "priority": task.priority,
        "note": task.note or "",
        "completionResult": task.completion_result or "",
        "plannedDate": task.planned_date.isoformat() if task.planned_date else "",
        "parentTaskId": task.parent_task_id,
        "parentTaskTitle": task.parent_task.title if task.parent_task else "",
        "childCount": len(task.subtasks),
        "completedChildCount": len([item for item in task.subtasks if item.status == "已完成"]),
        "status": task.status,
        "sortOrder": task.sort_order,
        "createdAt": task.created_at.strftime("%Y-%m-%d %H:%M"),
        "completedAt": task.completed_at.strftime("%Y-%m-%d %H:%M") if task.completed_at else "",
    }


def serialize_personal_risk(task: PersonalTask) -> dict:
    today = date.today()
    risk_type = "高优先级"
    if task.planned_date and task.planned_date < today:
        risk_type = "逾期"
    elif task.planned_date and (task.planned_date - today).days <= 3:
        risk_type = "临期"

    return {
        "id": task.id,
        "type": risk_type,
        "title": task.title,
        "category": task.category,
        "priority": task.priority,
        "plannedDate": task.planned_date.isoformat() if task.planned_date else "",
        "status": task.status,
        "note": task.note or "",
    }


@router.get("/tasks")
def list_personal_tasks(
    category: Optional[str] = None,
    parent_task_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    query = db.query(PersonalTask).filter(
        PersonalTask.user_id == current_user.id,
        PersonalTask.status != "已完成",
    )
    if category:
        query = query.filter(PersonalTask.category == category)
    if parent_task_id is not None:
        query = query.filter(PersonalTask.parent_task_id == parent_task_id)
    tasks = query.order_by(PersonalTask.sort_order.asc(), PersonalTask.created_at.desc()).all()
    return ok([serialize_task(task) for task in tasks])


@router.get("/history")
def list_personal_history(
    category: Optional[str] = None,
    parent_task_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    keyword: str = Query(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    query = db.query(PersonalTask).filter(
        PersonalTask.user_id == current_user.id,
        PersonalTask.status == "已完成",
    )
    if category:
        query = query.filter(PersonalTask.category == category)
    if parent_task_id is not None:
        query = query.filter(PersonalTask.parent_task_id == parent_task_id)
    if start_date is not None:
        query = query.filter(PersonalTask.completed_at >= datetime.combine(start_date, time.min))
    if end_date is not None:
        query = query.filter(PersonalTask.completed_at <= datetime.combine(end_date, time.max))
    if keyword.strip():
        fuzzy = f"%{keyword.strip()}%"
        query = query.filter(
            PersonalTask.title.like(fuzzy)
            | PersonalTask.note.like(fuzzy)
            | PersonalTask.completion_result.like(fuzzy)
        )
    tasks = query.order_by(PersonalTask.completed_at.desc()).all()
    return ok([serialize_task(task) for task in tasks])


@router.get("/risks")
def list_personal_risks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    today = date.today()
    tasks = (
        db.query(PersonalTask)
        .filter(
            PersonalTask.user_id == current_user.id,
            PersonalTask.status != "已完成",
        )
        .all()
    )

    risky_tasks = []
    for task in tasks:
        is_overdue = task.planned_date is not None and task.planned_date < today
        is_due_soon = task.planned_date is not None and 0 <= (task.planned_date - today).days <= 3
        is_high_priority = task.priority == "高"

        if is_overdue or is_due_soon or is_high_priority:
            risky_tasks.append(serialize_personal_risk(task))

    risky_tasks.sort(key=lambda item: (item["type"] != "逾期", item["priority"] != "高", item["plannedDate"]))
    return ok(risky_tasks)


@router.get("/reports/weekly")
def get_personal_weekly_report(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    today = date.today()
    completed_query = db.query(PersonalTask).filter(
        PersonalTask.user_id == current_user.id,
        PersonalTask.status == "已完成",
    )
    pending_query = db.query(PersonalTask).filter(
        PersonalTask.user_id == current_user.id,
        PersonalTask.status != "已完成",
    )

    if category:
        completed_query = completed_query.filter(PersonalTask.category == category)
        pending_query = pending_query.filter(PersonalTask.category == category)

    completed = completed_query.order_by(PersonalTask.completed_at.desc()).limit(5).all()
    pending = pending_query.order_by(PersonalTask.sort_order.asc(), PersonalTask.created_at.desc()).limit(5).all()
    overdue = [
        task
        for task in pending_query.all()
        if task.planned_date is not None and task.planned_date < today
    ][:5]
    risks = [
        task
        for task in pending_query.all()
        if task.priority == "高" or (task.planned_date is not None and task.planned_date < today)
    ][:5]

    scope_suffix = f"（{category}）" if category else ""

    return ok(
        {
            "summary": f"本周聚焦个人待办、长期事项推进和高优先级任务处理。{scope_suffix}",
            "completed": [
                f"{item.title}已完成：{item.completion_result or '已处理完成。'}"
                for item in completed
            ],
            "nextWeek": [f"{item.title}需要继续推进。" for item in pending],
            "overdue": [f"{item.title}已逾期，需要优先处理。" for item in overdue],
            "risks": [f"{item.title}：{item.note or '需重点关注。'}" for item in risks],
            "coordination": [item.note or f"{item.title}需要协调资源。" for item in pending[:3]],
        }
    )


@router.post("/tasks")
def create_personal_task(
    payload: PersonalTaskCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    task = PersonalTask(
        user_id=current_user.id,
        parent_task_id=payload.parent_task_id,
        title=payload.title,
        category=payload.category,
        priority=payload.priority,
        note=payload.note,
        planned_date=payload.planned_date,
        status="待办",
        sort_order=_next_sort_order(db, current_user.id, payload.category, payload.parent_task_id),
        created_at=datetime.now(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.put("/tasks/{task_id}")
def update_personal_task(
    task_id: int,
    payload: PersonalTaskUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    task = (
        db.query(PersonalTask)
        .filter(PersonalTask.id == task_id, PersonalTask.user_id == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Personal task not found")

    task.title = payload.title
    task.category = payload.category
    task.priority = payload.priority
    task.note = payload.note
    task.planned_date = payload.planned_date
    task.parent_task_id = payload.parent_task_id
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.post("/tasks/{task_id}/complete")
def complete_personal_task(
    task_id: int,
    payload: PersonalTaskCompletePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    task = (
        db.query(PersonalTask)
        .filter(PersonalTask.id == task_id, PersonalTask.user_id == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Personal task not found")

    task.status = "已完成"
    task.completion_result = payload.completion_result
    task.completed_at = datetime.now()
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.delete("/tasks/{task_id}")
def delete_personal_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    task = (
        db.query(PersonalTask)
        .filter(PersonalTask.id == task_id, PersonalTask.user_id == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Personal task not found")

    db.delete(task)
    db.commit()
    return ok({"id": task_id, "deleted": True})


@router.post("/tasks/sort")
def sort_personal_tasks(
    payload: PersonalTaskSortPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    for index, task_id in enumerate(payload.ordered_ids, start=1):
        task = (
            db.query(PersonalTask)
            .filter(PersonalTask.id == task_id, PersonalTask.user_id == current_user.id)
            .first()
        )
        if task is not None:
            task.sort_order = index
            db.add(task)

    db.commit()
    return ok({"updated": True})


@router.post("/tasks/reset-daily")
def reset_daily_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    tasks = (
        db.query(PersonalTask)
        .filter(
            PersonalTask.user_id == current_user.id,
            PersonalTask.category == "每日",
            PersonalTask.status != "已完成",
        )
        .all()
    )
    for task in tasks:
        task.status = "待办"
        task.completed_at = None
        db.add(task)

    db.commit()
    return ok({"count": len(tasks)})


def _next_sort_order(db: Session, user_id: int, category: str, parent_task_id: Optional[int]) -> int:
    last_item = (
        db.query(PersonalTask)
        .filter(
            PersonalTask.user_id == user_id,
            PersonalTask.category == category,
            PersonalTask.parent_task_id == parent_task_id,
            PersonalTask.status != "已完成",
        )
        .order_by(PersonalTask.sort_order.desc())
        .first()
    )
    if last_item is None:
        return 1
    return int(last_item.sort_order) + 1
