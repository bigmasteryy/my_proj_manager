from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Broker(Base):
    __tablename__ = "brokers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(50), nullable=False)
    contact_name = Column(String(50), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    note = Column(Text, nullable=True)

    projects = relationship("Project", back_populates="broker", cascade="all, delete-orphan")
    progress_instances = relationship("ProgressBrokerProjectInstance", back_populates="broker", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    broker_id = Column(Integer, ForeignKey("brokers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    project_type = Column(String(50), nullable=False)
    owner_name = Column(String(50), nullable=False)
    planned_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    progress_percent = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)

    broker = relationship("Broker", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("ProjectLog", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    owner_name = Column(String(50), nullable=False)
    planned_content = Column(Text, nullable=False)
    planned_date = Column(Date, nullable=False)
    actual_action = Column(Text, nullable=True)
    completion_result = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False)

    project = relationship("Project", back_populates="tasks")


class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    affects_milestone = Column(Boolean, nullable=False, default=False)
    owner_name = Column(String(50), nullable=False)
    planned_resolve_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    action_plan = Column(Text, nullable=False)

    project = relationship("Project", back_populates="risks")


class ProjectLog(Base):
    __tablename__ = "project_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    log_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    next_action = Column(Text, nullable=False)

    project = relationship("Project", back_populates="logs")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False)
    broker_name = Column(String(100), nullable=False)
    project_name = Column(String(100), nullable=False)
    item_name = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    template_type = Column(String(50), nullable=False)
    scene = Column(String(200), nullable=False)
    task_count = Column(Integer, nullable=False, default=0)
    risk_count = Column(Integer, nullable=False, default=0)
    recent_use_count = Column(Integer, nullable=False, default=0)

    tasks = relationship("TemplateTask", back_populates="template", cascade="all, delete-orphan")
    risks = relationship("TemplateRisk", back_populates="template", cascade="all, delete-orphan")


class TemplateTask(Base):
    __tablename__ = "template_tasks"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    name = Column(String(100), nullable=False)
    planned_content = Column(Text, nullable=False)
    default_owner_name = Column(String(50), nullable=True)
    offset_days = Column(Integer, nullable=False, default=0)

    template = relationship("Template", back_populates="tasks")


class TemplateRisk(Base):
    __tablename__ = "template_risks"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    title = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    affects_milestone = Column(Boolean, nullable=False, default=False)
    action_plan = Column(Text, nullable=False)
    offset_days = Column(Integer, nullable=False, default=0)

    template = relationship("Template", back_populates="risks")


class PersonalTask(Base):
    __tablename__ = "personal_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    parent_task_id = Column(Integer, ForeignKey("personal_tasks.id"), nullable=True)
    title = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)
    priority = Column(String(20), nullable=False, default="中")
    note = Column(Text, nullable=True)
    completion_result = Column(Text, nullable=True)
    planned_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="待办")
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="personal_tasks")
    parent_task = relationship("PersonalTask", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("PersonalTask", back_populates="parent_task", cascade="all, delete-orphan", single_parent=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="admin")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    personal_tasks = relationship("PersonalTask", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


class ProgressProjectTemplate(Base):
    __tablename__ = "progress_project_templates"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    project_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    sort_no = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    items = relationship("ProgressItemTemplate", back_populates="project_template", cascade="all, delete-orphan")
    instances = relationship("ProgressBrokerProjectInstance", back_populates="project_template", cascade="all, delete-orphan")
    stage2_groups = relationship("ProgressStage2GroupTemplate", back_populates="project_template", cascade="all, delete-orphan")
    stage2_steps = relationship("ProgressStage2StepTemplate", back_populates="project_template", cascade="all, delete-orphan")


class ProgressItemTemplate(Base):
    __tablename__ = "progress_item_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_template_id = Column(Integer, ForeignKey("progress_project_templates.id"), nullable=False)
    item_key = Column(String(50), nullable=False)
    item_label = Column(String(100), nullable=False)
    group_key = Column(String(50), nullable=True)
    group_label = Column(String(100), nullable=True)
    item_type = Column(String(30), nullable=False)
    weight = Column(Integer, nullable=False, default=0)
    allow_na = Column(Boolean, nullable=False, default=False)
    sort_no = Column(Integer, nullable=False, default=0)
    value_rule = Column(Text, nullable=True)
    remark = Column(Text, nullable=True)

    project_template = relationship("ProgressProjectTemplate", back_populates="items")
    values = relationship("ProgressItemValue", back_populates="item_template", cascade="all, delete-orphan")
    logs = relationship("ProgressLog", back_populates="item_template")


class ProgressBrokerProjectInstance(Base):
    __tablename__ = "progress_broker_project_instances"

    id = Column(Integer, primary_key=True, index=True)
    project_template_id = Column(Integer, ForeignKey("progress_project_templates.id"), nullable=False)
    broker_id = Column(Integer, ForeignKey("brokers.id"), nullable=False)
    input_mode = Column(String(20), nullable=False, default="明细")
    overall_status = Column(String(20), nullable=False, default="未开始")
    overall_conclusion = Column(String(20), nullable=True)
    owner_name = Column(String(100), nullable=True)
    progress_percent = Column(Integer, nullable=False, default=0)
    latest_update_at = Column(DateTime, nullable=True)
    risk_count = Column(Integer, nullable=False, default=0)
    milestone_count = Column(Integer, nullable=False, default=0)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    project_template = relationship("ProgressProjectTemplate", back_populates="instances")
    broker = relationship("Broker", back_populates="progress_instances")
    values = relationship("ProgressItemValue", back_populates="instance", cascade="all, delete-orphan")
    logs = relationship("ProgressLog", back_populates="instance", cascade="all, delete-orphan")
    risks = relationship("ProgressRisk", back_populates="instance", cascade="all, delete-orphan")
    stage2_step_instances = relationship("ProgressStage2StepInstance", back_populates="instance", cascade="all, delete-orphan")


class ProgressItemValue(Base):
    __tablename__ = "progress_item_values"

    id = Column(Integer, primary_key=True, index=True)
    broker_project_instance_id = Column(Integer, ForeignKey("progress_broker_project_instances.id"), nullable=False)
    item_template_id = Column(Integer, ForeignKey("progress_item_templates.id"), nullable=False)
    status_value = Column(String(30), nullable=True)
    current_num = Column(Integer, nullable=True)
    target_num = Column(Integer, nullable=True)
    bool_value = Column(Boolean, nullable=True)
    text_value = Column(String(500), nullable=True)
    is_na = Column(Boolean, nullable=False, default=False)
    calculated_percent = Column(Integer, nullable=False, default=0)
    remark = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False)

    instance = relationship("ProgressBrokerProjectInstance", back_populates="values")
    item_template = relationship("ProgressItemTemplate", back_populates="values")


class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id = Column(Integer, primary_key=True, index=True)
    broker_project_instance_id = Column(Integer, ForeignKey("progress_broker_project_instances.id"), nullable=False)
    item_template_id = Column(Integer, ForeignKey("progress_item_templates.id"), nullable=True)
    log_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    progress_delta = Column(Integer, nullable=False, default=0)
    progress_after = Column(Integer, nullable=False, default=0)
    is_milestone = Column(Boolean, nullable=False, default=False)
    remark = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False)

    instance = relationship("ProgressBrokerProjectInstance", back_populates="logs")
    item_template = relationship("ProgressItemTemplate", back_populates="logs")


