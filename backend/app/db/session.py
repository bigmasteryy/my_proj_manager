from __future__ import annotations

from pathlib import Path
from typing import Dict, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _sqlite_connect_args() -> Dict[str, bool]:
    if settings.database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.database_url,
    future=True,
    connect_args=_sqlite_connect_args(),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    if settings.database_url.startswith("sqlite:///"):
        db_file = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    from app.db import models  # noqa: F401
    from app.db.seed import seed_database

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        _apply_sqlite_compat_migrations(connection)

    with SessionLocal() as session:
        seed_database(session)


def reset_demo_database() -> None:
    if settings.database_url.startswith("sqlite:///"):
        db_file = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    from app.db import models  # noqa: F401
    from app.db.seed import seed_database

    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        _apply_sqlite_compat_migrations(connection)

    with SessionLocal() as session:
        seed_database(session)


def _apply_sqlite_compat_migrations(connection) -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    broker_columns = {
        row[1]
        for row in connection.execute(text("PRAGMA table_info(brokers)")).fetchall()
    }
    if broker_columns and "business_status" not in broker_columns:
        connection.execute(text("ALTER TABLE brokers ADD COLUMN business_status VARCHAR(20) DEFAULT '待对接'"))
        connection.execute(text("UPDATE brokers SET business_status = '待对接' WHERE business_status IS NULL"))
    if broker_columns and "system_version" not in broker_columns:
        connection.execute(text("ALTER TABLE brokers ADD COLUMN system_version VARCHAR(50)"))
    if broker_columns and "system_version_updated_at" not in broker_columns:
        connection.execute(text("ALTER TABLE brokers ADD COLUMN system_version_updated_at DATETIME"))
    if broker_columns and "system_version_content" not in broker_columns:
        connection.execute(text("ALTER TABLE brokers ADD COLUMN system_version_content TEXT"))
    if broker_columns and "is_featured" not in broker_columns:
        connection.execute(text("ALTER TABLE brokers ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
        connection.execute(
            text(
                """
                UPDATE brokers
                SET is_featured = 1
                WHERE id IN (
                    SELECT id
                    FROM brokers
                    ORDER BY id ASC
                    LIMIT 6
                )
                """
            )
        )

    personal_columns = {
        row[1]
        for row in connection.execute(text("PRAGMA table_info(personal_tasks)")).fetchall()
    }
    if personal_columns and "sort_order" not in personal_columns:
        connection.execute(text("ALTER TABLE personal_tasks ADD COLUMN sort_order INTEGER DEFAULT 0"))
    if personal_columns and "completion_result" not in personal_columns:
        connection.execute(text("ALTER TABLE personal_tasks ADD COLUMN completion_result TEXT"))
    if personal_columns and "user_id" not in personal_columns:
        connection.execute(text("ALTER TABLE personal_tasks ADD COLUMN user_id INTEGER DEFAULT 1"))
        connection.execute(text("UPDATE personal_tasks SET user_id = 1 WHERE user_id IS NULL"))
    if personal_columns and "parent_task_id" not in personal_columns:
        connection.execute(text("ALTER TABLE personal_tasks ADD COLUMN parent_task_id INTEGER"))

    progress_template_columns = {
        row[1]
        for row in connection.execute(text("PRAGMA table_info(progress_project_templates)")).fetchall()
    }
    if progress_template_columns and "is_featured" not in progress_template_columns:
        connection.execute(text("ALTER TABLE progress_project_templates ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
        connection.execute(
            text(
                """
                UPDATE progress_project_templates
                SET is_featured = 1
                WHERE id IN (
                    SELECT id
                    FROM progress_project_templates
                    ORDER BY sort_no ASC, id ASC
                    LIMIT 3
                )
                """
            )
        )

    progress_task_table = connection.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='progress_tasks'")
    ).fetchone()
    if progress_task_table is None:
        connection.execute(
            text(
                """
                CREATE TABLE progress_tasks (
                    id INTEGER NOT NULL,
                    broker_project_instance_id INTEGER NOT NULL,
                    item_template_id INTEGER,
                    stage2_step_instance_id INTEGER,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    owner_name VARCHAR(100),
                    collaborator_names VARCHAR(255),
                    priority VARCHAR(20) NOT NULL DEFAULT '中',
                    status VARCHAR(20) NOT NULL DEFAULT '未开始',
                    planned_start_date DATE,
                    planned_finish_date DATE,
                    actual_finish_date DATE,
                    completion_result TEXT,
                    remark TEXT,
                    created_by VARCHAR(100),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    PRIMARY KEY (id),
                    FOREIGN KEY(broker_project_instance_id) REFERENCES progress_broker_project_instances (id),
                    FOREIGN KEY(item_template_id) REFERENCES progress_item_templates (id),
                    FOREIGN KEY(stage2_step_instance_id) REFERENCES progress_stage2_step_instances (id)
                )
                """
            )
        )
