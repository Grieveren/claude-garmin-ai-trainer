"""
Recovery Advisor - Generate recovery recommendations.

Provides specialized interface for recovery guidance based on
training load, readiness, and recovery status.
"""

import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.services.readiness_analyzer import ReadinessAnalyzer
from app.services.claude_service import ClaudeService
from app.models.ai_schemas import RecoveryRecommendation

logger = logging.getLogger(__name__)


class RecoveryAdvisor:
    """
    Generate personalized recovery recommendations.

    Provides recovery guidance based on:
    - Current readiness status
    - Training load and fatigue
    - Sleep and recovery metrics
    - Training history
    """

    def __init__(
        self,
        db_session: Session,
        claude_service: Optional[ClaudeService] = None,
        use_mock: bool = False
    ):
        """
        Initialize recovery advisor.

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

    def recommend_recovery(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> RecoveryRecommendation:
        """
        Generate recovery recommendation for a user.

        Args:
            user_id: User identifier
            target_date: Date for recommendation (defaults to today)

        Returns:
            RecoveryRecommendation with priority, strategies, and guidance

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating recovery recommendation for {user_id} on {target_date}")

        try:
            # Get complete recommendation (includes recovery)
            complete = self.readiness_analyzer.get_complete_recommendation(
                user_id,
                target_date
            )

            logger.info(
                f"Recovery recommendation: {complete.recovery.recovery_priority} priority, "
                f"{complete.recovery.rest_days_needed} rest days needed"
            )

            return complete.recovery

        except Exception as e:
            logger.error(f"Failed to generate recovery recommendation: {e}")
            raise

    def get_recovery_summary(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> str:
        """
        Get brief recovery summary for quick reference.

        Args:
            user_id: User identifier
            target_date: Date for summary (defaults to today)

        Returns:
            Brief text summary of recovery recommendation

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        try:
            recovery = self.recommend_recovery(user_id, target_date)

            summary = f"{recovery.recovery_priority.capitalize()} recovery priority. "

            if recovery.sleep_target_hours:
                summary += f"Target {recovery.sleep_target_hours} hours sleep. "

            if recovery.rest_days_needed and recovery.rest_days_needed > 0:
                summary += f"{recovery.rest_days_needed} rest day(s) recommended. "

            if recovery.recovery_strategies:
                top_strategy = recovery.recovery_strategies[0]
                summary += f"Focus: {top_strategy}"

            return summary

        except Exception as e:
            logger.error(f"Failed to generate recovery summary: {e}")
            raise

    def check_recovery_status(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> dict:
        """
        Check current recovery status with key indicators.

        Args:
            user_id: User identifier
            target_date: Date to check (defaults to today)

        Returns:
            Dictionary with recovery status indicators

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        try:
            complete = self.readiness_analyzer.get_complete_recommendation(
                user_id,
                target_date
            )

            recovery = complete.recovery
            readiness = complete.readiness

            status = {
                "recovery_priority": recovery.recovery_priority,
                "readiness_level": readiness.readiness_level.value,
                "readiness_score": readiness.readiness_score,
                "rest_days_needed": recovery.rest_days_needed,
                "sleep_target": recovery.sleep_target_hours,
                "primary_concerns": readiness.concerns[:3] if readiness.concerns else [],
                "top_strategy": (
                    recovery.recovery_strategies[0]
                    if recovery.recovery_strategies
                    else None
                )
            }

            return status

        except Exception as e:
            logger.error(f"Failed to check recovery status: {e}")
            raise
