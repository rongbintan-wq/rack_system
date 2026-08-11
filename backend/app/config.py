"""应用配置：从环境变量读取，区分 DEV / PROD。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "企业级智能机柜管理系统 (DCIM-Lite)"
    ENV: str = "dev"  # dev | prod
    DEBUG: bool = True

    # SQLite 初期；后期切换 MySQL 只需改这条连接串
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'dcim.db'}"

    SECRET_KEY: str = "change-me-in-prod-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 默认管理员（仅 DEV 初始化用，PROD 应通过注册/导入创建）
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # DEV 下可关闭鉴权，方便本地联调；PROD 必须为 true
    REQUIRE_AUTH: bool = False

    CORS_ORIGINS: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
