from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import Broker, Project, Reminder, Risk, Task
from app.db.session import get_db
from app.modules.common import ok

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly/preview")
def get_weekly_preview(
    broker_id: Optional[int] = None,
    owner_name: str = Query(default=""),
    db: Session = Depends(get_db),
) -> dict:
    broker_name = None
    if broker_id is not None:
        broker = db.query(Broker).filter(Broker.id == broker_id).first()
        if broker is not None:
            broker_name = broker.name

    task_query = db.query(Task).join(Project, Task.project_id == Project.id)
    risk_query = db.query(Risk).join(Project, Risk.project_id == Project.id)
    reminder_query = db.query(Reminder)

    if broker_id is not None:
        task_query = task_query.filter(Project.broker_id == broker_id)
        risk_query = risk_query.filter(Project.broker_id == broker_id)
        if broker_name is not None:
            reminder_query = reminder_query.filter(Reminder.broker_name == broker_name)

    if owner_name.strip():
        task_query = task_query.filter(Task.owner_name.like(f"%{owner_name.strip()}%"))
        risk_query = risk_query.filter(Risk.owner_name.like(f"%{owner_name.strip()}%"))

    completed = task_query.filter(Task.status == "已完成").limit(5).all()
    next_week = task_query.filter(Task.status.in_(["进行中", "待对方反馈", "未开始"])).limit(5).all()
    overdue = task_query.filter(Task.status == "已逾期").limit(5).all()
    risks = risk_query.filter(Risk.level == "高风险").limit(5).all()
    coordination = reminder_query.filter(Reminder.type.in_(["高风险", "临期"])).limit(5).all()

    scope_text = []
    if broker_name:
        scope_text.append(f"券商：{broker_name}")
    if owner_name.strip():
        scope_text.append(f"负责人：{owner_name.strip()}")
    scope_suffix = f"（{' / '.join(scope_text)}）" if scope_text else ""

    return ok(
        {
            "summary": f"本周共推进多个关键项目，重点关注逾期事项、高风险问题和下周升级窗口确认。{scope_suffix}",
            "completed": [f"{item.name}已完成。" for item in completed],
            "nextWeek": [f"{item.name}需要持续推进。" for item in next_week],
            "overdue": [f"{item.name}已逾期，需要优先处理。" for item in overdue],
            "risks": [f"{item.title}。{item.action_plan}" for item in risks],
            "coordination": [item.description for item in coordination],
        }
    )
