from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import Broker, BrokerEntrustSite, BrokerServer, ProgressBrokerProjectInstance, ProgressRisk, Project, Risk, Task
from app.db.session import get_db
from app.modules.brokers.schemas import (
    BrokerCreatePayload,
    BrokerEntrustSitePayload,
    BrokerFeaturedUpdatePayload,
    BrokerServerPayload,
    BrokerUpdatePayload,
)
from app.modules.common import ok

router = APIRouter(prefix="/brokers", tags=["brokers"])


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def serialize_broker(broker: Broker) -> dict:
    projects = broker.projects
    next_project = min(projects, key=lambda item: item.planned_date) if projects else None
    return {
        "id": broker.id,
        "name": broker.name,
        "shortName": broker.short_name,
        "businessStatus": broker.business_status,
        "systemVersion": broker.system_version or "-",
        "systemVersionUpdatedAt": broker.system_version_updated_at.strftime("%Y-%m-%d") if broker.system_version_updated_at else "",
        "isFeatured": broker.is_featured,
        "serverCount": len(broker.servers),
        "entrustSiteCount": len(broker.entrust_sites),
        "currentProjects": len(projects),
        "activeProjects": len([project for project in projects if project.status in ["执行中", "准备中"]]),
        "nextMilestone": (
            f"{next_project.planned_date.month}/{next_project.planned_date.day} {next_project.name}"
            if next_project is not None
            else "-"
        ),
        "riskCount": sum(len(project.risks) for project in projects),
        "overdueCount": sum(
            len([task for task in project.tasks if task.status == "已逾期"])
            for project in projects
        ),
    }


def serialize_server(server: BrokerServer) -> dict:
    return {
        "id": server.id,
        "name": server.name,
        "cpu": server.cpu or "",
        "memory": server.memory or "",
        "operatingSystem": server.operating_system or "",
        "ipAddress": server.ip_address or "",
        "remark": server.remark or "",
    }


def serialize_entrust_site(site: BrokerEntrustSite) -> dict:
    return {
        "id": site.id,
        "name": site.name,
        "clientType": site.client_type,
        "softwareVersion": site.software_version or "",
        "updatedAt": site.updated_at.strftime("%Y-%m-%d %H:%M") if site.updated_at else "",
        "operatingSystem": site.operating_system or "",
        "isXinchuang": site.is_xinchuang,
        "remark": site.remark or "",
    }


def serialize_broker_detail(broker: Broker) -> dict:
    return {
        "id": broker.id,
        "name": broker.name,
        "shortName": broker.short_name,
        "contactName": broker.contact_name or "",
        "contactPhone": broker.contact_phone or "",
        "status": broker.status,
        "businessStatus": broker.business_status,
        "systemVersion": broker.system_version or "",
        "systemVersionUpdatedAt": broker.system_version_updated_at.strftime("%Y-%m-%d %H:%M") if broker.system_version_updated_at else "",
        "systemVersionContent": broker.system_version_content or "",
        "note": broker.note or "",
        "servers": [serialize_server(server) for server in sorted(broker.servers, key=lambda item: item.id)],
        "entrustSites": [serialize_entrust_site(site) for site in sorted(broker.entrust_sites, key=lambda item: item.id)],
    }


def _latest_progress_update(instances: list[ProgressBrokerProjectInstance]) -> datetime | None:
    dates = [item.latest_update_at or item.updated_at for item in instances if item.latest_update_at or item.updated_at]
    return max(dates) if dates else None


def _build_broker_overview_row(broker: Broker) -> dict:
    instances = list(broker.progress_instances)
    progress_project_count = len(instances)
    completed_count = len([item for item in instances if item.overall_status == "已完成"])
    in_progress_count = len([item for item in instances if item.overall_status == "推进中"])
    gray_count = len([item for item in instances if item.overall_status == "灰度中"])
    unfinished_count = len([item for item in instances if item.overall_status != "已完成"])
    avg_progress = round(sum(item.progress_percent for item in instances) / progress_project_count) if progress_project_count else 0
    risk_count = sum(item.risk_count for item in instances)
    latest_update = _latest_progress_update(instances)

    return {
        "id": broker.id,
        "name": broker.name,
        "shortName": broker.short_name,
        "businessStatus": broker.business_status,
        "systemVersion": broker.system_version or "-",
        "systemVersionUpdatedAt": broker.system_version_updated_at.strftime("%Y-%m-%d") if broker.system_version_updated_at else "",
        "isFeatured": broker.is_featured,
        "serverCount": len(broker.servers),
        "entrustSiteCount": len(broker.entrust_sites),
        "progressProjectCount": progress_project_count,
        "completedProjectCount": completed_count,
        "inProgressProjectCount": in_progress_count,
        "grayProjectCount": gray_count,
        "unfinishedProjectCount": unfinished_count,
        "avgProgress": avg_progress,
        "riskCount": risk_count,
        "latestUpdateAt": latest_update.strftime("%Y-%m-%d") if latest_update else "",
    }


def _risk_priority(level: str) -> int:
    if level in {"高", "高风险"}:
        return 0
    if level in {"中", "中风险"}:
        return 1
    if level in {"低", "低风险"}:
        return 2
    return 3


