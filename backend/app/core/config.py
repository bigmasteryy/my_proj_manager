from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


LOCAL_DATA_DIR = Path(os.getenv("LOCALAPPDATA", Path.cwd())) / "BrokerProjectManager"
DEFAULT_SQLITE_PATH = LOCAL_DATA_DIR / "broker_pm_local.db"


class Settings(BaseSettings):
    project_name: str = "项目管理平台 API"
    api_prefix: str = "/api/v1"
    debug: bool = True
    allowed_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
