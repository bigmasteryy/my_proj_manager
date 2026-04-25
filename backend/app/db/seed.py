from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.db.models import (
    Broker,
    PersonalTask,
    Project,
    ProjectLog,
    ProgressBrokerProjectInstance,
    ProgressItemTemplate,
    ProgressItemValue,
    ProgressLog,
    ProgressProjectTemplate,
    ProgressRisk,
    ProgressStage2GroupTemplate,
    ProgressStage2StepInstance,
    ProgressStage2StepTemplate,
    Reminder,
    Risk,
    Task,
    Template,
    TemplateRisk,
    TemplateTask,
    User,
)
from app.modules.auth.utils import hash_password


def seed_database(session: Session) -> None:
    ensure_users(session)
    has_runtime_project_data = session.query(Project).first()
    if has_runtime_project_data is None:
        seed_runtime_data(session)

    has_template_items = session.query(TemplateTask).first()
    if has_template_items is None:
        seed_template_blueprints(session)

    ensure_progress_seed(session)
    ensure_personal_tasks(session)


PROGRESS_BROKERS = [
    "太平洋",
    "东吴",
    "国金",
    "中金",
    "恒泰",
    "粤开",
    "江海",
    "渤海",
    "国新",
    "前海",
    "德邦",
    "天风",
    "中天国富",
    "财信",
    "华福",
    "兴业",
    "国联民生",
    "中信建投",
    "国融",
    "国元",
    "西部",
]

STATUS_PROGRESS_MAP = {
    "不支持": 0,
    "未开始": 0,
    "推进中": 50,
    "就绪": 80,
    "已支持": 100,
    "已完成": 100,
    "阻塞": 30,
}


def ensure_progress_seed(session: Session) -> None:
    broker_map = ensure_progress_brokers(session)
    template_map, item_map = ensure_progress_templates(session)
    ensure_stage2_templates(session, template_map)
    ensure_progress_instances(session, broker_map, template_map, item_map)
    ensure_stage2_instances(session, template_map)
    normalize_local_route_ready_status(session)
    session.commit()


def normalize_local_route_ready_status(session: Session) -> None:
    local_route_template = (
        session.query(ProgressProjectTemplate)
        .filter(ProgressProjectTemplate.code == "local_route_upgrade")
        .first()
    )
    if local_route_template is None:
        return

    local_route_instance_ids = [
        row.id
        for row in session.query(ProgressBrokerProjectInstance.id)
        .filter(ProgressBrokerProjectInstance.project_template_id == local_route_template.id)
        .all()
    ]
    if not local_route_instance_ids:
        return

    values = (
        session.query(ProgressItemValue)
        .filter(ProgressItemValue.broker_project_instance_id.in_(local_route_instance_ids))
        .filter(ProgressItemValue.status_value == "就绪")
        .all()
    )
    for value in values:
        value.status_value = "已支持"
        value.calculated_percent = 100
        value.updated_at = datetime.now()


def ensure_progress_brokers(session: Session) -> dict:
    broker_map = {broker.name: broker for broker in session.query(Broker).all()}
    pending = []
    for broker_name in PROGRESS_BROKERS:
        if broker_name not in broker_map:
            pending.append(Broker(name=broker_name, short_name=broker_name, status="active"))
    if pending:
        session.add_all(pending)
        session.flush()
        broker_map = {broker.name: broker for broker in session.query(Broker).all()}
    return broker_map


