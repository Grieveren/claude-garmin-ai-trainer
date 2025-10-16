"""
SQLAlchemy models for Garmin AI Training Optimization System.

This module defines the complete database schema for tracking:
- Daily health metrics (HRV, sleep, body battery)
- Detailed sleep sessions and stages
- Workout activities and performance data
- Heart rate and HRV time-series data
- AI-generated training recommendations
- Training plans and scheduled workouts
- Training load and recovery tracking
- User profiles and preferences
- Garmin sync history
"""

from datetime import datetime, date, time
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Time,
    Boolean, Text, ForeignKey, JSON, Enum, UniqueConstraint,
    Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
import enum


# Enums for type safety
class ActivityType(str, enum.Enum):
    """Garmin activity types."""
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    WALKING = "walking"
    HIKING = "hiking"
    STRENGTH_TRAINING = "strength_training"
    YOGA = "yoga"
    CARDIO = "cardio"
    OTHER = "other"


class WorkoutIntensity(str, enum.Enum):
    """Workout intensity levels."""
    REST = "rest"
    EASY = "easy"
    MODERATE = "moderate"
    HIGH_INTENSITY = "high_intensity"
    MAXIMUM = "maximum"


class ReadinessRecommendation(str, enum.Enum):
    """AI-generated daily workout recommendations."""
    HIGH_INTENSITY = "high_intensity"
    MODERATE = "moderate"
    EASY = "easy"
    REST = "rest"
    RECOVERY = "recovery"


class SleepStage(str, enum.Enum):
    """Sleep stage types."""
    DEEP = "deep"
    LIGHT = "light"
    REM = "rem"
    AWAKE = "awake"


