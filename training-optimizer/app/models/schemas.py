"""
Pydantic schemas for request/response validation.

This module defines the data models used for API requests and responses.
These will be expanded as the application develops.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(description="Application health status")
    version: str = Field(description="Application version")
    debug: bool = Field(description="Debug mode enabled")


class ActivityBase(BaseModel):
    """Base schema for activity data."""

    activity_id: str = Field(description="Unique activity identifier")
    activity_type: str = Field(description="Type of activity (running, cycling, etc.)")
    start_time: datetime = Field(description="Activity start time")
    duration: int = Field(description="Activity duration in seconds")
    distance: Optional[float] = Field(None, description="Distance in meters")


class ActivityCreate(ActivityBase):
    """Schema for creating a new activity."""

    pass


class Activity(ActivityBase):
    """Schema for activity response."""

    id: int = Field(description="Database ID")
    created_at: datetime = Field(description="Record creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class TrainingGoal(BaseModel):
    """Schema for training goal configuration."""

    goal_type: str = Field(description="Type of training goal")
    target_race_date: Optional[date] = Field(None, description="Target race date")
    target_distance: Optional[float] = Field(None, description="Target distance in meters")
    target_time: Optional[int] = Field(None, description="Target time in seconds")


class AthleteProfile(BaseModel):
    """Schema for athlete profile."""

    name: str = Field(description="Athlete name")
    age: int = Field(ge=10, le=100, description="Athlete age")
    max_heart_rate: int = Field(ge=100, le=250, description="Maximum heart rate")
    resting_heart_rate: int = Field(ge=30, le=100, description="Resting heart rate")
    training_goal: TrainingGoal = Field(description="Training goal")


class AIAnalysisRequest(BaseModel):
    """Schema for AI analysis request."""

    activity_ids: list[int] = Field(description="List of activity IDs to analyze")
    analysis_type: str = Field(
        default="general",
        description="Type of analysis (general, performance, recovery, etc.)"
    )


class AIAnalysisResponse(BaseModel):
    """Schema for AI analysis response."""

    analysis: str = Field(description="AI-generated analysis text")
    recommendations: list[str] = Field(description="Training recommendations")
    insights: dict = Field(description="Key insights and metrics")
    generated_at: datetime = Field(description="Analysis generation timestamp")
