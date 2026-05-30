from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.models import Broker, BrokerIssue, BrokerIssueStatus
from app.db.session import get_db
from app.modules.broker_issues.schemas import (
    BrokerIssueCreatePayload,
    BrokerIssueStatusUpdatePayload,
    BrokerIssueUpdatePayload,
)
from app.modules.common import ok

router = APIRouter(prefix="/broker-issues", tags=["broker-issues"])


def _date_text(value) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def _datetime_text(value) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")


def _serialize_status(item: BrokerIssueStatus) -> dict:
    return {
        "id": item.id,
        "brokerId": item.broker_id,
        "brokerName": item.broker.name if item.broker else "",
        "isAffected": item.is_affected,
        "impactDesc": item.impact_desc or "",
        "fixStatus": item.fix_status,
        "fixVersion": item.fix_version or "",
        "releasedAt": _datetime_text(item.released_at),
        "verifiedResult": item.verified_result or "",
        "ownerName": item.owner_name or "",
        "remark": item.remark or "",
        "updatedAt": _datetime_text(item.updated_at),
    }


def _issue_counts(issue: BrokerIssue) -> tuple[int, int]:
    statuses = [item for item in issue.broker_statuses if item.is_affected]
    fixed_statuses = [item for item in statuses if item.fix_status in {"已修复", "不适用"}]
    return len(statuses), len(fixed_statuses)


def _serialize_issue_summary(issue: BrokerIssue) -> dict:
    affected_count, fixed_count = _issue_counts(issue)
    return {
        "id": issue.id,
        "issueType": issue.issue_type,
        "title": issue.title,
        "priority": issue.priority,
        "status": issue.status,
        "impactScope": issue.impact_scope or "",
        "plannedFixVersion": issue.planned_fix_version or "",
        "affectedBrokerCount": affected_count,
        "fixedBrokerCount": fixed_count,
        "ownerName": issue.owner_name or "",
        "plannedFinishDate": _date_text(issue.planned_finish_date),
        "updatedAt": _datetime_text(issue.updated_at),
    }


def _serialize_issue_detail(issue: BrokerIssue) -> dict:
    result = _serialize_issue_summary(issue)
    result.update(
        {
            "description": issue.description or "",
            "solution": issue.solution or "",
            "remark": issue.remark or "",
            "createdAt": _datetime_text(issue.created_at),
            "affectedBrokers": [
                _serialize_status(item)
                for item in sorted(issue.broker_statuses, key=lambda status: status.broker.name if status.broker else "")
            ],
        }
    )
    return result


def _get_issue_or_404(issue_id: int, db: Session) -> BrokerIssue:
    issue = (
        db.query(BrokerIssue)
        .options(joinedload(BrokerIssue.broker_statuses).joinedload(BrokerIssueStatus.broker))
        .filter(BrokerIssue.id == issue_id)
        .first()
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="Broker issue not found")
    return issue


def _validate_brokers(broker_ids: List[int], db: Session) -> None:
    if not broker_ids:
        return
    existing_ids = {item.id for item in db.query(Broker).filter(Broker.id.in_(broker_ids)).all()}
    missing_ids = [item for item in broker_ids if item not in existing_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail="Broker not found")


def _replace_issue_statuses(issue: BrokerIssue, payload: BrokerIssueCreatePayload, db: Session) -> None:
    broker_ids = list(dict.fromkeys(item.broker_id for item in payload.affected_brokers))
    _validate_brokers(broker_ids, db)

    issue.broker_statuses.clear()
    for item in payload.affected_brokers:
        issue.broker_statuses.append(
            BrokerIssueStatus(
                broker_id=item.broker_id,
                is_affected=item.is_affected,
                impact_desc=item.impact_desc,
                fix_status=item.fix_status,
                fix_version=item.fix_version,
                released_at=item.released_at,
                verified_result=item.verified_result,
                owner_name=item.owner_name,
                remark=item.remark,
                updated_at=datetime.now(),
            )
        )


