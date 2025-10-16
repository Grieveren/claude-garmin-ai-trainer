"""
Comprehensive test suite for Data Processing layer.

Tests cover:
- Statistical functions (moving average, std dev, regression)
- HRV analysis (baseline, trend, drop detection)
- Training load (acute, chronic, ACWR, fitness-fatigue)
- Sleep analysis (quality scoring, debt detection)
- Data aggregation (daily, weekly, monthly)
- Main data processor orchestration
- Edge cases (missing data, NaN values, empty datasets)

Target Coverage: >90%
"""

import pytest
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.database_models import (
    UserProfile,
    DailyMetrics,
    Activity,
    SleepSession,
    ActivityType
)
from app.utils import statistics, hrv_analysis, training_load, sleep_analysis
from app.services.data_processor import DataProcessor
from app.services.aggregation_service import AggregationService


class TestHRVCalculations:
    """Test HRV analysis and calculations."""

    def test_calculate_hrv_baseline_7_day(self, data_processor, sample_hrv_data_7_days):
        """Test 7-day HRV baseline calculation."""
        baseline = data_processor.calculate_hrv_baseline(sample_hrv_data_7_days, days=7)

        assert baseline is not None
        assert 'mean' in baseline
        assert 'std' in baseline
        assert baseline['mean'] > 0

    def test_calculate_hrv_baseline_30_day(self, data_processor, sample_hrv_data_30_days):
        """Test 30-day HRV baseline calculation."""
        baseline = data_processor.calculate_hrv_baseline(sample_hrv_data_30_days, days=30)

        assert baseline is not None
        assert baseline['mean'] > 0
        assert baseline['std'] >= 0

    def test_detect_hrv_drop(self, data_processor):
        """Test HRV drop detection."""
        baseline = {'mean': 65.0, 'std': 8.0}
        current_hrv = 50.0  # Significant drop

        result = data_processor.detect_hrv_drop(current_hrv, baseline)

        assert result['is_significant'] is True
        assert result['drop_percentage'] > 15

    def test_no_hrv_drop_detected(self, data_processor):
        """Test normal HRV (no drop)."""
        baseline = {'mean': 65.0, 'std': 8.0}
        current_hrv = 68.0  # Normal range

        result = data_processor.detect_hrv_drop(current_hrv, baseline)

        assert result['is_significant'] is False
        assert result['drop_percentage'] < 15

    def test_hrv_trend_analysis(self, data_processor, sample_hrv_timeseries):
        """Test HRV trend analysis."""
        trend = data_processor.analyze_hrv_trend(sample_hrv_timeseries, days=30)

        assert 'slope' in trend
        assert 'direction' in trend  # 'increasing', 'decreasing', 'stable'
        assert 'r_squared' in trend

    def test_hrv_recovery_status(self, data_processor):
        """Test HRV-based recovery status assessment."""
        current_hrv = 70.0
        baseline = {'mean': 65.0, 'std': 5.0}

        status = data_processor.assess_recovery_status(current_hrv, baseline)

        assert status in ['well_recovered', 'recovered', 'recovering', 'not_recovered']

    def test_hrv_with_missing_data(self, data_processor):
        """Test HRV calculation with missing data points."""
        hrv_data = [65.0, None, 68.0, np.nan, 67.0, 70.0]

        baseline = data_processor.calculate_hrv_baseline(hrv_data, days=7)

        assert baseline is not None
        assert baseline['mean'] > 0
        # Should handle missing values gracefully

    def test_hrv_empty_dataset(self, data_processor):
        """Test HRV calculation with empty dataset."""
        hrv_data = []

        with pytest.raises(ValueError):
            data_processor.calculate_hrv_baseline(hrv_data, days=7)