def ensure_progress_templates(session: Session) -> tuple:
    now = datetime.now()
    template_specs = [
        {
            "code": "local_route_upgrade",
            "name": "本地路由升级",
            "project_type": "批量推进",
            "description": "多家券商推进本地路由升级",
            "sort_no": 1,
            "items": [
                {"item_key": "backend_support", "item_label": "后台程序", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 1, "value_rule": "不支持/未开始/推进中/就绪/已支持"},
                {"item_key": "condition_order", "item_label": "条件单", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 2, "value_rule": "不支持/未开始/推进中/就绪/已支持"},
                {"item_key": "main_site_app", "item_label": "APP", "group_key": "main_site_upgrade", "group_label": "主站升级", "item_type": "number_progress", "weight": 30, "allow_na": False, "sort_no": 3, "value_rule": "current/target"},
                {"item_key": "main_site_pc", "item_label": "PC", "group_key": "main_site_upgrade", "group_label": "主站升级", "item_type": "number_progress", "weight": 10, "allow_na": True, "sort_no": 4, "value_rule": "current/target"},
                {"item_key": "api_upgrade", "item_label": "接口升级", "item_type": "number_progress", "weight": 20, "allow_na": False, "sort_no": 5, "value_rule": "current/target"},
            ],
        },
        {
            "code": "linux_main_site",
            "name": "Linux主站推进",
            "project_type": "批量推进",
            "description": "多家券商推进 Linux 主站",
            "sort_no": 2,
            "items": [
                {"item_key": "solution_confirm", "item_label": "方案确认", "item_type": "status", "weight": 15, "allow_na": False, "sort_no": 1, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "env_prepare", "item_label": "环境准备", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 2, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "deploy_install", "item_label": "安装部署", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 3, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "joint_test", "item_label": "联调验证", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 4, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "go_live", "item_label": "上线完成", "item_type": "status", "weight": 25, "allow_na": False, "sort_no": 5, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
            ],
        },
        {
            "code": "xinchuang_upgrade",
            "name": "信创推进",
            "project_type": "批量推进",
            "description": "多家券商推进信创适配",
            "sort_no": 3,
            "items": [
                {"item_key": "broker_confirm", "item_label": "券商确认", "item_type": "status", "weight": 15, "allow_na": False, "sort_no": 1, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "env_prepare", "item_label": "环境准备", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 2, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "compatibility_test", "item_label": "兼容验证", "item_type": "status", "weight": 25, "allow_na": False, "sort_no": 3, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "joint_test", "item_label": "联调测试", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 4, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
                {"item_key": "acceptance", "item_label": "验收完成", "item_type": "status", "weight": 20, "allow_na": False, "sort_no": 5, "value_rule": "未开始/推进中/就绪/已完成/阻塞"},
            ],
        },
    ]

    template_map = {item.code: item for item in session.query(ProgressProjectTemplate).all()}
    for spec in template_specs:
        template = template_map.get(spec["code"])
        if template is None:
            template = ProgressProjectTemplate(
                code=spec["code"],
                name=spec["name"],
                project_type=spec["project_type"],
                description=spec["description"],
                status="active",
                sort_no=spec["sort_no"],
                created_at=now,
                updated_at=now,
            )
            session.add(template)
            session.flush()
            template_map[spec["code"]] = template

        existing_items = {item.item_key: item for item in template.items}
        for item_spec in spec["items"]:
            if item_spec["item_key"] in existing_items:
                continue
            session.add(
                ProgressItemTemplate(
                    project_template_id=template.id,
                    item_key=item_spec["item_key"],
                    item_label=item_spec["item_label"],
                    group_key=item_spec.get("group_key"),
                    group_label=item_spec.get("group_label"),
                    item_type=item_spec["item_type"],
                    weight=item_spec["weight"],
                    allow_na=item_spec["allow_na"],
                    sort_no=item_spec["sort_no"],
                    value_rule=item_spec["value_rule"],
                )
            )
        session.flush()

    session.flush()
    session.expire_all()

    template_map = {item.code: item for item in session.query(ProgressProjectTemplate).all()}
    item_map = {}
    for item in session.query(ProgressItemTemplate).all():
        item_map[(item.project_template.code, item.item_key)] = item

    return template_map, item_map


def ensure_stage2_templates(session: Session, template_map: dict) -> None:
    local_template = template_map.get("local_route_upgrade")
    if local_template is None:
        return

    group_specs = [
        {"group_code": "precheck", "group_name": "前置确认", "sort_no": 1},
        {"group_code": "backend_config", "group_name": "后台配置", "sort_no": 2},
        {"group_code": "pc_related", "group_name": "PC相关", "sort_no": 3},
        {"group_code": "gray_release", "group_name": "灰度与放开", "sort_no": 4},
        {"group_code": "optional_finish", "group_name": "收尾与可选动作", "sort_no": 5},
    ]

    existing_groups = {group.group_code: group for group in local_template.stage2_groups}
    for group_spec in group_specs:
        if group_spec["group_code"] in existing_groups:
            continue
        session.add(
            ProgressStage2GroupTemplate(
                project_template_id=local_template.id,
                group_code=group_spec["group_code"],
                group_name=group_spec["group_name"],
                sort_no=group_spec["sort_no"],
            )
        )
    session.flush()
    session.expire(local_template, ["stage2_groups"])

    group_map = {group.group_code: group for group in session.query(ProgressStage2GroupTemplate).filter(ProgressStage2GroupTemplate.project_template_id == local_template.id).all()}
    step_specs = [
        {"group_code": "precheck", "step_code": "5", "step_no_display": "5", "step_name": "主站对外地址通知并确认权重设置", "owners_default": "易勇、券商负责人、券商工程、陈良海", "sort_no": 1},
        {"group_code": "precheck", "step_code": "6", "step_no_display": "6", "step_name": "线上营业部配置对应关系检查（k客户号）", "owners_default": "陈良海", "dependency_step_codes": "5", "sort_no": 2},
        {"group_code": "backend_config", "step_code": "7", "step_no_display": "7", "step_name": "小财神后台-券商信息配置-新增券商", "owners_default": "蒋张飞/陈良海", "dependency_step_codes": "6", "sort_no": 1},
        {"group_code": "backend_config", "step_code": "8", "step_no_display": "8", "step_name": "订单系统本地路由相关开关开启", "owners_default": "戴洪添", "dependency_step_codes": "7", "remark_template": "具体打开方式详见生产主站路由券商切换本地路由实施方案", "sort_no": 2},
        {"group_code": "backend_config", "step_code": "9", "step_no_display": "9", "step_name": "将签约名单同步给小财神", "owners_default": "戴洪添", "dependency_step_codes": "8", "sort_no": 3},
        {"group_code": "backend_config", "step_code": "10", "step_no_display": "10", "step_name": "小财神后台-业务标签-增加默认配置", "owners_default": "蒋张飞/陈良海", "dependency_step_codes": "9", "sort_no": 4},
        {"group_code": "backend_config", "step_code": "14", "step_no_display": "14", "step_name": "营业部配置增加条件单、快速柜台标记", "owners_default": "陈良海", "dependency_step_codes": "10", "sort_no": 5},
        {"group_code": "pc_related", "step_code": "11", "step_no_display": "11", "step_name": "PC端券商DLL本地路由开关升级", "owners_default": "林坚恒、薛伟", "applicable_rule": "已支持PC的券商执行", "dependency_step_codes": "10", "is_optional": True, "sort_no": 1},
        {"group_code": "pc_related", "step_code": "12", "step_no_display": "12", "step_name": "PC端券商快速柜台/云条件单站点属性升级", "owners_default": "薛伟", "applicable_rule": "已支持PC的券商执行", "dependency_step_codes": "11", "is_optional": True, "sort_no": 2},
        {"group_code": "gray_release", "step_code": "15", "step_no_display": "15", "step_name": "本地路由灰度配置放开", "owners_default": "徐慧信", "dependency_step_codes": "14", "is_last_step": True, "remark_template": "最后执行", "sort_no": 1},
        {"group_code": "gray_release", "step_code": "18", "step_no_display": "18", "step_name": "本地路由灰度完成，全部放开", "owners_default": "申宝杰", "dependency_step_codes": "15", "sort_no": 2},
        {"group_code": "gray_release", "step_code": "19", "step_no_display": "19", "step_name": "监控终端 qbmonitor 配置调整为本地路由模式", "owners_default": "戴洪添", "dependency_step_codes": "18", "remark_template": "monitorinfo.xml", "sort_no": 3},
        {"group_code": "gray_release", "step_code": "19A", "step_no_display": "19A", "step_name": "认证程序支持主从", "owners_default": "", "dependency_step_codes": "18", "remark_template": "sysconf，key_name=unsign_effective_time，值 1 改为 0", "sort_no": 4},
        {"group_code": "gray_release", "step_code": "19B", "step_no_display": "19B", "step_name": "用户解约&转发生效时间开关改为实时生效", "owners_default": "", "dependency_step_codes": "18", "sort_no": 5},
        {"group_code": "gray_release", "step_code": "20", "step_no_display": "20", "step_name": "全部放开后检查 auth 是否还有主站路由请求", "owners_default": "戴洪添", "dependency_step_codes": "18", "sort_no": 6},
        {"group_code": "gray_release", "step_code": "20A", "step_no_display": "20A", "step_name": "本地路由放开后运行情况分析", "owners_default": "", "dependency_step_codes": "18", "sort_no": 7},
        {"group_code": "optional_finish", "step_code": "21", "step_no_display": "21", "step_name": "委托主站去除主站路由支持配置", "owners_default": "易勇、戴洪添、券商负责人、券商工程", "dependency_step_codes": "20", "is_optional": True, "remark_template": "根据券商情况确认是否做", "sort_no": 1},
        {"group_code": "optional_finish", "step_code": "22", "step_no_display": "22", "step_name": "委托主站程序、routeid.cfg配置&接口程序部署", "owners_default": "易勇、戴洪添、券商负责人、券商工程", "dependency_step_codes": "21", "is_optional": True, "remark_template": "主站路由下线后做", "sort_no": 2},
        {"group_code": "optional_finish", "step_code": "23", "step_no_display": "23", "step_name": "委托主站站点增加条件单、快速柜台标记、权重调整", "owners_default": "陈良海", "dependency_step_codes": "22", "is_optional": True, "sort_no": 3},
    ]

    existing_steps = {step.step_code: step for step in local_template.stage2_steps}
    for step_spec in step_specs:
        if step_spec["step_code"] in existing_steps:
            continue
        session.add(
            ProgressStage2StepTemplate(
                project_template_id=local_template.id,
                group_template_id=group_map[step_spec["group_code"]].id,
                step_code=step_spec["step_code"],
                step_no_display=step_spec["step_no_display"],
                step_name=step_spec["step_name"],
                owners_default=step_spec.get("owners_default"),
                is_optional=step_spec.get("is_optional", False),
                is_last_step=step_spec.get("is_last_step", False),
                applicable_rule=step_spec.get("applicable_rule"),
                dependency_step_codes=step_spec.get("dependency_step_codes"),
                remark_template=step_spec.get("remark_template"),
                sort_no=step_spec["sort_no"],
            )
        )
    session.flush()


def ensure_stage2_instances(session: Session, template_map: dict) -> None:
    local_template = template_map.get("local_route_upgrade")
    if local_template is None:
        return

    step_templates = (
        session.query(ProgressStage2StepTemplate)
        .options()
        .filter(ProgressStage2StepTemplate.project_template_id == local_template.id)
        .order_by(ProgressStage2StepTemplate.sort_no.asc(), ProgressStage2StepTemplate.id.asc())
        .all()
    )
    template_map_by_code = {item.step_code: item for item in step_templates}

    existing_instances = (
        session.query(ProgressBrokerProjectInstance)
        .filter(ProgressBrokerProjectInstance.project_template_id == local_template.id)
        .all()
    )

    seeded_status_map = {
        "太平洋": {
            "5": "已完成",
            "6": "已完成",
            "7": "已完成",
            "8": "已完成",
            "9": "已完成",
            "10": "已完成",
            "14": "已完成",
            "15": "已完成",
            "18": "进行中",
        },
        "东吴": {
            "5": "已完成",
            "6": "已完成",
            "7": "已完成",
            "8": "进行中",
        },
    }

    for instance in existing_instances:
        existing_step_instances = {item.step_template.step_code: item for item in instance.stage2_step_instances}
        seeded_steps = seeded_status_map.get(instance.broker.name, {})
        for step_template in step_templates:
            if step_template.step_code in existing_step_instances:
                continue
            status = seeded_steps.get(step_template.step_code, "未开始")
            started_at = datetime(2026, 4, 24, 9, 0) if status in {"进行中", "已完成"} else None
            finished_at = datetime(2026, 4, 24, 18, 0) if status == "已完成" else None
            session.add(
                ProgressStage2StepInstance(
                    broker_project_instance_id=instance.id,
                    step_template_id=step_template.id,
                    owner_actual=step_template.owners_default,
                    status=status,
                    remark=step_template.remark_template if status != "未开始" and step_template.remark_template else None,
                    blocker_reason=None,
                    started_at=started_at,
                    finished_at=finished_at,
                    updated_at=datetime.now(),
                )
            )
    session.flush()


def ensure_progress_instances(session: Session, broker_map: dict, template_map: dict, item_map: dict) -> None:
    existing_instances = {
        (instance.project_template.code, instance.broker.name): instance
        for instance in session.query(ProgressBrokerProjectInstance).all()
    }

    local_route_data = {
        "太平洋": {
            "input_mode": "明细",
            "overall_status": "推进中",
            "overall_conclusion": "推进中",
            "latest_update_at": datetime(2026, 4, 20, 9, 0),
            "remark": "主站APP已完成，接口未完成",
            "values": {
                "backend_support": {"status_value": "已支持"},
                "condition_order": {"status_value": "已支持"},
                "main_site_app": {"current_num": 14, "target_num": 14},
                "main_site_pc": {"current_num": 0, "target_num": 0, "is_na": True, "remark": "当前不涉及"},
                "api_upgrade": {"current_num": 0, "target_num": 4},
            },
            "logs": [
                {"log_date": datetime(2026, 2, 1, 10, 0), "item_key": "backend_support", "content": "后台程序支持完成", "progress_delta": 20, "progress_after": 20, "is_milestone": False},
                {"log_date": datetime(2026, 2, 10, 10, 0), "item_key": "condition_order", "content": "条件单支持完成", "progress_delta": 20, "progress_after": 40, "is_milestone": False},
                {"log_date": datetime(2026, 3, 5, 10, 0), "item_key": "main_site_app", "content": "APP升级完成14/14", "progress_delta": 30, "progress_after": 70, "is_milestone": True, "remark": "关键里程碑"},
            ],
            "risks": [
                {"title": "接口升级未完成", "description": "接口升级仍未开始", "impact_desc": "影响整体完结", "level": "中", "status": "处理中", "planned_resolve_date": date(2026, 4, 25)},
            ],
        },
        "东吴": {
            "input_mode": "明细",
            "overall_status": "推进中",
            "overall_conclusion": "推进中",
            "latest_update_at": datetime(2026, 4, 18, 9, 0),
            "remark": "APP推进中，接口未完成",
            "values": {
                "backend_support": {"status_value": "已支持"},
                "condition_order": {"status_value": "已支持"},
                "main_site_app": {"current_num": 10, "target_num": 60},
                "main_site_pc": {"current_num": 0, "target_num": 0, "remark": "暂未推进"},
                "api_upgrade": {"current_num": 0, "target_num": 4},
            },
            "logs": [
                {"log_date": datetime(2026, 1, 1, 9, 0), "item_key": "backend_support", "content": "完成后台程序支持", "progress_delta": 20, "progress_after": 20, "is_milestone": False},
                {"log_date": datetime(2026, 1, 5, 9, 0), "item_key": "condition_order", "content": "完成条件单支持", "progress_delta": 20, "progress_after": 40, "is_milestone": False},
                {"log_date": datetime(2026, 3, 1, 9, 0), "item_key": "main_site_app", "content": "APP完成10/60", "progress_delta": 5, "progress_after": 45, "is_milestone": False},
            ],
            "risks": [
                {"title": "接口升级未启动", "description": "接口升级仍为0/4", "impact_desc": "影响整体完成", "level": "高", "status": "处理中", "planned_resolve_date": date(2026, 4, 25)},
                {"title": "APP推进偏慢", "description": "当前仅完成10/60", "impact_desc": "影响主站升级节奏", "level": "中", "status": "持续关注", "planned_resolve_date": date(2026, 4, 28)},
            ],
        },
        "国金": {
            "input_mode": "明细",
            "overall_status": "推进中",
            "overall_conclusion": "推进中",
            "remark": "后台和条件单已就绪",
            "values": {
                "backend_support": {"status_value": "就绪"},
                "condition_order": {"status_value": "就绪"},
                "main_site_app": {"current_num": 0, "target_num": 0, "remark": "待补录"},
                "main_site_pc": {"current_num": 0, "target_num": 0, "remark": "待补录"},
                "api_upgrade": {"current_num": 0, "target_num": 0, "remark": "待补录"},
            },
        },
    }

    partial_ready_brokers = ["中金", "恒泰", "粤开", "江海", "渤海"]
    unsupported_brokers = ["国新", "前海", "德邦", "天风"]
    supported_brokers = ["中天国富", "财信", "华福", "兴业", "国联民生", "中信建投", "国融", "国元", "西部"]

    for broker_name in partial_ready_brokers:
        local_route_data[broker_name] = {
            "input_mode": "明细",
            "overall_status": "推进中",
            "overall_conclusion": "推进中",
            "remark": "后台就绪，条件单未完成",
            "values": {
                "backend_support": {"status_value": "就绪"},
                "condition_order": {"status_value": "未开始", "remark": "当前为0"},
                "main_site_app": {"current_num": 0, "target_num": 0, "remark": "待补录"},
                "main_site_pc": {"current_num": 0, "target_num": 0, "remark": "待补录"},
                "api_upgrade": {"current_num": 0, "target_num": 0, "remark": "待补录"},
            },
        }

    for broker_name in unsupported_brokers:
        local_route_data[broker_name] = {
            "input_mode": "简化",
            "overall_status": "未开始",
            "overall_conclusion": "不支持",
            "remark": "均不支持",
            "values": {
                "backend_support": {"status_value": "不支持"},
                "condition_order": {"status_value": "不支持"},
                "main_site_app": {"current_num": 0, "target_num": 0, "remark": "不支持"},
                "main_site_pc": {"current_num": 0, "target_num": 0, "remark": "不支持"},
                "api_upgrade": {"current_num": 0, "target_num": 4, "remark": "不支持"},
            },
        }

    for broker_name in supported_brokers:
        local_route_data[broker_name] = {
            "input_mode": "简化",
            "overall_status": "已完成",
            "overall_conclusion": "支持",
            "remark": "当前只有支持结论",
            "values": {
                "backend_support": {"status_value": "已支持", "remark": "简化导入"},
                "condition_order": {"status_value": "已支持", "remark": "简化导入"},
                "main_site_app": {"current_num": 1, "target_num": 1, "remark": "简化导入"},
                "main_site_pc": {"current_num": 1, "target_num": 1, "remark": "简化导入"},
                "api_upgrade": {"current_num": 1, "target_num": 1, "remark": "简化导入"},
            },
        }

    for broker_name in PROGRESS_BROKERS:
        _ensure_progress_instance(
            session=session,
            existing_instances=existing_instances,
            broker=broker_map[broker_name],
            template=template_map["local_route_upgrade"],
            item_map=item_map,
            payload=local_route_data[broker_name],
        )
        _ensure_progress_instance(
            session=session,
            existing_instances=existing_instances,
            broker=broker_map[broker_name],
            template=template_map["linux_main_site"],
            item_map=item_map,
            payload=_default_status_payload("未开始"),
        )
        _ensure_progress_instance(
            session=session,
            existing_instances=existing_instances,
            broker=broker_map[broker_name],
            template=template_map["xinchuang_upgrade"],
            item_map=item_map,
            payload=_default_status_payload("未开始"),
        )


def _default_status_payload(status_value: str) -> dict:
    return {
        "input_mode": "明细",
        "overall_status": "未开始",
        "overall_conclusion": "未开始",
        "remark": "初始导入",
        "values": {
            "solution_confirm": {"status_value": status_value},
            "env_prepare": {"status_value": status_value},
            "deploy_install": {"status_value": status_value},
            "joint_test": {"status_value": status_value},
            "go_live": {"status_value": status_value},
            "broker_confirm": {"status_value": status_value},
            "compatibility_test": {"status_value": status_value},
            "acceptance": {"status_value": status_value},
        },
    }


def _ensure_progress_instance(session: Session, existing_instances: dict, broker: Broker, template: ProgressProjectTemplate, item_map: dict, payload: dict) -> None:
    key = (template.code, broker.name)
    instance = existing_instances.get(key)
    now = datetime.now()
    if instance is None:
        instance = ProgressBrokerProjectInstance(
            project_template_id=template.id,
            broker_id=broker.id,
            input_mode=payload.get("input_mode", "明细"),
            overall_status=payload.get("overall_status", "未开始"),
            overall_conclusion=payload.get("overall_conclusion"),
            owner_name=payload.get("owner_name"),
            latest_update_at=payload.get("latest_update_at"),
            remark=payload.get("remark"),
            created_at=now,
            updated_at=now,
        )
        session.add(instance)
        session.flush()
        existing_instances[key] = instance

    existing_values = {item.item_template.item_key: item for item in instance.values}
    existing_log_keys = {(log.log_date, log.content) for log in instance.logs}
    existing_risk_keys = {risk.title for risk in instance.risks}

    for item in template.items:
        value_payload = payload.get("values", {}).get(item.item_key)
        if value_payload is None and template.code != "local_route_upgrade":
            value_payload = payload.get("values", {}).get(item.item_key, {"status_value": "未开始"})
        if value_payload is None:
            continue

        value = existing_values.get(item.item_key)
        if value is None:
            value = ProgressItemValue(
                broker_project_instance_id=instance.id,
                item_template_id=item.id,
                updated_at=payload.get("latest_update_at") or now,
            )
            session.add(value)
            instance.values.append(value)

        value.status_value = value_payload.get("status_value")
        value.current_num = value_payload.get("current_num")
        value.target_num = value_payload.get("target_num")
        value.bool_value = value_payload.get("bool_value")
        value.text_value = value_payload.get("text_value")
        value.is_na = bool(value_payload.get("is_na", False))
        value.remark = value_payload.get("remark")
        value.calculated_percent = _calculate_item_percent(item.item_type, value.status_value, value.current_num, value.target_num, value.is_na)
        value.updated_at = payload.get("latest_update_at") or now

    session.flush()

    for log_payload in payload.get("logs", []):
        log_key = (log_payload["log_date"], log_payload["content"])
        if log_key in existing_log_keys:
            continue
        session.add(
            ProgressLog(
                broker_project_instance_id=instance.id,
                item_template_id=item_map[(template.code, log_payload["item_key"])].id if log_payload.get("item_key") else None,
                log_date=log_payload["log_date"],
                content=log_payload["content"],
                progress_delta=log_payload.get("progress_delta", 0),
                progress_after=log_payload.get("progress_after", 0),
                is_milestone=log_payload.get("is_milestone", False),
                remark=log_payload.get("remark"),
                created_by="系统初始化",
                created_at=now,
            )
        )

    for risk_payload in payload.get("risks", []):
        if risk_payload["title"] in existing_risk_keys:
            continue
        session.add(
            ProgressRisk(
                broker_project_instance_id=instance.id,
                title=risk_payload["title"],
                description=risk_payload.get("description"),
                impact_desc=risk_payload.get("impact_desc"),
                level=risk_payload["level"],
                owner_name=risk_payload.get("owner_name"),
                planned_resolve_date=risk_payload.get("planned_resolve_date"),
                status=risk_payload.get("status", "待处理"),
                remark=risk_payload.get("remark"),
                created_at=now,
                updated_at=now,
            )
        )

    session.flush()
    _refresh_progress_instance(instance)


def _calculate_item_percent(item_type: str, status_value: str, current_num: int, target_num: int, is_na: bool) -> int:
    if is_na:
        return 0
    if item_type == "status":
        return STATUS_PROGRESS_MAP.get(status_value or "未开始", 0)
    if item_type == "number_progress":
        if not target_num or target_num <= 0:
            return 0
        return max(0, min(100, round((current_num or 0) / target_num * 100)))
    return 0


def _refresh_progress_instance(instance: ProgressBrokerProjectInstance) -> None:
    valid_values = [value for value in instance.values if not value.is_na]
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
    instance.latest_update_at = max(
        [item.log_date for item in instance.logs] + ([instance.latest_update_at] if instance.latest_update_at else []) + [item.updated_at for item in instance.values if item.updated_at],
        default=None,
    )

    if instance.overall_conclusion == "不支持":
        instance.overall_status = "未开始"
    elif progress_percent >= 100:
        instance.overall_status = "已完成"
    elif progress_percent > 0:
        instance.overall_status = "推进中"
    else:
        instance.overall_status = "未开始"


def seed_runtime_data(session: Session) -> None:

    broker_a = Broker(name="A券商", short_name="A券商", status="active")
    broker_b = Broker(name="B券商", short_name="B券商", status="active")
    broker_c = Broker(name="C券商", short_name="C券商", status="active")

    session.add_all([broker_a, broker_b, broker_c])
    session.flush()

    project_a = Project(
        broker_id=broker_a.id,
        name="2026-04-20 版本升级",
        project_type="版本升级",
        owner_name="张三",
        planned_date=date(2026, 4, 20),
        status="执行中",
        progress_percent=75,
        description="涉及后台程序包、接口包、条件单包交付与验证，当前最大风险点为条件单包交付延迟。",
    )
    project_b = Project(
        broker_id=broker_b.id,
        name="接口改造",
        project_type="接口改造",
        owner_name="李四",
        planned_date=date(2026, 4, 18),
        status="准备中",
        progress_percent=40,
        description="联调进入第二轮，验证任务临期，需关注接口窗口。",
    )
    project_c = Project(
        broker_id=broker_c.id,
        name="新接入项目",
        project_type="常规对接",
        owner_name="王五",
        planned_date=date(2026, 4, 24),
        status="执行中",
        progress_percent=55,
        description="当前主要风险为环境未就绪，影响首轮验证节奏。",
    )

    session.add_all([project_a, project_b, project_c])
    session.flush()

    session.add_all(
        [
            Task(
                project_id=project_a.id,
                name="后台程序包",
                owner_name="张三",
                planned_content="提供程序包",
                planned_date=date(2026, 4, 15),
                actual_action="已提交",
                completion_result="完成",
                status="已完成",
            ),
            Task(
                project_id=project_a.id,
                name="接口包",
                owner_name="李四",
                planned_content="提供接口包",
                planned_date=date(2026, 4, 16),
                actual_action="联调中",
                completion_result="进行中",
                status="进行中",
            ),
            Task(
                project_id=project_a.id,
                name="条件单包",
                owner_name="王五",
                planned_content="提供条件单包",
                planned_date=date(2026, 4, 14),
                actual_action="未提交",
                completion_result="未完成",
                status="已逾期",
            ),
            Task(
                project_id=project_b.id,
                name="接口验证",
                owner_name="李四",
                planned_content="完成第二轮联调验证",
                planned_date=date(2026, 4, 15),
                actual_action="联调中",
                completion_result="进行中",
                status="进行中",
            ),
            Task(
                project_id=project_c.id,
                name="环境确认",
                owner_name="王五",
                planned_content="协调对方开放验证环境",
                planned_date=date(2026, 4, 16),
                actual_action="待反馈",
                completion_result="未完成",
                status="待对方反馈",
            ),
        ]
    )

    session.add_all(
        [
            Risk(
                project_id=project_a.id,
                title="接口验证延迟",
                level="高风险",
                affects_milestone=True,
                owner_name="李四",
                planned_resolve_date=date(2026, 4, 17),
                status="处理中",
                action_plan="增加联调窗口，确保 4/17 前完成验证。",
            ),
            Risk(
                project_id=project_a.id,
                title="对方环境未就绪",
                level="中风险",
                affects_milestone=False,
                owner_name="张三",
                planned_resolve_date=date(2026, 4, 18),
                status="持续关注",
                action_plan="提前确认窗口，必要时拆分验证计划。",
            ),
            Risk(
                project_id=project_c.id,
                title="环境未提供",
                level="高风险",
                affects_milestone=True,
                owner_name="王五",
                planned_resolve_date=date(2026, 4, 16),
                status="待处理",
                action_plan="本周内协调对方开放环境，必要时升级处理。",
            ),
        ]
    )

    session.add_all(
        [
            ProjectLog(
                project_id=project_a.id,
                log_date=datetime(2026, 4, 13, 9, 30),
                content="接口包已开始第二轮联调",
                next_action="今晚确认联调结果，必要时明早补窗口。",
            ),
            ProjectLog(
                project_id=project_a.id,
                log_date=datetime(2026, 4, 13, 10, 20),
                content="条件单包仍未收到，已提醒负责人",
                next_action="在风险中心继续跟进并视情况调整计划。",
            ),
        ]
    )

    session.add_all(
        [
            Reminder(
                type="逾期",
                broker_name="A券商",
                project_name="4月20日版本升级",
                item_name="条件单包",
                level="高风险",
                deadline=date(2026, 4, 14),
                status="待处理",
                description="仍未提交，已影响升级准备。",
            ),
            Reminder(
                type="临期",
                broker_name="B券商",
                project_name="接口改造",
                item_name="接口验证",
                level="中风险",
                deadline=date(2026, 4, 15),
                status="处理中",
                description="距离计划时间还有 2 天，当前仍在联调。",
            ),
            Reminder(
                type="高风险",
                broker_name="C券商",
                project_name="新接入项目",
                item_name="环境未提供",
                level="高风险",
                deadline=date(2026, 4, 16),
                status="待处理",
                description="影响首轮验证，需要本周协调对方开放环境。",
            ),
        ]
    )

    session.add_all(
        [
            Template(
                name="版本升级模板",
                template_type="升级",
                scene="版本升级、投产、上线准备",
                task_count=8,
                risk_count=4,
                recent_use_count=10,
            ),
            Template(
                name="接口改造模板",
                template_type="改造",
                scene="接口联调、协议调整、改造验证",
                task_count=6,
                risk_count=3,
                recent_use_count=5,
            ),
            Template(
                name="常规对接模板",
                template_type="对接",
                scene="常规需求接入、资料准备、例行事项",
                task_count=7,
                risk_count=2,
                recent_use_count=3,
            ),
        ]
    )

    session.commit()


def seed_template_blueprints(session: Session) -> None:
    templates = session.query(Template).all()
    if not templates:
        return

    template_map = {item.name: item for item in templates}

    upgrade_template = template_map.get("版本升级模板")
    if upgrade_template is not None:
        session.add_all(
            [
                TemplateTask(
                    template_id=upgrade_template.id,
                    name="后台程序包",
                    planned_content="提供程序包",
                    default_owner_name="张三",
                    offset_days=-5,
                ),
                TemplateTask(
                    template_id=upgrade_template.id,
                    name="接口包",
                    planned_content="提供接口包",
                    default_owner_name="李四",
                    offset_days=-4,
                ),
                TemplateTask(
                    template_id=upgrade_template.id,
                    name="条件单包",
                    planned_content="提供条件单包",
                    default_owner_name="王五",
                    offset_days=-6,
                ),
                TemplateRisk(
                    template_id=upgrade_template.id,
                    title="交付延迟",
                    level="高风险",
                    affects_milestone=True,
                    action_plan="提前确认交付时间，如延误立即升级处理。",
                    offset_days=-3,
                ),
                TemplateRisk(
                    template_id=upgrade_template.id,
                    title="环境未就绪",
                    level="中风险",
                    affects_milestone=False,
                    action_plan="提前确认环境与窗口安排。",
                    offset_days=-2,
                ),
            ]
        )

    api_template = template_map.get("接口改造模板")
    if api_template is not None:
        session.add_all(
            [
                TemplateTask(
                    template_id=api_template.id,
                    name="接口联调",
                    planned_content="完成联调验证",
                    default_owner_name="李四",
                    offset_days=-3,
                ),
                TemplateTask(
                    template_id=api_template.id,
                    name="回归验证",
                    planned_content="完成回归验证",
                    default_owner_name="王五",
                    offset_days=-1,
                ),
                TemplateRisk(
                    template_id=api_template.id,
                    title="接口不兼容",
                    level="高风险",
                    affects_milestone=True,
                    action_plan="保留回退方案，并提前做兼容校验。",
                    offset_days=-2,
                ),
            ]
        )

    routine_template = template_map.get("常规对接模板")
    if routine_template is not None:
        session.add_all(
            [
                TemplateTask(
                    template_id=routine_template.id,
                    name="需求确认",
                    planned_content="确认需求与交付清单",
                    default_owner_name="张三",
                    offset_days=-4,
                ),
                TemplateTask(
                    template_id=routine_template.id,
                    name="资料准备",
                    planned_content="准备资料与对接清单",
                    default_owner_name="王五",
                    offset_days=-2,
                ),
                TemplateRisk(
                    template_id=routine_template.id,
                    title="资料缺失",
                    level="中风险",
                    affects_milestone=False,
                    action_plan="提前检查资料完整性，缺失项滚动追踪。",
                    offset_days=-2,
                ),
            ]
        )

    session.commit()


def ensure_personal_tasks(session: Session) -> None:
    admin_user = session.query(User).filter(User.username == "admin").first()
    admin_user_id = admin_user.id if admin_user is not None else 1
    normal_user = session.query(User).filter(User.username == "user01").first()
    normal_user_id = normal_user.id if normal_user is not None else admin_user_id

    if session.query(PersonalTask).filter(PersonalTask.user_id == admin_user_id).first() is None:
        parent_template = PersonalTask(
            user_id=admin_user_id,
            title="沉淀升级模板",
            category="长期",
            priority="中",
            note="把版本升级类项目整理成统一模板",
            planned_date=None,
            status="待办",
            sort_order=1,
            created_at=datetime(2026, 4, 10, 10, 0),
        )
        completed_parent = PersonalTask(
            user_id=admin_user_id,
            title="完善个人任务机制",
            category="长期",
            priority="低",
            note="拆分每日和长期任务，并沉淀完成记录",
            completion_result="已完成个人任务机制拆分，并验证历史沉淀流程。",
            planned_date=None,
            status="已完成",
            sort_order=2,
            created_at=datetime(2026, 4, 8, 11, 0),
            completed_at=datetime(2026, 4, 12, 18, 0),
        )
        session.add_all([parent_template, completed_parent])
        session.flush()

        session.add_all(
            [
                PersonalTask(
                    user_id=admin_user_id,
                    title="检查今日高风险事项",
                    category="每日",
                    priority="高",
                    note="先看风险中心里的逾期和高风险项目",
                    planned_date=date(2026, 4, 14),
                    status="待办",
                    sort_order=1,
                    created_at=datetime(2026, 4, 14, 9, 0),
                ),
                PersonalTask(
                    user_id=admin_user_id,
                    title="整理本周周报",
                    category="每日",
                    priority="中",
                    note="核对重点项目进展和需协调事项",
                    planned_date=date(2026, 4, 14),
                    status="待办",
                    sort_order=2,
                    created_at=datetime(2026, 4, 14, 9, 30),
                ),
                PersonalTask(
                    user_id=admin_user_id,
                    parent_task_id=parent_template.id,
                    title="补充升级模板任务字段",
                    category="每日",
                    priority="中",
                    note="把任务默认负责人和偏移天数补齐",
                    planned_date=date(2026, 4, 15),
                    status="待办",
                    sort_order=1,
                    created_at=datetime(2026, 4, 15, 9, 15),
                ),
            ]
        )

    if session.query(PersonalTask).filter(PersonalTask.user_id == normal_user_id).first() is None:
        weekly_parent = PersonalTask(
            user_id=normal_user_id,
            title="跟进个人周报",
            category="长期",
            priority="低",
            note="持续整理本周完成情况和下周计划",
            planned_date=None,
            status="待办",
            sort_order=1,
            created_at=datetime(2026, 4, 15, 9, 30),
        )
        session.add(weekly_parent)
        session.flush()

        session.add_all(
            [
                PersonalTask(
                    user_id=normal_user_id,
                    title="整理个人待办",
                    category="每日",
                    priority="中",
                    note="确认今天要完成的个人任务和临期事项",
                    planned_date=date(2026, 4, 15),
                    status="待办",
                    sort_order=1,
                    created_at=datetime(2026, 4, 15, 9, 0),
                ),
                PersonalTask(
                    user_id=normal_user_id,
                    parent_task_id=weekly_parent.id,
                    title="汇总本周完成事项",
                    category="每日",
                    priority="中",
                    note="整理本周已完成任务清单",
                    planned_date=date(2026, 4, 15),
                    status="待办",
                    sort_order=1,
                    created_at=datetime(2026, 4, 15, 10, 0),
                ),
            ]
        )

    admin_parent = (
        session.query(PersonalTask)
        .filter(
            PersonalTask.user_id == admin_user_id,
            PersonalTask.category == "长期",
            PersonalTask.title == "沉淀升级模板",
        )
        .first()
    )
    if admin_parent is not None and session.query(PersonalTask).filter(PersonalTask.parent_task_id == admin_parent.id).first() is None:
        session.add(
            PersonalTask(
                user_id=admin_user_id,
                parent_task_id=admin_parent.id,
                title="补充升级模板任务字段",
                category="每日",
                priority="中",
                note="把任务默认负责人和偏移天数补齐",
                planned_date=date(2026, 4, 15),
                status="待办",
                sort_order=1,
                created_at=datetime(2026, 4, 15, 9, 15),
            )
        )

    normal_parent = (
        session.query(PersonalTask)
        .filter(
            PersonalTask.user_id == normal_user_id,
            PersonalTask.category == "长期",
            PersonalTask.title == "跟进个人周报",
        )
        .first()
    )
    if normal_parent is not None and session.query(PersonalTask).filter(PersonalTask.parent_task_id == normal_parent.id).first() is None:
        session.add(
            PersonalTask(
                user_id=normal_user_id,
                parent_task_id=normal_parent.id,
                title="汇总本周完成事项",
                category="每日",
                priority="中",
                note="整理本周已完成任务清单",
                planned_date=date(2026, 4, 15),
                status="待办",
                sort_order=1,
                created_at=datetime(2026, 4, 15, 10, 0),
            )
        )
    session.commit()


def ensure_users(session: Session) -> None:
    existing = {user.username for user in session.query(User).all()}
    pending = []

    if "admin" not in existing:
        pending.append(
            User(
                username="admin",
                display_name="系统管理员",
                password_hash=hash_password("admin123"),
                role="admin",
                status="active",
                created_at=datetime.now(),
            )
        )

    if "user01" not in existing:
        pending.append(
            User(
                username="user01",
                display_name="普通成员",
                password_hash=hash_password("user123"),
                role="user",
                status="active",
                created_at=datetime.now(),
            )
        )

    if pending:
        session.add_all(pending)
        session.commit()
