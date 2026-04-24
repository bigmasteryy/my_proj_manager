from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Broker,
    ProgressBrokerProjectInstance,
    ProgressItemTemplate,
    ProgressItemValue,
    ProgressLog,
    ProgressProjectTemplate,
    ProgressRisk,
)
from app.db.session import get_db
from app.modules.common import ok
from app.modules.progress.schemas import (
    ProgressLogCreatePayload,
    ProgressRiskCreatePayload,
    ProgressRiskUpdatePayload,
    ProgressValueUpdatePayload,
)

router = APIRouter(prefix="/progress", tags=["progress"])

STATUS_PROGRESS_MAP = {
    "不支持": 0,
    "未开始": 0,
    "推进中": 50,
    "就绪": 80,
    "已支持": 100,
    "已完成": 100,
    "阻塞": 30,
}


def _calculate_item_percent(item_type: str, status_value: Optional[str], current_num: Optional[int], target_num: Optional[int], is_na: bool) -> int:
    if is_na:
        return 0
    if item_type == "status":
        return STATUS_PROGRESS_MAP.get(status_value or "未开始", 0)
    if item_type == "number_progress":
        if not target_num or target_num <= 0:
            return 0
        return max(0, min(100, round((current_num or 0) / target_num * 100)))
    return 0


def _refresh_instance(instance: ProgressBrokerProjectInstance) -> None:
    valid_values = [item for item in instance.values if not item.is_na]
    total_weight = 0
    weighted_score = 0
    for value in valid_values:
        weight = value.item_template.weight
        total_weight += weight
        weighted_score += weight * value.calculated_percent

    progress_percent = round(weighted_score / total_weight) if total_weight else 0
    instance.progress_percent = progress_percent
    instance.risk_count = len(instance.risks)
    instance.milestone_count = len([item for item in instance.logs if item.is_milestone])
    latest_candidates = [item.updated_at for item in instance.values if item.updated_at] + [item.log_date for item in instance.logs]
    instance.latest_update_at = max(latest_candidates) if latest_candidates else instance.latest_update_at

    if instance.overall_conclusion == "不支持":
        instance.overall_status = "未开始"
    elif progress_percent >= 100:
        instance.overall_status = "已完成"
    elif progress_percent > 0:
        instance.overall_status = "推进中"
    else:
        instance.overall_status = "未开始"

    instance.updated_at = datetime.now()


def _serialize_column(item: ProgressItemTemplate) -> dict:
    return {
        "id": item.id,
        "key": item.item_key,
        "label": item.item_label,
        "groupKey": item.group_key or "",
        "groupLabel": item.group_label or "",
        "type": item.item_type,
        "weight": item.weight,
        "allowNa": item.allow_na,
        "sortNo": item.sort_no,
    }


def _serialize_value(value: Optional[ProgressItemValue], item: ProgressItemTemplate) -> dict:
    if value is None:
        return {
            "type": item.item_type,
            "statusValue": "",
            "currentNum": None,
            "targetNum": None,
            "isNa": False,
            "remark": "",
            "calculatedPercent": 0,
        }
    return {
        "type": item.item_type,
        "statusValue": value.status_value or "",
        "currentNum": value.current_num,
        "targetNum": value.target_num,
        "isNa": value.is_na,
        "remark": value.remark or "",
        "calculatedPercent": value.calculated_percent,
    }


def _serialize_instance_row(instance: ProgressBrokerProjectInstance, items: list[ProgressItemTemplate]) -> dict:
    value_map = {value.item_template_id: value for value in instance.values}
    return {
        "instanceId": instance.id,
        "brokerId": instance.broker_id,
        "brokerName": instance.broker.name,
        "inputMode": instance.input_mode,
        "overallConclusion": instance.overall_conclusion or "",
        "progressPercent": instance.progress_percent,
        "status": instance.overall_status,
        "latestUpdateAt": instance.latest_update_at.strftime("%Y-%m-%d") if instance.latest_update_at else "",
        "milestoneCount": instance.milestone_count,
        "riskCount": instance.risk_count,
        "values": {
            item.item_key: _serialize_value(value_map.get(item.id), item)
            for item in items
        },
    }


