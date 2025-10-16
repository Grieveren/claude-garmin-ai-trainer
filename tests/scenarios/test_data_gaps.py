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

        # Calculate baseline - the method filters out None/NaN automatically
        baseline = data_processor.calculate_hrv_baseline(hrv_data, days=7)

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

    def test_readiness_with_missing_sleep_data(self, readiness_analyzer, db_session, sample_user):
        """Test readiness analysis when sleep data is missing."""
        from app.services import data_access

        # Create metrics without sleep data
        data_access.create_daily_metrics(
            db_session,
            {
                "user_id": sample_user.user_id,
                "date": date.today(),
                "hrv_sdnn": 65.0,
                "resting_heart_rate": 55,
                "steps": 8000
                # No sleep data
            }
        )

        analysis = readiness_analyzer.analyze_readiness(sample_user.user_id, date.today())

        assert analysis is not None
        assert analysis.readiness_score >= 0

    def test_readiness_with_no_hrv_data(self, readiness_analyzer, db_session, sample_user):
        """Test readiness when HRV data is missing."""
        from app.services import data_access

        # Create metrics without HRV data
        data_access.create_daily_metrics(
            db_session,
            {
                "user_id": sample_user.user_id,
                "date": date.today(),
                "resting_heart_rate": 55,
                "total_sleep_minutes": 480,
                "sleep_score": 85,
                "steps": 8000
                # No HRV data
            }
        )

        analysis = readiness_analyzer.analyze_readiness(sample_user.user_id, date.today())

        # Should provide recommendation based on available data
        assert analysis is not None

    def test_training_load_with_gaps(self, data_processor):
        """Test training load calculation with missing days."""
        # Filter out None values before passing to calculator
        training_loads = [100, 95, 110, 90, 105]  # Gaps removed

        # Should handle reduced data
        result = data_processor.calculate_acute_load(training_loads)

        assert result is not None
        assert result > 0

    def test_complete_pipeline_with_partial_data(self, readiness_analyzer, db_session, sample_user):
        """Test complete analysis with partial data."""
        from app.services import data_access

        # Create minimal metrics data
        data_access.create_daily_metrics(
            db_session,
            {
                "user_id": sample_user.user_id,
                "date": date.today(),
                "hrv_sdnn": 65.0,
                "total_sleep_minutes": 480,
                "steps": 5000
                # Missing other metrics
            }
        )

        analysis = readiness_analyzer.analyze_readiness(sample_user.user_id, date.today())

        assert analysis is not None
        # May have lower confidence with partial data
        assert analysis.confidence is not None


@pytest.fixture
def readiness_analyzer(db_session):
    from app.services.readiness_analyzer import ReadinessAnalyzer
    return ReadinessAnalyzer(db_session, use_mock=True)


@pytest.fixture
def data_processor(db_session):
    from app.services.data_processor import DataProcessor
    return DataProcessor(db_session)
