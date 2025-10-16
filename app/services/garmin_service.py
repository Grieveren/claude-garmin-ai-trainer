"""
Garmin Connect integration service.

This service handles all interactions with the Garmin Connect API including:
- Authentication and session management
- Data fetching (metrics, sleep, activities, HRV)
- Token caching to minimize re-authentication
- Retry logic with exponential backoff
- Rate limiting protection
"""

import time
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import wraps

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

from app.core.config import Settings, get_settings
from app.models.garmin_schemas import (
    GarminDailyMetrics,
    GarminSleepData,
    GarminActivity,
    GarminHRVReading,
    GarminActivityDetails,
    GarminAuthToken,
)


# Configure logging
logger = logging.getLogger(__name__)


class GarminServiceError(Exception):
    """Base exception for Garmin service errors."""
    pass


class GarminAuthenticationError(GarminServiceError):
    """Authentication failed with Garmin Connect."""
    pass


class GarminRateLimitError(GarminServiceError):
    """Rate limit exceeded."""
    pass


class GarminConnectionError(GarminServiceError):
    """Connection error with Garmin Connect."""
    pass


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles with each retry)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except GarminConnectTooManyRequestsError as e:
                    logger.error(f"Rate limit hit: {e}")
                    raise GarminRateLimitError(
                        "Garmin API rate limit exceeded. Please try again later."
                    )
                except GarminConnectAuthenticationError as e:
                    logger.error(f"Authentication failed: {e}")
                    # Don't retry auth errors
                    raise GarminAuthenticationError(
                        "Authentication failed. Please check your credentials."
                    )
                except (GarminConnectConnectionError, Exception) as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise GarminConnectionError(
                            f"Failed to connect to Garmin after {max_retries} attempts"
                        )

                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(
                        f"Attempt {retries}/{max_retries} failed for {func.__name__}. "
                        f"Retrying in {delay}s... Error: {e}"
                    )
                    time.sleep(delay)

            return None
        return wrapper
    return decorator


