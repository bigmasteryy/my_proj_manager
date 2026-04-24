from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.db.models import Project, Reminder, Risk, Task


def calculate_project_progress(project: Project) -> int:
    total_tasks = len(project.tasks)
    if total_tasks == 0:
        return 0

    completed_tasks = len([task for task in project.tasks if task.status == "已完成"])
    return int((completed_tasks / total_tasks) * 100)


def sync_project_progress(session: Session, project: Project) -> None:
    project.progress_percent = calculate_project_progress(project)
    session.add(project)


def create_task_reminder_if_needed(session: Session, project: Project, task: Task) -> None:
    if task.status == "已完成":
        return

    reminder_type = None
    today = date.today()

    if task.planned_date < today:
        reminder_type = "逾期"
    elif task.planned_date >= today:
        delta_days = (task.planned_date - today).days
        if delta_days <= 3:
            reminder_type = "临期"

    if reminder_type is None:
        return

    exists = (
        session.query(Reminder)
        .filter(
            Reminder.type == reminder_type,
            Reminder.broker_name == project.broker.name,
            Reminder.project_name == project.name,
            Reminder.item_name == task.name,
            Reminder.status.in_(["待处理", "处理中"]),
        )
        .first()
    )
    if exists is not None:
        return

    session.add(
        Reminder(
            type=reminder_type,
            broker_name=project.broker.name,
            project_name=project.name,
            item_name=task.name,
            level="中风险" if reminder_type == "临期" else "高风险",
            deadline=task.planned_date,
            status="待处理",
            description=f"{task.name}需要关注，当前状态：{task.status}。",
        )
    )


def create_risk_reminder_if_needed(session: Session, project: Project, risk: Risk) -> None:
    if risk.level != "高风险" and not risk.affects_milestone:
        return

    exists = (
        session.query(Reminder)
        .filter(
            Reminder.type == "高风险",
            Reminder.broker_name == project.broker.name,
            Reminder.project_name == project.name,
            Reminder.item_name == risk.title,
            Reminder.status.in_(["待处理", "处理中"]),
        )
        .first()
    )
    if exists is not None:
        return

    session.add(
        Reminder(
            type="高风险",
            broker_name=project.broker.name,
            project_name=project.name,
            item_name=risk.title,
            level=risk.level,
            deadline=risk.planned_resolve_date,
            status="待处理",
            description=risk.action_plan,
        )
    )


def close_reminders_for_item(session: Session, project: Project, item_name: str) -> None:
    reminders = (
        session.query(Reminder)
        .filter(
            Reminder.broker_name == project.broker.name,
            Reminder.project_name == project.name,
            Reminder.item_name == item_name,
            Reminder.status.in_(["待处理", "处理中"]),
        )
        .all()
    )

    for reminder in reminders:
        reminder.status = "已处理"
        session.add(reminder)