@router.get("")
def list_broker_issues(
    issue_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    broker_id: Optional[int] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(BrokerIssue).options(
        joinedload(BrokerIssue.broker_statuses).joinedload(BrokerIssueStatus.broker)
    )
    if issue_type:
        query = query.filter(BrokerIssue.issue_type == issue_type)
    if status:
        query = query.filter(BrokerIssue.status == status)
    if priority:
        query = query.filter(BrokerIssue.priority == priority)
    if keyword:
        like_text = f"%{keyword}%"
        query = query.filter(
            BrokerIssue.title.like(like_text)
            | BrokerIssue.description.like(like_text)
            | BrokerIssue.impact_scope.like(like_text)
            | BrokerIssue.solution.like(like_text)
        )
    if broker_id:
        query = query.join(BrokerIssueStatus).filter(BrokerIssueStatus.broker_id == broker_id)

    issues = query.order_by(BrokerIssue.updated_at.desc(), BrokerIssue.id.desc()).all()
    return ok([_serialize_issue_summary(issue) for issue in issues])


@router.get("/{issue_id}")
def get_broker_issue(issue_id: int, db: Session = Depends(get_db)) -> dict:
    return ok(_serialize_issue_detail(_get_issue_or_404(issue_id, db)))


@router.post("")
def create_broker_issue(payload: BrokerIssueCreatePayload, db: Session = Depends(get_db)) -> dict:
    now = datetime.now()
    issue = BrokerIssue(
        issue_type=payload.issue_type,
        title=payload.title,
        priority=payload.priority,
        status=payload.status,
        description=payload.description,
        impact_scope=payload.impact_scope,
        planned_fix_version=payload.planned_fix_version,
        solution=payload.solution,
        owner_name=payload.owner_name,
        planned_finish_date=payload.planned_finish_date,
        remark=payload.remark,
        created_at=now,
        updated_at=now,
    )
    _replace_issue_statuses(issue, payload, db)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return ok({"id": issue.id})


@router.put("/{issue_id}")
def update_broker_issue(issue_id: int, payload: BrokerIssueUpdatePayload, db: Session = Depends(get_db)) -> dict:
    issue = _get_issue_or_404(issue_id, db)
    issue.issue_type = payload.issue_type
    issue.title = payload.title
    issue.priority = payload.priority
    issue.status = payload.status
    issue.description = payload.description
    issue.impact_scope = payload.impact_scope
    issue.planned_fix_version = payload.planned_fix_version
    issue.solution = payload.solution
    issue.owner_name = payload.owner_name
    issue.planned_finish_date = payload.planned_finish_date
    issue.remark = payload.remark
    issue.updated_at = datetime.now()
    _replace_issue_statuses(issue, payload, db)
    db.add(issue)
    db.commit()
    return ok({"id": issue.id})


@router.put("/{issue_id}/brokers/{status_id}")
def update_broker_issue_status(
    issue_id: int,
    status_id: int,
    payload: BrokerIssueStatusUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    status = (
        db.query(BrokerIssueStatus)
        .join(BrokerIssue)
        .filter(BrokerIssue.id == issue_id, BrokerIssueStatus.id == status_id)
        .first()
    )
    if status is None:
        raise HTTPException(status_code=404, detail="Broker issue status not found")

    status.is_affected = payload.is_affected
    status.impact_desc = payload.impact_desc
    status.fix_status = payload.fix_status
    status.fix_version = payload.fix_version
    status.released_at = payload.released_at
    status.verified_result = payload.verified_result
    status.owner_name = payload.owner_name
    status.remark = payload.remark
    status.updated_at = datetime.now()
    status.issue.updated_at = datetime.now()
    db.add(status)
    db.add(status.issue)
    db.commit()
    return ok({"id": status.id})


@router.delete("/{issue_id}")
def delete_broker_issue(issue_id: int, db: Session = Depends(get_db)) -> dict:
    issue = _get_issue_or_404(issue_id, db)
    db.delete(issue)
    db.commit()
    return ok({"id": issue_id, "deleted": True})
