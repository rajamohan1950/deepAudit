from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    database_url: str = "postgresql+asyncpg://deepaudit:deepaudit@localhost:5432/deepaudit"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_llm_provider: Literal["openai", "anthropic"] = "openai"
    default_llm_model: str = "gpt-4o"
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 120

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # File storage
    repo_storage_path: str = "/tmp/deepaudit/repos"
    max_repo_size_mb: int = 500

    # Rate limiting
    rate_limit_requests_per_minute: int = 60

    # Audit engine
    max_concurrent_phases: int = 3

    # GitHub App
    github_app_id: str = ""
    github_app_private_key_path: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"


settings = Settings()