class UserProfile(Base):
    """
    User profile with athlete information and preferences.

    Stores personal information, training preferences, and configuration
    settings for AI recommendations.
    """
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Personal information
    name: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))

    # Physical attributes
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)

    # Training preferences (stored as JSON for flexibility)
    training_preferences: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Preferred activities, training days, intensity preferences"
    )

    # Garmin integration
    garmin_user_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    garmin_access_token: Mapped[Optional[str]] = mapped_column(Text)
    garmin_refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Settings
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    units_system: Mapped[str] = mapped_column(String(10), default="metric")  # metric or imperial

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    daily_metrics: Mapped[List["DailyMetrics"]] = relationship(
        "DailyMetrics",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    training_plans: Mapped[List["TrainingPlan"]] = relationship(
        "TrainingPlan",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sync_history: Mapped[List["SyncHistory"]] = relationship(
        "SyncHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, user_id='{self.user_id}', name='{self.name}')>"


class DailyMetrics(Base):
    """
    Daily aggregated health and fitness metrics.

    One row per user per day containing all daily health metrics
    from Garmin: steps, sleep, HRV, heart rate, body battery, etc.
    """
    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date"),
        Index("idx_daily_metrics_user_date", "user_id", "date"),
        Index("idx_daily_metrics_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Activity metrics
    steps: Mapped[Optional[int]] = mapped_column(Integer)
    distance_meters: Mapped[Optional[float]] = mapped_column(Float)
    calories: Mapped[Optional[int]] = mapped_column(Integer)
    active_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    floors_climbed: Mapped[Optional[int]] = mapped_column(Integer)

    # Heart rate metrics
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)

    # HRV and stress
    hrv_sdnn: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Standard deviation of NN intervals (milliseconds)"
    )
    hrv_rmssd: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Root mean square of successive differences"
    )
    stress_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Daily average stress (0-100)"
    )

    # Body battery and recovery
    body_battery_charged: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_drained: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_max: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_min: Mapped[Optional[int]] = mapped_column(Integer)

    # Sleep metrics (summary)
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer)
    total_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    deep_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    light_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    rem_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    awake_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Performance metrics
    vo2_max: Mapped[Optional[float]] = mapped_column(Float)
    fitness_age: Mapped[Optional[int]] = mapped_column(Integer)

    # Body composition
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    body_fat_percent: Mapped[Optional[float]] = mapped_column(Float)
    bmi: Mapped[Optional[float]] = mapped_column(Float)

    # Hydration
    hydration_ml: Mapped[Optional[int]] = mapped_column(Integer)

    # Respiration
    avg_respiration_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Breaths per minute"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="daily_metrics")
    sleep_session: Mapped[Optional["SleepSession"]] = relationship(
        "SleepSession",
        back_populates="daily_metric",
        uselist=False
    )
    hrv_readings: Mapped[List["HRVReading"]] = relationship(
        "HRVReading",
        back_populates="daily_metric",
        cascade="all, delete-orphan"
    )
    daily_readiness: Mapped[Optional["DailyReadiness"]] = relationship(
        "DailyReadiness",
        back_populates="daily_metric",
        uselist=False
    )
    training_load: Mapped[Optional["TrainingLoadTracking"]] = relationship(
        "TrainingLoadTracking",
        back_populates="daily_metric",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<DailyMetrics(id={self.id}, user_id='{self.user_id}', date={self.date})>"


class SleepSession(Base):
    """
    Detailed sleep session data with sleep stages.

    Stores comprehensive sleep information including start/end times,
    sleep stages duration, and quality metrics.
    """
    __tablename__ = "sleep_sessions"
    __table_args__ = (
        Index("idx_sleep_user_date", "user_id", "sleep_date"),
        Index("idx_sleep_start_time", "sleep_start_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    daily_metric_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("daily_metrics.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    # Sleep session timing
    sleep_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sleep_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sleep_end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Duration in minutes
    total_sleep_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    deep_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    light_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    rem_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    awake_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Sleep quality metrics
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer)
    sleep_quality: Mapped[Optional[str]] = mapped_column(String(20))  # poor, fair, good, excellent
    restlessness: Mapped[Optional[float]] = mapped_column(Float)

    # Heart rate during sleep
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    min_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)

    # HRV during sleep
    avg_hrv: Mapped[Optional[float]] = mapped_column(Float)

    # Respiration during sleep
    avg_respiration_rate: Mapped[Optional[float]] = mapped_column(Float)

    # Additional metrics
    awakenings_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Sleep stages data (time-series stored as JSON)
    sleep_stages_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Detailed sleep stage transitions with timestamps"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    daily_metric: Mapped["DailyMetrics"] = relationship("DailyMetrics", back_populates="sleep_session")

    def __repr__(self) -> str:
        return f"<SleepSession(id={self.id}, date={self.sleep_date}, duration={self.total_sleep_minutes}min)>"


class Activity(Base):
    """
    Workout and activity data from Garmin.

    Stores detailed information about each workout including type,
    duration, performance metrics, and training effect.
    """
    __tablename__ = "activities"
    __table_args__ = (
        Index("idx_activity_user_date", "user_id", "activity_date"),
        Index("idx_activity_type", "activity_type"),
        Index("idx_activity_date", "activity_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    garmin_activity_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Activity details
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False,
        index=True
    )
    activity_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Duration and distance
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[Optional[float]] = mapped_column(Float)
    distance_meters: Mapped[Optional[float]] = mapped_column(Float)

    # Heart rate metrics
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)

    # Pace and speed
    avg_pace_per_km: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Average pace in minutes per kilometer"
    )
    avg_speed_kmh: Mapped[Optional[float]] = mapped_column(Float)
    max_speed_kmh: Mapped[Optional[float]] = mapped_column(Float)

    # Energy
    calories: Mapped[Optional[int]] = mapped_column(Integer)

    # Elevation
    elevation_gain_meters: Mapped[Optional[float]] = mapped_column(Float)
    elevation_loss_meters: Mapped[Optional[float]] = mapped_column(Float)

    # Training effect (Garmin's proprietary metrics)
    training_effect_aerobic: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Aerobic training effect (0.0-5.0)"
    )
    training_effect_anaerobic: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Anaerobic training effect (0.0-5.0)"
    )

    # Training load
    training_load: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Training load score"
    )
    recovery_time_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Recommended recovery time"
    )

    # Power metrics (cycling/running)
    avg_power: Mapped[Optional[int]] = mapped_column(Integer, comment="Average power in watts")
    max_power: Mapped[Optional[int]] = mapped_column(Integer, comment="Maximum power in watts")
    normalized_power: Mapped[Optional[int]] = mapped_column(Integer)

    # Cadence
    avg_cadence: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Steps per minute (running) or RPM (cycling)"
    )
    max_cadence: Mapped[Optional[int]] = mapped_column(Integer)

    # Additional metrics
    avg_stride_length: Mapped[Optional[float]] = mapped_column(Float, comment="Meters")
    avg_vertical_oscillation: Mapped[Optional[float]] = mapped_column(Float, comment="Centimeters")
    avg_ground_contact_time: Mapped[Optional[int]] = mapped_column(Integer, comment="Milliseconds")

    # Intensity and zones
    intensity_factor: Mapped[Optional[float]] = mapped_column(Float)
    hr_zones_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Time spent in each heart rate zone"
    )

    # Notes and feedback
    notes: Mapped[Optional[str]] = mapped_column(Text)
    perceived_exertion: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="RPE scale 1-10"
    )

    # Weather conditions
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float)
    weather_condition: Mapped[Optional[str]] = mapped_column(String(50))

    # Raw data reference
    raw_activity_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Complete raw activity data from Garmin"
    )

    # Link to planned workout
    planned_workout_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("planned_workouts.id", ondelete="SET NULL")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="activities")
    heart_rate_samples: Mapped[List["HeartRateSample"]] = relationship(
        "HeartRateSample",
        back_populates="activity",
        cascade="all, delete-orphan"
    )
    planned_workout: Mapped[Optional["PlannedWorkout"]] = relationship(
        "PlannedWorkout",
        foreign_keys=[planned_workout_id],
        back_populates="actual_activities"
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, type={self.activity_type}, date={self.activity_date})>"


