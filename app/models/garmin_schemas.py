"""
Pydantic schemas for Garmin Connect data.

These schemas define the structure and validation rules for data fetched
from Garmin Connect API, ensuring type safety and data integrity before
storing in the database.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class SleepQuality(str, Enum):
    """Sleep quality ratings."""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class HRVStatus(str, Enum):
    """HRV status indicators."""
    BALANCED = "balanced"
    UNBALANCED = "unbalanced"
    LOW = "low"
    HIGH = "high"
    POOR = "poor"


class GarminDailyMetrics(BaseModel):
    """
    Daily aggregated health and fitness metrics from Garmin.

    This schema represents a complete day of health data including
    activity, heart rate, HRV, body battery, and sleep summary.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Required fields
    metric_date: date = Field(..., description="Date of metrics")

    # Activity metrics
    steps: Optional[int] = Field(default=None, ge=0, le=200000)
    distance_meters: Optional[float] = Field(default=None, ge=0)
    calories: Optional[int] = Field(default=None, ge=0, le=50000)
    active_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    floors_climbed: Optional[int] = Field(default=None, ge=0, le=1000)

    # Heart rate metrics
    resting_heart_rate: Optional[int] = Field(default=None, ge=20, le=200)
    max_heart_rate: Optional[int] = Field(default=None, ge=40, le=250)
    avg_heart_rate: Optional[int] = Field(default=None, ge=30, le=220)

    # HRV and stress
    hrv_sdnn: Optional[float] = Field(
        default=None,
        ge=0,
        le=500,
        description="Standard deviation of NN intervals in milliseconds"
    )
    hrv_rmssd: Optional[float] = Field(
        default=None,
        ge=0,
        le=500,
        description="Root mean square of successive differences"
    )
    stress_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Daily average stress score"
    )

    # Body battery
    body_battery_charged: Optional[int] = Field(default=None, ge=0, le=100)
    body_battery_drained: Optional[int] = Field(default=None, ge=0, le=100)
    body_battery_max: Optional[int] = Field(default=None, ge=0, le=100)
    body_battery_min: Optional[int] = Field(default=None, ge=0, le=100)

    # Sleep summary
    sleep_score: Optional[int] = Field(default=None, ge=0, le=100)
    total_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    deep_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    light_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    rem_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    awake_minutes: Optional[int] = Field(default=None, ge=0, le=1440)

    # Performance metrics
    vo2_max: Optional[float] = Field(default=None, ge=10, le=100)
    fitness_age: Optional[int] = Field(default=None, ge=10, le=100)

    # Body composition
    weight_kg: Optional[float] = Field(default=None, ge=20, le=500)
    body_fat_percent: Optional[float] = Field(default=None, ge=0, le=100)
    bmi: Optional[float] = Field(default=None, ge=10, le=80)

    # Hydration
    hydration_ml: Optional[int] = Field(default=None, ge=0, le=20000)

    # Respiration
    avg_respiration_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=60,
        description="Average breaths per minute"
    )

    # Raw data reference
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Complete raw data from Garmin API"
    )

    @field_validator('max_heart_rate')
    @classmethod
    def validate_max_hr(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure max HR is greater than resting HR if both present."""
        if v is not None and info.data.get('resting_heart_rate'):
            resting = info.data['resting_heart_rate']
            if v <= resting:
                raise ValueError(f"Max HR ({v}) must be greater than resting HR ({resting})")
        return v


class GarminSleepData(BaseModel):
    """
    Detailed sleep session data from Garmin.

    Contains comprehensive sleep metrics including stages, quality,
    and physiological measurements during sleep.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Required fields
    sleep_date: date = Field(..., description="Date of the sleep session")
    sleep_start_time: datetime = Field(..., description="Sleep start timestamp")
    sleep_end_time: datetime = Field(..., description="Sleep end timestamp")
    total_sleep_minutes: int = Field(..., ge=0, le=1440)

    # Sleep stages
    deep_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    light_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    rem_sleep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    awake_minutes: Optional[int] = Field(default=None, ge=0, le=1440)

    # Sleep quality
    sleep_score: Optional[int] = Field(default=None, ge=0, le=100)
    sleep_quality: Optional[SleepQuality] = Field(default=None)
    restlessness: Optional[float] = Field(default=None, ge=0)

    # Heart rate during sleep
    avg_heart_rate: Optional[int] = Field(default=None, ge=20, le=200)
    min_heart_rate: Optional[int] = Field(default=None, ge=20, le=200)
    max_heart_rate: Optional[int] = Field(default=None, ge=20, le=200)

    # HRV during sleep
    avg_hrv: Optional[float] = Field(default=None, ge=0, le=500)

    # Respiration during sleep
    avg_respiration_rate: Optional[float] = Field(default=None, ge=0, le=60)

    # Additional metrics
    awakenings_count: Optional[int] = Field(default=None, ge=0, le=100)

    # Detailed sleep stages data
    sleep_stages_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Time-series sleep stage transitions"
    )

    # Raw data
    raw_data: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('sleep_end_time')
    @classmethod
    def validate_sleep_duration(cls, v: datetime, info) -> datetime:
        """Ensure end time is after start time."""
        start_time = info.data.get('sleep_start_time')
        if start_time and v <= start_time:
            raise ValueError("Sleep end time must be after start time")
        return v


