"""
Pydantic schemas for AI analysis and recommendations.

These schemas provide:
- Type safety for API requests/responses
- Validation of data structures
- Clear contracts between services
- Documentation of expected formats
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ReadinessLevel(str, Enum):
    """Readiness level classification."""
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    LOW = "low"
    POOR = "poor"


class TrainingIntensity(str, Enum):
    """Training intensity classification."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    REST = "rest"


class WorkoutType(str, Enum):
    """Workout type classification."""
    ENDURANCE = "endurance"
    TEMPO = "tempo"
    INTERVAL = "interval"
    RECOVERY = "recovery"
    REST = "rest"
    STRENGTH = "strength"


# ============================================================================
# CONTEXT MODELS (Input to AI)
# ============================================================================

class ReadinessContext(BaseModel):
    """
    Context for AI readiness analysis.

    Contains all relevant metrics and data points needed for AI to assess
    training readiness and provide recommendations.
    """
    user_id: str = Field(..., description="Unique user identifier")
    analysis_date: date = Field(..., description="Analysis date")

    # HRV metrics
    hrv_current: Optional[float] = Field(None, description="Current HRV SDNN (ms)")
    hrv_baseline_7d: Optional[float] = Field(None, description="7-day HRV baseline (ms)")
    hrv_baseline_30d: Optional[float] = Field(None, description="30-day HRV baseline (ms)")
    hrv_percent_of_baseline: Optional[float] = Field(None, description="HRV % of baseline")

    # Sleep metrics
    sleep_last_night: Optional[int] = Field(None, description="Last night's sleep duration (minutes)")
    sleep_quality_score: Optional[float] = Field(None, description="Sleep quality score (0-100)")
    sleep_average_7d: Optional[int] = Field(None, description="7-day average sleep (minutes)")

    # Training load metrics
    training_load_7d: Optional[int] = Field(None, description="7-day training load")
    training_load_28d: Optional[int] = Field(None, description="28-day training load")
    acwr: Optional[float] = Field(None, description="Acute:Chronic Workload Ratio")

    # Fitness-fatigue metrics
    fitness_score: Optional[float] = Field(None, description="Fitness (CTL)")
    fatigue_score: Optional[float] = Field(None, description="Fatigue (ATL)")
    form_score: Optional[float] = Field(None, description="Form (TSB)")

    # Heart rate metrics
    resting_heart_rate: Optional[int] = Field(None, description="Resting heart rate (bpm)")
    rhr_baseline_7d: Optional[float] = Field(None, description="7-day RHR baseline")

    # Activity metrics
    steps_today: Optional[int] = Field(None, description="Steps today")
    calories_today: Optional[int] = Field(None, description="Calories burned today")

    # Recent activities
    recent_activities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of recent activities (last 7 days)"
    )

    # Additional context
    days_since_last_rest: Optional[int] = Field(None, description="Days since last rest day")
    consecutive_hard_days: Optional[int] = Field(None, description="Consecutive hard training days")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "date": "2025-10-16",
                "hrv_current": 62.5,
                "hrv_baseline_7d": 65.0,
                "hrv_percent_of_baseline": 96.15,
                "sleep_last_night": 420,
                "training_load_7d": 450,
                "acwr": 1.15,
                "recent_activities": [
                    {
                        "date": "2025-10-15",
                        "type": "running",
                        "duration_minutes": 45,
                        "intensity": "moderate"
                    }
                ]
            }
        }


# ============================================================================
# ANALYSIS MODELS (Output from AI)
# ============================================================================