@router.get("/projects")
def list_progress_projects(db: Session = Depends(get_db)) -> dict:
    templates = (
        db.query(ProgressProjectTemplate)
        .options(joinedload(ProgressProjectTemplate.instances))
        .order_by(ProgressProjectTemplate.sort_no.asc(), ProgressProjectTemplate.id.asc())
        .all()
    )

    rows = []
    for template in templates:
        instances = template.instances
        completed_count = len([item for item in instances if item.overall_status == "已完成"])
        in_progress_count = len([item for item in instances if item.overall_status == "推进中"])
        not_started_count = len([item for item in instances if item.overall_status == "未开始"])
        avg_progress = round(sum(item.progress_percent for item in instances) / len(instances)) if instances else 0
        risk_count = sum(item.risk_count for item in instances)
        rows.append(
            {
                "projectTemplateId": template.id,
                "projectCode": template.code,
                "projectName": template.name,
                "brokerCount": len(instances),
                "completedCount": completed_count,
                "inProgressCount": in_progress_count,
                "notStartedCount": not_started_count,
                "avgProgress": avg_progress,
                "riskCount": risk_count,
            }
        )
    return ok(rows)


@router.get("/projects/{project_template_id}/matrix")
def get_progress_matrix(project_template_id: int, db: Session = Depends(get_db)) -> dict:
    template = (
        db.query(ProgressProjectTemplate)
        .options(
            joinedload(ProgressProjectTemplate.items),
            joinedload(ProgressProjectTemplate.instances)
            .joinedload(ProgressBrokerProjectInstance.broker),
            joinedload(ProgressProjectTemplate.instances)
            .joinedload(ProgressBrokerProjectInstance.values)
            .joinedload(ProgressItemValue.item_template),
        )
        .filter(ProgressProjectTemplate.id == project_template_id)
        .first()
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Progress project template not found")

    items = sorted(template.items, key=lambda item: item.sort_no)
    rows = [_serialize_instance_row(instance, items) for instance in sorted(template.instances, key=lambda item: item.broker.name)]
    return ok(
        {
            "project": {
                "id": template.id,
                "code": template.code,
                "name": template.name,
                "description": template.description or "",
            },
            "summary": {
                "brokerCount": len(template.instances),
                "completedCount": len([item for item in template.instances if item.overall_status == "已完成"]),
                "inProgressCount": len([item for item in template.instances if item.overall_status == "推进中"]),
                "notStartedCount": len([item for item in template.instances if item.overall_status == "未开始"]),
                "avgProgress": round(sum(item.progress_percent for item in template.instances) / len(template.instances)) if template.instances else 0,
                "riskCount": sum(item.risk_count for item in template.instances),
            },
            "fixedColumns": [
                {"key": "brokerName", "label": "券商"},
                {"key": "inputMode", "label": "录入模式"},
                {"key": "overallConclusion", "label": "总体结论"},
                {"key": "progressPercent", "label": "总进度"},
                {"key": "status", "label": "当前状态"},
                {"key": "latestUpdateAt", "label": "最近更新"},
                {"key": "milestoneCount", "label": "里程碑"},
                {"key": "riskCount", "label": "风险"},
            ],
            "dynamicColumns": [_serialize_column(item) for item in items],
            "rows": rows,
        }
    )


@router.get("/brokers")
def list_progress_brokers(db: Session = Depends(get_db)) -> dict:
    brokers = (
        db.query(Broker)
        .join(ProgressBrokerProjectInstance, ProgressBrokerProjectInstance.broker_id == Broker.id)
        .distinct()
        .order_by(Broker.name.asc())
        .all()
    )
    return ok([{"id": broker.id, "name": broker.name} for broker in brokers])


@router.get("/brokers/{broker_id}/projects")
def get_broker_progress_projects(broker_id: int, db: Session = Depends(get_db)) -> dict:
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    instances = (
        db.query(ProgressBrokerProjectInstance)
        .options(joinedload(ProgressBrokerProjectInstance.project_template))
        .filter(ProgressBrokerProjectInstance.broker_id == broker_id)
        .order_by(ProgressBrokerProjectInstance.project_template_id.asc())
        .all()
    )

    return ok(
        {
            "brokerId": broker.id,
            "brokerName": broker.name,
            "projects": [
                {
                    "instanceId": instance.id,
                    "projectTemplateId": instance.project_template_id,
                    "projectName": instance.project_template.name,
                    "progressPercent": instance.progress_percent,
                    "status": instance.overall_status,
                    "latestUpdateAt": instance.latest_update_at.strftime("%Y-%m-%d") if instance.latest_update_at else "",
                    "riskCount": instance.risk_count,
                    "milestoneCount": instance.milestone_count,
                }
                for instance in instances
            ],
        }
    )


@router.get("/instances/{instance_id}")
def get_progress_instance_detail(instance_id: int, db: Session = Depends(get_db)) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.project_template).joinedload(ProgressProjectTemplate.items),
            joinedload(ProgressBrokerProjectInstance.broker),
            joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template),
            joinedload(ProgressBrokerProjectInstance.logs).joinedload(ProgressLog.item_template),
            joinedload(ProgressBrokerProjectInstance.risks),
        )
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    items = sorted(instance.project_template.items, key=lambda item: item.sort_no)
    value_map = {value.item_template_id: value for value in instance.values}
    return ok(
        {
            "instance": {
                "id": instance.id,
                "projectTemplateId": instance.project_template_id,
                "projectName": instance.project_template.name,
                "brokerId": instance.broker_id,
                "brokerName": instance.broker.name,
                "inputMode": instance.input_mode,
                "overallConclusion": instance.overall_conclusion or "",
                "progressPercent": instance.progress_percent,
                "status": instance.overall_status,
                "latestUpdateAt": instance.latest_update_at.strftime("%Y-%m-%d") if instance.latest_update_at else "",
                "riskCount": instance.risk_count,
                "milestoneCount": instance.milestone_count,
                "remark": instance.remark or "",
            },
            "progressItems": [
                {
                    "itemTemplateId": item.id,
                    "itemKey": item.item_key,
                    "itemLabel": item.item_label,
                    "groupKey": item.group_key or "",
                    "groupLabel": item.group_label or "",
                    "type": item.item_type,
                    "weight": item.weight,
                    "allowNa": item.allow_na,
                    "value": _serialize_value(value_map.get(item.id), item),
                }
                for item in items
            ],
            "logs": [
                {
                    "id": log.id,
                    "logDate": log.log_date.strftime("%Y-%m-%d"),
                    "itemTemplateId": log.item_template_id,
                    "itemLabel": log.item_template.item_label if log.item_template else "",
                    "content": log.content,
                    "progressDelta": log.progress_delta,
                    "progressAfter": log.progress_after,
                    "isMilestone": log.is_milestone,
                    "remark": log.remark or "",
                }
                for log in sorted(instance.logs, key=lambda item: item.log_date, reverse=True)
            ],
            "risks": [
                {
                    "id": risk.id,
                    "title": risk.title,
                    "description": risk.description or "",
                    "impactDesc": risk.impact_desc or "",
                    "level": risk.level,
                    "ownerName": risk.owner_name or "",
                    "plannedResolveDate": risk.planned_resolve_date.isoformat() if risk.planned_resolve_date else "",
                    "status": risk.status,
                    "remark": risk.remark or "",
                }
                for risk in sorted(instance.risks, key=lambda item: (item.level != "高", item.title))
            ],
        }
    )


