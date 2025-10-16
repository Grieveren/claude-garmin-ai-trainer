"""
Explanation Generator - Generate human-readable explanations.

Provides clear, understandable explanations of:
- Readiness scores and factors
- Training recommendations
- Recovery needs
- Metric interpretations
"""

import logging
from datetime import date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.readiness_analyzer import ReadinessAnalyzer
from app.services.claude_service import ClaudeService
from app.models.ai_schemas import CompleteRecommendation

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """
    Generate human-readable explanations of analysis and recommendations.

    Converts technical metrics and AI analysis into clear, actionable
    explanations for users.
    """

    def __init__(
        self,
        db_session: Session,
        claude_service: Optional[ClaudeService] = None,
        use_mock: bool = False
    ):
        """
        Initialize explanation generator.

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

    def explain_readiness(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> str:
        """
        Generate explanation of readiness analysis.

        Args:
            user_id: User identifier
            target_date: Date to explain (defaults to today)

        Returns:
            Human-readable explanation of readiness

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating readiness explanation for {user_id} on {target_date}")

        try:
            analysis = self.readiness_analyzer.analyze_readiness(user_id, target_date)

            explanation = f"# Readiness Assessment for {target_date}\n\n"
            explanation += f"**Overall Score: {analysis.readiness_score:.1f}/100** "
            explanation += f"({analysis.readiness_level.value.upper()})\n\n"

            # Summary
            explanation += f"## Summary\n{analysis.summary}\n\n"

            # Key factors
            if analysis.key_factors:
                explanation += "## Key Factors\n"
                for factor in analysis.key_factors:
                    explanation += f"- {factor}\n"
                explanation += "\n"

            # Positive indicators
            if analysis.positive_indicators:
                explanation += "## Positive Signs\n"
                for indicator in analysis.positive_indicators:
                    explanation += f"✓ {indicator}\n"
                explanation += "\n"

            # Concerns
            if analysis.concerns:
                explanation += "## Areas to Monitor\n"
                for concern in analysis.concerns:
                    explanation += f"⚠ {concern}\n"
                explanation += "\n"

            # Component scores
            if analysis.hrv_score or analysis.sleep_score or analysis.load_score:
                explanation += "## Component Scores\n"
                if analysis.hrv_score:
                    explanation += f"- HRV: {analysis.hrv_score:.1f}/100\n"
                if analysis.sleep_score:
                    explanation += f"- Sleep: {analysis.sleep_score:.1f}/100\n"
                if analysis.load_score:
                    explanation += f"- Training Load: {analysis.load_score:.1f}/100\n"
                explanation += "\n"

            return explanation

        except Exception as e:
            logger.error(f"Failed to generate readiness explanation: {e}")
            raise

    def explain_recommendation(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> str:
        """
        Generate comprehensive explanation of all recommendations.

        Args:
            user_id: User identifier
            target_date: Date to explain (defaults to today)

        Returns:
            Human-readable explanation of recommendations

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating recommendation explanation for {user_id} on {target_date}")

        try:
            complete = self.readiness_analyzer.get_complete_recommendation(
                user_id,
                target_date
            )

            explanation = f"# Training Plan for {target_date}\n\n"

            # Overall guidance
            explanation += f"## Daily Guidance\n{complete.daily_summary}\n\n"

            # Training recommendation
            explanation += "## Training Recommendation\n"
            explanation += f"**Intensity:** {complete.training.recommended_intensity.value.upper()}\n"
            if complete.training.recommended_duration_minutes:
                explanation += f"**Duration:** {complete.training.recommended_duration_minutes} minutes\n"
            explanation += f"**Focus:** {complete.training.training_focus}\n\n"

            explanation += f"**Why:** {complete.training.rationale}\n\n"

            if complete.training.key_considerations:
                explanation += "**Key Considerations:**\n"
                for consideration in complete.training.key_considerations:
                    explanation += f"- {consideration}\n"
                explanation += "\n"

            if complete.training.avoid_list:
                explanation += "**Avoid Today:**\n"
                for avoid in complete.training.avoid_list:
                    explanation += f"- {avoid}\n"
                explanation += "\n"

            # Workout details
            if complete.workout:
                explanation += "## Today's Workout\n"
                explanation += f"**Type:** {complete.workout.workout_type.value.title()}\n"
                explanation += f"**Total Time:** {complete.workout.total_duration_minutes} minutes\n"
                explanation += f"  - Warmup: {complete.workout.warmup_duration} min\n"
                explanation += f"  - Main Set: {complete.workout.main_duration} min\n"
                explanation += f"  - Cooldown: {complete.workout.cooldown_duration} min\n\n"

                explanation += f"**Description:** {complete.workout.workout_description}\n\n"

                if complete.workout.target_heart_rate_zone:
                    explanation += f"**Target HR Zone:** {complete.workout.target_heart_rate_zone}\n"
                if complete.workout.perceived_effort:
                    explanation += f"**Perceived Effort:** {complete.workout.perceived_effort}\n"
                explanation += "\n"

                if complete.workout.key_points:
                    explanation += "**Execution Tips:**\n"
                    for point in complete.workout.key_points:
                        explanation += f"- {point}\n"
                    explanation += "\n"

                if complete.workout.success_metrics:
                    explanation += "**Success Criteria:**\n"
                    for metric in complete.workout.success_metrics:
                        explanation += f"- {metric}\n"
                    explanation += "\n"

            # Recovery guidance
            explanation += "## Recovery Focus\n"
            explanation += f"**Priority:** {complete.recovery.recovery_priority.upper()}\n"
            if complete.recovery.sleep_target_hours:
                explanation += f"**Sleep Target:** {complete.recovery.sleep_target_hours} hours\n"
            if complete.recovery.rest_days_needed:
                explanation += f"**Rest Days Needed:** {complete.recovery.rest_days_needed}\n"
            explanation += "\n"

            explanation += f"{complete.recovery.guidance}\n\n"

            if complete.recovery.recovery_strategies:
                explanation += "**Recovery Strategies:**\n"
                for strategy in complete.recovery.recovery_strategies:
                    explanation += f"- {strategy}\n"
                explanation += "\n"

            if complete.recovery.warning_signs:
                explanation += "**Warning Signs to Monitor:**\n"
                for sign in complete.recovery.warning_signs:
                    explanation += f"- {sign}\n"
                explanation += "\n"

            return explanation

        except Exception as e:
            logger.error(f"Failed to generate recommendation explanation: {e}")
            raise

    def explain_quick_summary(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> str:
        """
        Generate brief summary for quick reference.

        Args:
            user_id: User identifier
            target_date: Date to summarize (defaults to today)

        Returns:
            Brief text summary

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

            summary = f"**{target_date}** | "
            summary += f"Readiness: {complete.readiness.readiness_level.value.title()} "
            summary += f"({complete.readiness.readiness_score:.0f}) | "
            summary += f"Training: {complete.training.recommended_intensity.value.title()}"

            if complete.training.recommended_duration_minutes:
                summary += f" ({complete.training.recommended_duration_minutes}min)"

            summary += f" | Recovery: {complete.recovery.recovery_priority.title()}"

            return summary

        except Exception as e:
            logger.error(f"Failed to generate quick summary: {e}")
            raise

    def explain_metrics(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate structured explanation of key metrics.

        Args:
            user_id: User identifier
            target_date: Date to explain (defaults to today)

        Returns:
            Dictionary with metric explanations

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

            metrics = {
                "readiness": {
                    "score": complete.readiness.readiness_score,
                    "level": complete.readiness.readiness_level.value,
                    "explanation": complete.readiness.summary,
                    "confidence": complete.readiness.confidence
                },
                "training": {
                    "intensity": complete.training.recommended_intensity.value,
                    "duration": complete.training.recommended_duration_minutes,
                    "focus": complete.training.training_focus,
                    "rationale": complete.training.rationale
                },
                "recovery": {
                    "priority": complete.recovery.recovery_priority,
                    "sleep_target": complete.recovery.sleep_target_hours,
                    "rest_days": complete.recovery.rest_days_needed,
                    "guidance": complete.recovery.guidance
                }
            }

            return metrics

        except Exception as e:
            logger.error(f"Failed to explain metrics: {e}")
            raise