class TestTrainingLoadCalculations:
    """Test training load calculations."""

    def test_calculate_acute_load(self, data_processor, sample_training_load_data):
        """Test acute training load (7-day rolling average)."""
        acute_load = data_processor.calculate_acute_load(sample_training_load_data)

        assert acute_load is not None
        assert acute_load > 0

    def test_calculate_chronic_load(self, data_processor, sample_training_load_data):
        """Test chronic training load (28-day rolling average)."""
        chronic_load = data_processor.calculate_chronic_load(sample_training_load_data)

        assert chronic_load is not None
        assert chronic_load > 0

    def test_calculate_acwr(self, data_processor, sample_training_load_data):
        """Test ACWR (Acute:Chronic Workload Ratio) calculation."""
        acwr = data_processor.calculate_acwr(sample_training_load_data)

        assert acwr is not None
        assert acwr > 0
        # Typical range 0.5 - 2.0

    def test_acwr_optimal_range(self, data_processor):
        """Test ACWR classification (optimal/moderate/high risk)."""
        acwr_optimal = 1.0
        acwr_moderate = 1.4
        acwr_high_risk = 1.6

        assert data_processor.classify_acwr(acwr_optimal) == 'optimal'
        assert data_processor.classify_acwr(acwr_moderate) == 'moderate'
        assert data_processor.classify_acwr(acwr_high_risk) == 'high_risk'

    def test_training_monotony(self, data_processor):
        """Test training monotony calculation."""
        # High monotony (similar daily loads)
        loads_monotonous = [100, 100, 100, 100, 100, 100, 100]

        # Low monotony (varied daily loads)
        loads_varied = [50, 150, 80, 120, 90, 110, 75]

        monotony_high = data_processor.calculate_monotony(loads_monotonous)
        monotony_low = data_processor.calculate_monotony(loads_varied)

        assert monotony_high > monotony_low

    def test_training_strain(self, data_processor):
        """Test training strain calculation."""
        weekly_loads = [100, 120, 80, 110, 90, 100, 95]

        strain = data_processor.calculate_training_strain(weekly_loads)

        assert strain is not None
        assert strain > 0

    def test_ramp_rate(self, data_processor):
        """Test weekly ramp rate calculation."""
        last_week_load = 700
        this_week_load = 770

        ramp_rate = data_processor.calculate_ramp_rate(last_week_load, this_week_load)

        assert ramp_rate == 10.0  # 10% increase

    def test_safe_ramp_rate(self, data_processor):
        """Test safe ramp rate (should be <10% per week)."""
        safe_ramp = 8.0
        unsafe_ramp = 15.0

        assert data_processor.is_safe_ramp_rate(safe_ramp) is True
        assert data_processor.is_safe_ramp_rate(unsafe_ramp) is False


class TestFitnessFatigueModel:
    """Test Banister fitness-fatigue model."""

    def test_calculate_fitness(self, data_processor, sample_training_history):
        """Test fitness calculation (CTL - Chronic Training Load)."""
        fitness = data_processor.calculate_fitness(sample_training_history)

        assert fitness is not None
        assert fitness >= 0

    def test_calculate_fatigue(self, data_processor, sample_training_history):
        """Test fatigue calculation (ATL - Acute Training Load)."""
        fatigue = data_processor.calculate_fatigue(sample_training_history)

        assert fatigue is not None
        assert fatigue >= 0

    def test_calculate_form(self, data_processor, sample_training_history):
        """Test form calculation (TSB - Training Stress Balance)."""
        form = data_processor.calculate_form(sample_training_history)

        assert form is not None
        # Form can be positive or negative

    def test_form_interpretation(self, data_processor):
        """Test form score interpretation."""
        form_fresh = 15  # Positive = fresh
        form_optimal = 0  # Neutral = optimal for performance
        form_fatigued = -15  # Negative = fatigued

        assert data_processor.interpret_form(form_fresh) == 'fresh'
        assert data_processor.interpret_form(form_optimal) == 'race_ready'
        assert data_processor.interpret_form(form_fatigued) == 'fatigued'

    def test_fitness_fatigue_evolution(self, data_processor, sample_training_history):
        """Test tracking fitness/fatigue evolution over time."""
        evolution = data_processor.calculate_fitness_fatigue_evolution(sample_training_history)

        assert 'dates' in evolution
        assert 'fitness' in evolution
        assert 'fatigue' in evolution
        assert 'form' in evolution
        assert len(evolution['dates']) == len(evolution['fitness'])