class HeartRateSample(Base):
    """
    Intra-workout heart rate time-series data.

    Stores heart rate samples during activities for detailed
    performance analysis and zone time calculations.
    """
    __tablename__ = "heart_rate_samples"
    __table_args__ = (
        Index("idx_hr_activity", "activity_id"),
        Index("idx_hr_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Time-series data
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optional position data
    elapsed_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Seconds since activity start"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    activity: Mapped["Activity"] = relationship("Activity", back_populates="heart_rate_samples")

    def __repr__(self) -> str:
        return f"<HeartRateSample(activity_id={self.activity_id}, hr={self.heart_rate})>"


class HRVReading(Base):
    """
    Heart Rate Variability readings (morning and all-day).

    Stores HRV data which is a key indicator of recovery status
    and autonomic nervous system health.
    """
    __tablename__ = "hrv_readings"
    __table_args__ = (
        Index("idx_hrv_user_date", "user_id", "reading_date"),
        Index("idx_hrv_type", "reading_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    daily_metric_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("daily_metrics.id", ondelete="CASCADE"),
        nullable=False
    )

    # Reading details
    reading_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reading_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reading_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="morning, all_day, sleep, or activity"
    )

    # HRV metrics
    hrv_sdnn: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Standard deviation of NN intervals (ms)"
    )
    hrv_rmssd: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Root mean square of successive differences (ms)"
    )
    hrv_pnn50: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Percentage of NN intervals > 50ms different"
    )

    # Context
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="balanced, unbalanced, low, or high"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    daily_metric: Mapped["DailyMetrics"] = relationship("DailyMetrics", back_populates="hrv_readings")

    def __repr__(self) -> str:
        return f"<HRVReading(date={self.reading_date}, type={self.reading_type}, sdnn={self.hrv_sdnn})>"


