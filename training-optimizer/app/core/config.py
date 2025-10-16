"""
Application configuration management.

This module handles all configuration settings using Pydantic Settings,
loading values from environment variables and .env files.
"""

from datetime import date
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Garmin Credentials
    garmin_email: str = Field(description="Garmin Connect email address")
    garmin_password: str = Field(description="Garmin Connect password")

    # Claude AI API
    anthropic_api_key: str = Field(description="Anthropic API key for Claude")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/training_data.db",
        description="Database connection URL"
    )

    # Application
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")
    secret_key: str = Field(description="Secret key for security")
    debug: bool = Field(default=False, description="Debug mode")

    # Scheduling
    sync_hour: int = Field(default=8, ge=0, le=23, description="Hour for daily sync")
    sync_minute: int = Field(default=0, ge=0, le=59, description="Minute for daily sync")
    timezone: str = Field(default="America/New_York", description="Application timezone")

    # Notifications
    enable_email_notifications: bool = Field(
        default=False,
        description="Enable email notifications"
    )
    smtp_server: Optional[str] = Field(default=None, description="SMTP server")
    smtp_port: Optional[int] = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")

    # User Profile
    athlete_name: str = Field(default="Athlete", description="Athlete's name")
    athlete_age: int = Field(default=30, ge=10, le=100, description="Athlete's age")
    max_heart_rate: int = Field(
        default=188,
        ge=100,
        le=250,
        description="Maximum heart rate"
    )
    resting_heart_rate: int = Field(
        default=48,
        ge=30,
        le=100,
        description="Resting heart rate"
    )

    # Training Goal
    training_goal: str = Field(
        default="general_fitness",
        description="Training goal (marathon, half_marathon, 5k, 10k, general_fitness)"
    )
    target_race_date: Optional[date] = Field(
        default=None,
        description="Target race date"
    )

    # AI Settings
    ai_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude AI model to use"
    )
    ai_cache_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours to cache AI responses"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(
        default="logs/training_optimizer.log",
        description="Log file path"
    )

    @field_validator("training_goal")
    @classmethod
    def validate_training_goal(cls, v: str) -> str:
        """Validate training goal is one of the allowed values."""
        allowed_goals = [
            "marathon",
            "half_marathon",
            "5k",
            "10k",
            "general_fitness",
            "triathlon"
        ]
        if v.lower() not in allowed_goals:
            raise ValueError(
                f"training_goal must be one of {allowed_goals}, got '{v}'"
            )
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(
                f"log_level must be one of {allowed_levels}, got '{v}'"
            )
        return v_upper

    @property
    def base_dir(self) -> Path:
        """Get the base directory of the application."""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self.base_dir / "data"

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory path."""
        return self.base_dir / "logs"

    @property
    def templates_dir(self) -> Path:
        """Get the templates directory path."""
        return self.base_dir / "app" / "templates"

    @property
    def static_dir(self) -> Path:
        """Get the static files directory path."""
        return self.base_dir / "app" / "static"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function is useful for dependency injection in FastAPI.

    Returns:
        Settings: The global settings instance
    """
    return settings
