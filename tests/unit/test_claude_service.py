"""
Unit tests for ClaudeService.

Tests using mock service to verify:
- Readiness analysis
- Training recommendations
- Recovery recommendations
- Workout generation
- Error handling
"""

import pytest
from datetime import date, timedelta
from app.models.ai_schemas import (
    ReadinessContext,
    ReadinessLevel,
    TrainingIntensity,
    WorkoutType
)
from tests.mocks.mock_claude_service import MockClaudeService


class TestClaudeServiceReadiness:
    """Test readiness analysis functionality."""

    def test_optimal_readiness_high_hrv(self):
        """Test optimal readiness with high HRV."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_current=70.0,
            hrv_baseline_7d=65.0,
            hrv_percent_of_baseline=107.7,
            sleep_last_night=480,  # 8 hours
            training_load_7d=400,
            training_load_28d=1600,
            acwr=1.0
        )

        analysis = service.analyze_readiness(context)

        assert analysis.user_id == "test_user"
        assert analysis.readiness_level in [ReadinessLevel.OPTIMAL, ReadinessLevel.GOOD]
        assert analysis.readiness_score >= 80
        assert analysis.confidence > 0

    def test_poor_readiness_low_hrv(self):
        """Test poor readiness with low HRV."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_current=45.0,
            hrv_baseline_7d=65.0,
            hrv_percent_of_baseline=69.2,  # <75%
            sleep_last_night=300,  # 5 hours
            acwr=1.8,  # High
            consecutive_hard_days=5
        )

        analysis = service.analyze_readiness(context)

        assert analysis.readiness_level in [ReadinessLevel.LOW, ReadinessLevel.POOR]
        assert analysis.readiness_score < 60
        assert len(analysis.concerns) > 0

    def test_moderate_readiness_mixed_signals(self):
        """Test moderate readiness with mixed metrics."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_current=58.0,
            hrv_baseline_7d=65.0,
            hrv_percent_of_baseline=89.2,
            sleep_last_night=420,  # 7 hours
            acwr=1.2
        )

        analysis = service.analyze_readiness(context)

        # Mixed signals could result in moderate to good readiness
        assert analysis.readiness_level in [ReadinessLevel.MODERATE, ReadinessLevel.GOOD, ReadinessLevel.OPTIMAL]
        assert 55 <= analysis.readiness_score <= 95

    def test_readiness_with_missing_data(self):
        """Test readiness analysis handles missing data."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_current=None,
            sleep_last_night=420
        )

        analysis = service.analyze_readiness(context)

        # Should still return analysis
        assert analysis.readiness_score >= 0
        assert analysis.readiness_level is not None

    def test_readiness_includes_component_scores(self):
        """Test that readiness includes component scores."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_current=65.0,
            hrv_baseline_7d=65.0,
            hrv_percent_of_baseline=100.0,
            sleep_last_night=480,
            acwr=1.0
        )

        analysis = service.analyze_readiness(context)

        assert analysis.hrv_score is not None
        assert analysis.sleep_score is not None
        assert 0 <= analysis.hrv_score <= 100
        assert 0 <= analysis.sleep_score <= 100


class TestClaudeServiceTraining:
    """Test training recommendation functionality."""

    def test_high_intensity_optimal_readiness(self):
        """Test high intensity recommended for optimal readiness."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=105.0
        )

        readiness = service.analyze_readiness(context)
        training = service.recommend_training(context, readiness)

        assert training.recommended_intensity == TrainingIntensity.HIGH
        assert training.recommended_duration_minutes >= 45
        assert len(training.workout_types) > 0

    def test_rest_poor_readiness(self):
        """Test rest recommended for poor readiness."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=65.0,
            sleep_last_night=300,
            acwr=1.9
        )

        readiness = service.analyze_readiness(context)
        training = service.recommend_training(context, readiness)

        assert training.recommended_intensity == TrainingIntensity.REST
        assert WorkoutType.REST in training.workout_types

    def test_moderate_intensity_good_readiness(self):
        """Test moderate intensity for good readiness."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=92.0,
            sleep_last_night=420
        )

        readiness = service.analyze_readiness(context)
        training = service.recommend_training(context, readiness)

        assert training.recommended_intensity in [
            TrainingIntensity.MODERATE,
            TrainingIntensity.HIGH
        ]
        assert training.recommended_duration_minutes > 0

    def test_training_includes_guidance(self):
        """Test training recommendation includes guidance fields."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=95.0
        )

        readiness = service.analyze_readiness(context)
        training = service.recommend_training(context, readiness)

        assert training.training_focus is not None
        assert len(training.key_considerations) > 0
        assert len(training.avoid_list) > 0
        assert training.rationale is not None


class TestClaudeServiceRecovery:
    """Test recovery recommendation functionality."""

    def test_high_recovery_priority_poor_readiness(self):
        """Test high recovery priority for poor readiness."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=70.0,
            sleep_last_night=300,
            consecutive_hard_days=5
        )

        readiness = service.analyze_readiness(context)
        recovery = service.recommend_recovery(context, readiness)

        assert recovery.recovery_priority == "high"
        assert recovery.rest_days_needed and recovery.rest_days_needed > 0
        assert recovery.sleep_target_hours >= 8.0

    def test_low_recovery_priority_optimal_readiness(self):
        """Test low recovery priority for optimal readiness."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=105.0,
            sleep_last_night=480
        )

        readiness = service.analyze_readiness(context)
        recovery = service.recommend_recovery(context, readiness)

        assert recovery.recovery_priority == "low"

    def test_recovery_includes_strategies(self):
        """Test recovery recommendation includes strategies."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=85.0
        )

        readiness = service.analyze_readiness(context)
        recovery = service.recommend_recovery(context, readiness)

        assert len(recovery.recovery_strategies) > 0
        assert len(recovery.nutrition_focus) > 0
        assert len(recovery.warning_signs) > 0
        assert recovery.guidance is not None


