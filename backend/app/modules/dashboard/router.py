from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Broker, Project, Risk, Task
from app.db.session import get_db
from app.modules.common import ok
from app.modules.projects.utils import calculate_project_progress

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)) -> dict:
    total_brokers = db.query(Broker).count()
    active_projects = db.query(Project).filter(Project.status.in_(["执行中", "准备中"])).count()
    pending_tasks = db.query(Task).filter(Task.status.in_(["进行中", "待对方反馈", "未开始"])).count()
    overdue_tasks = db.query(Task).filter(Task.status == "已逾期").count()
    high_risk_count = db.query(Risk).filter(Risk.level == "高风险").count()

    return ok(
        {
            "totalBrokers": total_brokers,
            "activeProjects": active_projects,
            "pendingTasks": pending_tasks,
            "overdueTasks": overdue_tasks,
            "highRiskCount": high_risk_count,
            "summary": "当前重点是处理本周升级节点、条件单包逾期和环境未就绪问题。",
        }
    )


@router.get("/projects")
def get_projects(db: Session = Depends(get_db)) -> dict:
    projects = db.query(Project).join(Broker).all()
    result = []

    for project in projects:
        risk_count = len(project.risks)
        overdue_count = len([task for task in project.tasks if task.status == "已逾期"])
        result.append(
            {
                "id": project.id,
                "brokerId": project.broker.id,
                "brokerName": project.broker.name,
                "projectName": project.name,
                "projectType": project.project_type,
                "ownerName": project.owner_name,
                "plannedDate": project.planned_date.isoformat(),
                "progressPercent": calculate_project_progress(project),
                "riskCount": risk_count,
                "overdueCount": overdue_count,
                "status": project.status,
            }
        )

    return ok(result)
