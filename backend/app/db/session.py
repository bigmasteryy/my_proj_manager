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