class TestClaudeServiceWorkout:
    """Test workout recommendation functionality."""

    def test_no_workout_for_rest_day(self):
        """Test no workout generated for rest intensity."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=65.0
        )

        readiness = service.analyze_readiness(context)
        training = service.recommend_training(context, readiness)
        workout = service.recommend_workout(context, training)

        if training.recommended_intensity == TrainingIntensity.REST:
            assert workout is None

    def test_workout_structure_complete(self):
        """Test workout has complete structure."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=95.0
        )

        readiness = service.analyze_readiness(context)
        training = service.recommend_training(context, readiness)
        workout = service.recommend_workout(context, training)

        if workout:  # Only if not rest day
            assert workout.total_duration_minutes > 0
            assert workout.warmup_duration > 0
            assert workout.main_duration > 0
            assert workout.cooldown_duration > 0
            assert workout.workout_description is not None
            assert len(workout.key_points) > 0
            assert len(workout.success_metrics) > 0

    def test_workout_zones_appropriate_for_intensity(self):
        """Test workout zones match training intensity."""
        service = MockClaudeService()

        # High intensity
        context_high = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=105.0
        )

        readiness_high = service.analyze_readiness(context_high)
        training_high = service.recommend_training(context_high, readiness_high)
        workout_high = service.recommend_workout(context_high, training_high)

        if workout_high and training_high.recommended_intensity == TrainingIntensity.HIGH:
            assert "Zone 4" in workout_high.target_heart_rate_zone or "Zone 5" in workout_high.target_heart_rate_zone


class TestClaudeServiceComplete:
    """Test complete recommendation generation."""

    def test_complete_recommendation_all_components(self):
        """Test complete recommendation includes all components."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=95.0,
            sleep_last_night=420
        )

        complete = service.get_complete_recommendation(context)

        assert complete.readiness is not None
        assert complete.training is not None
        assert complete.recovery is not None
        assert complete.daily_summary is not None

    def test_complete_recommendation_coherent(self):
        """Test complete recommendation is coherent across components."""
        service = MockClaudeService()

        # Poor readiness scenario
        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=70.0,
            sleep_last_night=300,
            acwr=1.8
        )

        complete = service.get_complete_recommendation(context)

        # All should indicate need for recovery
        assert complete.readiness.readiness_level in [
            ReadinessLevel.LOW,
            ReadinessLevel.POOR
        ]
        assert complete.training.recommended_intensity in [
            TrainingIntensity.LOW,
            TrainingIntensity.REST
        ]
        assert complete.recovery.recovery_priority in ["high", "moderate"]


class TestClaudeServiceErrorHandling:
    """Test error handling."""

    def test_failure_mode_raises_exception(self):
        """Test failure mode raises exceptions."""
        service = MockClaudeService()
        service.set_failure_mode(True)

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today()
        )

        with pytest.raises(Exception):
            service.analyze_readiness(context)

    def test_recovery_from_failure_mode(self):
        """Test service recovers after failure mode disabled."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_percent_of_baseline=95.0
        )

        # Enable failure
        service.set_failure_mode(True)

        with pytest.raises(Exception):
            service.analyze_readiness(context)

        # Disable failure
        service.set_failure_mode(False)

        # Should work now
        analysis = service.analyze_readiness(context)
        assert analysis is not None


class TestClaudeServiceCallTracking:
    """Test API call tracking."""

    def test_call_count_increments(self):
        """Test call count increments with each request."""
        service = MockClaudeService()

        initial_count = service.call_count

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today()
        )

        service.analyze_readiness(context)

        assert service.call_count == initial_count + 1

    def test_multiple_calls_tracked(self):
        """Test multiple calls are tracked."""
        service = MockClaudeService()

        context = ReadinessContext(
            user_id="test_user",
            analysis_date=date.today()
        )

        initial_count = service.call_count

        # Make multiple calls
        readiness = service.analyze_readiness(context)
        service.recommend_training(context, readiness)
        service.recommend_recovery(context, readiness)

        assert service.call_count == initial_count + 3
