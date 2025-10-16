"""
Scenario test: Tired athlete.

Tests system behavior for tired athlete:
- Low HRV (below baseline)
- Poor sleep (<6 hours)
- High stress
- Should recommend easy workout or rest
"""

import pytest
from datetime import date, timedelta


@pytest.mark.scenario
class TestTiredAthlete:
    """Test tired athlete scenario."""

    def test_hrv_below_baseline(self, data_processor, tired_hrv_data):
        """Test HRV is significantly below baseline."""
        baseline = data_processor.calculate_hrv_baseline(tired_hrv_data[:-1], days=7)
        current_hrv = tired_hrv_data[-1]

        drop_analysis = data_processor.detect_hrv_drop(current_hrv, baseline)

        assert drop_analysis['is_significant'] is True
        assert drop_analysis['drop_percentage'] > 10

    def test_poor_sleep_quality(self, data_processor, tired_sleep_data):
        """Test sleep quality is poor."""
        sleep_score = data_processor.calculate_sleep_quality_score(tired_sleep_data)

        assert sleep_score < 65
        assert tired_sleep_data['total_sleep_minutes'] < 360  # <6 hours

    def test_high_stress_levels(self, tired_metrics):
        """Test stress levels are elevated."""
        assert tired_metrics['stress_score'] > 60

    def test_readiness_recommendation_rest(self, db_session, readiness_analyzer, tired_context):
        """Test system recommends rest or easy workout."""
        from app.services import data_access

        # Create user and populate database
        user_id = "tired_test_user"
        test_date = date.today()

        data_access.create_user(db_session, {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Tired Test User"
        })

        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **tired_context['daily_metrics']
        }
        if 'sleep_data' in tired_context:
            metrics_data.update(tired_context['sleep_data'])
        data_access.create_daily_metrics(db_session, metrics_data)

        recommendation = readiness_analyzer.analyze_readiness(user_id, test_date)

        assert recommendation.readiness_level.value in ['poor', 'low', 'moderate']
        assert recommendation.readiness_score < 70

    def test_red_flags_present(self, db_session, readiness_analyzer, tired_context):
        """Test warning signals are detected."""
        from app.services import data_access

        user_id = "tired_redflag_user"
        test_date = date.today()

        data_access.create_user(db_session, {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Tired Red Flag User"
        })

        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **tired_context['daily_metrics']
        }
        if 'sleep_data' in tired_context:
            metrics_data.update(tired_context['sleep_data'])
        data_access.create_daily_metrics(db_session, metrics_data)

        recommendation = readiness_analyzer.analyze_readiness(user_id, test_date)

        # Check for concerns about low HRV or poor sleep
        assert len(recommendation.concerns) > 0


# Fixtures
@pytest.fixture
def tired_hrv_data():
    """HRV data for tired athlete (significant drop)."""
    return [65.0, 64.0, 66.0, 65.5, 63.0, 62.0, 48.0]  # Last: significant drop


@pytest.fixture
def tired_sleep_data():
    """Sleep data for tired athlete."""
    return {
        'total_sleep_minutes': 300,  # 5 hours - very short
        'deep_sleep_minutes': 25,   # Low deep sleep (~8%)
        'light_sleep_minutes': 200,
        'rem_sleep_minutes': 40,    # Low REM sleep (~13%)
        'awake_minutes': 35,        # High wake time (~12%)
        'sleep_score': 55
    }


@pytest.fixture
def tired_metrics():
    """Daily metrics for tired athlete."""
    return {
        'hrv_sdnn': 48.0,
        'resting_heart_rate': 62,  # Elevated
        'stress_score': 72,
        'body_battery_charged': 45,
        'sleep_score': 55
    }


@pytest.fixture
def tired_context(tired_metrics, tired_sleep_data):
    """Complete context for tired athlete."""
    return {
        'daily_metrics': tired_metrics,
        'sleep_data': tired_sleep_data,
        'training_history': {
            'daily_loads': [120, 110, 100, 95, 90, 85, 80],
            'dates': [date.today() - timedelta(days=i) for i in range(7)]
        },
        'user_profile': {'age': 35, 'fitness_level': 'advanced'}
    }


@pytest.fixture
def readiness_analyzer(db_session):
    """Create readiness analyzer."""
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer(db_session, use_mock=True)


@pytest.fixture
def data_processor(db_session):
    """Create data processor."""
    from app.services.data_processor import DataProcessor
    return DataProcessor(db_session)
