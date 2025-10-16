"""
Comprehensive tests for Data Access Layer operations.

Tests the new DAL functions from app/services/data_access.py:
- Query performance benchmarks
- Bulk operations
- Aggregation queries
- Common query patterns
"""

import pytest
from datetime import date, datetime, timedelta
import time

from app.services.data_access import (
    # User operations
    get_user_by_id, create_user,
    # Daily metrics
    get_daily_metrics, get_metrics_range, upsert_daily_metrics,
    bulk_insert_daily_metrics, get_latest_metrics,
    # Activities
    get_recent_activities, bulk_insert_activities,
    # Sleep
    get_sleep_stats,
    # HRV
    get_hrv_baseline,
    # Training load
    calculate_acwr, get_acute_training_load, get_chronic_training_load,
    # Aggregates
    get_dashboard_summary, get_weekly_summary,
    # Cleanup
    delete_old_data
)
from app.utils.database_utils import (
    ensure_user_exists, get_or_create, update_or_create,
    get_date_range_for_period, format_duration, format_pace
)
from app.models.database_models import (
    DailyMetrics, Activity, ActivityType
)


class TestPerformance:
    """Performance benchmark tests."""

    @pytest.mark.performance
    @pytest.mark.db
    def test_single_metrics_query_performance(self, test_db_session, sample_user, daily_metrics_30_days):
        """Test single day metrics query <10ms."""
        start_time = time.time()
        metrics = get_daily_metrics(test_db_session, sample_user.user_id, date.today())
        elapsed_ms = (time.time() - start_time) * 1000

        assert metrics is not None
        assert elapsed_ms < 10, f"Query took {elapsed_ms:.1f}ms, target is <10ms"

    @pytest.mark.performance
    @pytest.mark.db
    def test_range_query_performance(self, test_db_session, sample_user, daily_metrics_30_days):
        """Test 30-day range query <100ms."""
        start_date = date.today() - timedelta(days=29)
        end_date = date.today()

        start_time = time.time()
        metrics = get_metrics_range(test_db_session, sample_user.user_id, start_date, end_date)
        elapsed_ms = (time.time() - start_time) * 1000

        assert len(metrics) == 30
        assert elapsed_ms < 100, f"Query took {elapsed_ms:.1f}ms, target is <100ms"

    @pytest.mark.performance
    @pytest.mark.db
    def test_bulk_insert_performance(self, test_db_session, sample_user):
        """Test bulk insert 100 records <500ms."""
        metrics_list = []
        for i in range(100):
            metrics_list.append({
                "user_id": sample_user.user_id,
                "date": date.today() - timedelta(days=i + 100),  # Avoid conflicts
                "steps": 10000 + i,
                "calories": 2200,
            })

        start_time = time.time()
        count = bulk_insert_daily_metrics(test_db_session, metrics_list, upsert=False)
        test_db_session.commit()
        elapsed_ms = (time.time() - start_time) * 1000

        assert count == 100
        assert elapsed_ms < 500, f"Bulk insert took {elapsed_ms:.1f}ms, target is <500ms"

    @pytest.mark.performance
    @pytest.mark.db
    def test_dashboard_summary_performance(self, test_db_session, sample_user, daily_metrics_30_days, sample_activities):
        """Test dashboard summary <200ms."""
        start_time = time.time()
        summary = get_dashboard_summary(test_db_session, sample_user.user_id)
        elapsed_ms = (time.time() - start_time) * 1000

        assert summary is not None
        assert elapsed_ms < 200, f"Dashboard query took {elapsed_ms:.1f}ms, target is <200ms"