class TrainingPlan(Base):
    """
    Goal-based training programs.

    Stores training plans which can be AI-generated or user-created,
    containing a series of planned workouts leading to a specific goal.
    """
    __tablename__ = "training_plans"
    __table_args__ = (
        Index("idx_plan_user_active", "user_id", "is_active"),
        Index("idx_plan_dates", "start_date", "target_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Plan details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    goal: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Training goal description (e.g., '5K under 25 minutes')"
    )
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Timeline
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    completion_percent: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

    # AI generation
    created_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(50))
    ai_generation_prompt: Mapped[Optional[str]] = mapped_column(Text)

    # Training structure
    weekly_structure: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Weekly training structure and periodization"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="training_plans")
    planned_workouts: Mapped[List["PlannedWorkout"]] = relationship(
        "PlannedWorkout",
        back_populates="training_plan",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrainingPlan(id={self.id}, name='{self.name}', goal='{self.goal[:50]}')>"


class PlannedWorkout(Base):
    """
    Daily workout prescriptions within training plans.

    Stores scheduled workouts with target metrics and AI reasoning
    for the workout prescription.
    """
    __tablename__ = "planned_workouts"
    __table_args__ = (
        Index("idx_planned_user_date", "user_id", "workout_date"),
        Index("idx_planned_plan", "training_plan_id"),
        Index("idx_planned_completed", "was_completed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    training_plan_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        index=True
    )

    # Workout scheduling
    workout_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Workout prescription
    workout_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    workout_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Target metrics
    target_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    target_distance_meters: Mapped[Optional[float]] = mapped_column(Float)
    target_heart_rate_zone: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="Z1, Z2, Z3, Z4, Z5 or range like Z2-Z3"
    )
    target_pace_per_km: Mapped[Optional[float]] = mapped_column(Float)
    target_power: Mapped[Optional[int]] = mapped_column(Integer)

    # Intensity
    intensity_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="1-10 scale"
    )
    intensity_category: Mapped[WorkoutIntensity] = mapped_column(
        Enum(WorkoutIntensity),
        nullable=False
    )

    # Completion tracking
    was_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_activity_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("activities.id", ondelete="SET NULL")
    )

    # Workout structure
    workout_structure: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Detailed workout structure (warmup, intervals, cooldown)"
    )

    # AI reasoning
    ai_reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="AI explanation for this workout prescription"
    )
    ai_adaptations: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="AI-suggested adaptations based on recent performance"
    )

    # Notes
    coach_notes: Mapped[Optional[str]] = mapped_column(Text)
    athlete_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    training_plan: Mapped[Optional["TrainingPlan"]] = relationship(
        "TrainingPlan",
        back_populates="planned_workouts"
    )
    actual_activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        foreign_keys="[Activity.planned_workout_id]",
        back_populates="planned_workout"
    )

    def __repr__(self) -> str:
        return f"<PlannedWorkout(id={self.id}, date={self.workout_date}, type={self.workout_type})>"


class DailyReadiness(Base):
    """
    AI-generated daily readiness scores and workout recommendations.

    Analyzes daily metrics to provide actionable training recommendations
    considering recovery status, training load, and athlete preferences.
    """
    __tablename__ = "daily_readiness"
    __table_args__ = (
        UniqueConstraint("user_id", "readiness_date", name="uq_user_readiness_date"),
        Index("idx_readiness_user_date", "user_id", "readiness_date"),
        Index("idx_readiness_score", "readiness_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    daily_metric_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("daily_metrics.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    # Readiness assessment
    readiness_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    readiness_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="0-100 score indicating training readiness"
    )

    # AI recommendation
    recommendation: Mapped[ReadinessRecommendation] = mapped_column(
        Enum(ReadinessRecommendation),
        nullable=False
    )
    recommended_intensity: Mapped[Optional[str]] = mapped_column(String(50))

    # Key factors influencing readiness
    key_factors: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Factors supporting the readiness score (HRV, sleep, recovery)"
    )

    # Warning signals
    red_flags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Warning signals requiring attention (low HRV, poor sleep, high stress)"
    )

    # Recovery advice
    recovery_tips: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Actionable recovery recommendations"
    )

    # Workout suggestion
    suggested_workout_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("planned_workouts.id", ondelete="SET NULL")
    )
    suggested_workout_description: Mapped[Optional[str]] = mapped_column(Text)

    # AI analysis details
    ai_analysis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed AI analysis and reasoning"
    )
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(50))
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="AI confidence in recommendation (0-1)"
    )

    # Historical context
    training_load_7d: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="7-day training load at time of analysis"
    )
    training_load_28d: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="28-day training load at time of analysis"
    )
    acwr: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Acute:Chronic Workload Ratio at time of analysis"
    )

    # User feedback
    user_agreement: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        comment="Did user agree with recommendation?"
    )
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    daily_metric: Mapped["DailyMetrics"] = relationship("DailyMetrics", back_populates="daily_readiness")

    def __repr__(self) -> str:
        return f"<DailyReadiness(date={self.readiness_date}, score={self.readiness_score}, rec={self.recommendation})>"


