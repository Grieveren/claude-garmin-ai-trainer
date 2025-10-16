"""
Tests for configuration management.
"""

import os
import pytest
from datetime import date
from pydantic import ValidationError

from app.core.config import Settings, get_settings, reload_settings


class TestConfigValidation:
    """Test configuration validation"""

    def test_valid_config(self, monkeypatch):
        """Test valid configuration loads successfully"""
        # Set valid environment variables
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "test-password-12345")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-test-key-1234567890")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-32-chars-long")
        monkeypatch.setenv("ATHLETE_NAME", "Test Athlete")
        monkeypatch.setenv("ATHLETE_AGE", "35")
        monkeypatch.setenv("ATHLETE_GENDER", "male")
        monkeypatch.setenv("MAX_HEART_RATE", "185")
        monkeypatch.setenv("RESTING_HEART_RATE", "55")
        monkeypatch.setenv("TRAINING_GOAL", "Test goal")

        settings = reload_settings()

        assert settings.garmin_email == "test@example.com"
        assert settings.athlete_age == 35
        assert settings.max_heart_rate == 185

    def test_missing_required_field(self, monkeypatch, tmp_path):
        """Test that missing required fields raise ValidationError"""
        # Clear all required environment variables
        required_vars = [
            "GARMIN_EMAIL",
            "GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY",
            "SECRET_KEY",
            "ATHLETE_NAME",
            "ATHLETE_AGE",
            "ATHLETE_GENDER",
            "MAX_HEART_RATE",
            "RESTING_HEART_RATE",
            "TRAINING_GOAL",
        ]

        for var in required_vars:
            monkeypatch.delenv(var, raising=False)

        # Change to a temporary directory without .env file
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            with pytest.raises(ValidationError):
                Settings()
        finally:
            # Restore original directory
            os.chdir(original_dir)

    def test_invalid_email(self, monkeypatch):
        """Test invalid email format"""
        monkeypatch.setenv("GARMIN_EMAIL", "not-an-email")
        monkeypatch.setenv("GARMIN_PASSWORD", "test-password-12345")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-test-key-1234567890")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-32-chars-long")
        monkeypatch.setenv("ATHLETE_NAME", "Test")
        monkeypatch.setenv("ATHLETE_AGE", "35")
        monkeypatch.setenv("ATHLETE_GENDER", "male")
        monkeypatch.setenv("MAX_HEART_RATE", "185")
        monkeypatch.setenv("RESTING_HEART_RATE", "55")
        monkeypatch.setenv("TRAINING_GOAL", "Test")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "email" in str(exc_info.value).lower()

    def test_age_validation(self, monkeypatch):
        """Test age must be in valid range"""
        self._set_valid_env(monkeypatch)
        monkeypatch.setenv("ATHLETE_AGE", "150")  # Too old

        with pytest.raises(ValidationError):
            Settings()

    def test_heart_rate_validation(self, monkeypatch):
        """Test heart rate validation"""
        self._set_valid_env(monkeypatch)

        # Max HR too low
        monkeypatch.setenv("MAX_HEART_RATE", "50")
        with pytest.raises(ValidationError):
            Settings()

        # Resting HR >= Max HR
        monkeypatch.setenv("MAX_HEART_RATE", "150")
        monkeypatch.setenv("RESTING_HEART_RATE", "150")
        with pytest.raises(ValidationError):
            Settings()

    def test_hr_reserve_calculation(self, monkeypatch):
        """Test heart rate reserve calculation"""
        self._set_valid_env(monkeypatch)
        monkeypatch.setenv("MAX_HEART_RATE", "185")
        monkeypatch.setenv("RESTING_HEART_RATE", "55")

        settings = Settings()
        assert settings.hr_reserve == 130

    def test_secret_key_default_blocked(self, monkeypatch):
        """Test that default secret key is blocked"""
        self._set_valid_env(monkeypatch)
        monkeypatch.setenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")

        with pytest.raises(ValidationError):
            Settings()

    def test_training_types_list(self, monkeypatch):
        """Test training types parsing"""
        self._set_valid_env(monkeypatch)
        monkeypatch.setenv("PREFERRED_TRAINING_TYPES", "running,cycling,swimming")

        settings = Settings()
        assert settings.training_types_list == ["running", "cycling", "swimming"]

    def test_safe_config_dict_masks_sensitive(self, monkeypatch):
        """Test that sensitive data is masked in safe config"""
        self._set_valid_env(monkeypatch)

        settings = Settings()
        safe_config = settings.get_safe_config_dict()

        # Check sensitive fields are masked
        assert "*" in safe_config["garmin_password"]
        assert "*" in safe_config["anthropic_api_key"]
        assert "*" in safe_config["secret_key"]

        # Check non-sensitive fields are not masked
        assert safe_config["athlete_name"] == "Test Athlete"
        assert safe_config["max_heart_rate"] == 185

    @staticmethod
    def _set_valid_env(monkeypatch):
        """Helper to set valid environment variables"""
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "test-password-12345")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-test-key-1234567890")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-32-chars-long")
        monkeypatch.setenv("ATHLETE_NAME", "Test Athlete")
        monkeypatch.setenv("ATHLETE_AGE", "35")
        monkeypatch.setenv("ATHLETE_GENDER", "male")
        monkeypatch.setenv("MAX_HEART_RATE", "185")
        monkeypatch.setenv("RESTING_HEART_RATE", "55")
        monkeypatch.setenv("TRAINING_GOAL", "Test goal")


class TestAIModelValidation:
    """Test AI model validation"""

    def test_valid_models(self, monkeypatch):
        """Test valid AI models are accepted"""
        TestConfigValidation._set_valid_env(monkeypatch)

        valid_models = [
            "claude-sonnet-4-5-20250929",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
        ]

        for model in valid_models:
            monkeypatch.setenv("AI_MODEL", model)
            settings = Settings()
            assert settings.ai_model == model

    def test_invalid_model(self, monkeypatch):
        """Test invalid AI model raises error"""
        TestConfigValidation._set_valid_env(monkeypatch)
        monkeypatch.setenv("AI_MODEL", "invalid-model-name")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "Invalid AI model" in str(exc_info.value)


class TestTargetDateValidation:
    """Test target race date validation"""

    def test_future_date_valid(self, monkeypatch):
        """Test future date is valid"""
        TestConfigValidation._set_valid_env(monkeypatch)
        future_date = date(2026, 12, 31)
        monkeypatch.setenv("TARGET_RACE_DATE", future_date.isoformat())

        settings = Settings()
        assert settings.target_race_date == future_date

    def test_past_date_invalid(self, monkeypatch):
        """Test past date raises error"""
        TestConfigValidation._set_valid_env(monkeypatch)
        past_date = date(2020, 1, 1)
        monkeypatch.setenv("TARGET_RACE_DATE", past_date.isoformat())

        with pytest.raises(ValidationError):
            Settings()
