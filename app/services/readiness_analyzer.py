"""
Readiness Analyzer - Orchestrates data preparation and AI analysis.

This service acts as a facade that:
1. Fetches required data from database
2. Calculates derived metrics
3. Prepares context for AI analysis
4. Coordinates AI service calls
5. Returns comprehensive readiness assessment

Follows the facade pattern to provide a simple interface to complex subsystems.
"""

import logging
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.services.claude_service import ClaudeService, ClaudeServiceError
from app.services.data_processor import DataProcessor
from app.services.cache_service import CacheService
from app.services import data_access
from app.models.ai_schemas import (
    ReadinessContext,
    ReadinessAnalysis,
    CompleteRecommendation
)

logger = logging.getLogger(__name__)


class ReadinessAnalyzer:
    """
    Analyze training readiness by coordinating data and AI services.

    This is the main entry point for readiness analysis. It handles:
    - Data fetching and preparation
    - Context building for AI
    - AI service orchestration
    - Result aggregation
    """

    def __init__(
        self,
        db_session: Session,
        claude_service: Optional[ClaudeService] = None,
        use_mock: bool = False,
        use_cache: bool = True
    ):
        """
        Initialize readiness analyzer.

        Args:
            db_session: Database session
            claude_service: Claude AI service (optional, will create if not provided)
            use_mock: Use mock service for testing (default False)
            use_cache: Enable response caching (default True)
        """
        self.db = db_session
        self.data_processor = DataProcessor(db_session)

        # Initialize cache service
        if use_cache:
            self.cache_service = CacheService(db_session)
            logger.info("Cache service enabled")
        else:
            self.cache_service = None
            logger.info("Cache service disabled")

        if use_mock:
            from tests.mocks.mock_claude_service import MockClaudeService
            self.claude_service = MockClaudeService()
            logger.info("Using mock Claude service")
        elif claude_service:
            self.claude_service = claude_service
        else:
            # Create real service if not provided
            try:
                self.claude_service = ClaudeService()
                logger.info("Initialized real Claude service")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude service: {e}. Using mock.")
                from tests.mocks.mock_claude_service import MockClaudeService
                self.claude_service = MockClaudeService()

    def analyze_readiness(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> ReadinessAnalysis:
        """
        Perform complete readiness analysis for a user on a specific date.

        Args:
            user_id: User identifier
            target_date: Date to analyze (defaults to today)

        Returns:
            ReadinessAnalysis with score, level, and detailed insights

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Analyzing readiness for user {user_id} on {target_date}")

        try:
            # Step 1: Prepare context
            context = self._prepare_readiness_context(user_id, target_date)

            # Step 2: Check cache
            if self.cache_service:
                cached_analysis = self.cache_service.get_readiness_analysis(context)
                if cached_analysis:
                    logger.info(f"Returning cached readiness analysis for {user_id}")
                    return cached_analysis

            # Step 3: Get AI analysis (cache miss)
            analysis = self.claude_service.analyze_readiness(context)

            # Step 4: Cache the result
            if self.cache_service:
                self.cache_service.cache_readiness_analysis(context, analysis)

            logger.info(
                f"Readiness analysis complete: {analysis.readiness_level.value} "
                f"(score: {analysis.readiness_score:.1f})"
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze readiness: {e}")
            raise

    def get_complete_recommendation(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> CompleteRecommendation:
        """
        Get complete set of recommendations including readiness, training, and recovery.

        Args:
            user_id: User identifier
            target_date: Date to analyze (defaults to today)

        Returns:
            CompleteRecommendation with all components

        Raises:
            ValueError: If required data is missing
            ClaudeServiceError: If AI service fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating complete recommendation for {user_id} on {target_date}")

        try:
            # Step 1: Prepare context
            context = self._prepare_readiness_context(user_id, target_date)

            # Step 2: Check cache
            if self.cache_service:
                cached_recommendation = self.cache_service.get_complete_recommendation(context)
                if cached_recommendation:
                    logger.info(f"Returning cached complete recommendation for {user_id}")
                    return cached_recommendation

            # Step 3: Get AI recommendation (cache miss)
            recommendation = self.claude_service.get_complete_recommendation(context)

            # Step 4: Cache the result
            if self.cache_service:
                self.cache_service.cache_complete_recommendation(context, recommendation)

            logger.info("Complete recommendation generated successfully")

            return recommendation

        except Exception as e:
            logger.error(f"Failed to generate complete recommendation: {e}")
            raise

    def _prepare_readiness_context(
        self,
        user_id: str,
        target_date: date
    ) -> ReadinessContext:
        """
        Prepare readiness context by fetching and calculating required metrics.

        Args:
            user_id: User identifier
            target_date: Date to analyze

        Returns:
            ReadinessContext with all relevant metrics

        Raises:
            ValueError: If critical data is missing
        """
        logger.debug(f"Preparing context for {user_id} on {target_date}")

        # Get daily metrics
        daily_metrics = data_access.get_daily_metrics(self.db, user_id, target_date)

        if not daily_metrics:
            logger.warning(f"No daily metrics found for {user_id} on {target_date}")
            # Return minimal context - AI can handle missing data
            return ReadinessContext(
                user_id=user_id,
                analysis_date=target_date
            )

        # Get HRV metrics
        hrv_current = daily_metrics.hrv_sdnn
        hrv_baseline_7d = self.data_processor.calculate_hrv_baseline_from_db(
            user_id=user_id,
            days=7
        )
        hrv_baseline_30d = self.data_processor.calculate_hrv_baseline_from_db(
            user_id=user_id,
            days=30
        )

        # Calculate HRV percentage of baseline
        hrv_percent_of_baseline = None
        if hrv_current and hrv_baseline_7d:
            hrv_percent_of_baseline = (hrv_current / hrv_baseline_7d) * 100

        # Get sleep metrics
        sleep_last_night = None
        sleep_quality_score = None
        if hasattr(daily_metrics, 'total_sleep_minutes'):
            sleep_last_night = daily_metrics.total_sleep_minutes

        sleep_average_7d = self._calculate_average_sleep_7d(user_id, target_date)

        # Get training load metrics
        training_load_7d = self._calculate_training_load_7d(user_id, target_date)
        training_load_28d = self._calculate_training_load_28d(user_id, target_date)

        # Calculate ACWR
        acwr = None
        if training_load_7d and training_load_28d and training_load_28d > 0:
            chronic_load = training_load_28d / 4  # Weekly average over 28 days
            if chronic_load > 0:
                acwr = training_load_7d / chronic_load

        # Get fitness-fatigue metrics
        fitness_score = None
        fatigue_score = None
        form_score = None
        try:
            ff_metrics = self.data_processor.calculate_fitness_fatigue_from_db(
                user_id=user_id,
                days=42
            )
            if ff_metrics:
                fitness_score = ff_metrics.get('ctl')
                fatigue_score = ff_metrics.get('atl')
                form_score = ff_metrics.get('tsb')
        except Exception as e:
            logger.debug(f"Could not calculate fitness-fatigue: {e}")

        # Get heart rate baseline
        rhr_baseline_7d = self._calculate_rhr_baseline_7d(user_id, target_date)

        # Get recent activities
        recent_activities = self._get_recent_activities(user_id, target_date, days=7)

        # Calculate training patterns
        days_since_last_rest = self._calculate_days_since_last_rest(
            user_id,
            target_date
        )
        consecutive_hard_days = self._calculate_consecutive_hard_days(
            user_id,
            target_date
        )

        # Build context
        context = ReadinessContext(
            user_id=user_id,
            analysis_date=target_date,
            hrv_current=hrv_current,
            hrv_baseline_7d=hrv_baseline_7d,
            hrv_baseline_30d=hrv_baseline_30d,
            hrv_percent_of_baseline=hrv_percent_of_baseline,
            sleep_last_night=sleep_last_night,
            sleep_quality_score=sleep_quality_score,
            sleep_average_7d=sleep_average_7d,
            training_load_7d=training_load_7d,
            training_load_28d=training_load_28d,
            acwr=acwr,
            fitness_score=fitness_score,
            fatigue_score=fatigue_score,
            form_score=form_score,
            resting_heart_rate=daily_metrics.resting_heart_rate,
            rhr_baseline_7d=rhr_baseline_7d,
            steps_today=daily_metrics.steps,
            calories_today=daily_metrics.calories,
            recent_activities=recent_activities,
            days_since_last_rest=days_since_last_rest,
            consecutive_hard_days=consecutive_hard_days
        )

        logger.debug(f"Context prepared with HRV: {hrv_current}, Sleep: {sleep_last_night}, ACWR: {acwr}")

        return context

    def _calculate_average_sleep_7d(self, user_id: str, target_date: date) -> Optional[int]:
        """Calculate 7-day average sleep duration."""
        start_date = target_date - timedelta(days=7)
        metrics_list = data_access.get_metrics_range(
            self.db,
            user_id,
            start_date,
            target_date
        )

        if not metrics_list:
            return None

        sleep_values = []
        for m in metrics_list:
            if hasattr(m, 'total_sleep_minutes') and m.total_sleep_minutes:
                sleep_values.append(m.total_sleep_minutes)

        if not sleep_values:
            return None

        return int(sum(sleep_values) / len(sleep_values))

    def _calculate_training_load_7d(self, user_id: str, target_date: date) -> Optional[int]:
        """Calculate 7-day training load."""
        try:
            result = self.data_processor.calculate_training_load_from_db(
                user_id=user_id,
                days=7
            )
            # Extract acute_load (7-day load) from the dict
            if result and isinstance(result, dict):
                return result.get('acute_load')
            return None
        except Exception as e:
            logger.debug(f"Could not calculate 7-day training load: {e}")
            return None

    def _calculate_training_load_28d(self, user_id: str, target_date: date) -> Optional[int]:
        """Calculate 28-day training load."""
        try:
            result = self.data_processor.calculate_training_load_from_db(
                user_id=user_id,
                days=28
            )
            # Extract chronic_load (28-day load) from the dict
            if result and isinstance(result, dict):
                return result.get('chronic_load')
            return None
        except Exception as e:
            logger.debug(f"Could not calculate 28-day training load: {e}")
            return None

    def _calculate_rhr_baseline_7d(self, user_id: str, target_date: date) -> Optional[float]:
        """Calculate 7-day resting heart rate baseline."""
        start_date = target_date - timedelta(days=7)
        metrics_list = data_access.get_metrics_range(
            self.db,
            user_id,
            start_date,
            target_date
        )

        if not metrics_list:
            return None

        rhr_values = [m.resting_heart_rate for m in metrics_list if m.resting_heart_rate]

        if not rhr_values:
            return None

        return sum(rhr_values) / len(rhr_values)

    def _get_recent_activities(
        self,
        user_id: str,
        target_date: date,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get recent activities for context."""
        try:
            activities = data_access.get_recent_activities(
                self.db,
                user_id,
                limit=20
            )

            # Filter to date range and format
            start_date = target_date - timedelta(days=days)
            recent = []

            for activity in activities:
                if hasattr(activity, 'date') and activity.date >= start_date:
                    activity_dict = {
                        'date': activity.date.isoformat(),
                        'type': activity.type if hasattr(activity, 'type') else 'unknown',
                        'duration_minutes': activity.duration_minutes if hasattr(activity, 'duration_minutes') else None,
                        'distance': activity.distance if hasattr(activity, 'distance') else None
                    }
                    recent.append(activity_dict)

            return recent

        except Exception as e:
            logger.debug(f"Could not fetch recent activities: {e}")
            return []

    def _calculate_days_since_last_rest(
        self,
        user_id: str,
        target_date: date
    ) -> Optional[int]:
        """Calculate days since last rest day."""
        try:
            # Look back up to 14 days
            start_date = target_date - timedelta(days=14)
            activities = data_access.get_recent_activities(
                self.db,
                user_id,
                limit=30
            )

            if not activities:
                return None

            # Count days with no activity
            current = target_date - timedelta(days=1)
            days_count = 0

            for i in range(14):
                day_activities = [
                    a for a in activities
                    if hasattr(a, 'date') and a.date == current
                ]

                if not day_activities:
                    # Found a rest day
                    return days_count

                days_count += 1
                current -= timedelta(days=1)

            return None

        except Exception as e:
            logger.debug(f"Could not calculate days since last rest: {e}")
            return None

    def _calculate_consecutive_hard_days(
        self,
        user_id: str,
        target_date: date
    ) -> Optional[int]:
        """Calculate consecutive hard training days."""
        try:
            # Get recent activities
            activities = data_access.get_recent_activities(
                self.db,
                user_id,
                limit=30
            )

            if not activities:
                return None

            # Count consecutive days with "hard" activities
            # Define "hard" as duration > 45 minutes or high intensity
            consecutive = 0
            current = target_date - timedelta(days=1)

            for i in range(7):
                day_activities = [
                    a for a in activities
                    if hasattr(a, 'date') and a.date == current
                ]

                # Check if any activity was "hard"
                is_hard_day = False
                for activity in day_activities:
                    if hasattr(activity, 'duration_minutes') and activity.duration_minutes:
                        if activity.duration_minutes > 45:
                            is_hard_day = True
                            break

                if is_hard_day:
                    consecutive += 1
                else:
                    # Streak broken
                    break

                current -= timedelta(days=1)

            return consecutive if consecutive > 0 else None

        except Exception as e:
            logger.debug(f"Could not calculate consecutive hard days: {e}")
            return None
