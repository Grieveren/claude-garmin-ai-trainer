"""
Tests for Garmin integration service.

Phase 2: Integration with Garmin Connect API
Tests mock Garmin service behavior and error handling.
"""

import pytest
from datetime import date, timedelta

from tests.mocks.mock_garmin import (
    MockGarminConnect,
    MockGarminConfig,
    UserScenario,
    GarminAuthError,
    GarminRateLimitError,
    GarminNetworkError,
)

# Check if garminconnect is available
try:
    import garminconnect
    GARMINCONNECT_AVAILABLE = True
except ImportError:
    GARMINCONNECT_AVAILABLE = False

skipif_no_garminconnect = pytest.mark.skipif(
    not GARMINCONNECT_AVAILABLE,
    reason="garminconnect module not installed"
)


class TestMockGarminAuthentication:
    """Test Garmin authentication mock."""

    @pytest.mark.unit
    def test_successful_authentication(self):
        """Test successful authentication returns token."""
        mock_garmin = MockGarminConnect()

        result = mock_garmin.authenticate("test@example.com", "password")

        assert "auth_token" in result
        assert "session_id" in result
        assert "user_id" in result
        assert mock_garmin.authenticated is True

    @pytest.mark.unit
    def test_authentication_failure(self):
        """Test authentication failure raises error."""
        config = MockGarminConfig(fail_on_auth=True)
        mock_garmin = MockGarminConnect(config)

        with pytest.raises(GarminAuthError):
            mock_garmin.authenticate("test@example.com", "wrong_password")

    @pytest.mark.unit
    def test_network_error_during_auth(self):
        """Test network error during authentication."""
        config = MockGarminConfig(fail_on_network=True)
        mock_garmin = MockGarminConnect(config)

        with pytest.raises(GarminNetworkError):
            mock_garmin.authenticate("test@example.com", "password")


class TestMockGarminDailyMetrics:
    """Test daily metrics retrieval."""

    @pytest.mark.unit
    def test_get_daily_metrics_well_rested(self):
        """Test daily metrics for well-rested user."""
        config = MockGarminConfig(user_scenario=UserScenario.WELL_RESTED)
        mock_garmin = MockGarminConnect(config)
        mock_garmin.authenticated = True

        metrics = mock_garmin.get_daily_metrics("user_123", date.today())

        assert metrics["hrv_sdnn"] > 50
        assert metrics["stress_score"] < 40
        assert metrics["sleep_score"] > 75

    @pytest.mark.unit
    def test_get_daily_metrics_tired(self):
        """Test daily metrics for tired user."""
        config = MockGarminConfig(user_scenario=UserScenario.TIRED)
        mock_garmin = MockGarminConnect(config)

        metrics = mock_garmin.get_daily_metrics("user_123", date.today())

        assert metrics["hrv_sdnn"] < 45
        assert metrics["stress_score"] > 60
        assert metrics["sleep_score"] < 70

    @pytest.mark.unit
    def test_get_daily_metrics_rate_limit(self):
        """Test rate limit error."""
        config = MockGarminConfig(fail_on_rate_limit=True)
        mock_garmin = MockGarminConnect(config)

        with pytest.raises(GarminRateLimitError):
            mock_garmin.get_daily_metrics("user_123", date.today())

    @pytest.mark.unit
    def test_metrics_with_partial_data(self):
        """Test metrics with missing fields."""
        config = MockGarminConfig(partial_data=True)
        mock_garmin = MockGarminConnect(config)

        metrics = mock_garmin.get_daily_metrics("user_123", date.today())

        assert "steps" in metrics
        assert "calories" in metrics


class TestMockGarminActivities:
    """Test activity retrieval."""

    @pytest.mark.unit
    def test_get_activities_date_range(self):
        """Test retrieving activities for date range."""
        mock_garmin = MockGarminConnect()

        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        activities = mock_garmin.get_activities("user_123", start_date, end_date)

        assert isinstance(activities, list)
        for activity in activities:
            assert "activity_type" in activity
            assert "duration_seconds" in activity

    @pytest.mark.unit
    def test_activities_have_realistic_types(self):
        """Test activities have realistic types."""
        mock_garmin = MockGarminConnect()

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        activities = mock_garmin.get_activities("user_123", start_date, end_date)

        valid_types = ["running", "cycling", "swimming", "strength_training", "yoga"]

        for activity in activities:
            assert activity["activity_type"] in valid_types


class TestMockGarminSleep:
    """Test sleep data retrieval."""

    @pytest.mark.unit
    def test_get_sleep_data(self):
        """Test retrieving sleep data."""
        mock_garmin = MockGarminConnect()

        sleep_data = mock_garmin.get_sleep_data("user_123", date.today())

        assert "duration_minutes" in sleep_data
        assert sleep_data["duration_minutes"] > 300
        assert sleep_data["duration_minutes"] < 600
        assert sleep_data["deep_sleep_minutes"] > 0
        assert sleep_data["rem_sleep_minutes"] > 0

    @pytest.mark.unit
    def test_sleep_data_well_rested(self):
        """Test sleep data for well-rested user."""
        config = MockGarminConfig(user_scenario=UserScenario.WELL_RESTED)
        mock_garmin = MockGarminConnect(config)

        sleep_data = mock_garmin.get_sleep_data("user_123", date.today())

        assert sleep_data["duration_minutes"] > 420
        assert sleep_data["sleep_quality"] == "excellent"

    @pytest.mark.unit
    def test_sleep_data_tired(self):
        """Test sleep data for tired user."""
        config = MockGarminConfig(user_scenario=UserScenario.TIRED)
        mock_garmin = MockGarminConnect(config)

        sleep_data = mock_garmin.get_sleep_data("user_123", date.today())

        assert sleep_data["duration_minutes"] < 360
        assert sleep_data["sleep_quality"] == "poor"