class GarminActivity(BaseModel):
    """
    Workout activity data from Garmin.

    Contains detailed information about a single workout including
    performance metrics, training effect, and heart rate data.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Required fields
    garmin_activity_id: str = Field(..., description="Unique Garmin activity ID")
    activity_date: date = Field(..., description="Date of activity")
    start_time: datetime = Field(..., description="Activity start timestamp")
    activity_type: str = Field(..., description="Type of activity")
    duration_seconds: int = Field(..., ge=0, le=86400)

    # Optional identification
    activity_name: Optional[str] = Field(default=None, max_length=200)

    # Duration and distance
    duration_minutes: Optional[float] = Field(default=None, ge=0)
    distance_meters: Optional[float] = Field(default=None, ge=0)

    # Heart rate metrics
    avg_heart_rate: Optional[int] = Field(default=None, ge=20, le=250)
    max_heart_rate: Optional[int] = Field(default=None, ge=20, le=250)

    # Pace and speed
    avg_pace_per_km: Optional[float] = Field(
        default=None,
        ge=0,
        description="Average pace in minutes per kilometer"
    )
    avg_speed_kmh: Optional[float] = Field(default=None, ge=0)
    max_speed_kmh: Optional[float] = Field(default=None, ge=0)

    # Energy
    calories: Optional[int] = Field(default=None, ge=0, le=50000)

    # Elevation
    elevation_gain_meters: Optional[float] = Field(default=None, ge=0)
    elevation_loss_meters: Optional[float] = Field(default=None, ge=0)

    # Training effect (Garmin metrics)
    training_effect_aerobic: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Aerobic training effect"
    )
    training_effect_anaerobic: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Anaerobic training effect"
    )

    # Training load
    training_load: Optional[int] = Field(default=None, ge=0, le=1000)
    recovery_time_hours: Optional[int] = Field(default=None, ge=0, le=200)

    # Power metrics
    avg_power: Optional[int] = Field(default=None, ge=0, le=2000)
    max_power: Optional[int] = Field(default=None, ge=0, le=3000)
    normalized_power: Optional[int] = Field(default=None, ge=0, le=2000)

    # Cadence
    avg_cadence: Optional[int] = Field(default=None, ge=0, le=300)
    max_cadence: Optional[int] = Field(default=None, ge=0, le=400)

    # Running dynamics
    avg_stride_length: Optional[float] = Field(default=None, ge=0, le=5)
    avg_vertical_oscillation: Optional[float] = Field(default=None, ge=0, le=50)
    avg_ground_contact_time: Optional[int] = Field(default=None, ge=0, le=1000)

    # Intensity
    intensity_factor: Optional[float] = Field(default=None, ge=0, le=3)
    hr_zones_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Time spent in each heart rate zone"
    )

    # Weather
    temperature_celsius: Optional[float] = Field(default=None, ge=-50, le=60)
    weather_condition: Optional[str] = Field(default=None, max_length=50)

    # Notes
    notes: Optional[str] = Field(default=None)
    perceived_exertion: Optional[int] = Field(default=None, ge=1, le=10)

    # Raw data
    raw_data: Optional[Dict[str, Any]] = Field(default=None)


class GarminHRVReading(BaseModel):
    """
    Heart Rate Variability reading from Garmin.

    HRV is a key indicator of recovery status and autonomic
    nervous system health. Garmin provides morning and all-day readings.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Required fields
    reading_date: date = Field(..., description="Date of HRV reading")
    reading_time: datetime = Field(..., description="Timestamp of reading")
    reading_type: str = Field(
        ...,
        description="Type of reading: morning, all_day, sleep, or activity"
    )
    hrv_sdnn: float = Field(
        ...,
        ge=0,
        le=500,
        description="Standard deviation of NN intervals in milliseconds"
    )

    # Optional HRV metrics
    hrv_rmssd: Optional[float] = Field(
        default=None,
        ge=0,
        le=500,
        description="Root mean square of successive differences"
    )
    hrv_pnn50: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage of NN intervals > 50ms different"
    )

    # Context
    avg_heart_rate: Optional[int] = Field(default=None, ge=20, le=200)
    status: Optional[HRVStatus] = Field(default=None)

    # Raw data
    raw_data: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('reading_type')
    @classmethod
    def validate_reading_type(cls, v: str) -> str:
        """Ensure reading type is valid."""
        valid_types = {'morning', 'all_day', 'sleep', 'activity'}
        if v.lower() not in valid_types:
            raise ValueError(
                f"Reading type must be one of: {', '.join(valid_types)}"
            )
        return v.lower()