def _date_priority(value: str) -> int:
    if not value:
        return 0
    try:
        return int(value.replace("-", ""))
    except ValueError:
        return 0


def _get_broker_or_404(broker_id: int, db: Session) -> Broker:
    broker = (
        db.query(Broker)
        .options(
            selectinload(Broker.projects).selectinload(Project.tasks),
            selectinload(Broker.projects).selectinload(Project.risks),
            selectinload(Broker.servers),
            selectinload(Broker.entrust_sites),
        )
        .filter(Broker.id == broker_id)
        .first()
    )
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")
    return broker


@router.post("")
def create_broker(payload: BrokerCreatePayload, db: Session = Depends(get_db)) -> dict:
    broker = Broker(
        name=payload.name,
        short_name=payload.short_name,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        status=payload.status,
        business_status=payload.business_status,
        system_version=payload.system_version,
        system_version_updated_at=_parse_datetime(payload.system_version_updated_at),
        system_version_content=payload.system_version_content,
        note=payload.note,
    )
    db.add(broker)
    db.commit()
    db.refresh(broker)
    return ok(serialize_broker(broker))


@router.put("/{broker_id}")
def update_broker(
    broker_id: int,
    payload: BrokerUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    broker.name = payload.name
    broker.short_name = payload.short_name
    broker.contact_name = payload.contact_name
    broker.contact_phone = payload.contact_phone
    broker.status = payload.status
    broker.business_status = payload.business_status
    broker.system_version = payload.system_version
    broker.system_version_updated_at = _parse_datetime(payload.system_version_updated_at)
    broker.system_version_content = payload.system_version_content
    broker.note = payload.note
    db.add(broker)
    db.commit()
    db.refresh(broker)
    return ok(serialize_broker(broker))


@router.delete("/{broker_id}")
def delete_broker(broker_id: int, db: Session = Depends(get_db)) -> dict:
    broker = db.query(Broker).filter(Broker.id == broker_id).first()
    if broker is None:
        raise HTTPException(status_code=404, detail="Broker not found")

    db.delete(broker)
    db.commit()
    return ok({"id": broker_id, "deleted": True})


@router.get("")
def list_brokers(db: Session = Depends(get_db)) -> dict:
    brokers = (
        db.query(Broker)
        .options(
            selectinload(Broker.projects).selectinload(Project.tasks),
            selectinload(Broker.projects).selectinload(Project.risks),
            selectinload(Broker.servers),
            selectinload(Broker.entrust_sites),
        )
        .all()
    )
    return ok([serialize_broker(broker) for broker in brokers])


@router.get("/overview")
def get_broker_overview(db: Session = Depends(get_db)) -> dict:
    brokers = (
        db.query(Broker)
        .options(
            selectinload(Broker.progress_instances).selectinload(ProgressBrokerProjectInstance.project_template),
            selectinload(Broker.progress_instances).selectinload(ProgressBrokerProjectInstance.risks),
            selectinload(Broker.servers),
            selectinload(Broker.entrust_sites),
        )
        .all()
    )
    rows = [_build_broker_overview_row(broker) for broker in brokers]
    rows.sort(key=lambda item: (item["name"]))

    auto_focus_brokers = sorted(
        rows,
        key=lambda item: (
            0 if item["riskCount"] > 0 else 1 if item["unfinishedProjectCount"] > 0 else 2,
            -item["riskCount"],
            -item["unfinishedProjectCount"],
            -item["avgProgress"],
            item["name"],
        ),
    )[:6]
    configured_focus_brokers = [item for item in rows if item["isFeatured"]]
    focus_brokers = configured_focus_brokers[:6] if configured_focus_brokers else auto_focus_brokers
    follow_up_brokers = [
        item
        for item in sorted(
            rows,
            key=lambda item: (
                0 if item["riskCount"] > 0 else 1,
                -item["unfinishedProjectCount"],
                -_date_priority(item["latestUpdateAt"]),
                item["name"],
            ),
        )
        if item["unfinishedProjectCount"] > 0 or item["riskCount"] > 0
    ][:8]

    risks = (
        db.query(ProgressRisk)
        .options(
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.broker),
            joinedload(ProgressRisk.instance).joinedload(ProgressBrokerProjectInstance.project_template),
        )
        .all()
    )
    risks = [
        risk
        for risk in risks
        if risk.level in {"高", "高风险"} or risk.status in {"阻塞", "处理中", "待处理", "持续关注"}
    ]
    risks = sorted(
        risks,
        key=lambda risk: (_risk_priority(risk.level), -(risk.updated_at or risk.created_at).timestamp()),
    )[:6]

    summary = {
        "totalBrokers": len(rows),
        "onlineBrokers": len([item for item in rows if item["businessStatus"] == "已上线"]),
        "connectingBrokers": len([item for item in rows if item["businessStatus"] == "对接中"]),
        "grayBrokers": len([item for item in rows if item["businessStatus"] == "灰度中"]),
        "totalServers": sum(item["serverCount"] for item in rows),
        "totalEntrustSites": sum(item["entrustSiteCount"] for item in rows),
        "riskBrokers": len([item for item in rows if item["riskCount"] > 0]),
    }

    return ok(
        {
            "summary": summary,
            "focusBrokers": focus_brokers,
            "brokerRows": rows,
            "followUpBrokers": follow_up_brokers,
            "riskHighlights": [
                {
                    "id": risk.id,
                    "brokerId": risk.instance.broker_id,
                    "brokerName": risk.instance.broker.name,
                    "projectTemplateId": risk.instance.project_template_id,
                    "projectName": risk.instance.project_template.name,
                    "title": risk.title,
                    "level": risk.level,
                    "status": risk.status,
                    "updatedAt": risk.updated_at.strftime("%Y-%m-%d") if risk.updated_at else "",
                }
                for risk in risks
            ],
        }
    )


