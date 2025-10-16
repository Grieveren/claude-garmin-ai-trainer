"""
Training Recommender - Generate training recommendations.

Provides specialized interface for training recommendations based on
readiness analysis and training history.
"""

import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.services.readiness_analyzer import ReadinessAnalyzer
from app.services.claude_service import ClaudeService
from app.models.ai_schemas import (
    ReadinessContext,
    TrainingRecommendation,
    WorkoutRecommendation
)

logger = logging.getLogger(__name__)


class TrainingRecommender:
    """
    Generate personalized training recommendations.

    Provides training guidance based on:
    - Current readiness status
    - Training history
    - Training load balance
    - Recovery status
    """

    def __init__(
        self,
        db_session: Session,
        claude_service: Optional[ClaudeService] = None,
        use_mock: bool = False
    ):
        """
        Initialize training recommender.

        Args:
            db_session: Database session
            claude_service: Claude AI service (optional)
            use_mock: Use mock service for testing
        """
        self.db = db_session
        self.readiness_analyzer = ReadinessAnalyzer(
            db_session,
            claude_service=claude_service,
            use_mock=use_mock
        )

    def recommend_training(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> TrainingRecommendation:
        """
        Generate training recommendation for a user.

        Args:
            user_id: User identifier
            target_date: Date for recommendation (defaults to today)

        Returns:
            TrainingRecommendation with intensity, duration, and guidance

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating training recommendation for {user_id} on {target_date}")

        try:
            # Get complete recommendation (includes training)
            complete = self.readiness_analyzer.get_complete_recommendation(
                user_id,
                target_date
            )

            logger.info(
                f"Training recommendation: {complete.training.recommended_intensity.value} "
                f"for {complete.training.recommended_duration_minutes}min"
            )

            return complete.training

        except Exception as e:
            logger.error(f"Failed to generate training recommendation: {e}")
            raise

    def recommend_workout(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> Optional[WorkoutRecommendation]:
        """
        Generate specific workout recommendation.

        Args:
            user_id: User identifier
            target_date: Date for workout (defaults to today)

        Returns:
            WorkoutRecommendation with specific workout details, or None for rest day

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating workout recommendation for {user_id} on {target_date}")

        try:
            # Get complete recommendation (includes workout)
            complete = self.readiness_analyzer.get_complete_recommendation(
                user_id,
                target_date
            )

            if complete.workout:
                logger.info(
                    f"Workout recommendation: {complete.workout.workout_type.value} "
                    f"for {complete.workout.total_duration_minutes}min"
                )
            else:
                logger.info("Rest day recommended - no specific workout")

            return complete.workout

        except Exception as e:
            logger.error(f"Failed to generate workout recommendation: {e}")
            raise

    def get_training_summary(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> str:
        """
        Get brief training summary for quick reference.

        Args:
            user_id: User identifier
            target_date: Date for summary (defaults to today)

        Returns:
            Brief text summary of training recommendation

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        try:
            training = self.recommend_training(user_id, target_date)

            summary = (
                f"{training.recommended_intensity.value.capitalize()} intensity "
                f"training recommended"
            )

            if training.recommended_duration_minutes:
                summary += f" for {training.recommended_duration_minutes} minutes"

            summary += f". Focus: {training.training_focus}"

            return summary

        except Exception as e:
            logger.error(f"Failed to generate training summary: {e}")
            raise