class ProgressRisk(Base):
    __tablename__ = "progress_risks"

    id = Column(Integer, primary_key=True, index=True)
    broker_project_instance_id = Column(Integer, ForeignKey("progress_broker_project_instances.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    impact_desc = Column(Text, nullable=True)
    level = Column(String(20), nullable=False)
    owner_name = Column(String(100), nullable=True)
    planned_resolve_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="待处理")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    instance = relationship("ProgressBrokerProjectInstance", back_populates="risks")


class ProgressStage2GroupTemplate(Base):
    __tablename__ = "progress_stage2_group_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_template_id = Column(Integer, ForeignKey("progress_project_templates.id"), nullable=False)
    group_code = Column(String(50), nullable=False)
    group_name = Column(String(100), nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    remark = Column(Text, nullable=True)

    project_template = relationship("ProgressProjectTemplate", back_populates="stage2_groups")
    step_templates = relationship("ProgressStage2StepTemplate", back_populates="group_template", cascade="all, delete-orphan")


class ProgressStage2StepTemplate(Base):
    __tablename__ = "progress_stage2_step_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_template_id = Column(Integer, ForeignKey("progress_project_templates.id"), nullable=False)
    group_template_id = Column(Integer, ForeignKey("progress_stage2_group_templates.id"), nullable=False)
    step_code = Column(String(50), nullable=False)
    step_no_display = Column(String(20), nullable=False)
    step_name = Column(String(255), nullable=False)
    owners_default = Column(String(255), nullable=True)
    is_optional = Column(Boolean, nullable=False, default=False)
    is_last_step = Column(Boolean, nullable=False, default=False)
    applicable_rule = Column(Text, nullable=True)
    dependency_step_codes = Column(String(255), nullable=True)
    remark_template = Column(Text, nullable=True)
    sort_no = Column(Integer, nullable=False, default=0)

    project_template = relationship("ProgressProjectTemplate", back_populates="stage2_steps")
    group_template = relationship("ProgressStage2GroupTemplate", back_populates="step_templates")
    step_instances = relationship("ProgressStage2StepInstance", back_populates="step_template", cascade="all, delete-orphan")


class ProgressStage2StepInstance(Base):
    __tablename__ = "progress_stage2_step_instances"

    id = Column(Integer, primary_key=True, index=True)
    broker_project_instance_id = Column(Integer, ForeignKey("progress_broker_project_instances.id"), nullable=False)
    step_template_id = Column(Integer, ForeignKey("progress_stage2_step_templates.id"), nullable=False)
    owner_actual = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="未开始")
    remark = Column(Text, nullable=True)
    blocker_reason = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False)

    instance = relationship("ProgressBrokerProjectInstance", back_populates="stage2_step_instances")
    step_template = relationship("ProgressStage2StepTemplate", back_populates="step_instances")