class TestMockGarminHRV:
    """Test HRV data retrieval."""

    @pytest.mark.unit
    def test_get_hrv_data(self):
        """Test retrieving HRV data."""
        mock_garmin = MockGarminConnect()

        hrv_data = mock_garmin.get_hrv_data("user_123", date.today())

        assert "hrv_sdnn" in hrv_data
        assert hrv_data["hrv_sdnn"] > 0
        assert hrv_data["hrv_sdnn"] < 150
        assert "status" in hrv_data


class TestGarminServiceRealImplementation:
    """Test the actual GarminService implementation."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        from app.core.config import Settings
        return Settings(
            garmin_email="test@example.com",
            garmin_password="test_password_123",
            anthropic_api_key="sk-ant-test-key-12345678901234567890",
            secret_key="test_secret_key_32_characters_long_ok",
            athlete_name="Test Athlete",
            athlete_age=30,
            athlete_gender="male",
            max_heart_rate=190,
            resting_heart_rate=50,
            training_goal="Test goal",
        )

    @pytest.mark.unit
    @skipif_no_garminconnect
    def test_service_initialization(self, mock_settings, tmp_path):
        """Test service initializes correctly."""
        from app.services.garmin_service import GarminService

        service = GarminService(settings=mock_settings, token_cache_dir=tmp_path)

        assert service.settings == mock_settings
        assert service.token_cache_dir == tmp_path
        assert service._authenticated is False

    @pytest.mark.unit
    @skipif_no_garminconnect
    def test_token_cache_file_path(self, mock_settings, tmp_path):
        """Test token cache file path generation."""
        from app.services.garmin_service import GarminService

        service = GarminService(settings=mock_settings, token_cache_dir=tmp_path)

        # Cache file should exist in cache directory
        assert service.token_cache_file.parent == tmp_path
        assert "garmin_token" in service.token_cache_file.name

    @pytest.mark.unit
    @pytest.mark.asyncio
    @skipif_no_garminconnect
    async def test_context_manager(self, mock_settings, tmp_path):
        """Test GarminService works as context manager."""
        from app.services.garmin_service import GarminService
        from unittest.mock import patch, MagicMock

        with patch('app.services.garmin_service.Garmin') as mock_garmin:
            mock_client = MagicMock()
            mock_client.session_data = {"token": "test"}
            mock_garmin.return_value = mock_client

            service = GarminService(settings=mock_settings, token_cache_dir=tmp_path)

            with service:
                assert service._authenticated is True

            mock_client.logout.assert_called_once()


class TestGarminServiceSchemaValidation:
    """Test Pydantic schema validation."""

    @pytest.mark.unit
    def test_daily_metrics_schema_validation(self):
        """Test GarminDailyMetrics schema validation."""
        from app.models.garmin_schemas import GarminDailyMetrics

        valid_data = {
            "metric_date": date.today(),
            "steps": 10000,
            "calories": 2500,
            "resting_heart_rate": 55,
            "max_heart_rate": 170,
        }

        metrics = GarminDailyMetrics(**valid_data)
        assert metrics.steps == 10000
        assert metrics.resting_heart_rate == 55

    @pytest.mark.unit
    def test_daily_metrics_invalid_hr_validation(self):
        """Test heart rate validation in schema."""
        from app.models.garmin_schemas import GarminDailyMetrics
        from pydantic import ValidationError

        invalid_data = {
            "metric_date": date.today(),
            "resting_heart_rate": 100,
            "max_heart_rate": 90,  # Max < Resting (invalid)
        }

        with pytest.raises(ValidationError):
            GarminDailyMetrics(**invalid_data)

    @pytest.mark.unit
    def test_sleep_data_schema_validation(self):
        """Test GarminSleepData schema validation."""
        from app.models.garmin_schemas import GarminSleepData
        from datetime import datetime

        sleep_start = datetime.now() - timedelta(hours=8)
        sleep_end = datetime.now()

        valid_data = {
            "sleep_date": date.today(),
            "sleep_start_time": sleep_start,
            "sleep_end_time": sleep_end,
            "total_sleep_minutes": 480,
            "deep_sleep_minutes": 120,
            "light_sleep_minutes": 240,
            "rem_sleep_minutes": 100,
            "awake_minutes": 20,
        }

        sleep_data = GarminSleepData(**valid_data)
        assert sleep_data.total_sleep_minutes == 480

    @pytest.mark.unit
    def test_activity_schema_validation(self):
        """Test GarminActivity schema validation."""
        from app.models.garmin_schemas import GarminActivity
        from datetime import datetime

        valid_data = {
            "garmin_activity_id": "12345",
            "activity_date": date.today(),
            "start_time": datetime.now(),
            "activity_type": "running",
            "duration_seconds": 3600,
            "distance_meters": 10000,
            "calories": 600,
        }

        activity = GarminActivity(**valid_data)
        assert activity.garmin_activity_id == "12345"
        assert activity.activity_type == "running"