class TestSleepAnalysis:
    """Test sleep analysis functions."""

    def test_calculate_sleep_quality_score(self, data_processor, sample_sleep_data):
        """Test sleep quality score calculation."""
        score = data_processor.calculate_sleep_quality_score(sample_sleep_data)

        assert 0 <= score <= 100

    def test_detect_poor_sleep_pattern(self, data_processor):
        """Test detection of poor sleep patterns."""
        # Multiple nights of poor sleep
        sleep_data = [
            {'total_sleep_minutes': 300},  # 5 hours
            {'total_sleep_minutes': 330},  # 5.5 hours
            {'total_sleep_minutes': 310},  # 5.2 hours
        ]

        result = data_processor.detect_poor_sleep_pattern(sleep_data, days=3)

        assert result['is_poor'] is True
        assert result['average_sleep_hours'] < 6.0

    def test_calculate_sleep_debt(self, data_processor):
        """Test sleep debt calculation."""
        target_sleep_hours = 8.0
        actual_sleep_data = [
            {'total_sleep_minutes': 420},  # 7 hours
            {'total_sleep_minutes': 390},  # 6.5 hours
            {'total_sleep_minutes': 450},  # 7.5 hours
        ]

        debt = data_processor.calculate_sleep_debt(actual_sleep_data, target_sleep_hours, days=3)

        assert debt > 0  # Has accumulated debt

    def test_analyze_sleep_consistency(self, data_processor):
        """Test sleep consistency analysis."""
        # Consistent sleep pattern
        consistent_sleep = [
            {'sleep_start_time': datetime(2025, 10, 1, 22, 30), 'total_sleep_minutes': 480},
            {'sleep_start_time': datetime(2025, 10, 2, 22, 45), 'total_sleep_minutes': 470},
            {'sleep_start_time': datetime(2025, 10, 3, 22, 20), 'total_sleep_minutes': 490},
        ]

        # Inconsistent sleep pattern
        inconsistent_sleep = [
            {'sleep_start_time': datetime(2025, 10, 1, 22, 0), 'total_sleep_minutes': 480},
            {'sleep_start_time': datetime(2025, 10, 2, 1, 30), 'total_sleep_minutes': 300},
            {'sleep_start_time': datetime(2025, 10, 3, 23, 45), 'total_sleep_minutes': 420},
        ]

        consistency_good = data_processor.analyze_sleep_consistency(consistent_sleep)
        consistency_poor = data_processor.analyze_sleep_consistency(inconsistent_sleep)

        assert consistency_good['is_consistent'] is True
        assert consistency_poor['is_consistent'] is False

    def test_sleep_stage_distribution(self, data_processor, sample_sleep_data):
        """Test sleep stage distribution analysis."""
        distribution = data_processor.analyze_sleep_stage_distribution(sample_sleep_data)

        assert 'deep_percentage' in distribution
        assert 'light_percentage' in distribution
        assert 'rem_percentage' in distribution
        assert sum([distribution['deep_percentage'],
                   distribution['light_percentage'],
                   distribution['rem_percentage']]) <= 100