@router.get("/logs")
def list_progress_logs(
    project_template_id: Optional[int] = None,
    broker_id: Optional[int] = None,
    instance_id: Optional[int] = None,
    keyword: str = Query(default=""),
    only_milestone: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    query = (
        db.query(ProgressLog)
        .join(ProgressBrokerProjectInstance, ProgressBrokerProjectInstance.id == ProgressLog.broker_project_instance_id)
        .join(ProgressProjectTemplate, ProgressProjectTemplate.id == ProgressBrokerProjectInstance.project_template_id)
        .join(Broker, Broker.id == ProgressBrokerProjectInstance.broker_id)
        .options(
            joinedload(ProgressLog.instance).joinedload(ProgressBrokerProjectInstance.project_template),
            joinedload(ProgressLog.instance).joinedload(ProgressBrokerProjectInstance.broker),
            joinedload(ProgressLog.item_template),
        )
    )
    if project_template_id is not None:
        query = query.filter(ProgressBrokerProjectInstance.project_template_id == project_template_id)
    if broker_id is not None:
        query = query.filter(ProgressBrokerProjectInstance.broker_id == broker_id)
    if instance_id is not None:
        query = query.filter(ProgressLog.broker_project_instance_id == instance_id)
    if only_milestone:
        query = query.filter(ProgressLog.is_milestone.is_(True))
    if keyword.strip():
        fuzzy = f"%{keyword.strip()}%"
        query = query.filter(ProgressLog.content.like(fuzzy) | ProgressLog.remark.like(fuzzy))

    logs = query.order_by(ProgressLog.log_date.desc()).all()
    return ok(
        [
            {
                "id": log.id,
                "projectName": log.instance.project_template.name,
                "brokerName": log.instance.broker.name,
                "logDate": log.log_date.strftime("%Y-%m-%d"),
                "itemLabel": log.item_template.item_label if log.item_template else "",
                "content": log.content,
                "progressDelta": log.progress_delta,
                "progressAfter": log.progress_after,
                "isMilestone": log.is_milestone,
                "remark": log.remark or "",
            }
            for log in logs
        ]
    )


@router.get("/risks")
def list_progress_risks(
    project_template_id: Optional[int] = None,
    broker_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    query = (
        db.query(ProgressRisk)
        .join(ProgressBrokerProjectInstance, ProgressBrokerProjectInstance.id == ProgressRisk.broker_project_instance_id)
        .options(
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.project_template),
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.broker),
        )
    )
    if project_template_id is not None:
        query = query.filter(ProgressBrokerProjectInstance.project_template_id == project_template_id)
    if broker_id is not None:
        query = query.filter(ProgressBrokerProjectInstance.broker_id == broker_id)
    if status:
        query = query.filter(ProgressRisk.status == status)

    risks = query.order_by(ProgressRisk.level.asc(), ProgressRisk.updated_at.desc()).all()
    return ok(
        [
            {
                "id": risk.id,
                "projectName": risk.instance.project_template.name,
                "brokerName": risk.instance.broker.name,
                "title": risk.title,
                "description": risk.description or "",
                "impactDesc": risk.impact_desc or "",
                "level": risk.level,
                "ownerName": risk.owner_name or "",
                "plannedResolveDate": risk.planned_resolve_date.isoformat() if risk.planned_resolve_date else "",
                "status": risk.status,
                "remark": risk.remark or "",
            }
            for risk in risks
        ]
    )


