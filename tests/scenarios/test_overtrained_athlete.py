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
        acwr = data_processor.calculate_acwr(overtrained_training_data)

        assert acwr > 1.5  # High risk

    def test_elevated_resting_hr(self, overtrained_metrics):
        """Test resting heart rate is elevated."""
        # Assuming baseline RHR is ~55
        assert overtrained_metrics['resting_heart_rate'] > 62

    def test_readiness_recommendation_rest(self, readiness_analyzer, overtrained_context):
        """Test system strongly recommends rest."""
        recommendation = readiness_analyzer.analyze_readiness(overtrained_context)

        assert recommendation['recommendation'] == 'rest'
        assert recommendation['readiness_score'] < 50

    def test_overtraining_warning(self, readiness_analyzer, overtrained_context):
        """Test overtraining warning is issued."""
        recommendation = readiness_analyzer.analyze_readiness(overtrained_context)

        red_flags = recommendation.get('red_flags', [])
        assert any('overtraining' in flag.lower() for flag in red_flags)


# Fixtures
@pytest.fixture
def overtrained_hrv_data():
    """HRV data showing overtraining pattern."""
    return [65.0, 62.0, 58.0, 52.0, 50.0, 48.0, 45.0]


@pytest.fixture
def overtrained_training_data():
    """Training data with high ACWR."""
    return {
        'daily_loads': [150, 140, 130, 145, 135, 140, 150] + [80] * 21,  # Spike in acute load
        'dates': [date.today() - timedelta(days=i) for i in range(28)]
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
def readiness_analyzer():
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer()


@pytest.fixture
def data_processor():
    from app.services.data_processor import DataProcessor
    return DataProcessor()