class TestDailyMetricsQueries:
    """Test daily metrics query operations."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_latest_metrics(self, test_db_session, sample_user, daily_metrics_30_days):
        """Test getting latest N days of metrics."""
        metrics = get_latest_metrics(test_db_session, sample_user.user_id, limit=10)

        assert len(metrics) == 10
        # Should be sorted by date descending
        assert metrics[0].date >= metrics[-1].date

    @pytest.mark.unit
    @pytest.mark.db
    def test_upsert_daily_metrics(self, test_db_session, sample_user):
        """Test upsert (insert or update) daily metrics."""
        today = date.today()

        # First insert
        metrics1 = upsert_daily_metrics(test_db_session, {
            "user_id": sample_user.user_id,
            "date": today,
            "steps": 10000,
            "calories": 2200
        })
        test_db_session.commit()

        assert metrics1.steps == 10000

        # Update with upsert
        metrics2 = upsert_daily_metrics(test_db_session, {
            "user_id": sample_user.user_id,
            "date": today,
            "steps": 12000,
            "calories": 2400
        })
        test_db_session.commit()

        # Should be same record, updated
        assert metrics2.id == metrics1.id
        assert metrics2.steps == 12000
        assert metrics2.calories == 2400


class TestActivityQueries:
    """Test activity query operations."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_recent_activities(self, test_db_session, sample_user, sample_activities):
        """Test getting recent activities."""
        activities = get_recent_activities(test_db_session, sample_user.user_id, limit=3)

        assert len(activities) == 3
        # Should be sorted by start_time descending
        assert activities[0].start_time >= activities[-1].start_time

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_activities_by_type(self, test_db_session, sample_user, sample_activities):
        """Test filtering activities by type."""
        running_activities = get_recent_activities(
            test_db_session,
            sample_user.user_id,
            limit=10,
            activity_type=ActivityType.RUNNING
        )

        assert all(a.activity_type == ActivityType.RUNNING for a in running_activities)

    @pytest.mark.unit
    @pytest.mark.db
    def test_bulk_insert_activities(self, test_db_session, sample_user):
        """Test bulk activity insert."""
        activities_list = []
        for i in range(20):
            activities_list.append({
                "user_id": sample_user.user_id,
                "garmin_activity_id": f"bulk_activity_{i:04d}",
                "activity_date": date.today() - timedelta(days=i + 50),
                "start_time": datetime.now() - timedelta(days=i + 50),
                "activity_type": ActivityType.RUNNING,
                "duration_seconds": 1800,
                "distance_meters": 5000.0,
            })

        count = bulk_insert_activities(test_db_session, activities_list, upsert=False)
        test_db_session.commit()

        assert count == 20


class TestSleepQueries:
    """Test sleep query operations."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_sleep_stats(self, test_db_session, sample_user, sleep_sessions_7_days):
        """Test sleep statistics aggregation."""
        stats = get_sleep_stats(test_db_session, sample_user.user_id, days=7)

        assert stats is not None
        assert "avg_total_sleep_minutes" in stats
        assert stats["avg_total_sleep_minutes"] > 0
        assert "avg_sleep_score" in stats


class TestHRVQueries:
    """Test HRV query operations."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_hrv_baseline(self, test_db_session, sample_user, hrv_readings_30_days):
        """Test HRV baseline calculation."""
        baseline = get_hrv_baseline(test_db_session, sample_user.user_id, days=30)

        assert baseline is not None
        assert "avg_hrv_sdnn" in baseline
        assert baseline["avg_hrv_sdnn"] > 0
        assert "stddev_hrv_sdnn" in baseline
        assert baseline["days_analyzed"] == 30


