"""
Scenario test: Handling missing data and gaps.

Tests system behavior with incomplete data:
- Missing HRV readings
- Missing activities
- Data gaps
- Should handle gracefully and provide best-effort recommendations
"""

import pytest
import numpy as np
from datetime import date, timedelta


@pytest.mark.scenario
class TestDataGapsHandling:
    """Test handling of missing and incomplete data."""

    def test_missing_hrv_values(self, data_processor):
        """Test HRV calculation with missing values."""
        hrv_data = [65.0, None, 68.0, np.nan, 70.0, 67.0, 69.0]

        baseline = data_processor.calculate_hrv_baseline(hrv_data, days=7, allow_partial=True)

        assert baseline is not None
        assert baseline['mean'] > 0

    def test_insufficient_data_warning(self, data_processor):
        """Test warning when insufficient data for analysis."""
        hrv_data = [65.0, 68.0]  # Only 2 days

        try:
            baseline = data_processor.calculate_hrv_baseline(hrv_data, days=7)
            # Should either raise or return None
            assert baseline is None
        except ValueError as e:
            assert "insufficient" in str(e).lower()

    def test_readiness_with_missing_sleep_data(self, readiness_analyzer):
        """Test readiness analysis when sleep data is missing."""
        context = {
            'daily_metrics': {'hrv_sdnn': 65.0, 'resting_heart_rate': 55},
            'sleep_data': None,  # Missing
            'training_history': {'daily_loads': [100] * 7},
            'user_profile': {'age': 35}
        }

        recommendation = readiness_analyzer.analyze_readiness(context)

        assert recommendation is not None
        assert 'readiness_score' in recommendation

    def test_readiness_with_no_hrv_data(self, readiness_analyzer):
        """Test readiness when HRV data is missing."""
        context = {
            'daily_metrics': {'resting_heart_rate': 55},
            'sleep_data': {'total_sleep_minutes': 480, 'sleep_score': 85},
            'training_history': {'daily_loads': [100] * 7},
            'user_profile': {'age': 35}
        }

        recommendation = readiness_analyzer.analyze_readiness(context)

        # Should provide recommendation based on available data
        assert recommendation is not None

    def test_training_load_with_gaps(self, data_processor):
        """Test training load calculation with missing days."""
        training_data = {
            'daily_loads': [100, None, 95, None, 110, 90, 105],
            'dates': [date.today() - timedelta(days=i) for i in range(7)]
        }

        # Should handle gaps
        result = data_processor.calculate_acute_load(training_data, allow_gaps=True)

        assert result is not None

    def test_complete_pipeline_with_partial_data(self, readiness_analyzer):
        """Test complete analysis with partial data."""
        partial_context = {
            'daily_metrics': {
                'hrv_sdnn': 65.0,
                # Missing other metrics
            },
            'sleep_data': {
                'total_sleep_minutes': 480
                # Missing sleep stages
            },
            'training_history': {
                'daily_loads': [100, 95, None, 110, None, 90, 105]
            },
            'user_profile': {'age': 35}
        }

        recommendation = readiness_analyzer.analyze_readiness(partial_context, allow_partial=True)

        assert recommendation is not None
        # May have lower confidence
        if 'confidence_score' in recommendation:
            assert recommendation['confidence_score'] < 0.9


@pytest.fixture
def readiness_analyzer():
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer()


@pytest.fixture
def data_processor():
    from app.services.data_processor import DataProcessor
    return DataProcessor()
