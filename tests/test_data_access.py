"""
Tests for data access layer (DAL).

Phase 2: Database access tests
Tests CRUD operations on all Phase 2 models.
"""

import pytest
from datetime import date, timedelta

from app.models.database_models import ActivityType, ReadinessRecommendation
from tests.utils.db_test_utils import DatabaseTestUtils, DatabaseAssertions


class TestUserProfileDAL:
    """Test UserProfile data access."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_create_user_profile(self, test_db_session, sample_user):
        """Test creating a user profile."""
        users = test_db_session.query(__import__('app.models.database_models', fromlist=['UserProfile']).UserProfile).all()
        assert len(users) == 1
        assert users[0].user_id == sample_user.user_id

    @pytest.mark.unit
    @pytest.mark.db
    def test_query_user_by_id(self, test_db_session, sample_user):
        """Test querying user by ID."""
        user = DatabaseAssertions.assert_user_exists(test_db_session, sample_user.user_id)
        assert user.name == sample_user.name
        assert user.email == sample_user.email


class TestDailyMetricsDAL:
    """Test DailyMetrics data access."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_create_daily_metrics(self, test_db_session, sample_daily_metrics):
        """Test creating daily metrics."""
        assert sample_daily_metrics.id is not None
        assert sample_daily_metrics.steps > 0

    @pytest.mark.unit
    @pytest.mark.db
    def test_query_metrics_by_date(self, test_db_session, sample_user, sample_daily_metrics):
        """Test querying metrics by date."""
        metrics = DatabaseAssertions.assert_metrics_exist_for_date(
            test_db_session, sample_user.user_id, sample_daily_metrics.date
        )
        assert metrics.date == sample_daily_metrics.date

    @pytest.mark.unit
    @pytest.mark.db
    def test_metrics_date_range_query(self, test_db_session, sample_user, daily_metrics_7_days):
        """Test querying metrics for date range."""
        start_date = daily_metrics_7_days[0].date
        end_date = daily_metrics_7_days[-1].date

        metrics = DatabaseTestUtils.get_user_metrics_range(
            test_db_session, sample_user.user_id, start_date, end_date
        )

        assert len(metrics) == 7


class TestActivityDAL:
    """Test Activity data access."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_create_activity(self, test_db_session, sample_activity):
        """Test creating an activity."""
        assert sample_activity.id is not None
        assert sample_activity.activity_type == ActivityType.RUNNING

    @pytest.mark.unit
    @pytest.mark.db
    def test_query_activities_by_user(self, test_db_session, sample_user, sample_activities):
        """Test querying activities for user."""
        activities = DatabaseTestUtils.get_user_activities(
            test_db_session, sample_user.user_id
        )

        assert len(activities) == 5

    @pytest.mark.unit
    @pytest.mark.db
    def test_activities_date_range_query(self, test_db_session, sample_user, sample_activities):
        """Test querying activities for date range."""
        start_date = sample_activities[0].activity_date
        end_date = sample_activities[-1].activity_date

        activities = DatabaseTestUtils.get_user_activities(
            test_db_session, sample_user.user_id, start_date, end_date
        )

        assert len(activities) == 5


class TestSleepSessionDAL:
    """Test SleepSession data access."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_create_sleep_session(self, test_db_session, sample_sleep_data):
        """Test creating sleep session."""
        assert sample_sleep_data.id is not None
        assert sample_sleep_data.total_sleep_minutes > 0

    @pytest.mark.unit
    @pytest.mark.db
    def test_sleep_session_relationships(self, test_db_session, sample_sleep_data):
        """Test sleep session relationships."""
        assert sample_sleep_data.daily_metric_id is not None
        assert sample_sleep_data.daily_metric is not None


class TestHRVReadingDAL:
    """Test HRVReading data access."""

    @pytest.mark.unit
    @pytest.mark.db
    def test_create_hrv_reading(self, test_db_session, sample_hrv_reading):
        """Test creating HRV reading."""
        assert sample_hrv_reading.id is not None
        assert sample_hrv_reading.hrv_sdnn > 0

    @pytest.mark.unit
    @pytest.mark.db
    def test_hrv_readings_30_days(self, test_db_session, hrv_readings_30_days):
        """Test creating 30 days of HRV data."""
        assert len(hrv_readings_30_days) == 30


@pytest.mark.integration
@pytest.mark.db
class TestPopulateTestData:
    """Test data population utilities."""

    def test_populate_test_data_complete(self, test_db_session):
        """Test populating complete test dataset."""
        user = DatabaseTestUtils.populate_test_data(
            test_db_session, "test_user", "Test User", days=30
        )

        assert user is not None
        DatabaseTestUtils.assert_db_state(
            test_db_session,
            {
                "users": 1,
                "daily_metrics": 30,
                "sleep_sessions": 30,
                "hrv_readings": 30,
            },
        )

    def test_populate_without_activities(self, test_db_session):
        """Test populating data without activities."""
        DatabaseTestUtils.populate_test_data(
            test_db_session, "test_user", days=7, include_activities=False
        )

        DatabaseTestUtils.assert_db_state(
            test_db_session,
            {
                "activities": 0,
            },
        )

    def test_clear_test_data(self, test_db_session):
        """Test clearing test data."""
        DatabaseTestUtils.populate_test_data(test_db_session, "user1", days=10)
        DatabaseTestUtils.populate_test_data(test_db_session, "user2", days=10)

        DatabaseTestUtils.clear_test_data(test_db_session, "user1")

        # User1 data should be gone
        DatabaseAssertions.assert_user_exists(test_db_session, "user2")
        with pytest.raises(AssertionError):
            DatabaseAssertions.assert_user_exists(test_db_session, "user1")