@router.post("/overview/featured")
def update_broker_featured(payload: BrokerFeaturedUpdatePayload, db: Session = Depends(get_db)) -> dict:
    broker_ids = list(dict.fromkeys(payload.broker_ids))
    if len(broker_ids) > 6:
        raise HTTPException(status_code=400, detail="Featured brokers cannot exceed 6")

    brokers = db.query(Broker).all()
    existing_ids = {item.id for item in brokers}
    missing_ids = [item for item in broker_ids if item not in existing_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail="Broker not found")

    selected_ids = set(broker_ids)
    for broker in brokers:
        broker.is_featured = broker.id in selected_ids

    db.commit()
    return ok({"brokerIds": broker_ids})


@router.get("/{broker_id}")
def get_broker_detail(broker_id: int, db: Session = Depends(get_db)) -> dict:
    broker = _get_broker_or_404(broker_id, db)
    return ok(serialize_broker_detail(broker))


@router.post("/{broker_id}/servers")
def create_broker_server(broker_id: int, payload: BrokerServerPayload, db: Session = Depends(get_db)) -> dict:
    broker = _get_broker_or_404(broker_id, db)
    server = BrokerServer(
        broker_id=broker.id,
        name=payload.name,
        cpu=payload.cpu,
        memory=payload.memory,
        operating_system=payload.operating_system,
        ip_address=payload.ip_address,
        remark=payload.remark,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return ok(serialize_server(server))


@router.put("/servers/{server_id}")
def update_broker_server(server_id: int, payload: BrokerServerPayload, db: Session = Depends(get_db)) -> dict:
    server = db.query(BrokerServer).filter(BrokerServer.id == server_id).first()
    if server is None:
        raise HTTPException(status_code=404, detail="Broker server not found")

    server.name = payload.name
    server.cpu = payload.cpu
    server.memory = payload.memory
    server.operating_system = payload.operating_system
    server.ip_address = payload.ip_address
    server.remark = payload.remark
    server.updated_at = datetime.now()
    db.add(server)
    db.commit()
    db.refresh(server)
    return ok(serialize_server(server))


@router.delete("/servers/{server_id}")
def delete_broker_server(server_id: int, db: Session = Depends(get_db)) -> dict:
    server = db.query(BrokerServer).filter(BrokerServer.id == server_id).first()
    if server is None:
        raise HTTPException(status_code=404, detail="Broker server not found")

    db.delete(server)
    db.commit()
    return ok({"id": server_id, "deleted": True})


@router.post("/{broker_id}/entrust-sites")
def create_broker_entrust_site(broker_id: int, payload: BrokerEntrustSitePayload, db: Session = Depends(get_db)) -> dict:
    broker = _get_broker_or_404(broker_id, db)
    site = BrokerEntrustSite(
        broker_id=broker.id,
        name=payload.name,
        client_type=payload.client_type,
        software_version=payload.software_version,
        updated_at=_parse_datetime(payload.updated_at),
        operating_system=payload.operating_system,
        is_xinchuang=payload.is_xinchuang,
        remark=payload.remark,
        created_at=datetime.now(),
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return ok(serialize_entrust_site(site))


@router.put("/entrust-sites/{site_id}")
def update_broker_entrust_site(site_id: int, payload: BrokerEntrustSitePayload, db: Session = Depends(get_db)) -> dict:
    site = db.query(BrokerEntrustSite).filter(BrokerEntrustSite.id == site_id).first()
    if site is None:
        raise HTTPException(status_code=404, detail="Broker entrust site not found")

    site.name = payload.name
    site.client_type = payload.client_type
    site.software_version = payload.software_version
    site.updated_at = _parse_datetime(payload.updated_at)
    site.operating_system = payload.operating_system
    site.is_xinchuang = payload.is_xinchuang
    site.remark = payload.remark
    db.add(site)
    db.commit()
    db.refresh(site)
    return ok(serialize_entrust_site(site))


@router.delete("/entrust-sites/{site_id}")
def delete_broker_entrust_site(site_id: int, db: Session = Depends(get_db)) -> dict:
    site = db.query(BrokerEntrustSite).filter(BrokerEntrustSite.id == site_id).first()
    if site is None:
        raise HTTPException(status_code=404, detail="Broker entrust site not found")

    db.delete(site)
    db.commit()
    return ok({"id": site_id, "deleted": True})
