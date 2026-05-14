from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "guardrail.db"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Enterprise Security Guardrail Auditor"
    app_env: str = "local"
    debug: bool = False

    database_url: str = f"sqlite:///{_DEFAULT_DB_PATH}"

    upload_dir: Path = PROJECT_ROOT / "uploads"
    reports_dir: Path = PROJECT_ROOT / "reports"
    max_upload_mb: int = 16


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
