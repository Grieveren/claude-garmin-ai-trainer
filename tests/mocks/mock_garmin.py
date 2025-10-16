"""
Mock Garmin Connect service for testing.

Provides:
- Realistic API response simulation
- Different user scenarios (well-rested, tired, overtrained)
- API error simulation (rate limits, network errors)
- Performance testing data generation
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json
import random
from enum import Enum


class GarminError(Exception):
    """Base exception for Garmin mock errors."""

    pass


class GarminAuthError(GarminError):
    """Authentication error (invalid credentials)."""

    pass


class GarminRateLimitError(GarminError):
    """Rate limit exceeded error."""

    pass


class GarminNetworkError(GarminError):
    """Network connection error."""

    pass


class UserScenario(str, Enum):
    """User health scenarios for mock data generation."""

    WELL_RESTED = "well_rested"  # High HRV, good sleep, low stress
    NORMAL = "normal"  # Balanced metrics
    TIRED = "tired"  # Low HRV, poor sleep, high stress
    OVERTRAINED = "overtrained"  # Very low HRV, high stress, poor recovery


@dataclass
class MockGarminConfig:
    """Configuration for mock Garmin service behavior."""

    user_scenario: UserScenario = UserScenario.NORMAL
    fail_on_auth: bool = False
    fail_on_rate_limit: bool = False
    fail_on_network: bool = False
    delay_seconds: float = 0.0
    partial_data: bool = False


class MockGarminConnect:
    """
    Mock GarminConnect service matching real API behavior.

    Simulates realistic Garmin Connect responses including:
    - Daily metrics and activities
    - Sleep data with stages
    - HRV and stress readings
    - Heart rate zones
    - Different user states
    """

    def __init__(self, config: Optional[MockGarminConfig] = None):
        """
        Initialize mock Garmin service.

        Args:
            config: MockGarminConfig for behavior customization
        """
        self.config = config or MockGarminConfig()
        self.authenticated = False
        self.auth_token = None

    def authenticate(self, email: str, password: str) -> Dict[str, str]:
        """
        Simulate authentication to Garmin.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with auth_token and session_id

        Raises:
            GarminAuthError: If auth fails
            GarminNetworkError: If network error
        """
        if self.config.fail_on_auth:
            raise GarminAuthError("Invalid credentials (mock)")

        if self.config.fail_on_network:
            raise GarminNetworkError("Network connection failed (mock)")

        self.authenticated = True
        self.auth_token = f"mock_token_{random.randint(10000, 99999)}"

        return {
            "auth_token": self.auth_token,
            "session_id": f"session_{random.randint(10000, 99999)}",
            "user_id": "mock_user_123",
        }

    def get_daily_metrics(
        self, user_id: str, date_obj: date
    ) -> Dict[str, Any]:
        """
        Get daily metrics for a specific date.

        Args:
            user_id: Garmin user ID
            date_obj: Date for metrics

        Returns:
            Dict with daily metrics

        Raises:
            GarminRateLimitError: If rate limited
            GarminNetworkError: If network error
        """
        if self.config.fail_on_rate_limit:
            raise GarminRateLimitError("Rate limit exceeded (mock)")

        if self.config.fail_on_network:
            raise GarminNetworkError("Network connection failed (mock)")

        # Generate realistic metrics based on scenario
        metrics = self._generate_daily_metrics(self.config.user_scenario, date_obj)

        if self.config.partial_data:
            # Remove some fields to simulate incomplete data
            metrics.pop("stress_score", None)
            metrics.pop("hrv_sdnn", None)

        return metrics

    def get_activities(self, user_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get activities for date range.

        Args:
            user_id: Garmin user ID
            start_date: Start date
            end_date: End date

        Returns:
            List of activity dicts

        Raises:
            GarminRateLimitError: If rate limited
        """
        if self.config.fail_on_rate_limit:
            raise GarminRateLimitError("Rate limit exceeded (mock)")

        num_days = (end_date - start_date).days + 1
        activities = []

        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)

            # ~70% chance of activity per day
            if random.random() < 0.7:
                activity = self._generate_activity(current_date)
                activities.append(activity)

        return activities

    def get_sleep_data(self, user_id: str, date_obj: date) -> Dict[str, Any]:
        """
        Get sleep data for a specific date.

        Args:
            user_id: Garmin user ID
            date_obj: Date for sleep data

        Returns:
            Dict with sleep session data

        Raises:
            GarminNetworkError: If network error
        """
        if self.config.fail_on_network:
            raise GarminNetworkError("Network connection failed (mock)")

        return self._generate_sleep_data(self.config.user_scenario, date_obj)

    def get_hrv_data(self, user_id: str, date_obj: date) -> Dict[str, Any]:
        """
        Get HRV (Heart Rate Variability) data.

        Args:
            user_id: Garmin user ID
            date_obj: Date for HRV data

        Returns:
            Dict with HRV readings

        Raises:
            GarminNetworkError: If network error
        """
        if self.config.fail_on_network:
            raise GarminNetworkError("Network connection failed (mock)")

        return self._generate_hrv_data(self.config.user_scenario, date_obj)

    def get_heart_rate_zones(self, user_id: str, activity_id: str) -> Dict[str, Any]:
        """
        Get heart rate zone breakdown for activity.

        Args:
            user_id: Garmin user ID
            activity_id: Activity ID

        Returns:
            Dict with HR zone data
        """
        return {
            "activity_id": activity_id,
            "zones": [
                {"zone": 1, "seconds": 300, "display": "Zone 1 (50-60%)", "label": "Warm Up"},
                {"zone": 2, "seconds": 1200, "display": "Zone 2 (60-70%)", "label": "Endurance"},
                {"zone": 3, "seconds": 900, "display": "Zone 3 (70-80%)", "label": "Steady State"},
                {"zone": 4, "seconds": 600, "display": "Zone 4 (80-90%)", "label": "Threshold"},
                {"zone": 5, "seconds": 300, "display": "Zone 5 (90-100%)", "label": "Maximum"},
            ],
        }

    # ========================================================================
    # PRIVATE: DATA GENERATION METHODS
    # ========================================================================

    @staticmethod
    def _generate_daily_metrics(
        scenario: UserScenario, date_obj: date
    ) -> Dict[str, Any]:
        """Generate realistic daily metrics based on user scenario."""
        base_metrics = {
            "date": date_obj.isoformat(),
            "steps": random.randint(5000, 15000),
            "distance_meters": random.randint(3000, 15000),
            "calories": random.randint(1800, 3000),
            "active_minutes": random.randint(30, 120),
            "floors_climbed": random.randint(1, 20),
            "resting_heart_rate": 55,
            "max_heart_rate": random.randint(160, 180),
            "avg_heart_rate": random.randint(85, 130),
            "body_battery_charged": random.randint(20, 50),
            "body_battery_drained": random.randint(30, 60),
            "body_battery_max": 100,
            "body_battery_min": random.randint(10, 30),
            "vo2_max": random.uniform(50.0, 55.0),
            "fitness_age": random.randint(25, 35),
            "weight_kg": random.uniform(73.0, 77.0),
            "body_fat_percent": random.uniform(14.0, 18.0),
            "bmi": random.uniform(22.0, 24.0),
            "hydration_ml": random.randint(1800, 2500),
            "avg_respiration_rate": random.uniform(13.0, 16.0),
        }

        # Adjust metrics based on scenario
        if scenario == UserScenario.WELL_RESTED:
            base_metrics.update({
                "hrv_sdnn": random.uniform(55.0, 70.0),  # High HRV
                "hrv_rmssd": random.uniform(40.0, 55.0),
                "stress_score": random.randint(15, 35),  # Low stress
                "resting_heart_rate": 52,
                "avg_heart_rate": random.randint(85, 110),
                "sleep_score": random.randint(80, 95),
                "total_sleep_minutes": random.randint(420, 480),
            })

        elif scenario == UserScenario.TIRED:
            base_metrics.update({
                "hrv_sdnn": random.uniform(30.0, 40.0),  # Low HRV
                "hrv_rmssd": random.uniform(20.0, 30.0),
                "stress_score": random.randint(65, 85),  # High stress
                "resting_heart_rate": 62,
                "avg_heart_rate": random.randint(110, 140),
                "sleep_score": random.randint(50, 65),
                "total_sleep_minutes": random.randint(300, 360),
            })

        elif scenario == UserScenario.OVERTRAINED:
            base_metrics.update({
                "hrv_sdnn": random.uniform(25.0, 35.0),  # Very low HRV
                "hrv_rmssd": random.uniform(15.0, 25.0),
                "stress_score": random.randint(75, 95),  # Very high stress
                "resting_heart_rate": 65,
                "avg_heart_rate": random.randint(130, 150),
                "sleep_score": random.randint(35, 55),
                "total_sleep_minutes": random.randint(270, 330),
            })

        else:  # NORMAL
            base_metrics.update({
                "hrv_sdnn": random.uniform(40.0, 55.0),  # Normal HRV
                "hrv_rmssd": random.uniform(30.0, 40.0),
                "stress_score": random.randint(35, 55),  # Normal stress
                "sleep_score": random.randint(65, 80),
                "total_sleep_minutes": random.randint(360, 420),
            })

        # Add sleep stage breakdown
        base_metrics.update({
            "deep_sleep_minutes": int(base_metrics["total_sleep_minutes"] * 0.20),
            "light_sleep_minutes": int(base_metrics["total_sleep_minutes"] * 0.58),
            "rem_sleep_minutes": int(base_metrics["total_sleep_minutes"] * 0.18),
            "awake_minutes": int(base_metrics["total_sleep_minutes"] * 0.04),
        })

        return base_metrics

    @staticmethod
    def _generate_activity(date_obj: date) -> Dict[str, Any]:
        """Generate realistic activity data."""
        activity_types = ["running", "cycling", "swimming", "strength_training", "yoga"]
        activity_type = random.choice(activity_types)

        # Duration based on type
        durations = {
            "running": random.randint(1800, 5400),  # 30-90 min
            "cycling": random.randint(2400, 7200),  # 40-120 min
            "swimming": random.randint(1800, 3600),  # 30-60 min
            "strength_training": random.randint(1800, 3600),  # 30-60 min
            "yoga": random.randint(1200, 2400),  # 20-40 min
        }

        duration_seconds = durations.get(activity_type, 3000)

        start_time = datetime.combine(date_obj, datetime.min.time()).replace(
            hour=random.randint(5, 18), minute=random.randint(0, 59)
        )

        return {
            "id": random.randint(10000000, 99999999),
            "activity_name": f"Mock {activity_type.title()}",
            "start_time_in_seconds": int(start_time.timestamp()),
            "activity_type": activity_type,
            "duration_seconds": duration_seconds,
            "distance_meters": random.uniform(1000, 20000),
            "average_heart_rate": random.randint(120, 160),
            "max_heart_rate": random.randint(160, 180),
            "calories": int(duration_seconds / 10),
            "training_effect_aerobic": random.uniform(1.0, 4.0),
            "training_effect_anaerobic": random.uniform(0.0, 2.0),
            "training_load": random.randint(50, 300),
            "recovery_time_hours": random.randint(12, 48),
        }

    @staticmethod
    def _generate_sleep_data(
        scenario: UserScenario, date_obj: date
    ) -> Dict[str, Any]:
        """Generate realistic sleep data based on scenario."""
        if scenario == UserScenario.WELL_RESTED:
            sleep_duration = random.randint(420, 480)  # 7-8 hours
            quality = "excellent"

        elif scenario == UserScenario.TIRED:
            sleep_duration = random.randint(270, 330)  # 4.5-5.5 hours
            quality = "poor"

        elif scenario == UserScenario.OVERTRAINED:
            sleep_duration = random.randint(300, 360)  # 5-6 hours
            quality = "fair"

        else:  # NORMAL
            sleep_duration = random.randint(360, 420)  # 6-7 hours
            quality = "good"

        sleep_start = datetime.combine(
            date_obj - timedelta(days=1), datetime.min.time()
        ).replace(hour=23, minute=random.randint(0, 59))
        sleep_end = sleep_start + timedelta(minutes=sleep_duration)

        return {
            "date": date_obj.isoformat(),
            "sleep_start_timestamp": int(sleep_start.timestamp()),
            "sleep_end_timestamp": int(sleep_end.timestamp()),
            "duration_minutes": sleep_duration,
            "deep_sleep_minutes": int(sleep_duration * 0.20),
            "light_sleep_minutes": int(sleep_duration * 0.58),
            "rem_sleep_minutes": int(sleep_duration * 0.18),
            "awake_minutes": int(sleep_duration * 0.04),
            "average_heart_rate": random.randint(45, 65),
            "max_heart_rate": random.randint(70, 95),
            "min_heart_rate": random.randint(40, 55),
            "average_respiration_rate": random.uniform(12.0, 16.0),
            "sleep_quality": quality,
            "sleep_score": random.randint(50, 95),
            "awakenings_count": random.randint(0, 5),
        }

    @staticmethod
    def _generate_hrv_data(scenario: UserScenario, date_obj: date) -> Dict[str, Any]:
        """Generate realistic HRV data based on scenario."""
        reading_time = datetime.combine(date_obj, datetime.min.time()).replace(hour=6, minute=0)

        if scenario == UserScenario.WELL_RESTED:
            hrv_sdnn = random.uniform(55.0, 70.0)
            status = "high"

        elif scenario == UserScenario.TIRED:
            hrv_sdnn = random.uniform(30.0, 40.0)
            status = "low"

        elif scenario == UserScenario.OVERTRAINED:
            hrv_sdnn = random.uniform(25.0, 35.0)
            status = "low"

        else:  # NORMAL
            hrv_sdnn = random.uniform(40.0, 55.0)
            status = "balanced"

        return {
            "date": date_obj.isoformat(),
            "reading_time": reading_time.isoformat(),
            "reading_type": "morning",
            "hrv_sdnn": hrv_sdnn,
            "hrv_rmssd": hrv_sdnn * 0.72,
            "hrv_pnn50": hrv_sdnn * 0.45,
            "average_heart_rate": random.randint(48, 72),
            "status": status,
            "recovery_status": "good" if status == "high" else "recovering" if status == "balanced" else "poor",
        }

    @staticmethod
    def simulate_sync_multiple_days(
        mock_garmin: "MockGarminConnect",
        user_id: str,
        start_date: date,
        end_date: date,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> Dict[str, Any]:
        """
        Simulate syncing multiple days of data.

        Useful for testing data import pipelines.

        Args:
            mock_garmin: MockGarminConnect instance
            user_id: User ID
            start_date: Start date
            end_date: End date
            on_error: Callback for error handling

        Returns:
            Summary of synced data
        """
        summary = {
            "total_days": 0,
            "metrics_synced": 0,
            "activities_synced": 0,
            "sleep_sessions_synced": 0,
            "errors": [],
        }

        current_date = start_date
        while current_date <= end_date:
            try:
                # Sync daily metrics
                mock_garmin.get_daily_metrics(user_id, current_date)
                summary["metrics_synced"] += 1

                # Sync activities
                activities = mock_garmin.get_activities(user_id, current_date, current_date)
                summary["activities_synced"] += len(activities)

                # Sync sleep data
                mock_garmin.get_sleep_data(user_id, current_date)
                summary["sleep_sessions_synced"] += 1

                summary["total_days"] += 1

            except Exception as e:
                summary["errors"].append(str(e))
                if on_error:
                    on_error(e)

            current_date += timedelta(days=1)

        return summary
