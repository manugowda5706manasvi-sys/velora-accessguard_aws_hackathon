"""
Pydantic Settings for AccessGuard AI.
All configuration comes from environment variables (never hardcoded).
"""

from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Auth
    admin_username: str = "admin"
    admin_password: str  # Required — no default, must be in env
    secret_key: str      # Required — no default, must be in env

    # Storage
    storage_backend: str = "sqlite"
    sqlite_db_path: str = "./data/accessguard.db"
    dynamodb_region: str = "ap-south-1"
    dynamodb_records_table: str = "accessguard-records"
    dynamodb_audit_table: str = "accessguard-audit"

    # App
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"

    # ML
    if_contamination: float = 0.08
    if_n_estimators: int = 200
    if_random_state: int = 42

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