class ReadinessAnalysis(BaseModel):
    """
    Complete readiness analysis from AI.

    Includes readiness score, level classification, and detailed explanation
    of the assessment.
    """
    user_id: str = Field(..., description="User identifier")
    analysis_date: date = Field(..., description="Date of analysis")
    readiness_score: float = Field(..., ge=0, le=100, description="Overall readiness score (0-100)")
    readiness_level: ReadinessLevel = Field(..., description="Readiness classification")

    # Component scores
    hrv_score: Optional[float] = Field(None, ge=0, le=100, description="HRV contribution score")
    sleep_score: Optional[float] = Field(None, ge=0, le=100, description="Sleep contribution score")
    load_score: Optional[float] = Field(None, ge=0, le=100, description="Training load score")

    # Analysis details
    key_factors: List[str] = Field(
        default_factory=list,
        description="Key factors affecting readiness"
    )
    positive_indicators: List[str] = Field(
        default_factory=list,
        description="Positive indicators noted"
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="Areas of concern"
    )

    # Human-readable explanation
    summary: str = Field(..., description="Plain English summary of readiness")

    # AI metadata
    confidence: float = Field(..., ge=0, le=1, description="AI confidence in analysis")
    model_version: str = Field(..., description="AI model version used")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

    @field_validator('readiness_score')
    @classmethod
    def validate_readiness_score(cls, v):
        """Ensure readiness score is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError('Readiness score must be between 0 and 100')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "analysis_date": "2025-10-16",
                "readiness_score": 78.5,
                "readiness_level": "good",
                "hrv_score": 82.0,
                "sleep_score": 75.0,
                "load_score": 70.0,
                "key_factors": [
                    "HRV slightly below baseline",
                    "Good sleep duration",
                    "ACWR in optimal range"
                ],
                "positive_indicators": [
                    "Consistent sleep pattern",
                    "No signs of overtraining"
                ],
                "concerns": [
                    "HRV trending downward"
                ],
                "summary": "You're in good shape for training today. Your HRV is slightly below baseline but within normal variation.",
                "confidence": 0.85,
                "model_version": "claude-3-5-sonnet-20241022"
            }
        }


class TrainingRecommendation(BaseModel):
    """
    Training recommendation from AI.

    Provides specific training guidance including intensity, duration,
    and type of workout recommended.
    """
    user_id: str = Field(..., description="User identifier")
    recommendation_date: date = Field(..., description="Date of recommendation")

    # Recommendation details
    recommended_intensity: TrainingIntensity = Field(..., description="Recommended training intensity")
    recommended_duration_minutes: Optional[int] = Field(None, description="Recommended duration")
    workout_types: List[WorkoutType] = Field(
        default_factory=list,
        description="Recommended workout types"
    )

    # Guidance
    training_focus: str = Field(..., description="Primary training focus")
    key_considerations: List[str] = Field(
        default_factory=list,
        description="Key considerations for training"
    )
    avoid_list: List[str] = Field(
        default_factory=list,
        description="Activities to avoid"
    )

    # Explanation
    rationale: str = Field(..., description="Explanation of recommendation")

    # AI metadata
    confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendation")
    model_version: str = Field(..., description="AI model version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Recommendation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "recommendation_date": "2025-10-16",
                "recommended_intensity": "moderate",
                "recommended_duration_minutes": 45,
                "workout_types": ["endurance", "recovery"],
                "training_focus": "Aerobic base building",
                "key_considerations": [
                    "Keep heart rate in Zone 2",
                    "Monitor how you feel"
                ],
                "avoid_list": [
                    "High intensity intervals",
                    "Very long duration"
                ],
                "rationale": "Your readiness is good, but HRV suggests moderate training is optimal today.",
                "confidence": 0.82,
                "model_version": "claude-3-5-sonnet-20241022"
            }
        }


class RecoveryRecommendation(BaseModel):
    """
    Recovery recommendation from AI.

    Provides specific recovery guidance and strategies to optimize
    adaptation and prevent overtraining.
    """
    user_id: str = Field(..., description="User identifier")
    recommendation_date: date = Field(..., description="Date of recommendation")

    # Recovery priority
    recovery_priority: str = Field(..., description="Recovery priority level (high/moderate/low)")

    # Recommendations
    sleep_target_hours: Optional[float] = Field(None, description="Target sleep duration")
    rest_days_needed: Optional[int] = Field(None, description="Number of rest days recommended")

    recovery_strategies: List[str] = Field(
        default_factory=list,
        description="Recommended recovery strategies"
    )

    nutrition_focus: List[str] = Field(
        default_factory=list,
        description="Nutritional recommendations"
    )

    # Warnings
    warning_signs: List[str] = Field(
        default_factory=list,
        description="Warning signs to watch for"
    )

    # Explanation
    guidance: str = Field(..., description="Recovery guidance explanation")

    # AI metadata
    confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendation")
    model_version: str = Field(..., description="AI model version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Recommendation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "recommendation_date": "2025-10-16",
                "recovery_priority": "moderate",
                "sleep_target_hours": 8.0,
                "rest_days_needed": 1,
                "recovery_strategies": [
                    "Active recovery walk",
                    "Stretching/mobility work",
                    "Foam rolling"
                ],
                "nutrition_focus": [
                    "Adequate protein intake",
                    "Hydration"
                ],
                "warning_signs": [
                    "Persistent fatigue",
                    "Elevated resting heart rate"
                ],
                "guidance": "Your body needs moderate recovery focus. Consider a rest day within the next 2 days.",
                "confidence": 0.80,
                "model_version": "claude-3-5-sonnet-20241022"
            }
        }


class WorkoutRecommendation(BaseModel):
    """
    Specific workout recommendation.

    Provides detailed workout structure including phases, intensities,
    and specific guidance.
    """
    user_id: str = Field(..., description="User identifier")
    workout_date: date = Field(..., description="Date of workout")

    # Workout structure
    workout_type: WorkoutType = Field(..., description="Type of workout")
    total_duration_minutes: int = Field(..., description="Total workout duration")

    # Phases
    warmup_duration: Optional[int] = Field(None, description="Warmup duration (minutes)")
    main_duration: Optional[int] = Field(None, description="Main set duration (minutes)")
    cooldown_duration: Optional[int] = Field(None, description="Cooldown duration (minutes)")

    # Intensity guidance
    target_heart_rate_zone: Optional[str] = Field(None, description="Target HR zone")
    target_pace: Optional[str] = Field(None, description="Target pace description")
    perceived_effort: Optional[str] = Field(None, description="Target perceived effort")

    # Workout details
    workout_description: str = Field(..., description="Detailed workout description")
    key_points: List[str] = Field(
        default_factory=list,
        description="Key execution points"
    )

    # Success criteria
    success_metrics: List[str] = Field(
        default_factory=list,
        description="How to know workout was successful"
    )

    # AI metadata
    confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendation")
    model_version: str = Field(..., description="AI model version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Recommendation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "workout_date": "2025-10-16",
                "workout_type": "endurance",
                "total_duration_minutes": 45,
                "warmup_duration": 10,
                "main_duration": 30,
                "cooldown_duration": 5,
                "target_heart_rate_zone": "Zone 2 (60-70% max HR)",
                "target_pace": "Conversational pace",
                "perceived_effort": "5-6 out of 10",
                "workout_description": "Easy endurance run focusing on aerobic base",
                "key_points": [
                    "Start slow and build gradually",
                    "Stay in Zone 2",
                    "Focus on breathing rhythm"
                ],
                "success_metrics": [
                    "Maintained target heart rate",
                    "Felt comfortable throughout",
                    "Could hold conversation"
                ],
                "confidence": 0.85,
                "model_version": "claude-3-5-sonnet-20241022"
            }
        }


# ============================================================================
# COMPOSITE MODELS
# ============================================================================

class CompleteRecommendation(BaseModel):
    """
    Complete set of recommendations combining all aspects.

    This is the primary output model that combines readiness analysis,
    training recommendations, recovery guidance, and workout details.
    """
    readiness: ReadinessAnalysis
    training: TrainingRecommendation
    recovery: RecoveryRecommendation
    workout: Optional[WorkoutRecommendation] = None

    # Overall guidance
    daily_summary: str = Field(..., description="Overall daily guidance summary")

    class Config:
        json_schema_extra = {
            "example": {
                "readiness": {"readiness_score": 78.5},
                "training": {"recommended_intensity": "moderate"},
                "recovery": {"recovery_priority": "moderate"},
                "workout": {"workout_type": "endurance"},
                "daily_summary": "Good day for moderate training with recovery focus."
            }
        }


# ============================================================================
# ERROR MODELS
# ============================================================================

class AIServiceError(BaseModel):
    """Error response from AI service."""
    error_type: str = Field(..., description="Error type classification")
    error_message: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")

    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "RateLimitError",
                "error_message": "API rate limit exceeded. Please retry after 60 seconds.",
                "error_code": "429",
                "retry_after": 60
            }
        }