@router.get("/reports/weekly")
def get_progress_weekly_report(project_template_id: Optional[int] = None, db: Session = Depends(get_db)) -> dict:
    template_query = db.query(ProgressProjectTemplate)
    if project_template_id is not None:
        template_query = template_query.filter(ProgressProjectTemplate.id == project_template_id)
    templates = template_query.options(joinedload(ProgressProjectTemplate.instances)).all()

    completed = []
    next_week = []
    risks = []
    overdue = []
    coordination = []
    for template in templates:
        for instance in template.instances:
            if instance.progress_percent >= 100:
                completed.append(f"{instance.broker.name}：{template.name}已完成")
            elif instance.progress_percent > 0:
                next_week.append(f"{instance.broker.name}：继续推进{template.name}")
            if instance.risk_count:
                risks.append(f"{instance.broker.name}：{template.name}有{instance.risk_count}项风险")
            if instance.overall_status == "推进中" and (instance.latest_update_at is None):
                overdue.append(f"{instance.broker.name}：{template.name}暂无进展更新")
            if instance.overall_conclusion in {"不支持", "推进中"}:
                coordination.append(f"{instance.broker.name}：{template.name}需持续协调推进")

    project_name = templates[0].name if project_template_id and templates else "重点项目"
    return ok(
        {
            "summary": f"本周围绕{project_name}查看多家券商推进情况、关键里程碑和风险阻塞。",
            "completed": completed[:10],
            "nextWeek": next_week[:10],
            "overdue": overdue[:10],
            "risks": risks[:10],
            "coordination": coordination[:10],
        }
    )


