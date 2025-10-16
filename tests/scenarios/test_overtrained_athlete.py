"""
Scenario test: Overtrained athlete.

Tests system behavior for overtrained athlete:
- Consistently low HRV for multiple days
- High ACWR (>1.5)
- Elevated resting heart rate
- Should recommend rest and recovery
"""

import pytest
from datetime import date, timedelta


@pytest.mark.scenario
class TestOvertrainedAthlete:
    """Test overtrained athlete scenario."""

    def test_persistently_low_hrv(self, data_processor, overtrained_hrv_data):
        """Test HRV is consistently low over multiple days."""
        baseline = {'mean': 65.0, 'std': 5.0}

        # Check last 3 days are low
        recent_hrvs = overtrained_hrv_data[-3:]
        for hrv in recent_hrvs:
            drop = data_processor.detect_hrv_drop(hrv, baseline)
            assert drop['is_significant'] is True

    def test_high_acwr(self, data_processor, overtrained_training_data):
        """Test ACWR is in high-risk zone."""
        # Extract the list of daily loads from the training data dict
        daily_loads = overtrained_training_data['daily_loads']
        acwr = data_processor.calculate_acwr(daily_loads)

        assert acwr > 1.5  # High risk

    def test_elevated_resting_hr(self, overtrained_metrics):
        """Test resting heart rate is elevated."""
        # Assuming baseline RHR is ~55
        assert overtrained_metrics['resting_heart_rate'] > 62

    def test_readiness_recommendation_rest(self, db_session, readiness_analyzer, overtrained_context):
        """Test system strongly recommends rest."""
        from app.services import data_access

        # Create user and populate database with overtrained athlete data
        user_id = "overtrained_test_user"
        test_date = date.today()

        # Create user
        data_access.create_user(db_session, {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Overtrained Test User"
        })

        # Create metrics with overtraining signals
        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **overtrained_context['daily_metrics']
        }
        if 'sleep_data' in overtrained_context:
            metrics_data.update(overtrained_context['sleep_data'])
        data_access.create_daily_metrics(db_session, metrics_data)

        # Analyze readiness with user_id
        recommendation = readiness_analyzer.analyze_readiness(user_id, test_date)

        assert recommendation.readiness_level.value in ['poor', 'low']
        assert recommendation.readiness_score < 60

    def test_overtraining_warning(self, db_session, readiness_analyzer, overtrained_context):
        """Test overtraining warning is issued."""
        from app.services import data_access

        # Create user and populate database
        user_id = "overtrained_warning_user"
        test_date = date.today()

        data_access.create_user(db_session, {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Overtrained Warning User"
        })

        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **overtrained_context['daily_metrics']
        }
        if 'sleep_data' in overtrained_context:
            metrics_data.update(overtrained_context['sleep_data'])
        data_access.create_daily_metrics(db_session, metrics_data)

        recommendation = readiness_analyzer.analyze_readiness(user_id, test_date)

        # Check for concerns about overtraining
        assert len(recommendation.concerns) > 0


# Fixtures
@pytest.fixture
def overtrained_hrv_data():
    """HRV data showing overtraining pattern."""
    return [65.0, 62.0, 58.0, 52.0, 50.0, 48.0, 45.0]


@pytest.fixture
def overtrained_training_data():
    """Training data with high ACWR."""
    # Most recent 7 days have high load, previous 21 days have lower load
    # This creates high ACWR (acute >> chronic)
    return {
        'daily_loads': [75] * 21 + [155, 145, 135, 150, 140, 145, 155],  # High acute load at end
        'dates': [date.today() - timedelta(days=i) for i in range(28, 0, -1)]
    }


@pytest.fixture
def overtrained_metrics():
    """Metrics for overtrained athlete."""
    return {
        'hrv_sdnn': 45.0,
        'resting_heart_rate': 68,
        'stress_score': 78,
        'body_battery_charged': 35,
        'sleep_score': 62
    }


@pytest.fixture
def overtrained_context(overtrained_metrics, overtrained_training_data):
    """Context for overtrained athlete."""
    return {
        'daily_metrics': overtrained_metrics,
        'sleep_data': {'total_sleep_minutes': 390, 'sleep_score': 62},
        'training_history': overtrained_training_data,
        'user_profile': {'age': 35, 'fitness_level': 'advanced'}
    }


@pytest.fixture
def readiness_analyzer(db_session):
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer(db_session, use_mock=True)


@pytest.fixture
def data_processor(db_session):
    from app.services.data_processor import DataProcessor
    return DataProcessor(db_session)