class AIAnalysisCache(Base):
    """
    Cache for AI-generated analyses and responses.

    Reduces API costs and improves response times by caching
    AI analysis results for similar contexts.
    """
    __tablename__ = "ai_analysis_cache"
    __table_args__ = (
        Index("idx_cache_hash", "content_hash"),
        Index("idx_cache_created", "created_at"),
        Index("idx_cache_type", "analysis_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Cache key
    content_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of input context"
    )

    # Analysis details
    analysis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="readiness, workout_suggestion, plan_generation, etc."
    )

    # Input context
    input_context: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Input data that generated this analysis"
    )

    # AI response
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    ai_model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Structured output (if applicable)
    structured_output: Mapped[Optional[dict]] = mapped_column(JSON)

    # Cache metadata
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AIAnalysisCache(id={self.id}, type={self.analysis_type}, hits={self.hit_count})>"


class TrainingLoadTracking(Base):
    """
    Training load monitoring with ACWR, fitness, and fatigue tracking.

    Implements acute:chronic workload ratio and fitness-fatigue model
    to monitor training stress and prevent overtraining.
    """
    __tablename__ = "training_load_tracking"
    __table_args__ = (
        UniqueConstraint("user_id", "tracking_date", name="uq_user_tracking_date"),
        Index("idx_load_user_date", "user_id", "tracking_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    daily_metric_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("daily_metrics.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    # Date
    tracking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Daily training load
    daily_training_load: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Training load for this day"
    )

    # Acute workload (7-day rolling average)
    acute_training_load: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="7-day rolling average training load"
    )

    # Chronic workload (28-day rolling average)
    chronic_training_load: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="28-day rolling average training load"
    )

    # ACWR (Acute:Chronic Workload Ratio)
    acwr: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Acute:Chronic Workload Ratio (optimal: 0.8-1.3)"
    )
    acwr_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="optimal, moderate, high_risk based on ACWR value"
    )

    # Fitness-Fatigue Model
    fitness: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Long-term training adaptation (chronic training load)"
    )
    fatigue: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Short-term fatigue accumulation (acute training load)"
    )
    form: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Current form (fitness - fatigue)"
    )

    # Training monotony and strain
    training_monotony: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Average load / standard deviation of load (7 days)"
    )
    training_strain: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Total weekly load * monotony"
    )

    # Ramp rate (week-over-week change)
    weekly_ramp_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Percentage change in weekly load vs previous week"
    )

    # Recovery status
    recovery_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="0-100 recovery score based on HRV, sleep, resting HR"
    )

    # Training stress indicators
    overtraining_risk: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="low, moderate, high, or very_high"
    )
    injury_risk: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="low, moderate, high, or very_high based on load spikes"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    daily_metric: Mapped["DailyMetrics"] = relationship("DailyMetrics", back_populates="training_load")

    def __repr__(self) -> str:
        return f"<TrainingLoadTracking(date={self.tracking_date}, acwr={self.acwr}, form={self.form})>"


class SyncHistory(Base):
    """
    Garmin data synchronization history and audit trail.

    Tracks all sync operations with Garmin to ensure data consistency,
    enable incremental syncs, and troubleshoot sync issues.
    """
    __tablename__ = "sync_history"
    __table_args__ = (
        Index("idx_sync_user_status", "user_id", "sync_status"),
        Index("idx_sync_time", "sync_started_at"),
        Index("idx_sync_type", "sync_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Sync details
    sync_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="full, incremental, activities_only, metrics_only, etc."
    )
    sync_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="pending, in_progress, completed, failed, partial"
    )

    # Time range
    data_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Start date of data range synced"
    )
    data_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="End date of data range synced"
    )

    # Timing
    sync_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    sync_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Results
    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Data types synced
    synced_data_types: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Breakdown of records by type (activities, metrics, sleep, etc.)"
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON)

    # Garmin API details
    api_calls_made: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    api_rate_limit_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="sync_history")

    def __repr__(self) -> str:
        return f"<SyncHistory(id={self.id}, user='{self.user_id}', status={self.sync_status})>"