@router.post("/instances/{instance_id}/items/{item_template_id}/update")
def update_progress_item_value(
    instance_id: int,
    item_template_id: int,
    payload: ProgressValueUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template),
            joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressBrokerProjectInstance.risks),
        )
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    item_template = (
        db.query(ProgressItemTemplate)
        .filter(ProgressItemTemplate.id == item_template_id, ProgressItemTemplate.project_template_id == instance.project_template_id)
        .first()
    )
    if item_template is None:
        raise HTTPException(status_code=404, detail="Progress item template not found")

    value = next((item for item in instance.values if item.item_template_id == item_template_id), None)
    if value is None:
        value = ProgressItemValue(
            broker_project_instance_id=instance_id,
            item_template_id=item_template_id,
            updated_at=datetime.now(),
        )
        db.add(value)
        db.flush()
        instance.values.append(value)

    value.status_value = payload.status_value
    value.current_num = payload.current_num
    value.target_num = payload.target_num
    value.bool_value = payload.bool_value
    value.text_value = payload.text_value
    value.is_na = payload.is_na
    value.remark = payload.remark
    value.calculated_percent = _calculate_item_percent(item_template.item_type, payload.status_value, payload.current_num, payload.target_num, payload.is_na)
    value.updated_at = datetime.now()

    _refresh_instance(instance)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return ok({"instanceId": instance.id, "progressPercent": instance.progress_percent})


@router.post("/instances/{instance_id}/logs")
def create_progress_log(instance_id: int, payload: ProgressLogCreatePayload, db: Session = Depends(get_db)) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(joinedload(ProgressBrokerProjectInstance.logs), joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template), joinedload(ProgressBrokerProjectInstance.risks))
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    log = ProgressLog(
        broker_project_instance_id=instance_id,
        item_template_id=payload.item_template_id,
        log_date=payload.log_date,
        content=payload.content,
        progress_delta=payload.progress_delta,
        progress_after=payload.progress_after,
        is_milestone=payload.is_milestone,
        remark=payload.remark,
        created_by="系统管理员",
        created_at=datetime.now(),
    )
    db.add(log)
    db.flush()
    instance.logs.append(log)
    _refresh_instance(instance)
    db.add(instance)
    db.commit()
    return ok({"id": log.id})


@router.post("/instances/{instance_id}/risks")
def create_progress_risk(instance_id: int, payload: ProgressRiskCreatePayload, db: Session = Depends(get_db)) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(joinedload(ProgressBrokerProjectInstance.risks), joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template), joinedload(ProgressBrokerProjectInstance.logs))
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    risk = ProgressRisk(
        broker_project_instance_id=instance_id,
        title=payload.title,
        description=payload.description,
        impact_desc=payload.impact_desc,
        level=payload.level,
        owner_name=payload.owner_name,
        planned_resolve_date=payload.planned_resolve_date,
        status=payload.status,
        remark=payload.remark,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(risk)
    db.flush()
    instance.risks.append(risk)
    _refresh_instance(instance)
    db.add(instance)
    db.commit()
    return ok({"id": risk.id})


@router.put("/risks/{risk_id}")
def update_progress_risk(risk_id: int, payload: ProgressRiskUpdatePayload, db: Session = Depends(get_db)) -> dict:
    risk = (
        db.query(ProgressRisk)
        .options(
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.risks),
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template),
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.logs),
        )
        .filter(ProgressRisk.id == risk_id)
        .first()
    )
    if risk is None:
        raise HTTPException(status_code=404, detail="Progress risk not found")

    risk.title = payload.title
    risk.description = payload.description
    risk.impact_desc = payload.impact_desc
    risk.level = payload.level
    risk.owner_name = payload.owner_name
    risk.planned_resolve_date = payload.planned_resolve_date
    risk.status = payload.status
    risk.remark = payload.remark
    risk.updated_at = datetime.now()

    _refresh_instance(risk.instance)
    db.add(risk.instance)
    db.commit()
    return ok({"id": risk.id})
