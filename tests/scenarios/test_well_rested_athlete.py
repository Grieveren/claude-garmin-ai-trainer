"""
Scenario test: Well-rested athlete.

Tests system behavior when athlete is well-recovered:
- High HRV (above baseline)
- Good sleep (7-8 hours, good quality)
- Low stress
- Appropriate ACWR
- Should recommend high-intensity workout
"""

import pytest
from datetime import date, timedelta


@pytest.mark.scenario
class TestWellRestedAthlete:
    """Test well-rested athlete scenario."""

    def test_hrv_above_baseline(self, data_processor, well_rested_hrv_data):
        """Test HRV is above baseline for well-rested athlete."""
        baseline = data_processor.calculate_hrv_baseline(well_rested_hrv_data[:-1], days=7)
        current_hrv = well_rested_hrv_data[-1]

        drop_analysis = data_processor.detect_hrv_drop(current_hrv, baseline)

        assert drop_analysis['is_significant'] is False
        assert current_hrv >= baseline['mean']

    def test_good_sleep_quality(self, data_processor, well_rested_sleep_data):
        """Test sleep quality is good."""
        sleep_score = data_processor.calculate_sleep_quality_score(well_rested_sleep_data)

        assert sleep_score >= 75
        assert well_rested_sleep_data['total_sleep_minutes'] >= 420  # 7+ hours

    def test_low_stress_levels(self, well_rested_metrics):
        """Test stress levels are low."""
        assert well_rested_metrics['stress_score'] < 40

    def test_appropriate_training_load(self, data_processor, well_rested_training_data):
        """Test training load is appropriate (not overtrained)."""
        acwr = data_processor.calculate_acwr(well_rested_training_data)

        assert 0.8 <= acwr <= 1.3  # Optimal range

    def test_readiness_recommendation(self, readiness_analyzer, well_rested_context):
        """Test that system recommends high-intensity workout."""
        recommendation = readiness_analyzer.analyze_readiness(well_rested_context)

        assert recommendation['recommendation'] in ['high_intensity', 'moderate']
        assert recommendation['readiness_score'] >= 75

    def test_workout_suggestion_appropriate(self, readiness_analyzer, well_rested_context):
        """Test suggested workout is appropriately challenging."""
        recommendation = readiness_analyzer.analyze_readiness(well_rested_context)

        suggested_workout = recommendation.get('suggested_workout')
        if suggested_workout:
            assert suggested_workout['intensity_level'] >= 7

    def test_no_red_flags(self, readiness_analyzer, well_rested_context):
        """Test no warning signals for well-rested athlete."""
        recommendation = readiness_analyzer.analyze_readiness(well_rested_context)

        red_flags = recommendation.get('red_flags', [])
        assert len(red_flags) == 0

    def test_recovery_status_excellent(self, data_processor, well_rested_metrics):
        """Test recovery status is excellent."""
        current_hrv = well_rested_metrics['hrv_sdnn']
        baseline = {'mean': 60.0, 'std': 5.0}

        status = data_processor.assess_recovery_status(current_hrv, baseline)

        assert status == 'well_recovered'


# Fixtures
@pytest.fixture
def well_rested_hrv_data():
    """HRV data for well-rested athlete (consistently high)."""
    return [68.0, 70.0, 69.0, 71.0, 68.5, 70.5, 72.0]  # Last value is current


@pytest.fixture
def well_rested_sleep_data():
    """Sleep data for well-rested athlete."""
    return {
        'total_sleep_minutes': 480,  # 8 hours
        'deep_sleep_minutes': 130,
        'light_sleep_minutes': 240,
        'rem_sleep_minutes': 90,
        'awake_minutes': 20,
        'sleep_score': 88
    }


@pytest.fixture
def well_rested_metrics():
    """Daily metrics for well-rested athlete."""
    return {
        'hrv_sdnn': 72.0,
        'resting_heart_rate': 52,
        'stress_score': 28,
        'body_battery_charged': 90,
        'sleep_score': 88,
        'steps': 12000
    }


@pytest.fixture
def well_rested_training_data():
    """Training data showing appropriate load."""
    return {
        'daily_loads': [100, 95, 110, 85, 105, 90, 100] + [80] * 21,  # 7 days acute, 21 chronic
        'dates': [date.today() - timedelta(days=i) for i in range(28)]
    }


@pytest.fixture
def well_rested_context(well_rested_metrics, well_rested_sleep_data, well_rested_training_data):
    """Complete context for well-rested athlete."""
    return {
        'daily_metrics': well_rested_metrics,
        'sleep_data': well_rested_sleep_data,
        'training_history': well_rested_training_data,
        'user_profile': {
            'age': 35,
            'gender': 'male',
            'fitness_level': 'advanced'
        }
    }


@pytest.fixture
def readiness_analyzer():
    """Create readiness analyzer instance."""
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer()


@pytest.fixture
def data_processor():
    """Create data processor instance."""
    from app.services.data_processor import DataProcessor
    return DataProcessor()
