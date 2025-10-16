"""
Unit tests for AI-powered services.

Tests:
- TrainingRecommender
- RecoveryAdvisor
- ExplanationGenerator
"""

import pytest
from datetime import date, timedelta
from app.services.training_recommender import TrainingRecommender
from app.services.recovery_advisor import RecoveryAdvisor
from app.services.explanation_generator import ExplanationGenerator


@pytest.mark.unit
class TestTrainingRecommender:
    """Test TrainingRecommender service."""

    def test_recommend_training_basic(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test basic training recommendation."""
        recommender = TrainingRecommender(db_session, use_mock=True)

        recommendation = recommender.recommend_training(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert recommendation is not None
        assert recommendation.user_id == sample_user.user_id
        assert recommendation.recommended_intensity is not None
        assert recommendation.training_focus is not None

    def test_recommend_workout_not_rest_day(
        self,
        db_session,
        sample_user,
        optimal_metrics
    ):
        """Test workout recommendation for non-rest day."""
        recommender = TrainingRecommender(db_session, use_mock=True)

        workout = recommender.recommend_workout(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        # Should get workout for optimal metrics
        if workout:
            assert workout.total_duration_minutes > 0
            assert workout.workout_type is not None

    def test_get_training_summary(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test training summary generation."""
        recommender = TrainingRecommender(db_session, use_mock=True)

        summary = recommender.get_training_summary(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "intensity" in summary.lower() or "training" in summary.lower()


@pytest.mark.unit
class TestRecoveryAdvisor:
    """Test RecoveryAdvisor service."""

    def test_recommend_recovery_basic(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test basic recovery recommendation."""
        advisor = RecoveryAdvisor(db_session, use_mock=True)

        recommendation = advisor.recommend_recovery(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert recommendation is not None
        assert recommendation.user_id == sample_user.user_id
        assert recommendation.recovery_priority in ["high", "moderate", "low"]

    def test_recommend_recovery_high_priority_poor_metrics(
        self,
        db_session,
        sample_user,
        poor_metrics
    ):
        """Test high recovery priority for poor metrics."""
        advisor = RecoveryAdvisor(db_session, use_mock=True)

        recommendation = advisor.recommend_recovery(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        # Poor metrics should trigger high/moderate recovery priority
        assert recommendation.recovery_priority in ["high", "moderate"]

    def test_get_recovery_summary(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test recovery summary generation."""
        advisor = RecoveryAdvisor(db_session, use_mock=True)

        summary = advisor.get_recovery_summary(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "recovery" in summary.lower() or "priority" in summary.lower()

    def test_check_recovery_status(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test recovery status check."""
        advisor = RecoveryAdvisor(db_session, use_mock=True)

        status = advisor.check_recovery_status(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(status, dict)
        assert "recovery_priority" in status
        assert "readiness_level" in status
        assert "readiness_score" in status


@pytest.mark.unit
class TestExplanationGenerator:
    """Test ExplanationGenerator service."""

    def test_explain_readiness(
        self,
        db_session,
        sample_user,
        optimal_metrics
    ):
        """Test readiness explanation generation."""
        generator = ExplanationGenerator(db_session, use_mock=True)

        explanation = generator.explain_readiness(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "Readiness" in explanation

    def test_explain_recommendation(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test recommendation explanation generation."""
        generator = ExplanationGenerator(db_session, use_mock=True)

        explanation = generator.explain_recommendation(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "Training" in explanation or "Recommendation" in explanation

    def test_explain_quick_summary(
        self,
        db_session,
        sample_user,
        basic_metrics
    ):
        """Test quick summary generation."""
        generator = ExplanationGenerator(db_session, use_mock=True)

        summary = generator.explain_quick_summary(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Should be concise
        assert len(summary) < 500

    def test_explain_metrics(
        self,
        db_session,
        sample_user,
        optimal_metrics
    ):
        """Test metrics explanation generation."""
        generator = ExplanationGenerator(db_session, use_mock=True)

        metrics = generator.explain_metrics(
            user_id=sample_user.user_id,
            target_date=date.today()
        )

        assert isinstance(metrics, dict)
        assert "readiness" in metrics
        assert "training" in metrics
        assert "recovery" in metrics

        # Check readiness structure
        assert "score" in metrics["readiness"]
        assert "level" in metrics["readiness"]

        # Check training structure
        assert "intensity" in metrics["training"]
        assert "focus" in metrics["training"]

        # Check recovery structure
        assert "priority" in metrics["recovery"]


# Fixtures

@pytest.fixture
def basic_metrics(db_session, sample_user):
    """Create basic metrics for testing."""
    from app.services import data_access

    data_access.create_daily_metrics(
        db_session,
        {
            "user_id": sample_user.user_id,
            "date": date.today(),
            "steps": 10000,
            "calories": 2200,
            "hrv_sdnn": 65.0,
            "resting_heart_rate": 55
        }
    )

    return sample_user


@pytest.fixture
def optimal_metrics(db_session, sample_user):
    """Create optimal metrics for testing."""
    from app.services import data_access

    for i in range(7):
        current_date = date.today() - timedelta(days=i)
        data_access.create_daily_metrics(
            db_session,
            {
                "user_id": sample_user.user_id,
                "date": current_date,
                "steps": 12000,
                "calories": 2400,
                "hrv_sdnn": 72.0,
                "resting_heart_rate": 52,
                "total_sleep_minutes": 480
            }
        )

    return sample_user


@pytest.fixture
def poor_metrics(db_session, sample_user):
    """Create poor metrics for testing."""
    from app.services import data_access

    for i in range(3):
        current_date = date.today() - timedelta(days=i)
        data_access.create_daily_metrics(
            db_session,
            {
                "user_id": sample_user.user_id,
                "date": current_date,
                "steps": 6000,
                "calories": 1800,
                "hrv_sdnn": 45.0,
                "resting_heart_rate": 68,
                "total_sleep_minutes": 300
            }
        )

    return sample_user
