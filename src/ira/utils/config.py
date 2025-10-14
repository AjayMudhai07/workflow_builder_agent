"""
Configuration management for IRA Workflow Builder.

Handles loading and accessing configuration from environment variables
and configuration files.
"""

import os
from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="IRA Workflow Builder", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=True, alias="API_RELOAD")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_chat_model_id: str = Field(default="gpt-4o", alias="OPENAI_CHAT_MODEL_ID")

    # Azure OpenAI
    azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_chat_deployment_name: Optional[str] = Field(
        default=None, alias="AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
    )

    # Storage
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    uploads_dir: str = Field(default="./data/uploads", alias="UPLOADS_DIR")
    outputs_dir: str = Field(default="./data/outputs", alias="OUTPUTS_DIR")
    storage_dir: str = Field(default="./storage", alias="STORAGE_DIR")
    checkpoints_dir: str = Field(default="./storage/checkpoints", alias="CHECKPOINTS_DIR")
    logs_dir: str = Field(default="./logs", alias="LOGS_DIR")

    # Workflow
    max_questions: int = Field(default=10, alias="MAX_QUESTIONS")
    max_code_execution_time: int = Field(default=120, alias="MAX_CODE_EXECUTION_TIME")
    max_file_size_mb: int = Field(default=100, alias="MAX_FILE_SIZE_MB")

    # Observability
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    tracing_level: str = Field(default="framework", alias="TRACING_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_config() -> Settings:
    """
    Get the global configuration settings.

    Returns:
        Settings instance with all configuration values

    Example:
        >>> config = get_config()
        >>> print(config.api_port)
        8000
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def load_config(config_file: Optional[str] = None) -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_file: Path to YAML configuration file

    Returns:
        Dictionary containing configuration

    Example:
        >>> config = load_config("config/development.yaml")
        >>> print(config["app"]["name"])
        'IRA Workflow Builder'
    """
    if config_file is None:
        # Auto-detect based on environment
        env = os.getenv("APP_ENV", "development")
        config_file = f"config/{env}.yaml"

    config_path = Path(config_file)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration setting.

    Args:
        key: Configuration key (dot-notation supported)
        default: Default value if key not found

    Returns:
        Configuration value or default

    Example:
        >>> port = get_setting("api_port", 8000)
        >>> print(port)
        8000
    """
    config = get_config()
    return getattr(config, key, default)