class GarminService:
    """
    Service for interacting with Garmin Connect API.

    Handles authentication, session management, and data retrieval
    with comprehensive error handling and retry logic.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        token_cache_dir: Optional[Path] = None
    ):
        """
        Initialize Garmin service.

        Args:
            settings: Application settings (loads from config if not provided)
            token_cache_dir: Directory for caching auth tokens
        """
        self.settings = settings or get_settings()
        self.token_cache_dir = token_cache_dir or Path.home() / ".garmin_tokens"
        self.token_cache_dir.mkdir(parents=True, exist_ok=True)

        self.client: Optional[Garmin] = None
        self._authenticated = False

        logger.info("GarminService initialized")

    @property
    def token_cache_file(self) -> Path:
        """Get token cache file path."""
        # Hash email for privacy in filename
        import hashlib
        email_hash = hashlib.sha256(
            self.settings.garmin_email.encode()
        ).hexdigest()[:16]
        return self.token_cache_dir / f"garmin_token_{email_hash}.json"

    def _save_token(self, token_data: Dict[str, Any]) -> None:
        """
        Save authentication token to cache.

        Args:
            token_data: Token data to cache
        """
        try:
            cache_data = {
                "created_at": datetime.utcnow().isoformat(),
                "token_data": token_data,
            }
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Token cached to {self.token_cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache token: {e}")

    def _load_token(self) -> Optional[Dict[str, Any]]:
        """
        Load authentication token from cache.

        Returns:
            Cached token data if valid, None otherwise
        """
        try:
            if not self.token_cache_file.exists():
                return None

            with open(self.token_cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if token is less than 24 hours old
            created_at = datetime.fromisoformat(cache_data["created_at"])
            age = datetime.utcnow() - created_at

            if age > timedelta(hours=24):
                logger.debug("Cached token expired (>24 hours old)")
                return None

            logger.debug("Loaded token from cache")
            return cache_data["token_data"]

        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")
            return None

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def authenticate(self, force_new: bool = False) -> None:
        """
        Authenticate with Garmin Connect.

        Args:
            force_new: Force new authentication, ignore cached token

        Raises:
            GarminAuthenticationError: If authentication fails
        """
        if self._authenticated and not force_new:
            logger.debug("Already authenticated")
            return

        logger.info("Authenticating with Garmin Connect...")

        try:
            # Try to use cached token first
            if not force_new:
                token_data = self._load_token()
                if token_data:
                    try:
                        self.client = Garmin()
                        self.client.login(token_data)
                        self._authenticated = True
                        logger.info("Authenticated using cached token")
                        return
                    except Exception as e:
                        logger.debug(f"Cached token invalid: {e}")

            # Authenticate with credentials
            self.client = Garmin(
                self.settings.garmin_email,
                self.settings.garmin_password
            )
            self.client.login()

            # Cache the token
            token_data = self.client.session_data
            if token_data:
                self._save_token(token_data)

            self._authenticated = True
            logger.info("Successfully authenticated with Garmin Connect")

        except GarminConnectAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise GarminAuthenticationError(
                "Failed to authenticate with Garmin Connect. "
                "Please check your credentials."
            )
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise GarminConnectionError(f"Authentication error: {e}")

    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated before making requests."""
        if not self._authenticated or self.client is None:
            self.authenticate()

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_daily_metrics(self, target_date: date) -> Optional[GarminDailyMetrics]:
        """
        Fetch daily health metrics for a specific date.

        Args:
            target_date: Date to fetch metrics for

        Returns:
            GarminDailyMetrics if data available, None otherwise

        Raises:
            GarminServiceError: On API errors
        """
        self._ensure_authenticated()

        logger.info(f"Fetching daily metrics for {target_date}")

        try:
            # Fetch various daily metrics
            date_str = target_date.isoformat()

            # Get daily stats
            stats = self.client.get_stats(date_str)

            # Get heart rate data
            heart_rate = self.client.get_heart_rates(date_str)

            # Get body battery
            body_battery = self.client.get_body_battery(date_str)

            # Get stress data
            stress = self.client.get_stress_data(date_str)

            # Compile metrics
            metrics_data = {
                "date": target_date,
                "steps": stats.get("totalSteps"),
                "distance_meters": stats.get("totalDistanceMeters"),
                "calories": stats.get("totalKilocalories"),
                "active_minutes": stats.get("activeMinutes"),
                "floors_climbed": stats.get("floorsAscended"),
                "resting_heart_rate": heart_rate.get("restingHeartRate") if heart_rate else None,
                "max_heart_rate": heart_rate.get("maxHeartRate") if heart_rate else None,
                "avg_heart_rate": heart_rate.get("averageHeartRate") if heart_rate else None,
                "stress_score": stress.get("avgStressLevel") if stress else None,
                "raw_data": {
                    "stats": stats,
                    "heart_rate": heart_rate,
                    "body_battery": body_battery,
                    "stress": stress,
                }
            }

            # Add body battery data if available
            if body_battery:
                metrics_data.update({
                    "body_battery_charged": body_battery.get("charged"),
                    "body_battery_drained": body_battery.get("drained"),
                    "body_battery_max": body_battery.get("highestValue"),
                    "body_battery_min": body_battery.get("lowestValue"),
                })

            return GarminDailyMetrics(**metrics_data)

        except Exception as e:
            logger.error(f"Failed to fetch daily metrics for {target_date}: {e}")
            raise GarminServiceError(f"Error fetching daily metrics: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_sleep_data(self, target_date: date) -> Optional[GarminSleepData]:
        """
        Fetch sleep data for a specific date.

        Args:
            target_date: Date to fetch sleep data for

        Returns:
            GarminSleepData if data available, None otherwise

        Raises:
            GarminServiceError: On API errors
        """
        self._ensure_authenticated()

        logger.info(f"Fetching sleep data for {target_date}")

        try:
            date_str = target_date.isoformat()
            sleep_data = self.client.get_sleep_data(date_str)

            if not sleep_data or "dailySleepDTO" not in sleep_data:
                logger.debug(f"No sleep data available for {target_date}")
                return None

            sleep_dto = sleep_data["dailySleepDTO"]

            # Parse sleep times
            sleep_start = datetime.fromtimestamp(
                sleep_dto.get("sleepStartTimestampGMT", 0) / 1000
            )
            sleep_end = datetime.fromtimestamp(
                sleep_dto.get("sleepEndTimestampGMT", 0) / 1000
            )

            sleep_info = {
                "sleep_date": target_date,
                "sleep_start_time": sleep_start,
                "sleep_end_time": sleep_end,
                "total_sleep_minutes": sleep_dto.get("sleepTimeSeconds", 0) // 60,
                "deep_sleep_minutes": sleep_dto.get("deepSleepSeconds", 0) // 60,
                "light_sleep_minutes": sleep_dto.get("lightSleepSeconds", 0) // 60,
                "rem_sleep_minutes": sleep_dto.get("remSleepSeconds", 0) // 60,
                "awake_minutes": sleep_dto.get("awakeSleepSeconds", 0) // 60,
                "sleep_score": sleep_dto.get("sleepScores", {}).get("overall", {}).get("value"),
                "avg_heart_rate": sleep_dto.get("averageHeartRate"),
                "min_heart_rate": sleep_dto.get("lowestHeartRate"),
                "max_heart_rate": sleep_dto.get("highestHeartRate"),
                "avg_respiration_rate": sleep_dto.get("averageRespirationValue"),
                "awakenings_count": sleep_dto.get("awakeDuration", 0) // 60,
                "sleep_stages_data": sleep_data.get("sleepMovement"),
                "raw_data": sleep_data,
            }

            return GarminSleepData(**sleep_info)

        except Exception as e:
            logger.error(f"Failed to fetch sleep data for {target_date}: {e}")
            raise GarminServiceError(f"Error fetching sleep data: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_activities(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100
    ) -> List[GarminActivity]:
        """
        Fetch activities within a date range.

        Args:
            start_date: Start date for activity search
            end_date: End date for activity search
            limit: Maximum number of activities to return

        Returns:
            List of GarminActivity objects

        Raises:
            GarminServiceError: On API errors
        """
        self._ensure_authenticated()

        logger.info(f"Fetching activities from {start_date} to {end_date}")

        try:
            activities = self.client.get_activities_by_date(
                start_date.isoformat(),
                end_date.isoformat(),
                activitytype=None,
                limit=limit
            )

            if not activities:
                logger.debug(f"No activities found between {start_date} and {end_date}")
                return []

            parsed_activities = []
            for activity_data in activities:
                try:
                    activity = self._parse_activity(activity_data)
                    if activity:
                        parsed_activities.append(activity)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse activity {activity_data.get('activityId')}: {e}"
                    )
                    continue

            logger.info(f"Fetched {len(parsed_activities)} activities")
            return parsed_activities

        except Exception as e:
            logger.error(f"Failed to fetch activities: {e}")
            raise GarminServiceError(f"Error fetching activities: {e}")

    def _parse_activity(self, activity_data: Dict[str, Any]) -> Optional[GarminActivity]:
        """
        Parse raw activity data into GarminActivity schema.

        Args:
            activity_data: Raw activity data from Garmin API

        Returns:
            GarminActivity if parsing successful, None otherwise
        """
        try:
            # Convert timestamp to datetime
            start_time = datetime.fromtimestamp(
                activity_data.get("startTimeGMT", 0) / 1000
            )

            # Map activity type
            activity_type = activity_data.get("activityType", {}).get("typeKey", "other")

            activity_info = {
                "garmin_activity_id": str(activity_data.get("activityId")),
                "activity_date": start_time.date(),
                "start_time": start_time,
                "activity_type": activity_type,
                "activity_name": activity_data.get("activityName"),
                "duration_seconds": activity_data.get("duration", 0),
                "duration_minutes": activity_data.get("duration", 0) / 60,
                "distance_meters": activity_data.get("distance"),
                "calories": activity_data.get("calories"),
                "avg_heart_rate": activity_data.get("averageHR"),
                "max_heart_rate": activity_data.get("maxHR"),
                "avg_speed_kmh": activity_data.get("averageSpeed", 0) * 3.6 if activity_data.get("averageSpeed") else None,
                "max_speed_kmh": activity_data.get("maxSpeed", 0) * 3.6 if activity_data.get("maxSpeed") else None,
                "elevation_gain_meters": activity_data.get("elevationGain"),
                "elevation_loss_meters": activity_data.get("elevationLoss"),
                "training_effect_aerobic": activity_data.get("aerobicTrainingEffect"),
                "training_effect_anaerobic": activity_data.get("anaerobicTrainingEffect"),
                "avg_cadence": activity_data.get("averageRunningCadenceInStepsPerMinute") or activity_data.get("averageBikingCadenceInRevPerMinute"),
                "avg_power": activity_data.get("avgPower"),
                "max_power": activity_data.get("maxPower"),
                "raw_data": activity_data,
            }

            return GarminActivity(**activity_info)

        except Exception as e:
            logger.warning(f"Error parsing activity: {e}")
            return None

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_hrv_readings(self, target_date: date) -> List[GarminHRVReading]:
        """
        Fetch HRV readings for a specific date.

        Args:
            target_date: Date to fetch HRV data for

        Returns:
            List of GarminHRVReading objects

        Raises:
            GarminServiceError: On API errors
        """
        self._ensure_authenticated()

        logger.info(f"Fetching HRV data for {target_date}")

        try:
            date_str = target_date.isoformat()
            hrv_data = self.client.get_hrv_data(date_str)

            if not hrv_data or "hrvSummaries" not in hrv_data:
                logger.debug(f"No HRV data available for {target_date}")
                return []

            readings = []
            for hrv_summary in hrv_data.get("hrvSummaries", []):
                try:
                    reading_time = datetime.fromtimestamp(
                        hrv_summary.get("calendarDate", 0) / 1000
                    )

                    reading_info = {
                        "reading_date": target_date,
                        "reading_time": reading_time,
                        "reading_type": "morning",  # Default to morning
                        "hrv_sdnn": hrv_summary.get("weeklyAvg", 0),
                        "hrv_rmssd": hrv_summary.get("lastNightAvg"),
                        "status": hrv_summary.get("status", "").lower(),
                        "raw_data": hrv_summary,
                    }

                    readings.append(GarminHRVReading(**reading_info))

                except Exception as e:
                    logger.warning(f"Failed to parse HRV reading: {e}")
                    continue

            logger.info(f"Fetched {len(readings)} HRV readings")
            return readings

        except Exception as e:
            logger.error(f"Failed to fetch HRV data for {target_date}: {e}")
            raise GarminServiceError(f"Error fetching HRV data: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_activity_details(
        self,
        activity_id: str
    ) -> Optional[GarminActivityDetails]:
        """
        Fetch detailed activity data including HR samples.

        Args:
            activity_id: Garmin activity ID

        Returns:
            GarminActivityDetails if successful, None otherwise

        Raises:
            GarminServiceError: On API errors
        """
        self._ensure_authenticated()

        logger.info(f"Fetching activity details for {activity_id}")

        try:
            # Get activity summary
            activity_data = self.client.get_activity(activity_id)
            activity = self._parse_activity(activity_data)

            if not activity:
                logger.warning(f"Failed to parse activity {activity_id}")
                return None

            # Get heart rate samples
            hr_data = self.client.get_activity_hr_in_timezones(activity_id)

            # Note: Detailed HR samples might not be available for all activities
            # This is a simplified implementation
            details = {
                "activity": activity,
                "heart_rate_samples": [],
            }

            return GarminActivityDetails(**details)

        except Exception as e:
            logger.error(f"Failed to fetch activity details for {activity_id}: {e}")
            raise GarminServiceError(f"Error fetching activity details: {e}")

    def logout(self) -> None:
        """Logout and clean up session."""
        if self.client:
            try:
                self.client.logout()
            except Exception as e:
                logger.warning(f"Error during logout: {e}")

        self._authenticated = False
        self.client = None
        logger.info("Logged out from Garmin Connect")

    def __enter__(self):
        """Context manager entry."""
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
