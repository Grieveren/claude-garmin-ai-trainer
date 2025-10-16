"""
Models package for Garmin AI Training System.

This package contains all SQLAlchemy models for the database schema.
Import models from database_models module.
"""

from app.models.database_models import (
    # Enums
    ActivityType,
    WorkoutIntensity,
    ReadinessRecommendation,
    SleepStage,

    # Models
    UserProfile,
    DailyMetrics,
    SleepSession,
    Activity,
    HeartRateSample,
    HRVReading,
    TrainingPlan,
    PlannedWorkout,
    DailyReadiness,
    AIAnalysisCache,
    TrainingLoadTracking,
    SyncHistory,
)

__all__ = [
    # Enums
    "ActivityType",
    "WorkoutIntensity",
    "ReadinessRecommendation",
    "SleepStage",

    # Models
    "UserProfile",
    "DailyMetrics",
    "SleepSession",
    "Activity",
    "HeartRateSample",
    "HRVReading",
    "TrainingPlan",
    "PlannedWorkout",
    "DailyReadiness",
    "AIAnalysisCache",
    "TrainingLoadTracking",
    "SyncHistory",
]