class TestStatisticalFunctions:
    """Test statistical analysis functions."""

    def test_moving_average(self, data_processor):
        """Test moving average calculation."""
        data = [10, 12, 11, 13, 15, 14, 16, 18, 17, 19]

        ma_3 = data_processor.moving_average(data, window=3)
        ma_7 = data_processor.moving_average(data, window=7)

        assert len(ma_3) <= len(data)
        assert len(ma_7) <= len(data)

    def test_exponential_moving_average(self, data_processor):
        """Test exponential moving average (EMA)."""
        data = [10, 12, 11, 13, 15, 14, 16, 18, 17, 19]

        ema = data_processor.exponential_moving_average(data, span=7)

        assert len(ema) == len(data)
        # EMA is more responsive to recent changes than simple MA

    def test_standard_deviation(self, data_processor):
        """Test standard deviation calculation."""
        data = [10, 12, 11, 13, 15, 14, 16, 18, 17, 19]

        std = data_processor.standard_deviation(data)

        assert std > 0

    def test_percentile_calculation(self, data_processor):
        """Test percentile calculations."""
        data = list(range(1, 101))  # 1 to 100

        p50 = data_processor.percentile(data, 50)
        p95 = data_processor.percentile(data, 95)

        assert p50 == 50.5  # Median of 1-100 is (50+51)/2 = 50.5
        assert p95 == 95.05  # 95th percentile

    def test_z_score(self, data_processor):
        """Test z-score calculation."""
        data = [10, 12, 11, 13, 15, 14, 16, 18, 17, 19]
        value = 20

        z = data_processor.z_score(value, data)

        assert z > 0  # Value above mean

    def test_detect_outliers(self, data_processor):
        """Test outlier detection."""
        data = [10, 12, 11, 13, 15, 14, 16, 100, 17, 19]  # 100 is outlier

        outliers = data_processor.detect_outliers(data, threshold=2.0)  # Lower threshold

        assert 100 in outliers

    def test_linear_regression(self, data_processor):
        """Test linear regression for trend analysis."""
        x = list(range(10))
        y = [i * 2 + 5 for i in x]  # Linear relationship

        result = data_processor.linear_regression(x, y)

        assert 'slope' in result
        assert 'intercept' in result
        assert 'r_squared' in result
        assert result['r_squared'] > 0.95  # Strong correlation


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataset(self, data_processor):
        """Test processing empty dataset."""
        with pytest.raises(ValueError):
            data_processor.calculate_hrv_baseline([], days=7)

    def test_insufficient_data(self, data_processor):
        """Test processing insufficient data."""
        hrv_data = [65.0, 68.0]  # Only 2 days, need 7

        with pytest.raises(ValueError) as exc_info:
            data_processor.calculate_hrv_baseline(hrv_data, days=7)

        assert "insufficient data" in str(exc_info.value).lower()

    def test_all_nan_values(self, data_processor):
        """Test dataset with all NaN values."""
        data = [np.nan, np.nan, np.nan, np.nan]

        with pytest.raises(ValueError):
            data_processor.calculate_hrv_baseline(data, days=7)

    def test_mixed_nan_values(self, data_processor):
        """Test dataset with some NaN values."""
        data = [65.0, np.nan, 68.0, 67.0, np.nan, 70.0, 69.0]

        baseline = data_processor.calculate_hrv_baseline(data, days=7)

        assert baseline is not None
        # Should handle NaN gracefully

    def test_negative_values(self, data_processor):
        """Test handling of negative values (invalid)."""
        data = [65.0, 68.0, -5.0, 67.0]  # -5 is invalid for HRV

        # Should either filter out or raise error
        with pytest.raises(ValueError):
            data_processor.calculate_hrv_baseline(data, days=7)

    def test_extreme_outliers(self, data_processor):
        """Test handling of extreme outliers."""
        data = [65.0, 68.0, 67.0, 1000.0, 69.0]  # 1000 is unrealistic

        # Should detect and handle outlier
        baseline = data_processor.calculate_hrv_baseline(data, days=7, remove_outliers=True)

        assert baseline is not None
        # Baseline should not be heavily skewed by outlier

    def test_single_data_point(self, data_processor):
        """Test with single data point."""
        data = [65.0]

        with pytest.raises(ValueError):
            data_processor.calculate_hrv_baseline(data, days=7)

    def test_zero_division(self, data_processor):
        """Test handling of zero division scenarios."""
        last_week_load = 0
        this_week_load = 100

        # Should handle gracefully
        ramp_rate = data_processor.calculate_ramp_rate(last_week_load, this_week_load)

        assert ramp_rate is not None or ramp_rate == float('inf')


# Fixtures
@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = UserProfile(
        user_id="test_user_123",
        name="Test User",
        email="test@example.com",
        height_cm=180,
        weight_kg=75,
        resting_heart_rate=50,
        max_heart_rate=190
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_daily_metrics(db_session, test_user):
    """Create sample daily metrics for testing."""
    metrics = []
    base_date = date.today() - timedelta(days=30)

    for i in range(30):
        metric = DailyMetrics(
            user_id=test_user.user_id,
            date=base_date + timedelta(days=i),
            steps=10000 + (i * 100),
            resting_heart_rate=50 + (i % 5),
            hrv_rmssd=45.0 + (i % 10),
            hrv_sdnn=40.0 + (i % 8),
            total_sleep_minutes=420 + (i % 60),
            deep_sleep_minutes=80 + (i % 20),
            light_sleep_minutes=220 + (i % 30),
            rem_sleep_minutes=100 + (i % 15),
            awake_minutes=20 + (i % 10),
            body_battery_max=90 - (i % 20),
            body_battery_min=20 + (i % 15),
            stress_score=30 + (i % 40)
        )
        metrics.append(metric)
        db_session.add(metric)

    db_session.commit()
    return metrics


@pytest.fixture
def sample_activities(db_session, test_user):
    """Create sample activities for testing."""
    activities = []
    base_date = date.today() - timedelta(days=30)

    for i in range(15):  # Every other day
        activity = Activity(
            user_id=test_user.user_id,
            garmin_activity_id=f"activity_{i}",
            activity_date=base_date + timedelta(days=i * 2),
            start_time=datetime.now() - timedelta(days=i * 2),
            activity_type=ActivityType.RUNNING,
            activity_name="Morning Run",
            duration_seconds=3600,
            duration_minutes=60.0,
            distance_meters=10000,
            avg_heart_rate=150,
            training_load=100 + (i * 10),
            calories=600
        )
        activities.append(activity)
        db_session.add(activity)

    db_session.commit()
    return activities


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
