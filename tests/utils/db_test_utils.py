"""
Database utilities for testing.

Provides helper functions for:
- Database initialization and cleanup
- Test data population
- Database state assertions
- Transaction management
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.database_models import (
    UserProfile,
    DailyMetrics,
    SleepSession,
    Activity,
    ActivityType,
    HRVReading,
    TrainingLoadTracking,
    SyncHistory,
)


class DatabaseTestUtils:
    """Utilities for database testing operations."""

    @staticmethod
    def setup_test_database(session: Session) -> None:
        """
        Initialize test database with required schema.

        Args:
            session: SQLAlchemy session
        """
        # Tables are created via conftest fixtures
        pass

    @staticmethod
    def populate_test_data(
        session: Session,
        user_id: str,
        user_name: str = "Test User",
        days: int = 30,
        include_activities: bool = True,
        include_sleep: bool = True,
        include_hrv: bool = True,
    ) -> UserProfile:
        """
        Populate test database with realistic sample data.

        Args:
            session: SQLAlchemy session
            user_id: User identifier
            user_name: User display name
            days: Number of days of data to generate
            include_activities: Whether to generate activities
            include_sleep: Whether to generate sleep data
            include_hrv: Whether to generate HRV data

        Returns:
            UserProfile: Created user
        """
        # Create user
        user = UserProfile(
            user_id=user_id,
            name=user_name,
            email=f"{user_id}@test.com",
            date_of_birth=date(1990, 1, 15),
            gender="male",
            height_cm=180.0,
            weight_kg=75.0,
            resting_heart_rate=55,
            max_heart_rate=185,
            timezone="UTC",
            units_system="metric",
        )
        session.add(user)
        session.flush()

        # Generate metrics for each day
        base_date = date.today() - timedelta(days=days - 1)

        for day in range(days):
            current_date = base_date + timedelta(days=day)

            # Create daily metrics
            metrics = DailyMetrics(
                user_id=user_id,
                date=current_date,
                steps=7000 + (day % 3000),
                distance_meters=5000 + (day % 2000),
                calories=2000 + (day % 500),
                active_minutes=40 + (day % 20),
                floors_climbed=3 + (day % 8),
                resting_heart_rate=55,
                max_heart_rate=170 + (day % 20),
                avg_heart_rate=100 + (day % 40),
                hrv_sdnn=45.0 + ((day % 5) * 2),
                hrv_rmssd=32.0 + ((day % 5) * 1.5),
                stress_score=40 + (day % 30),
                body_battery_charged=30 + (day % 20),
                body_battery_drained=40 + (day % 20),
                body_battery_max=100,
                body_battery_min=15 + (day % 15),
                sleep_score=75 + (day % 15),
                total_sleep_minutes=420 + (day % 60),
                deep_sleep_minutes=80 + (day % 20),
                light_sleep_minutes=250 + (day % 40),
                rem_sleep_minutes=70 + (day % 20),
                awake_minutes=20 + (day % 10),
                vo2_max=52.0 + (day % 3),
                fitness_age=28 + (day % 5),
                weight_kg=75.0 - (day * 0.1),
                body_fat_percent=15.5 - (day * 0.05),
                bmi=23.3 - (day * 0.03),
                hydration_ml=2000 + (day % 500),
                avg_respiration_rate=14.5,
            )
            session.add(metrics)
            session.flush()

            # Create sleep data if requested
            if include_sleep:
                sleep_start = datetime.combine(
                    current_date - timedelta(days=1),
                    datetime.min.time()
                ).replace(hour=23, minute=0)
                sleep_end = datetime.combine(
                    current_date, datetime.min.time()
                ).replace(hour=7, minute=0)

                sleep = SleepSession(
                    user_id=user_id,
                    daily_metric_id=metrics.id,
                    sleep_date=current_date,
                    sleep_start_time=sleep_start,
                    sleep_end_time=sleep_end,
                    total_sleep_minutes=480,
                    deep_sleep_minutes=85,
                    light_sleep_minutes=280,
                    rem_sleep_minutes=85,
                    awake_minutes=50,
                    sleep_score=75,
                    avg_heart_rate=52,
                )
                session.add(sleep)

            # Create HRV data if requested
            if include_hrv:
                hrv = HRVReading(
                    user_id=user_id,
                    daily_metric_id=metrics.id,
                    reading_date=current_date,
                    reading_time=datetime.combine(
                        current_date, datetime.min.time()
                    ).replace(hour=6),
                    reading_type="morning",
                    hrv_sdnn=45.0 + ((day % 5) * 2),
                    hrv_rmssd=32.0 + ((day % 5) * 1.5),
                    avg_heart_rate=54,
                    status="balanced",
                )
                session.add(hrv)

            # Create activity if requested
            if include_activities and day % 2 == 0:
                activity_time = datetime.combine(
                    current_date, datetime.min.time()
                ).replace(hour=7, minute=0)

                activity = Activity(
                    user_id=user_id,
                    garmin_activity_id=f"{user_id}_activity_{day:03d}",
                    activity_date=current_date,
                    start_time=activity_time,
                    activity_type=ActivityType.RUNNING,
                    activity_name=f"Run {day}",
                    duration_seconds=2700 + (day % 900),
                    distance_meters=7000 + (day % 2000),
                    avg_heart_rate=150 + (day % 20),
                    max_heart_rate=170 + (day % 20),
                    calories=600 + (day % 200),
                    training_effect_aerobic=2.5 + (day % 2),
                    training_load=150 + (day % 100),
                )
                session.add(activity)

        session.commit()
        return user

    @staticmethod
    def clear_test_data(session: Session, user_id: Optional[str] = None) -> None:
        """
        Clean up test data.

        Args:
            session: SQLAlchemy session
            user_id: Specific user to clear (or None for all)
        """
        if user_id:
            # Clear specific user's data
            session.query(HRVReading).filter_by(user_id=user_id).delete()
            session.query(SleepSession).filter_by(user_id=user_id).delete()
            session.query(Activity).filter_by(user_id=user_id).delete()
            session.query(TrainingLoadTracking).filter_by(user_id=user_id).delete()
            session.query(DailyMetrics).filter_by(user_id=user_id).delete()
            session.query(UserProfile).filter_by(user_id=user_id).delete()
        else:
            # Clear all data
            session.query(HRVReading).delete()
            session.query(SleepSession).delete()
            session.query(Activity).delete()
            session.query(TrainingLoadTracking).delete()
            session.query(DailyMetrics).delete()
            session.query(UserProfile).delete()

        session.commit()

    @staticmethod
    def assert_db_state(
        session: Session,
        expected: Dict[str, Any],
    ) -> None:
        """
        Assert database state matches expectations.

        Args:
            session: SQLAlchemy session
            expected: Dict with expected counts, e.g.:
                {
                    "users": 1,
                    "daily_metrics": 30,
                    "activities": 15,
                    "sleep_sessions": 30,
                }

        Raises:
            AssertionError: If state doesn't match expectations
        """
        if "users" in expected:
            count = session.query(UserProfile).count()
            assert count == expected["users"], f"Expected {expected['users']} users, got {count}"

        if "daily_metrics" in expected:
            count = session.query(DailyMetrics).count()
            assert count == expected["daily_metrics"], \
                f"Expected {expected['daily_metrics']} metrics, got {count}"

        if "activities" in expected:
            count = session.query(Activity).count()
            assert count == expected["activities"], \
                f"Expected {expected['activities']} activities, got {count}"

        if "sleep_sessions" in expected:
            count = session.query(SleepSession).count()
            assert count == expected["sleep_sessions"], \
                f"Expected {expected['sleep_sessions']} sleep sessions, got {count}"

        if "hrv_readings" in expected:
            count = session.query(HRVReading).count()
            assert count == expected["hrv_readings"], \
                f"Expected {expected['hrv_readings']} HRV readings, got {count}"

    @staticmethod
    def get_user_metrics_range(
        session: Session,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyMetrics]:
        """
        Retrieve user metrics for a date range.

        Args:
            session: SQLAlchemy session
            user_id: User identifier
            start_date: Start date
            end_date: End date

        Returns:
            List of DailyMetrics
        """
        return session.query(DailyMetrics).filter(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date,
        ).order_by(DailyMetrics.date).all()

    @staticmethod
    def get_user_activities(
        session: Session,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Activity]:
        """
        Retrieve user activities.

        Args:
            session: SQLAlchemy session
            user_id: User identifier
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            List of Activities
        """
        query = session.query(Activity).filter_by(user_id=user_id)

        if start_date:
            query = query.filter(Activity.activity_date >= start_date)
        if end_date:
            query = query.filter(Activity.activity_date <= end_date)

        return query.order_by(Activity.activity_date).all()

    @staticmethod
    def assert_metric_values(
        metrics: DailyMetrics,
        expected: Dict[str, Any],
    ) -> None:
        """
        Assert specific metric values.

        Args:
            metrics: DailyMetrics instance
            expected: Dict of expected values

        Raises:
            AssertionError: If values don't match (with tolerance for floats)
        """
        tolerance = 0.01  # 1% tolerance for float comparisons

        for key, expected_value in expected.items():
            if not hasattr(metrics, key):
                raise AssertionError(f"Metrics object has no attribute '{key}'")

            actual_value = getattr(metrics, key)

            if isinstance(expected_value, float):
                # Float comparison with tolerance
                diff = abs(actual_value - expected_value)
                pct_diff = diff / expected_value if expected_value != 0 else diff
                assert pct_diff <= tolerance, \
                    f"{key}: expected {expected_value}, got {actual_value} " \
                    f"({pct_diff*100:.2f}% difference)"
            else:
                # Exact comparison
                assert actual_value == expected_value, \
                    f"{key}: expected {expected_value}, got {actual_value}"

    @staticmethod
    def reset_sequences(session: Session) -> None:
        """
        Reset database sequences for fresh ID generation.

        Useful for integration tests that check specific IDs.

        Args:
            session: SQLAlchemy session
        """
        # SQLite doesn't use sequences, this is a no-op
        # For PostgreSQL, this would reset sequences
        pass


class DatabaseAssertions:
    """Helper class for common database assertions."""

    @staticmethod
    def assert_user_exists(session: Session, user_id: str) -> UserProfile:
        """
        Assert user exists in database.

        Args:
            session: SQLAlchemy session
            user_id: User identifier

        Returns:
            UserProfile: The found user

        Raises:
            AssertionError: If user doesn't exist
        """
        user = session.query(UserProfile).filter_by(user_id=user_id).first()
        assert user is not None, f"User '{user_id}' not found in database"
        return user

    @staticmethod
    def assert_metrics_exist_for_date(
        session: Session,
        user_id: str,
        date_obj: date,
    ) -> DailyMetrics:
        """
        Assert daily metrics exist for date.

        Args:
            session: SQLAlchemy session
            user_id: User identifier
            date_obj: Date

        Returns:
            DailyMetrics: The found metrics

        Raises:
            AssertionError: If metrics don't exist
        """
        metrics = session.query(DailyMetrics).filter_by(
            user_id=user_id, date=date_obj
        ).first()
        assert metrics is not None, \
            f"Metrics not found for user '{user_id}' on {date_obj}"
        return metrics

    @staticmethod
    def assert_date_range_complete(
        session: Session,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """
        Assert metrics exist for entire date range (no gaps).

        Args:
            session: SQLAlchemy session
            user_id: User identifier
            start_date: Start date
            end_date: End date

        Raises:
            AssertionError: If any dates are missing
        """
        metrics = DatabaseTestUtils.get_user_metrics_range(
            session, user_id, start_date, end_date
        )

        expected_days = (end_date - start_date).days + 1
        actual_days = len(metrics)

        assert actual_days == expected_days, \
            f"Expected metrics for {expected_days} days, found {actual_days}"

        # Check for gaps
        current_date = start_date
        for metric in metrics:
            assert metric.date == current_date, \
                f"Gap in metrics: expected {current_date}, found {metric.date}"
            current_date += timedelta(days=1)
