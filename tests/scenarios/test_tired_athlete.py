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

    def test_readiness_recommendation_rest(self, readiness_analyzer, tired_context):
        """Test system recommends rest or easy workout."""
        recommendation = readiness_analyzer.analyze_readiness(tired_context)

        assert recommendation['recommendation'] in ['rest', 'easy', 'recovery']
        assert recommendation['readiness_score'] < 60

    def test_red_flags_present(self, readiness_analyzer, tired_context):
        """Test warning signals are detected."""
        recommendation = readiness_analyzer.analyze_readiness(tired_context)

        red_flags = recommendation.get('red_flags', [])
        assert len(red_flags) > 0
        assert any('hrv' in flag.lower() or 'sleep' in flag.lower() for flag in red_flags)


# Fixtures
@pytest.fixture
def tired_hrv_data():
    """HRV data for tired athlete (significant drop)."""
    return [65.0, 64.0, 66.0, 65.5, 63.0, 62.0, 48.0]  # Last: significant drop


@pytest.fixture
def tired_sleep_data():
    """Sleep data for tired athlete."""
    return {
        'total_sleep_minutes': 330,  # 5.5 hours
        'deep_sleep_minutes': 60,
        'light_sleep_minutes': 180,
        'rem_sleep_minutes': 60,
        'awake_minutes': 30,
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
def readiness_analyzer():
    """Create readiness analyzer."""
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer()


@pytest.fixture
def data_processor():
    """Create data processor."""
    from app.services.data_processor import DataProcessor
    return DataProcessor()
