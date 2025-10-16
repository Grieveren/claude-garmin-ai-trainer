"""
Configuration management using Pydantic settings.

Loads configuration from environment variables and .env file with comprehensive
validation and type checking. Handles sensitive credentials securely.
"""

import os
from datetime import date, time
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import EmailStr, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable loading.

    All settings can be overridden via environment variables.
    Sensitive values (passwords, API keys) should be provided via environment
    variables or .env file, never committed to version control.
    """

    # ==================== Database Settings ====================
    database_url: str = Field(
        default="sqlite:///./data/training_data.db",
        description="Database connection URL",
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Database connection pool size",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Database pool timeout in seconds",
    )

    # ==================== Garmin Settings (Sensitive) ====================
    garmin_email: EmailStr = Field(
        ...,
        description="Garmin Connect account email",
    )
    garmin_password: str = Field(
        ...,
        min_length=8,
        description="Garmin Connect account password (encrypted at rest)",
    )
    garmin_sync_enabled: bool = Field(
        default=True,
        description="Enable automatic Garmin data synchronization",
    )

    # ==================== Claude AI Settings (Sensitive) ====================
    anthropic_api_key: str = Field(
        ...,
        min_length=20,
        description="Anthropic API key for Claude AI",
    )
    ai_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude AI model to use for analysis",
    )
    ai_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=8192,
        description="Maximum tokens for AI responses",
    )
    ai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for AI response generation",
    )
    ai_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="API request timeout in seconds",
    )

    # ==================== Application Settings ====================
    app_name: str = Field(
        default="AI Training Optimizer",
        description="Application name",
    )
    app_host: str = Field(
        default="0.0.0.0",
        description="FastAPI server host",
    )
    app_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="FastAPI server port",
    )
    secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key for session management and encryption",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )

    # ==================== Scheduling Settings ====================
    sync_time: time = Field(
        default=time(6, 0),
        description="Daily Garmin sync time (HH:MM)",
    )
    sync_timezone: str = Field(
        default="UTC",
        description="Timezone for scheduling (e.g., 'Europe/Berlin', 'America/New_York')",
    )
    sync_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed syncs",
    )

    # ==================== Notification Settings ====================
    notifications_enabled: bool = Field(
        default=True,
        description="Enable notifications",
    )
    notification_email: Optional[EmailStr] = Field(
        default=None,
        description="Email address for notifications",
    )
    smtp_host: Optional[str] = Field(
        default=None,
        description="SMTP server host",
    )
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port",
    )
    smtp_username: Optional[str] = Field(
        default=None,
        description="SMTP authentication username",
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP authentication password",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP connection",
    )

    # ==================== User Profile Settings ====================
    athlete_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Athlete's full name",
    )
    athlete_age: int = Field(
        ...,
        ge=10,
        le=100,
        description="Athlete's age in years",
    )
    athlete_gender: Literal["male", "female", "other"] = Field(
        ...,
        description="Athlete's gender for HR calculations",
    )
    athlete_weight: Optional[float] = Field(
        default=None,
        ge=30.0,
        le=300.0,
        description="Athlete's weight in kilograms",
    )
    athlete_height: Optional[float] = Field(
        default=None,
        ge=100.0,
        le=250.0,
        description="Athlete's height in centimeters",
    )

    # Heart Rate Settings
    max_heart_rate: int = Field(
        ...,
        ge=100,
        le=220,
        description="Maximum heart rate (bpm)",
    )
    resting_heart_rate: int = Field(
        ...,
        ge=30,
        le=100,
        description="Resting heart rate (bpm)",
    )
    lactate_threshold_hr: Optional[int] = Field(
        default=None,
        ge=100,
        le=220,
        description="Lactate threshold heart rate (bpm) - optional",
    )
    vo2_max: Optional[float] = Field(
        default=None,
        ge=20.0,
        le=100.0,
        description="VO2 max value (ml/kg/min) - optional",
    )

    # ==================== Training Settings ====================
    training_goal: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Primary training goal (e.g., 'Marathon under 3 hours')",
    )
    target_race_date: Optional[date] = Field(
        default=None,
        description="Target race/event date",
    )
    weekly_training_days: int = Field(
        default=6,
        ge=1,
        le=7,
        description="Number of training days per week",
    )
    weekly_training_hours: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=40.0,
        description="Target weekly training hours",
    )
    injury_history: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Relevant injury history",
    )

    # Training preferences
    preferred_training_types: str = Field(
        default="running,cycling",
        description="Comma-separated list of preferred training types",
    )
    avoid_morning_runs: bool = Field(
        default=False,
        description="Avoid scheduling morning runs",
    )

    # ==================== Logging Settings ====================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_file: str = Field(
        default="logs/training_optimizer.log",
        description="Log file path",
    )
    log_max_bytes: int = Field(
        default=10485760,  # 10MB
        ge=1048576,  # 1MB
        le=104857600,  # 100MB
        description="Maximum log file size in bytes",
    )
    log_backup_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of log file backups to keep",
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )

    # ==================== Feature Flags ====================
    enable_ai_analysis: bool = Field(
        default=True,
        description="Enable AI-powered analysis features",
    )
    enable_fatigue_monitoring: bool = Field(
        default=True,
        description="Enable fatigue monitoring and alerts",
    )
    enable_workout_recommendations: bool = Field(
        default=True,
        description="Enable AI workout recommendations",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        use_enum_values=True,
    )

    # ==================== Validators ====================

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is sufficiently complex"""
        if v == "CHANGE_ME_IN_PRODUCTION":
            raise ValueError(
                "Secret key must be changed from default value. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    @field_validator("ai_model")
    @classmethod
    def validate_ai_model(cls, v: str) -> str:
        """Validate AI model name"""
        valid_models = [
            "claude-sonnet-4-5-20250929",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        if v not in valid_models:
            raise ValueError(
                f"Invalid AI model '{v}'. Must be one of: {', '.join(valid_models)}"
            )
        return v

    @field_validator("sync_timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone string"""
        try:
            import zoneinfo
            zoneinfo.ZoneInfo(v)
        except Exception:
            # Fallback for systems without zoneinfo
            try:
                import pytz
                pytz.timezone(v)
            except Exception:
                raise ValueError(
                    f"Invalid timezone '{v}'. Examples: 'UTC', 'Europe/Berlin', 'America/New_York'"
                )
        return v

    @model_validator(mode='after')
    def validate_heart_rates(self) -> 'Settings':
        """Validate heart rate relationships"""
        max_hr = self.max_heart_rate
        resting_hr = self.resting_heart_rate
        lactate_hr = self.lactate_threshold_hr

        if max_hr and resting_hr:
            if resting_hr >= max_hr:
                raise ValueError(
                    f"Resting heart rate ({resting_hr}) must be less than "
                    f"maximum heart rate ({max_hr})"
                )

            # Check if values are physiologically reasonable
            hr_reserve = max_hr - resting_hr
            if hr_reserve < 50:
                raise ValueError(
                    f"Heart rate reserve ({hr_reserve} bpm) seems too low. "
                    "Please verify your max and resting heart rates."
                )

        if lactate_hr and max_hr and resting_hr:
            if lactate_hr <= resting_hr or lactate_hr >= max_hr:
                raise ValueError(
                    f"Lactate threshold HR ({lactate_hr}) must be between "
                    f"resting ({resting_hr}) and max ({max_hr}) heart rates"
                )

        return self

    @model_validator(mode='after')
    def validate_notifications(self) -> 'Settings':
        """Validate notification settings"""
        if self.notifications_enabled:
            if not self.notification_email:
                raise ValueError(
                    "notification_email is required when notifications are enabled"
                )

            if self.notification_email:
                # Check SMTP settings if email is configured
                required_smtp = ["smtp_host", "smtp_username", "smtp_password"]
                missing = []
                if not self.smtp_host:
                    missing.append("smtp_host")
                if not self.smtp_username:
                    missing.append("smtp_username")
                if not self.smtp_password:
                    missing.append("smtp_password")

                if missing:
                    raise ValueError(
                        f"SMTP configuration incomplete. Missing: {', '.join(missing)}"
                    )

        return self

    @model_validator(mode='after')
    def validate_training_goal(self) -> 'Settings':
        """Validate training goal and target date relationship"""
        target_date = self.target_race_date

        if target_date:
            from datetime import date as date_module
            today = date_module.today()

            if target_date < today:
                raise ValueError(
                    f"Target race date ({target_date}) cannot be in the past"
                )

            # Warn if race is very soon (less than 4 weeks)
            days_until_race = (target_date - today).days
            if days_until_race < 28:
                import warnings
                warnings.warn(
                    f"Target race is only {days_until_race} days away. "
                    "Limited time for training adaptations.",
                    UserWarning
                )

        return self

    # ==================== Computed Properties ====================

    @property
    def database_path(self) -> Path:
        """Get database file path"""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            return Path(db_path)
        return None

    @property
    def log_file_path(self) -> Path:
        """Get log file path"""
        return Path(self.log_file)

    @property
    def hr_reserve(self) -> int:
        """Calculate heart rate reserve (Karvonen method)"""
        return self.max_heart_rate - self.resting_heart_rate

    @property
    def training_types_list(self) -> list[str]:
        """Get list of preferred training types"""
        return [t.strip() for t in self.preferred_training_types.split(",")]

    def get_safe_config_dict(self) -> dict:
        """
        Get configuration dictionary with sensitive values masked.

        Use this for logging or displaying configuration.
        """
        config = self.dict()

        # Mask sensitive fields
        sensitive_fields = [
            "garmin_password",
            "anthropic_api_key",
            "secret_key",
            "smtp_password",
        ]

        for field in sensitive_fields:
            if field in config and config[field]:
                # Show first 4 chars + asterisks
                value = str(config[field])
                if len(value) > 4:
                    config[field] = f"{value[:4]}{'*' * (len(value) - 4)}"
                else:
                    config[field] = "****"

        return config

    def ensure_directories_exist(self) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            self.log_file_path.parent,
        ]

        if self.database_path:
            directories.append(self.database_path.parent)

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to ensure we only load and validate
    settings once during the application lifecycle.

    Returns:
        Settings: Validated settings instance

    Raises:
        ValidationError: If configuration is invalid
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Force reload settings (clear cache).

    Useful for testing or when configuration changes at runtime.

    Returns:
        Settings: New settings instance
    """
    get_settings.cache_clear()
    return get_settings()
