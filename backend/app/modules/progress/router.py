from __future__ import annotations

from datetime import datetime
from typing import Optional
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import (
    Broker,
    ProgressBrokerProjectInstance,
    ProgressItemTemplate,
    ProgressItemValue,
    ProgressLog,
    ProgressProjectTemplate,
    ProgressRisk,
    ProgressStage2GroupTemplate,
    ProgressStage2StepInstance,
    ProgressStage2StepTemplate,
)
from app.db.session import get_db
from app.modules.common import ok
from app.modules.progress.schemas import (
    ProgressLogCreatePayload,
    ProgressLogUpdatePayload,
    ProgressItemTemplateCreatePayload,
    ProgressProjectBrokerAddPayload,
    ProgressProjectCreatePayload,
    ProgressRiskCreatePayload,
    ProgressRiskUpdatePayload,
    ProgressStage2StepCreatePayload,
    ProgressStage2StepMovePayload,
    ProgressStage2StepUpdatePayload,
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


def _normalize_status_value(status_value: Optional[str]) -> Optional[str]:
    if status_value is None:
        return None
    normalized = status_value.strip()
    if not normalized:
        return None
    return normalized if normalized in STATUS_PROGRESS_MAP else None


def _format_progress_value(item_type: str, status_value: Optional[str], current_num: Optional[int], target_num: Optional[int], bool_value: Optional[bool], text_value: Optional[str], is_na: bool) -> str:
    if is_na:
        return "不适用"
    if item_type == "status":
        return _normalize_status_value(status_value) or "未开始"
    if item_type == "number_progress":
        if current_num is None and target_num is None:
            return "-"
        return f"{current_num or 0}/{target_num or 0}"
    if item_type == "boolean":
        if bool_value is None:
            return "-"
        return "是" if bool_value else "否"
    return text_value or "-"


def _build_auto_log_content(item_template: ProgressItemTemplate, before_text: str, after_text: str) -> str:
    return f"{item_template.item_label} 更新：{before_text} -> {after_text}"


def _build_stage2_auto_log_content(step_template: ProgressStage2StepTemplate, before_status: str, after_status: str) -> str:
    return f"阶段2 步骤 {step_template.step_no_display} {step_template.step_name} 状态更新：{before_status} -> {after_status}"


def _normalize_key(raw_value: Optional[str], fallback_prefix: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", (raw_value or "").strip().lower()).strip("_")
    if normalized:
        return normalized
    return f"{fallback_prefix}_{int(datetime.now().timestamp())}"


def _build_unique_project_code(db: Session, raw_code: Optional[str], name: str) -> str:
    base_code = _normalize_key(raw_code or name, "progress_project")
    candidate = base_code
    suffix = 2
    while db.query(ProgressProjectTemplate).filter(ProgressProjectTemplate.code == candidate).first():
        candidate = f"{base_code}_{suffix}"
        suffix += 1
    return candidate


def _build_unique_item_key(project_template_id: int, raw_key: Optional[str], item_label: str, db: Session) -> str:
    base_key = _normalize_key(raw_key or item_label, "progress_item")
    candidate = base_key
    suffix = 2
    while (
        db.query(ProgressItemTemplate)
        .filter(
            ProgressItemTemplate.project_template_id == project_template_id,
            ProgressItemTemplate.item_key == candidate,
        )
        .first()
    ):
        candidate = f"{base_key}_{suffix}"
        suffix += 1
    return candidate


def _create_default_value(instance_id: int, item_template: ProgressItemTemplate) -> ProgressItemValue:
    return ProgressItemValue(
        broker_project_instance_id=instance_id,
        item_template_id=item_template.id,
        status_value="未开始" if item_template.item_type == "status" else None,
        current_num=None,
        target_num=None,
        bool_value=None,
        text_value=None,
        is_na=False,
        calculated_percent=0,
        remark=None,
        updated_at=datetime.now(),
    )


def _create_stage2_step_instances(instance: ProgressBrokerProjectInstance, db: Session) -> None:
    step_templates = (
        db.query(ProgressStage2StepTemplate)
        .filter(ProgressStage2StepTemplate.project_template_id == instance.project_template_id)
        .order_by(ProgressStage2StepTemplate.sort_no.asc(), ProgressStage2StepTemplate.id.asc())
        .all()
    )
    if not step_templates:
        return

    existing_template_ids = {item.step_template_id for item in instance.stage2_step_instances}
    new_steps = []
    for step_template in step_templates:
        if step_template.id in existing_template_ids:
            continue
        new_steps.append(
            ProgressStage2StepInstance(
                broker_project_instance_id=instance.id,
                step_template_id=step_template.id,
                owner_actual=None,
                status="未开始",
                remark=None,
                blocker_reason=None,
                started_at=None,
                finished_at=None,
                updated_at=datetime.now(),
            )
        )
    if new_steps:
        db.add_all(new_steps)


def _ensure_stage2_default_group(project_template_id: int, db: Session) -> ProgressStage2GroupTemplate:
    group = (
        db.query(ProgressStage2GroupTemplate)
        .filter(ProgressStage2GroupTemplate.project_template_id == project_template_id)
        .order_by(ProgressStage2GroupTemplate.sort_no.asc(), ProgressStage2GroupTemplate.id.asc())
        .first()
    )
    if group is not None:
        return group
    group = ProgressStage2GroupTemplate(
        project_template_id=project_template_id,
        group_code="all_steps",
        group_name="步骤清单",
        sort_no=1,
        remark=None,
    )
    db.add(group)
    db.flush()
    return group


def _split_dependency_codes(raw_codes: Optional[str]) -> list[str]:
    if not raw_codes:
        return []
    return [item.strip() for item in raw_codes.split(",") if item.strip()]


def _stage2_effective_status(step_instance: ProgressStage2StepInstance, completed_step_codes: set[str]) -> str:
    if step_instance.status in {"已完成", "进行中", "阻塞", "不适用", "已跳过"}:
        return step_instance.status
    dependency_codes = _split_dependency_codes(step_instance.step_template.dependency_step_codes)
    if dependency_codes and not all(code in completed_step_codes for code in dependency_codes):
        return "未开始"
    return "可开始" if step_instance.status == "未开始" else step_instance.status


def _build_stage2_summary(instance: ProgressBrokerProjectInstance) -> dict:
    steps = sorted(
        instance.stage2_step_instances,
        key=lambda item: (item.step_template.group_template.sort_no, item.step_template.sort_no, item.step_template.id),
    )
    required_steps = [item for item in steps if not item.step_template.is_optional and item.status not in {"不适用", "已跳过"}]
    completed_step_codes = {item.step_template.step_code for item in steps if item.status == "已完成"}
    blocked_steps = [item for item in steps if item.status == "阻塞"]
    current_step = None
    if blocked_steps:
        current_step = blocked_steps[0]
    else:
        for item in steps:
            effective_status = _stage2_effective_status(item, completed_step_codes)
            if effective_status not in {"已完成", "不适用", "已跳过"}:
                current_step = item
                break

    completed_required_count = len([item for item in required_steps if item.status == "已完成"])
    total_required_count = len(required_steps)
    progress_percent = round((completed_required_count / total_required_count) * 100) if total_required_count else 0

    if blocked_steps:
        stage_status = "阻塞"
    elif current_step is None and total_required_count > 0:
        stage_status = "已完成"
    elif completed_required_count > 0:
        stage_status = "推进中"
    else:
        stage_status = "未开始"

    return {
        "status": stage_status,
        "completedCount": completed_required_count,
        "totalCount": total_required_count,
        "progressPercent": progress_percent,
        "blockedCount": len(blocked_steps),
        "currentStepCode": current_step.step_template.step_code if current_step else "",
        "currentStepNo": current_step.step_template.step_no_display if current_step else "",
        "currentStepName": current_step.step_template.step_name if current_step else "",
        "currentStepOwner": current_step.owner_actual or current_step.step_template.owners_default or "" if current_step else "",
    }


def _serialize_stage2_groups(instance: ProgressBrokerProjectInstance) -> list[dict]:
    group_order = {}
    for item in instance.project_template.stage2_groups:
        group_order[item.id] = item.sort_no

    steps = sorted(
        instance.stage2_step_instances,
        key=lambda item: (group_order.get(item.step_template.group_template_id, 0), item.step_template.sort_no, item.step_template.id),
    )
    completed_step_codes = {item.step_template.step_code for item in steps if item.status == "已完成"}
    grouped: dict[str, dict] = {}

    for step in steps:
        group_code = step.step_template.group_template.group_code
        group_name = step.step_template.group_template.group_name
        group = grouped.setdefault(
            group_code,
            {
                "groupCode": group_code,
                "groupName": group_name,
                "completedCount": 0,
                "totalCount": 0,
                "steps": [],
            },
        )
        effective_status = _stage2_effective_status(step, completed_step_codes)
        if not step.step_template.is_optional and step.status not in {"不适用", "已跳过"}:
            group["totalCount"] += 1
            if step.status == "已完成":
                group["completedCount"] += 1

        group["steps"].append(
            {
                "stepInstanceId": step.id,
                "stepCode": step.step_template.step_code,
                "stepNoDisplay": step.step_template.step_no_display,
                "stepName": step.step_template.step_name,
                "ownersDefault": step.step_template.owners_default or "",
                "ownerActual": step.owner_actual or "",
                "status": step.status,
                "effectiveStatus": effective_status,
                "isOptional": step.step_template.is_optional,
                "isLastStep": step.step_template.is_last_step,
                "applicableRule": step.step_template.applicable_rule or "",
                "dependencyStepCodes": _split_dependency_codes(step.step_template.dependency_step_codes),
                "remarkTemplate": step.step_template.remark_template or "",
                "remark": step.remark or "",
                "blockerReason": step.blocker_reason or "",
                "startedAt": step.started_at.strftime("%Y-%m-%d") if step.started_at else "",
                "finishedAt": step.finished_at.strftime("%Y-%m-%d") if step.finished_at else "",
            }
        )

    return list(grouped.values())


def _build_stage2_summary_simple(instance: ProgressBrokerProjectInstance) -> dict:
    steps = sorted(
        instance.stage2_step_instances,
        key=lambda item: (item.step_template.sort_no, item.step_template.id),
    )
    required_steps = [item for item in steps if not item.step_template.is_optional and item.status not in {"不适用", "已跳过"}]
    blocked_steps = [item for item in steps if item.status == "阻塞"]
    current_step = None
    current_step_index = None
    if blocked_steps:
        current_step = blocked_steps[0]
        current_step_index = next((index for index, item in enumerate(steps, start=1) if item.id == current_step.id), None)
    else:
        for index, item in enumerate(steps, start=1):
            if item.status not in {"已完成", "不适用", "已跳过"}:
                current_step = item
                current_step_index = index
                break

    completed_required_count = len([item for item in required_steps if item.status == "已完成"])
    total_required_count = len(required_steps)
    progress_percent = round((completed_required_count / total_required_count) * 100) if total_required_count else 0

    if blocked_steps:
        stage_status = "阻塞"
    elif current_step is None and total_required_count > 0:
        stage_status = "已完成"
    elif completed_required_count > 0:
        stage_status = "推进中"
    else:
        stage_status = "未开始"

    return {
        "status": stage_status,
        "completedCount": completed_required_count,
        "totalCount": total_required_count,
        "progressPercent": progress_percent,
        "blockedCount": len(blocked_steps),
        "currentStepCode": current_step.step_template.step_code if current_step else "",
        "currentStepNo": str(current_step_index) if current_step_index is not None else "",
        "currentStepName": current_step.step_template.step_name if current_step else "",
        "currentStepOwner": current_step.owner_actual or current_step.step_template.owners_default or "" if current_step else "",
    }


def _serialize_stage2_steps_flat(instance: ProgressBrokerProjectInstance) -> list[dict]:
    steps = sorted(
        instance.stage2_step_instances,
        key=lambda item: (item.step_template.sort_no, item.step_template.id),
    )
    group = {
        "groupCode": "all_steps",
        "groupName": "步骤清单",
        "completedCount": 0,
        "totalCount": 0,
        "steps": [],
    }
    for index, step in enumerate(steps, start=1):
        if not step.step_template.is_optional and step.status not in {"不适用", "已跳过"}:
            group["totalCount"] += 1
            if step.status == "已完成":
                group["completedCount"] += 1
        group["steps"].append(
            {
                "stepInstanceId": step.id,
                "stepCode": step.step_template.step_code,
                "stepNoDisplay": str(index),
                "stepName": step.step_template.step_name,
                "ownersDefault": step.step_template.owners_default or "",
                "ownerActual": step.owner_actual or "",
                "status": step.status,
                "effectiveStatus": step.status,
                "isOptional": step.step_template.is_optional,
                "isLastStep": step.step_template.is_last_step,
                "applicableRule": "",
                "dependencyStepCodes": [],
                "remarkTemplate": step.step_template.remark_template or "",
                "remark": step.remark or "",
                "blockerReason": step.blocker_reason or "",
                "startedAt": step.started_at.strftime("%Y-%m-%d") if step.started_at else "",
                "finishedAt": step.finished_at.strftime("%Y-%m-%d") if step.finished_at else "",
            }
        )
    return [group]


def _calculate_item_percent(item_type: str, status_value: Optional[str], current_num: Optional[int], target_num: Optional[int], is_na: bool) -> int:
    if is_na:
        return 0
    if item_type == "status":
        return STATUS_PROGRESS_MAP.get(_normalize_status_value(status_value) or "未开始", 0)
    if item_type == "number_progress":
        if not target_num or target_num <= 0:
            return 0
        return max(0, min(100, round((current_num or 0) / target_num * 100)))
    return 0


def _refresh_instance(instance: ProgressBrokerProjectInstance) -> None:
    valid_values = [item for item in instance.values if not item.is_na and item.item_template is not None]
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
    stage2_summary = _build_stage2_summary_simple(instance) if instance.project_template.code == "local_route_upgrade" else None
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
        "stage2": stage2_summary
        or {
            "status": "未开始",
            "completedCount": 0,
            "totalCount": 0,
            "progressPercent": 0,
            "blockedCount": 0,
            "currentStepCode": "",
            "currentStepNo": "",
            "currentStepName": "",
            "currentStepOwner": "",
        },
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


@router.post("/projects")
def create_progress_project(payload: ProgressProjectCreatePayload, db: Session = Depends(get_db)) -> dict:
    now = datetime.now()
    project_code = _build_unique_project_code(db, payload.code, payload.name)
    max_sort_no = db.query(ProgressProjectTemplate).count()
    template = ProgressProjectTemplate(
        code=project_code,
        name=payload.name.strip(),
        project_type=payload.project_type.strip(),
        description=(payload.description or "").strip() or None,
        status=payload.status,
        sort_no=payload.sort_no if payload.sort_no is not None else max_sort_no + 1,
        created_at=now,
        updated_at=now,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return ok(
        {
            "projectTemplateId": template.id,
            "projectCode": template.code,
            "projectName": template.name,
        }
    )


@router.post("/projects/{project_template_id}/brokers")
def add_progress_project_brokers(
    project_template_id: int,
    payload: ProgressProjectBrokerAddPayload,
    db: Session = Depends(get_db),
) -> dict:
    template = (
        db.query(ProgressProjectTemplate)
        .options(
            joinedload(ProgressProjectTemplate.items),
            joinedload(ProgressProjectTemplate.instances).joinedload(ProgressBrokerProjectInstance.stage2_step_instances),
        )
        .filter(ProgressProjectTemplate.id == project_template_id)
        .first()
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Progress project template not found")
    if not payload.broker_ids:
        raise HTTPException(status_code=400, detail="Please choose at least one broker")

    brokers = (
        db.query(Broker)
        .filter(Broker.id.in_(payload.broker_ids))
        .order_by(Broker.name.asc())
        .all()
    )
    if not brokers:
        raise HTTPException(status_code=404, detail="Broker not found")

    existing_broker_ids = {item.broker_id for item in template.instances}
    added_instances: list[ProgressBrokerProjectInstance] = []
    for broker in brokers:
        if broker.id in existing_broker_ids:
            continue
        instance = ProgressBrokerProjectInstance(
            project_template_id=template.id,
            broker_id=broker.id,
            input_mode=payload.input_mode,
            overall_status="未开始",
            overall_conclusion="未开始",
            owner_name=(payload.owner_name or "").strip() or None,
            progress_percent=0,
            latest_update_at=None,
            risk_count=0,
            milestone_count=0,
            remark=(payload.remark or "").strip() or None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(instance)
        db.flush()
        for item_template in template.items:
            db.add(_create_default_value(instance.id, item_template))
        instance.stage2_step_instances = []
        _create_stage2_step_instances(instance, db)
        added_instances.append(instance)

    if not added_instances:
        return ok({"addedCount": 0})

    db.commit()
    return ok({"addedCount": len(added_instances)})


@router.post("/projects/{project_template_id}/items")
def create_progress_project_item(
    project_template_id: int,
    payload: ProgressItemTemplateCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    template = (
        db.query(ProgressProjectTemplate)
        .options(joinedload(ProgressProjectTemplate.items), joinedload(ProgressProjectTemplate.instances))
        .filter(ProgressProjectTemplate.id == project_template_id)
        .first()
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Progress project template not found")
    if payload.item_type not in {"status", "number_progress", "boolean", "text"}:
        raise HTTPException(status_code=400, detail="Unsupported item type")

    item_key = _build_unique_item_key(project_template_id, payload.item_key, payload.item_label, db)
    group_key = None
    if payload.group_key or payload.group_label:
        if payload.group_key:
            group_key = _normalize_key(payload.group_key, "group")
        elif payload.group_label:
            existing_group_item = (
                db.query(ProgressItemTemplate)
                .filter(
                    ProgressItemTemplate.project_template_id == project_template_id,
                    ProgressItemTemplate.group_label == payload.group_label.strip(),
                    ProgressItemTemplate.group_key.isnot(None),
                )
                .first()
            )
            group_key = existing_group_item.group_key if existing_group_item else _normalize_key(payload.group_label, "group")
    max_sort_no = max([item.sort_no for item in template.items], default=0)
    item_template = ProgressItemTemplate(
        project_template_id=template.id,
        item_key=item_key,
        item_label=payload.item_label.strip(),
        group_key=group_key,
        group_label=(payload.group_label or "").strip() or None,
        item_type=payload.item_type,
        weight=payload.weight,
        allow_na=payload.allow_na,
        sort_no=payload.sort_no if payload.sort_no is not None else max_sort_no + 1,
        value_rule=(payload.value_rule or "").strip() or None,
        remark=(payload.remark or "").strip() or None,
    )
    db.add(item_template)
    db.flush()

    for instance in template.instances:
        default_value = _create_default_value(instance.id, item_template)
        default_value.item_template = item_template
        db.add(default_value)
        instance.values.append(default_value)
        _refresh_instance(instance)
        instance.updated_at = datetime.now()
        db.add(instance)

    db.commit()
    return ok(
        {
            "itemTemplateId": item_template.id,
            "itemKey": item_template.item_key,
            "itemLabel": item_template.item_label,
        }
    )


@router.put("/projects/{project_template_id}/items/{item_template_id}")
def update_progress_project_item(
    project_template_id: int,
    item_template_id: int,
    payload: ProgressItemTemplateCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    item_template = (
        db.query(ProgressItemTemplate)
        .filter(
            ProgressItemTemplate.id == item_template_id,
            ProgressItemTemplate.project_template_id == project_template_id,
        )
        .first()
    )
    if item_template is None:
        raise HTTPException(status_code=404, detail="Progress item template not found")
    if payload.item_type != item_template.item_type:
        raise HTTPException(status_code=400, detail="Item type cannot be changed after creation")

    item_template.item_label = payload.item_label.strip()
    if payload.group_key or payload.group_label:
        if payload.group_key:
            item_template.group_key = _normalize_key(payload.group_key, "group")
        elif payload.group_label:
            existing_group_item = (
                db.query(ProgressItemTemplate)
                .filter(
                    ProgressItemTemplate.project_template_id == project_template_id,
                    ProgressItemTemplate.id != item_template_id,
                    ProgressItemTemplate.group_label == payload.group_label.strip(),
                    ProgressItemTemplate.group_key.isnot(None),
                )
                .first()
            )
            item_template.group_key = existing_group_item.group_key if existing_group_item else _normalize_key(payload.group_label, "group")
        item_template.group_label = payload.group_label.strip() if payload.group_label else None
    else:
        item_template.group_key = None
        item_template.group_label = None
    item_template.weight = payload.weight
    item_template.allow_na = payload.allow_na
    if payload.sort_no is not None:
        item_template.sort_no = payload.sort_no
    item_template.value_rule = (payload.value_rule or "").strip() or None
    item_template.remark = (payload.remark or "").strip() or None

    instances = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template),
            joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressBrokerProjectInstance.risks),
        )
        .filter(ProgressBrokerProjectInstance.project_template_id == project_template_id)
        .all()
    )
    for instance in instances:
        _refresh_instance(instance)
        db.add(instance)

    db.commit()
    return ok({"itemTemplateId": item_template.id})


@router.delete("/projects/{project_template_id}/items/{item_template_id}")
def delete_progress_project_item(project_template_id: int, item_template_id: int, db: Session = Depends(get_db)) -> dict:
    item_template = (
        db.query(ProgressItemTemplate)
        .filter(
            ProgressItemTemplate.id == item_template_id,
            ProgressItemTemplate.project_template_id == project_template_id,
        )
        .first()
    )
    if item_template is None:
        raise HTTPException(status_code=404, detail="Progress item template not found")

    instance_ids = [
        item.id
        for item in db.query(ProgressBrokerProjectInstance.id)
        .filter(ProgressBrokerProjectInstance.project_template_id == project_template_id)
        .all()
    ]

    db.query(ProgressLog).filter(ProgressLog.item_template_id == item_template_id).update(
        {ProgressLog.item_template_id: None},
        synchronize_session=False,
    )
    db.query(ProgressItemValue).filter(ProgressItemValue.item_template_id == item_template_id).delete(synchronize_session=False)
    db.delete(item_template)
    db.flush()

    if instance_ids:
        instances = (
            db.query(ProgressBrokerProjectInstance)
            .options(
                joinedload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template),
                joinedload(ProgressBrokerProjectInstance.logs),
                joinedload(ProgressBrokerProjectInstance.risks),
            )
            .filter(ProgressBrokerProjectInstance.id.in_(instance_ids))
            .all()
        )
        for instance in instances:
            _refresh_instance(instance)
            db.add(instance)

    db.commit()
    return ok({"deleted": True})


@router.get("/projects/{project_template_id}/matrix")
def get_progress_matrix(project_template_id: int, db: Session = Depends(get_db)) -> dict:
    template = (
        db.query(ProgressProjectTemplate)
        .options(
            selectinload(ProgressProjectTemplate.items),
            selectinload(ProgressProjectTemplate.instances).joinedload(ProgressBrokerProjectInstance.broker),
            selectinload(ProgressProjectTemplate.instances)
            .selectinload(ProgressBrokerProjectInstance.values)
            .joinedload(ProgressItemValue.item_template),
            selectinload(ProgressProjectTemplate.instances)
            .selectinload(ProgressBrokerProjectInstance.stage2_step_instances)
            .joinedload(ProgressStage2StepInstance.step_template),
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
            selectinload(ProgressBrokerProjectInstance.project_template).selectinload(ProgressProjectTemplate.items),
            selectinload(ProgressBrokerProjectInstance.project_template).selectinload(ProgressProjectTemplate.stage2_groups),
            selectinload(ProgressBrokerProjectInstance.project_template).selectinload(ProgressProjectTemplate.stage2_steps),
            joinedload(ProgressBrokerProjectInstance.broker),
            selectinload(ProgressBrokerProjectInstance.values).joinedload(ProgressItemValue.item_template),
            selectinload(ProgressBrokerProjectInstance.logs).joinedload(ProgressLog.item_template),
            selectinload(ProgressBrokerProjectInstance.risks),
            selectinload(ProgressBrokerProjectInstance.stage2_step_instances)
            .joinedload(ProgressStage2StepInstance.step_template)
            .joinedload(ProgressStage2StepTemplate.group_template),
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
            "stage2": _build_stage2_summary_simple(instance) if instance.project_template.code == "local_route_upgrade" else None,
            "stage2Groups": _serialize_stage2_steps_flat(instance) if instance.project_template.code == "local_route_upgrade" else [],
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
    previous_progress = instance.progress_percent
    if value is None:
        value = ProgressItemValue(
            broker_project_instance_id=instance_id,
            item_template_id=item_template_id,
            updated_at=datetime.now(),
        )
        db.add(value)
        db.flush()
        instance.values.append(value)

    before_snapshot = (
        value.status_value,
        value.current_num,
        value.target_num,
        value.bool_value,
        value.text_value,
        value.is_na,
    )
    before_text = _format_progress_value(
        item_template.item_type,
        value.status_value,
        value.current_num,
        value.target_num,
        value.bool_value,
        value.text_value,
        value.is_na,
    )

    normalized_status_value = payload.status_value
    if item_template.item_type == "status":
        normalized_status_value = _normalize_status_value(payload.status_value)
        if payload.status_value and normalized_status_value is None:
            raise HTTPException(status_code=400, detail="Invalid progress status value")

    value.status_value = normalized_status_value
    value.current_num = payload.current_num
    value.target_num = payload.target_num
    value.bool_value = payload.bool_value
    value.text_value = payload.text_value
    value.is_na = payload.is_na
    value.remark = payload.remark
    value.calculated_percent = _calculate_item_percent(item_template.item_type, normalized_status_value, payload.current_num, payload.target_num, payload.is_na)
    value.updated_at = datetime.now()

    _refresh_instance(instance)
    after_snapshot = (
        value.status_value,
        value.current_num,
        value.target_num,
        value.bool_value,
        value.text_value,
        value.is_na,
    )
    if before_snapshot != after_snapshot:
        after_text = _format_progress_value(
            item_template.item_type,
            value.status_value,
            value.current_num,
            value.target_num,
            value.bool_value,
            value.text_value,
            value.is_na,
        )
        auto_log = ProgressLog(
            broker_project_instance_id=instance.id,
            item_template_id=item_template.id,
            log_date=datetime.now(),
            content=_build_auto_log_content(item_template, before_text, after_text),
            progress_delta=instance.progress_percent - previous_progress,
            progress_after=instance.progress_percent,
            is_milestone=False,
            remark=value.remark,
            created_by="系统自动记录",
            created_at=datetime.now(),
        )
        db.add(auto_log)
        db.flush()
        instance.logs.append(auto_log)
        _refresh_instance(instance)

    db.add(instance)
    db.commit()
    db.refresh(instance)
    return ok({"instanceId": instance.id, "progressPercent": instance.progress_percent})


@router.post("/instances/{instance_id}/stage2/steps/{step_instance_id}/update")
def update_progress_stage2_step(
    instance_id: int,
    step_instance_id: int,
    payload: ProgressStage2StepUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressBrokerProjectInstance.stage2_step_instances)
            .joinedload(ProgressStage2StepInstance.step_template)
            .joinedload(ProgressStage2StepTemplate.group_template),
        )
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    step_instance = next((item for item in instance.stage2_step_instances if item.id == step_instance_id), None)
    if step_instance is None:
        raise HTTPException(status_code=404, detail="Stage2 step instance not found")

    before_status = step_instance.status
    before_snapshot = (
        step_instance.step_template.step_no_display,
        step_instance.step_template.step_name,
        step_instance.owner_actual,
        step_instance.status,
        step_instance.remark,
        step_instance.blocker_reason,
    )

    if payload.step_no_display:
        step_instance.step_template.step_no_display = payload.step_no_display.strip()
    if payload.step_name:
        step_instance.step_template.step_name = payload.step_name.strip()

    step_instance.owner_actual = payload.owner_actual
    step_instance.status = payload.status
    step_instance.remark = payload.remark
    step_instance.blocker_reason = payload.blocker_reason
    step_instance.started_at = payload.started_at or step_instance.started_at or (datetime.now() if payload.status in {"进行中", "阻塞", "已完成"} else None)
    if payload.status == "已完成":
        step_instance.finished_at = payload.finished_at or step_instance.finished_at or datetime.now()
    elif payload.status not in {"已完成", "已跳过", "不适用"}:
        step_instance.finished_at = payload.finished_at
    step_instance.updated_at = datetime.now()

    after_snapshot = (
        step_instance.step_template.step_no_display,
        step_instance.step_template.step_name,
        step_instance.owner_actual,
        step_instance.status,
        step_instance.remark,
        step_instance.blocker_reason,
    )
    if before_snapshot != after_snapshot:
        log = ProgressLog(
            broker_project_instance_id=instance.id,
            item_template_id=None,
            log_date=datetime.now(),
            content=_build_stage2_auto_log_content(step_instance.step_template, before_status, step_instance.status),
            progress_delta=0,
            progress_after=instance.progress_percent,
            is_milestone=False,
            remark=step_instance.remark,
            created_by="系统自动记录",
            created_at=datetime.now(),
        )
        db.add(log)
        db.flush()
        instance.logs.append(log)
        _refresh_instance(instance)

    db.add(instance)
    db.commit()
    return ok({"stepInstanceId": step_instance.id})


@router.post("/instances/{instance_id}/stage2/steps")
def create_progress_stage2_step(
    instance_id: int,
    payload: ProgressStage2StepCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressBrokerProjectInstance.stage2_step_instances).joinedload(ProgressStage2StepInstance.step_template),
        )
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    group = _ensure_stage2_default_group(instance.project_template_id, db)
    max_sort_no = max([item.step_template.sort_no for item in instance.stage2_step_instances], default=0)
    step_template = ProgressStage2StepTemplate(
        project_template_id=instance.project_template_id,
        group_template_id=group.id,
        step_code=_normalize_key(payload.step_no_display or payload.step_name, "stage2_step"),
        step_no_display=payload.step_no_display.strip(),
        step_name=payload.step_name.strip(),
        owners_default=payload.owner_actual,
        is_optional=False,
        is_last_step=False,
        applicable_rule=None,
        dependency_step_codes=None,
        remark_template=None,
        sort_no=max_sort_no + 1,
    )
    db.add(step_template)
    db.flush()

    step_instance = ProgressStage2StepInstance(
        broker_project_instance_id=instance.id,
        step_template_id=step_template.id,
        owner_actual=payload.owner_actual,
        status=payload.status,
        remark=payload.remark,
        blocker_reason=None,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
        updated_at=datetime.now(),
    )
    db.add(step_instance)
    db.flush()
    instance.stage2_step_instances.append(step_instance)

    auto_log = ProgressLog(
        broker_project_instance_id=instance.id,
        item_template_id=None,
        log_date=datetime.now(),
        content=f"阶段2新增步骤：{step_template.step_no_display} {step_template.step_name}",
        progress_delta=0,
        progress_after=instance.progress_percent,
        is_milestone=False,
        remark=payload.remark,
        created_by="系统管理员",
        created_at=datetime.now(),
    )
    db.add(auto_log)
    db.flush()
    instance.logs.append(auto_log)
    _refresh_instance(instance)
    db.add(instance)
    db.commit()
    return ok({"stepInstanceId": step_instance.id})


@router.post("/instances/{instance_id}/stage2/steps/{step_instance_id}/move")
def move_progress_stage2_step(
    instance_id: int,
    step_instance_id: int,
    payload: ProgressStage2StepMovePayload,
    db: Session = Depends(get_db),
) -> dict:
    if payload.direction not in {"up", "down"}:
        raise HTTPException(status_code=400, detail="Unsupported move direction")

    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressBrokerProjectInstance.stage2_step_instances).joinedload(ProgressStage2StepInstance.step_template),
        )
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    ordered_steps = sorted(
        instance.stage2_step_instances,
        key=lambda item: (item.step_template.sort_no, item.step_template.id),
    )
    current_index = next((index for index, item in enumerate(ordered_steps) if item.id == step_instance_id), None)
    if current_index is None:
        raise HTTPException(status_code=404, detail="Stage2 step instance not found")

    target_index = current_index - 1 if payload.direction == "up" else current_index + 1
    if target_index < 0 or target_index >= len(ordered_steps):
        return ok({"moved": False})

    current_step = ordered_steps[current_index]
    target_step = ordered_steps[target_index]
    current_sort_no = current_step.step_template.sort_no
    current_step.step_template.sort_no = target_step.step_template.sort_no
    target_step.step_template.sort_no = current_sort_no

    auto_log = ProgressLog(
        broker_project_instance_id=instance.id,
        item_template_id=None,
        log_date=datetime.now(),
        content=f"阶段2步骤排序调整：{current_step.step_template.step_name}",
        progress_delta=0,
        progress_after=instance.progress_percent,
        is_milestone=False,
        remark=f"方向：{payload.direction}",
        created_by="系统管理员",
        created_at=datetime.now(),
    )
    db.add(auto_log)
    db.flush()
    instance.logs.append(auto_log)
    _refresh_instance(instance)
    db.add(instance)
    db.commit()
    return ok({"moved": True})


@router.delete("/instances/{instance_id}/stage2/steps/{step_instance_id}")
def delete_progress_stage2_step(instance_id: int, step_instance_id: int, db: Session = Depends(get_db)) -> dict:
    instance = (
        db.query(ProgressBrokerProjectInstance)
        .options(
            joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressBrokerProjectInstance.stage2_step_instances).joinedload(ProgressStage2StepInstance.step_template),
        )
        .filter(ProgressBrokerProjectInstance.id == instance_id)
        .first()
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Progress instance not found")

    step_instance = next((item for item in instance.stage2_step_instances if item.id == step_instance_id), None)
    if step_instance is None:
        raise HTTPException(status_code=404, detail="Stage2 step instance not found")

    step_template = step_instance.step_template
    if step_instance in instance.stage2_step_instances:
        instance.stage2_step_instances.remove(step_instance)
    db.delete(step_instance)
    db.flush()

    remaining_count = db.query(ProgressStage2StepInstance).filter(ProgressStage2StepInstance.step_template_id == step_template.id).count()
    if remaining_count == 0:
        db.delete(step_template)

    auto_log = ProgressLog(
        broker_project_instance_id=instance.id,
        item_template_id=None,
        log_date=datetime.now(),
        content=f"阶段2删除步骤：{step_template.step_no_display} {step_template.step_name}",
        progress_delta=0,
        progress_after=instance.progress_percent,
        is_milestone=False,
        remark=None,
        created_by="系统管理员",
        created_at=datetime.now(),
    )
    db.add(auto_log)
    db.flush()
    instance.logs.append(auto_log)
    _refresh_instance(instance)
    db.add(instance)
    db.commit()
    return ok({"deleted": True})


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


@router.put("/logs/{log_id}")
def update_progress_log(log_id: int, payload: ProgressLogUpdatePayload, db: Session = Depends(get_db)) -> dict:
    log = (
        db.query(ProgressLog)
        .options(
            joinedload(ProgressLog.instance)
            .joinedload(ProgressBrokerProjectInstance.logs),
            joinedload(ProgressLog.instance)
            .joinedload(ProgressBrokerProjectInstance.values)
            .joinedload(ProgressItemValue.item_template),
            joinedload(ProgressLog.instance)
            .joinedload(ProgressBrokerProjectInstance.risks),
        )
        .filter(ProgressLog.id == log_id)
        .first()
    )
    if log is None:
        raise HTTPException(status_code=404, detail="Progress log not found")

    log.item_template_id = payload.item_template_id
    log.log_date = payload.log_date
    log.content = payload.content
    log.progress_delta = payload.progress_delta
    log.progress_after = payload.progress_after
    log.is_milestone = payload.is_milestone
    log.remark = payload.remark

    _refresh_instance(log.instance)
    db.add(log.instance)
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