class GarminHeartRateSample(BaseModel):
    """
    Individual heart rate sample during an activity.

    Used for detailed heart rate analysis and zone calculations.
    """
    model_config = ConfigDict(validate_assignment=True)

    timestamp: datetime = Field(..., description="Sample timestamp")
    heart_rate: int = Field(..., ge=20, le=250, description="Heart rate in bpm")
    elapsed_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        description="Seconds since activity start"
    )


class GarminActivityDetails(BaseModel):
    """
    Detailed activity data including time-series heart rate samples.

    Extends basic activity information with sample-level data.
    """
    model_config = ConfigDict(validate_assignment=True)

    # Basic activity info
    activity: GarminActivity

    # Time-series data
    heart_rate_samples: List[GarminHeartRateSample] = Field(
        default_factory=list,
        description="Heart rate samples throughout activity"
    )

    # Additional time-series (optional)
    pace_samples: Optional[List[Dict[str, Any]]] = Field(default=None)
    power_samples: Optional[List[Dict[str, Any]]] = Field(default=None)
    cadence_samples: Optional[List[Dict[str, Any]]] = Field(default=None)


class GarminSyncResult(BaseModel):
    """
    Result of a Garmin data synchronization operation.

    Used to track sync progress and report results.
    """
    model_config = ConfigDict(validate_assignment=True)

    sync_type: str = Field(..., description="Type of sync: full, incremental, etc.")
    start_date: date
    end_date: date
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None

    # Results
    success: bool = Field(default=True)
    records_synced: int = Field(default=0, ge=0)
    records_failed: int = Field(default=0, ge=0)

    # Breakdown by data type
    daily_metrics_synced: int = Field(default=0, ge=0)
    sleep_sessions_synced: int = Field(default=0, ge=0)
    activities_synced: int = Field(default=0, ge=0)
    hrv_readings_synced: int = Field(default=0, ge=0)

    # Error tracking
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # API stats
    api_calls_made: int = Field(default=0, ge=0)
    rate_limit_hit: bool = Field(default=False)


class GarminAuthToken(BaseModel):
    """
    Garmin authentication token for session persistence.

    Stored to avoid repeated login attempts.
    """
    model_config = ConfigDict(validate_assignment=True)

    oauth1_token: str
    oauth2_token: str
    session_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