class TestTrainingLoadQueries:
    """Test training load query operations."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_acute_training_load(self, test_db_session, sample_user, training_load_14_days):
        """Test acute training load calculation (7-day average)."""
        acute_load = get_acute_training_load(test_db_session, sample_user.user_id, days=7)

        assert acute_load is not None
        assert acute_load > 0

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_chronic_training_load(self, test_db_session, sample_user, training_load_30_days):
        """Test chronic training load calculation (28-day average)."""
        chronic_load = get_chronic_training_load(test_db_session, sample_user.user_id, days=28)

        assert chronic_load is not None
        assert chronic_load > 0

    @pytest.mark.unit
    @pytest.mark.db
    def test_calculate_acwr(self, test_db_session, sample_user, training_load_30_days):
        """Test ACWR calculation."""
        acwr = calculate_acwr(test_db_session, sample_user.user_id)

        assert acwr is not None
        assert 0.5 <= acwr <= 2.0  # Reasonable ACWR range


class TestAggregatedQueries:
    """Test aggregated query operations."""

    @pytest.mark.integration
    @pytest.mark.db
    def test_get_dashboard_summary(self, test_db_session, sample_user, daily_metrics_30_days, sample_activities):
        """Test comprehensive dashboard summary."""
        summary = get_dashboard_summary(test_db_session, sample_user.user_id)

        assert summary is not None
        assert summary["user_id"] == sample_user.user_id
        assert "latest_metrics" in summary
        assert "training_load" in summary
        assert "sleep_summary" in summary

    @pytest.mark.integration
    @pytest.mark.db
    def test_get_weekly_summary(self, test_db_session, sample_user, daily_metrics_30_days, sample_activities):
        """Test weekly training summary."""
        summary = get_weekly_summary(test_db_session, sample_user.user_id, weeks_back=0)

        assert summary is not None
        assert "week_start" in summary
        assert "week_end" in summary
        assert "activities" in summary
        assert "health" in summary


class TestUtilityFunctions:
    """Test utility functions from database_utils."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_ensure_user_exists(self, test_db_session):
        """Test ensure_user_exists utility."""
        # First call creates user
        user1 = ensure_user_exists(test_db_session, "new_user_001", {
            "name": "New User",
            "email": "new@example.com"
        })
        test_db_session.commit()

        assert user1.user_id == "new_user_001"
        assert user1.name == "New User"

        # Second call returns existing user
        user2 = ensure_user_exists(test_db_session, "new_user_001")

        assert user2.id == user1.id

    @pytest.mark.unit
    @pytest.mark.db
    def test_get_or_create(self, test_db_session, sample_user):
        """Test generic get_or_create utility."""
        # First call creates
        metrics1, created1 = get_or_create(
            test_db_session,
            DailyMetrics,
            defaults={"steps": 10000},
            user_id=sample_user.user_id,
            date=date.today()
        )
        test_db_session.commit()

        assert created1 is True

        # Second call retrieves
        metrics2, created2 = get_or_create(
            test_db_session,
            DailyMetrics,
            defaults={"steps": 12000},
            user_id=sample_user.user_id,
            date=date.today()
        )

        assert created2 is False
        assert metrics2.id == metrics1.id

    @pytest.mark.unit
    @pytest.mark.db
    def test_update_or_create(self, test_db_session, sample_user):
        """Test update_or_create utility."""
        # First call creates
        metrics1, created1 = update_or_create(
            test_db_session,
            DailyMetrics,
            lookup_fields={"user_id": sample_user.user_id, "date": date.today()},
            update_data={"steps": 10000}
        )
        test_db_session.commit()

        assert created1 is True

        # Second call updates
        metrics2, created2 = update_or_create(
            test_db_session,
            DailyMetrics,
            lookup_fields={"user_id": sample_user.user_id, "date": date.today()},
            update_data={"steps": 12000}
        )
        test_db_session.commit()

        assert created2 is False
        assert metrics2.steps == 12000

    @pytest.mark.unit
    def test_get_date_range_for_period(self):
        """Test date range helper."""
        start, end = get_date_range_for_period('week')
        assert (end - start).days == 6

        start, end = get_date_range_for_period('last_7_days')
        assert (end - start).days == 7

    @pytest.mark.unit
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(90) == "1h 30m"
        assert format_duration(45) == "45m"
        assert format_duration(None) == "N/A"

    @pytest.mark.unit
    def test_format_pace(self):
        """Test pace formatting."""
        assert format_pace(5.5) == "5:30"
        assert format_pace(4.25) == "4:15"
        assert format_pace(None) == "N/A"


class TestCleanupOperations:
    """Test data cleanup operations."""

    @pytest.mark.integration
    @pytest.mark.db
    def test_delete_old_data(self, test_db_session, sample_user):
        """Test old data deletion."""
        # Create old metrics (400 days ago)
        old_date = date.today() - timedelta(days=400)
        upsert_daily_metrics(test_db_session, {
            "user_id": sample_user.user_id,
            "date": old_date,
            "steps": 5000,
        })

        # Create recent metrics
        recent_date = date.today() - timedelta(days=30)
        upsert_daily_metrics(test_db_session, {
            "user_id": sample_user.user_id,
            "date": recent_date,
            "steps": 10000,
        })
        test_db_session.commit()

        # Delete data older than 365 days
        deleted = delete_old_data(test_db_session, days_to_keep=365)
        test_db_session.commit()

        assert deleted["daily_metrics"] >= 1

        # Verify old data is gone
        old_metrics = get_daily_metrics(test_db_session, sample_user.user_id, old_date)
        assert old_metrics is None

        # Verify recent data remains
        recent_metrics = get_daily_metrics(test_db_session, sample_user.user_id, recent_date)
        assert recent_metrics is not None
