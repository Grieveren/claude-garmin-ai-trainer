"""
Pytest configuration and fixtures for Phase 2 testing infrastructure.

Provides test database setup, sample data fixtures, and mock services for:
- Garmin integration testing
- Database access layer testing
- Data processing pipeline testing
- Daily readiness analysis testing
"""

import pytest
import os
from datetime import datetime, date, timedelta
from typing import Generator, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.database_models import (
    UserProfile,
    DailyMetrics,
    SleepSession,
    Activity,
    ActivityType,
    HRVReading,
    TrainingPlan,
    PlannedWorkout,
    WorkoutIntensity,
    DailyReadiness,
    ReadinessRecommendation,
    TrainingLoadTracking,
    SyncHistory,
    HeartRateSample,
)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db_session() -> Generator[Session, None, None]:
    """
    In-memory SQLite database session for testing.

    Creates a fresh database for each test and cleans up after.
    This ensures test isolation and fast execution (<5s per test).

    Yields:
        Session: SQLAlchemy session connected to in-memory test database
    """
    # Create in-memory SQLite engine for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ============================================================================
# USER AND PROFILE FIXTURES
# ============================================================================

@pytest.fixture
def sample_user(test_db_session: Session) -> UserProfile:
    """
    Create a test user profile with realistic athlete data.

    Returns:
        UserProfile: Test athlete with typical metrics
    """
    user = UserProfile(
        user_id="test_user_001",
        name="Test Athlete",
        email="athlete@test.com",
        date_of_birth=date(1990, 1, 15),
        gender="male",
        height_cm=180.0,
        weight_kg=75.0,
        resting_heart_rate=55,
        max_heart_rate=185,
        training_preferences={
            "preferred_activities": ["running", "cycling"],
            "training_days": 5,
            "preferred_intensity": "moderate",
        },
        garmin_user_id="garmin_123",
        timezone="Europe/Berlin",
        units_system="metric",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def sample_user_well_rested(test_db_session: Session) -> UserProfile:
    """
    Create test user scenario: well-rested athlete ready for hard training.

    Returns:
        UserProfile: Well-recovered athlete
    """
    user = UserProfile(
        user_id="test_user_well_rested",
        name="Well Rested Athlete",
        email="well-rested@test.com",
        date_of_birth=date(1988, 5, 20),
        gender="male",
        height_cm=182.0,
        weight_kg=76.0,
        resting_heart_rate=52,
        max_heart_rate=188,
        training_preferences={
            "preferred_activities": ["running", "cycling", "swimming"],
            "training_days": 6,
            "recovery_focus": "moderate",
        },
        timezone="Europe/Berlin",
        units_system="metric",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def sample_user_tired(test_db_session: Session) -> UserProfile:
    """
    Create test user scenario: fatigued athlete needing recovery.

    Returns:
        UserProfile: Fatigued athlete
    """
    user = UserProfile(
        user_id="test_user_tired",
        name="Tired Athlete",
        email="tired@test.com",
        date_of_birth=date(1992, 8, 10),
        gender="female",
        height_cm=170.0,
        weight_kg=62.0,
        resting_heart_rate=68,
        max_heart_rate=192,
        training_preferences={
            "preferred_activities": ["running", "yoga"],
            "training_days": 4,
            "recovery_focus": "high",
        },
        timezone="Europe/Berlin",
        units_system="metric",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


# ============================================================================
# DAILY METRICS FIXTURES
# ============================================================================

@pytest.fixture
def sample_daily_metrics(test_db_session: Session, sample_user: UserProfile) -> DailyMetrics:
    """
    Create a single day of realistic daily metrics.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        DailyMetrics: Sample metrics for one day
    """
    metrics = DailyMetrics(
        user_id=sample_user.user_id,
        date=date.today(),
        # Activity metrics
        steps=8500,
        distance_meters=6800,
        calories=2100,
        active_minutes=45,
        floors_climbed=5,
        # Heart rate metrics
        resting_heart_rate=56,
        max_heart_rate=168,
        avg_heart_rate=105,
        # HRV and stress
        hrv_sdnn=45.2,
        hrv_rmssd=32.5,
        stress_score=35,
        # Body battery
        body_battery_charged=35,
        body_battery_drained=42,
        body_battery_max=100,
        body_battery_min=18,
        # Sleep metrics
        sleep_score=78,
        total_sleep_minutes=420,
        deep_sleep_minutes=85,
        light_sleep_minutes=245,
        rem_sleep_minutes=70,
        awake_minutes=20,
        # Performance
        vo2_max=52.5,
        fitness_age=28,
        # Body composition
        weight_kg=75.2,
        body_fat_percent=15.2,
        bmi=23.2,
        # Hydration and respiration
        hydration_ml=2200,
        avg_respiration_rate=14.5,
    )
    test_db_session.add(metrics)
    test_db_session.commit()
    return metrics


@pytest.fixture
def daily_metrics_7_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[DailyMetrics]:
    """
    Create 7 days of realistic daily metrics for time-series analysis.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[DailyMetrics]: 7 days of daily metrics
    """
    metrics_list = []
    base_date = date.today() - timedelta(days=6)

    for day in range(7):
        current_date = base_date + timedelta(days=day)
        # Gradually improving metrics pattern
        improvement_factor = 1.0 + (day * 0.05)
        stress_factor = 100 - (day * 5)  # Decreasing stress

        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            steps=int(7500 * improvement_factor),
            distance_meters=int(6000 * improvement_factor),
            calories=int(2000 * improvement_factor),
            active_minutes=int(40 * improvement_factor),
            floors_climbed=4 + day,
            resting_heart_rate=max(54, 62 - day),
            max_heart_rate=165 + day,
            avg_heart_rate=int(100 * improvement_factor),
            hrv_sdnn=float(40 + (day * 1.5)),  # Improving HRV
            hrv_rmssd=float(30 + (day * 1.0)),
            stress_score=max(20, int(stress_factor)),
            body_battery_charged=30 + (day * 3),
            body_battery_drained=40 - (day * 2),
            body_battery_max=100,
            body_battery_min=15 + (day * 2),
            sleep_score=70 + (day * 1),
            total_sleep_minutes=int(400 + (day * 3)),
            deep_sleep_minutes=75 + (day * 2),
            light_sleep_minutes=235 + (day * 1),
            rem_sleep_minutes=65 + day,
            awake_minutes=max(15, 25 - day),
            vo2_max=51.0 + (day * 0.2),
            fitness_age=29 - day,
            weight_kg=75.0 - (day * 0.15),
            body_fat_percent=15.5 - (day * 0.1),
            bmi=23.3 - (day * 0.05),
            hydration_ml=int(2000 + (day * 50)),
            avg_respiration_rate=14.5 - (day * 0.1),
        )
        test_db_session.add(metrics)
        metrics_list.append(metrics)

    test_db_session.commit()
    return metrics_list


# ============================================================================
# ACTIVITY/WORKOUT FIXTURES
# ============================================================================

@pytest.fixture
def sample_activity(test_db_session: Session, sample_user: UserProfile) -> Activity:
    """
    Create a single realistic workout activity.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        Activity: Sample running workout
    """
    start_time = datetime.combine(date.today(), datetime.min.time()).replace(hour=6, minute=30)

    activity = Activity(
        user_id=sample_user.user_id,
        garmin_activity_id="garmin_activity_001",
        activity_date=date.today(),
        start_time=start_time,
        activity_type=ActivityType.RUNNING,
        activity_name="Morning Run",
        duration_seconds=2700,  # 45 minutes
        duration_minutes=45.0,
        distance_meters=7200,  # ~10km
        avg_heart_rate=155,
        max_heart_rate=172,
        avg_pace_per_km=6.25,  # 6:15 per km
        avg_speed_kmh=9.6,
        max_speed_kmh=12.5,
        calories=680,
        elevation_gain_meters=45,
        elevation_loss_meters=42,
        training_effect_aerobic=3.2,
        training_effect_anaerobic=0.8,
        training_load=180,
        recovery_time_hours=24,
        avg_cadence=168,
        max_cadence=182,
        avg_stride_length=1.18,
        avg_vertical_oscillation=8.2,
        avg_ground_contact_time=245,
        intensity_factor=0.85,
        hr_zones_data={
            "zone_1": {"seconds": 300, "label": "Zone 1 (50-60%)"},
            "zone_2": {"seconds": 900, "label": "Zone 2 (60-70%)"},
            "zone_3": {"seconds": 900, "label": "Zone 3 (70-80%)"},
            "zone_4": {"seconds": 600, "label": "Zone 4 (80-90%)"},
        },
        perceived_exertion=7,
        temperature_celsius=12.5,
        weather_condition="clear",
        notes="Great morning run, felt strong",
        raw_activity_data={"source": "garmin_connect"},
    )
    test_db_session.add(activity)
    test_db_session.commit()
    return activity


@pytest.fixture
def sample_activities(test_db_session: Session, sample_user: UserProfile) -> List[Activity]:
    """
    Create realistic variety of workout activities.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[Activity]: 5 different workout types
    """
    activities = []
    base_date = date.today() - timedelta(days=4)
    activity_types = [
        (ActivityType.RUNNING, "Morning Run", 2700, 7200, 155),
        (ActivityType.CYCLING, "Evening Ride", 3600, 18000, 140),
        (ActivityType.SWIMMING, "Pool Session", 2400, 2000, 130),
        (ActivityType.STRENGTH_TRAINING, "Weight Session", 3000, 500, 120),
        (ActivityType.YOGA, "Yoga Flow", 1800, 1200, 95),
    ]

    for i, (act_type, name, duration_sec, distance_m, avg_hr) in enumerate(activity_types):
        start_time = datetime.combine(base_date + timedelta(days=i), datetime.min.time())
        start_time = start_time.replace(hour=6, minute=30)

        activity = Activity(
            user_id=sample_user.user_id,
            garmin_activity_id=f"garmin_activity_{i:03d}",
            activity_date=base_date + timedelta(days=i),
            start_time=start_time,
            activity_type=act_type,
            activity_name=name,
            duration_seconds=duration_sec,
            duration_minutes=duration_sec / 60,
            distance_meters=distance_m,
            avg_heart_rate=avg_hr,
            max_heart_rate=avg_hr + 20,
            calories=int(duration_sec / 10),
            training_effect_aerobic=2.5 + (i * 0.1),
            training_effect_anaerobic=0.5 + (i * 0.05),
            training_load=100 + (i * 20),
            recovery_time_hours=18 + (i * 6),
            perceived_exertion=5 + i,
            temperature_celsius=10.0 + (i * 2),
            weather_condition="clear",
        )
        test_db_session.add(activity)
        activities.append(activity)

    test_db_session.commit()
    return activities


# ============================================================================
# SLEEP DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_sleep_data(test_db_session: Session, sample_user: UserProfile) -> SleepSession:
    """
    Create a realistic sleep session.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        SleepSession: Sample night of sleep
    """
    sleep_date = date.today()
    sleep_start = datetime.combine(
        sleep_date - timedelta(days=1),
        datetime.min.time()
    ).replace(hour=23, minute=15)
    sleep_end = datetime.combine(sleep_date, datetime.min.time()).replace(hour=7, minute=0)

    # Create corresponding daily metrics first
    metrics = DailyMetrics(
        user_id=sample_user.user_id,
        date=sleep_date,
        total_sleep_minutes=465,
    )
    test_db_session.add(metrics)
    test_db_session.flush()

    sleep = SleepSession(
        user_id=sample_user.user_id,
        daily_metric_id=metrics.id,
        sleep_date=sleep_date,
        sleep_start_time=sleep_start,
        sleep_end_time=sleep_end,
        total_sleep_minutes=465,  # 7h 45m
        deep_sleep_minutes=95,
        light_sleep_minutes=270,
        rem_sleep_minutes=85,
        awake_minutes=15,
        sleep_score=82,
        sleep_quality="good",
        restlessness=2.5,
        avg_heart_rate=52,
        min_heart_rate=48,
        max_heart_rate=65,
        avg_hrv=55.0,
        avg_respiration_rate=13.8,
        awakenings_count=2,
        sleep_stages_data={
            "transitions": [
                {"time": "23:15", "stage": "awake"},
                {"time": "23:35", "stage": "light"},
                {"time": "00:45", "stage": "deep"},
                {"time": "02:30", "stage": "light"},
                {"time": "03:15", "stage": "rem"},
                {"time": "04:30", "stage": "light"},
                {"time": "06:00", "stage": "rem"},
                {"time": "06:45", "stage": "light"},
                {"time": "07:00", "stage": "awake"},
            ]
        },
    )
    test_db_session.add(sleep)
    test_db_session.commit()
    return sleep


@pytest.fixture
def sleep_data_30_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[SleepSession]:
    """
    Create 30 days of realistic sleep data with variation.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[SleepSession]: 30 nights of sleep
    """
    sleep_sessions = []
    base_date = date.today() - timedelta(days=29)

    for day in range(30):
        current_date = base_date + timedelta(days=day)
        sleep_start = datetime.combine(
            current_date - timedelta(days=1),
            datetime.min.time()
        ).replace(hour=23, minute=15)

        # Realistic sleep variation (6-9 hours)
        sleep_duration = 450 + (day % 7) * 15 - (day // 7) * 10
        sleep_end = sleep_start + timedelta(minutes=sleep_duration)

        # Create metrics
        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            total_sleep_minutes=sleep_duration,
        )
        test_db_session.add(metrics)
        test_db_session.flush()

        # Create sleep session
        sleep = SleepSession(
            user_id=sample_user.user_id,
            daily_metric_id=metrics.id,
            sleep_date=current_date,
            sleep_start_time=sleep_start,
            sleep_end_time=sleep_end,
            total_sleep_minutes=sleep_duration,
            deep_sleep_minutes=int(sleep_duration * 0.20),
            light_sleep_minutes=int(sleep_duration * 0.58),
            rem_sleep_minutes=int(sleep_duration * 0.18),
            awake_minutes=int(sleep_duration * 0.04),
            sleep_score=70 + (day % 10),
            sleep_quality=["poor", "fair", "good", "excellent"][(day // 10) % 4],
            restlessness=float((day % 5) + 1),
            avg_heart_rate=50 + (day % 8),
            min_heart_rate=45 + (day % 8),
            max_heart_rate=70 + (day % 10),
            avg_hrv=float(50 + (day % 10)),
            avg_respiration_rate=13.5 + (day % 3) * 0.2,
            awakenings_count=(day % 4),
        )
        test_db_session.add(sleep)
        sleep_sessions.append(sleep)

    test_db_session.commit()
    return sleep_sessions


@pytest.fixture
def sleep_sessions_7_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[SleepSession]:
    """
    Create 7 days of sleep sessions for weekly analysis.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[SleepSession]: 7 nights of sleep
    """
    sleep_sessions = []
    base_date = date.today() - timedelta(days=6)

    for day in range(7):
        current_date = base_date + timedelta(days=day)
        sleep_start = datetime.combine(
            current_date - timedelta(days=1),
            datetime.min.time()
        ).replace(hour=23, minute=0)

        # Sleep duration 7-8 hours with variation
        sleep_duration = 420 + (day * 10)
        sleep_end = sleep_start + timedelta(minutes=sleep_duration)

        # Create metrics
        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            total_sleep_minutes=sleep_duration,
        )
        test_db_session.add(metrics)
        test_db_session.flush()

        # Create sleep session
        sleep = SleepSession(
            user_id=sample_user.user_id,
            daily_metric_id=metrics.id,
            sleep_date=current_date,
            sleep_start_time=sleep_start,
            sleep_end_time=sleep_end,
            total_sleep_minutes=sleep_duration,
            deep_sleep_minutes=int(sleep_duration * 0.22),
            light_sleep_minutes=int(sleep_duration * 0.56),
            rem_sleep_minutes=int(sleep_duration * 0.19),
            awake_minutes=int(sleep_duration * 0.03),
            sleep_score=75 + (day * 2),
            sleep_quality="good",
            restlessness=2.0 + (day * 0.3),
            avg_heart_rate=52 + day,
            min_heart_rate=47 + day,
            max_heart_rate=68 + day,
            avg_hrv=float(52 + day),
            avg_respiration_rate=13.5 + (day * 0.1),
            awakenings_count=2 if day < 4 else 3,
        )
        test_db_session.add(sleep)
        sleep_sessions.append(sleep)

    test_db_session.commit()
    return sleep_sessions


# ============================================================================
# HRV DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_hrv_reading(test_db_session: Session, sample_user: UserProfile) -> HRVReading:
    """
    Create a single HRV reading with realistic values.

    HRV ranges (SDNN in ms):
    - 30-40: Low (requires recovery)
    - 40-60: Normal (baseline)
    - 60-100: High (well-recovered)

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        HRVReading: Sample HRV measurement
    """
    current_date = date.today()
    reading_time = datetime.combine(current_date, datetime.min.time()).replace(hour=6, minute=0)

    # Create metrics first
    metrics = DailyMetrics(
        user_id=sample_user.user_id,
        date=current_date,
        hrv_sdnn=48.5,
    )
    test_db_session.add(metrics)
    test_db_session.flush()

    reading = HRVReading(
        user_id=sample_user.user_id,
        daily_metric_id=metrics.id,
        reading_date=current_date,
        reading_time=reading_time,
        reading_type="morning",
        hrv_sdnn=48.5,
        hrv_rmssd=35.2,
        hrv_pnn50=22.5,
        avg_heart_rate=54,
        status="balanced",
    )
    test_db_session.add(reading)
    test_db_session.commit()
    return reading


@pytest.fixture
def hrv_readings_30_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[HRVReading]:
    """
    Create 30 days of HRV readings with realistic variation.

    Simulates recovery pattern over month:
    - Days 1-7: Low HRV (overtraining, stress)
    - Days 8-14: Recovery beginning
    - Days 15-21: Normalized HRV
    - Days 22-30: High HRV (well-recovered)

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[HRVReading]: 30 days of HRV data
    """
    readings = []
    base_date = date.today() - timedelta(days=29)

    for day in range(30):
        current_date = base_date + timedelta(days=day)
        reading_time = datetime.combine(
            current_date, datetime.min.time()
        ).replace(hour=6, minute=0)

        # Recovery trajectory HRV values (SDNN in ms)
        if day < 7:
            hrv_sdnn = 35.0 + (day * 0.5)  # 35-38.5 (low, stressed)
        elif day < 14:
            hrv_sdnn = 38.5 + ((day - 7) * 1.5)  # 38.5-48.5 (recovering)
        elif day < 21:
            hrv_sdnn = 48.5 + ((day - 14) * 1.0)  # 48.5-55.5 (normalizing)
        else:
            hrv_sdnn = 55.5 + ((day - 21) * 0.8)  # 55.5-62 (well-recovered)

        # Create metrics
        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            hrv_sdnn=hrv_sdnn,
        )
        test_db_session.add(metrics)
        test_db_session.flush()

        # Create HRV reading
        reading = HRVReading(
            user_id=sample_user.user_id,
            daily_metric_id=metrics.id,
            reading_date=current_date,
            reading_time=reading_time,
            reading_type="morning",
            hrv_sdnn=hrv_sdnn,
            hrv_rmssd=hrv_sdnn * 0.72,
            hrv_pnn50=hrv_sdnn * 0.45,
            avg_heart_rate=int(62 - (day % 8)),
            status="low" if hrv_sdnn < 40 else "balanced" if hrv_sdnn < 55 else "high",
        )
        test_db_session.add(reading)
        readings.append(reading)

    test_db_session.commit()
    return readings


# ============================================================================
# ADDITIONAL FIXTURES FOR COMMON TEST SCENARIOS
# ============================================================================

@pytest.fixture
def sample_training_plan(
    test_db_session: Session, sample_user: UserProfile
) -> TrainingPlan:
    """
    Create a sample training plan.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        TrainingPlan: Sample 8-week training plan
    """
    start_date = date.today()
    target_date = start_date + timedelta(days=56)

    plan = TrainingPlan(
        user_id=sample_user.user_id,
        name="5K Speed Build",
        goal="Improve 5K pace to sub-20 minutes",
        description="8-week progressive training plan focusing on speed work and lactate threshold",
        start_date=start_date,
        target_date=target_date,
        is_active=True,
        completion_percent=0.0,
        created_by_ai=True,
        ai_model_version="claude-3-5-sonnet",
        ai_generation_prompt="Create 8-week 5K training plan for sub-20 minute goal",
        weekly_structure={
            "week_1": {
                "monday": "Easy 30min",
                "wednesday": "Threshold 5x2min at 5K pace",
                "friday": "Easy 25min",
                "sunday": "Long run 50min",
            }
        },
        notes="Customized for high mileage tolerance",
    )
    test_db_session.add(plan)
    test_db_session.commit()
    return plan


@pytest.fixture
def sample_daily_readiness(
    test_db_session: Session,
    sample_user: UserProfile,
    sample_daily_metrics: DailyMetrics,
) -> DailyReadiness:
    """
    Create a daily readiness assessment.

    Args:
        test_db_session: Database session
        sample_user: Test user
        sample_daily_metrics: Associated daily metrics

    Returns:
        DailyReadiness: AI-generated readiness score
    """
    readiness = DailyReadiness(
        user_id=sample_user.user_id,
        daily_metric_id=sample_daily_metrics.id,
        readiness_date=date.today(),
        readiness_score=78,
        recommendation=ReadinessRecommendation.MODERATE,
        recommended_intensity="moderate",
        key_factors={
            "hrv": "Good (45ms, +12% vs 7-day avg)",
            "sleep": "Good (420min, 78 score)",
            "recovery": "Adequate",
        },
        red_flags=None,
        recovery_tips={
            "hydration": "Maintain 2.5L+ daily",
            "sleep": "Aim for 8 hours tonight",
            "nutrition": "Focus on protein and carbs",
        },
        ai_analysis="Ready for moderate training. HRV shows good recovery. Sleep quality excellent.",
        ai_model_version="claude-3-5-sonnet",
        ai_confidence_score=0.85,
        training_load_7d=950,
        training_load_28d=3200,
        acwr=1.15,
    )
    test_db_session.add(readiness)
    test_db_session.commit()
    return readiness


# ============================================================================
# PYTEST HOOKS AND CONFIGURATION
# ============================================================================

@pytest.fixture
def cleanup_after_test():
    """Cleanup fixture for test teardown operations."""
    yield
    # Any cleanup code here


def pytest_configure(config):
    """Configure pytest and register custom markers."""
    # This is called before test collection
    pass


# ============================================================================
# DATA PROCESSOR FIXTURES
# ============================================================================

@pytest.fixture
def data_processor(test_db_session: Session):
    """
    Create DataProcessor instance for testing.

    Args:
        test_db_session: Database session

    Returns:
        DataProcessor: Data processing service
    """
    from app.services.data_processor import DataProcessor
    return DataProcessor(test_db_session)


@pytest.fixture
def sample_hrv_data_7_days():
    """Generate 7 days of HRV data for baseline testing."""
    return [65.0, 68.0, 67.0, 70.0, 69.0, 71.0, 68.0]


@pytest.fixture
def sample_hrv_data_30_days():
    """Generate 30 days of HRV data for baseline testing."""
    import numpy as np
    base_hrv = 65.0
    return [base_hrv + np.random.normal(0, 5) for _ in range(30)]


@pytest.fixture
def sample_hrv_timeseries():
    """Generate time series HRV data for trend analysis."""
    from datetime import date, timedelta
    base_date = date.today() - timedelta(days=29)
    base_hrv = 60.0
    # Increasing trend: +0.3 ms per day
    return [
        {"date": base_date + timedelta(days=i), "hrv": base_hrv + (i * 0.3)}
        for i in range(30)
    ]


@pytest.fixture
def sample_training_load_data():
    """Generate training load data for ACWR testing."""
    # Last 28 days of training loads
    return [100, 120, 80, 110, 90, 100, 95,  # Week 1
            105, 115, 85, 108, 92, 98, 100,   # Week 2
            110, 118, 88, 112, 95, 102, 105,  # Week 3
            115, 122, 90, 115, 98, 105, 110]  # Week 4


@pytest.fixture
def sample_training_history():
    """Generate training history for fitness-fatigue model."""
    from datetime import date, timedelta
    base_date = date.today() - timedelta(days=41)  # 6 weeks
    return [
        {"date": base_date + timedelta(days=i), "training_load": 100 + (i % 7) * 20}
        for i in range(42)
    ]


@pytest.fixture
def db_session(test_db_session):
    """Alias for test_db_session to match some test expectations."""
    return test_db_session


@pytest.fixture
def daily_metrics_30_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[DailyMetrics]:
    """
    Create 30 days of daily metrics for performance testing.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[DailyMetrics]: 30 days of metrics
    """
    metrics_list = []
    base_date = date.today() - timedelta(days=29)

    for day in range(30):
        current_date = base_date + timedelta(days=day)

        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            steps=int(8000 + (day * 100)),
            distance_meters=int(6500 + (day * 80)),
            calories=int(2100 + (day * 20)),
            active_minutes=int(45 + (day % 15)),
            floors_climbed=5 + (day % 8),
            resting_heart_rate=max(52, 60 - (day % 10)),
            max_heart_rate=165 + (day % 12),
            avg_heart_rate=int(105 + (day % 20)),
            hrv_sdnn=float(42 + (day % 18)),
            hrv_rmssd=float(32 + (day % 12)),
            stress_score=max(25, int(50 - (day % 25))),
            body_battery_charged=32 + (day % 15),
            body_battery_drained=38 - (day % 10),
            body_battery_max=100,
            body_battery_min=18 + (day % 12),
            sleep_score=72 + (day % 18),
            total_sleep_minutes=int(410 + (day % 70)),
            deep_sleep_minutes=78 + (day % 25),
            light_sleep_minutes=240 + (day % 40),
            rem_sleep_minutes=68 + (day % 20),
            awake_minutes=max(12, 24 - (day % 12)),
            vo2_max=51.5 + (day % 5) * 0.3,
            fitness_age=28 + (day % 4),
            weight_kg=75.0 + (day % 3) * 0.2,
            body_fat_percent=15.3 - (day % 3) * 0.1,
            bmi=23.2 + (day % 2) * 0.1,
            hydration_ml=int(2100 + (day % 10) * 50),
            avg_respiration_rate=14.3 + (day % 3) * 0.2,
        )
        test_db_session.add(metrics)
        metrics_list.append(metrics)

    test_db_session.commit()
    return metrics_list


@pytest.fixture
def training_load_14_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[TrainingLoadTracking]:
    """
    Create 14 days of training load data for acute load testing.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[TrainingLoadTracking]: 14 days of training load
    """
    training_loads = []
    base_date = date.today() - timedelta(days=13)

    for day in range(14):
        current_date = base_date + timedelta(days=day)

        # Create metrics first (required for foreign key)
        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            steps=8000,
        )
        test_db_session.add(metrics)
        test_db_session.flush()

        # Training load pattern: 80-120 range with weekly variation
        daily_load = 100 + ((day % 7) * 5) - ((day // 7) * 10)

        training_load = TrainingLoadTracking(
            user_id=sample_user.user_id,
            daily_metric_id=metrics.id,
            tracking_date=current_date,
            daily_training_load=daily_load,
            acute_training_load=100 if day < 7 else 95,
            chronic_training_load=100,
            acwr=1.0 if day < 7 else 0.95,
            acwr_status="optimal",
            fitness=100.0,
            fatigue=50.0,
            form=50.0,
        )
        test_db_session.add(training_load)
        training_loads.append(training_load)

    test_db_session.commit()
    return training_loads


@pytest.fixture
def training_load_30_days(
    test_db_session: Session, sample_user: UserProfile
) -> List[TrainingLoadTracking]:
    """
    Create 30 days of training load data for chronic load and ACWR testing.

    Args:
        test_db_session: Database session
        sample_user: Test user

    Returns:
        List[TrainingLoadTracking]: 30 days of training load
    """
    training_loads = []
    base_date = date.today() - timedelta(days=29)

    for day in range(30):
        current_date = base_date + timedelta(days=day)

        # Create metrics first (required for foreign key)
        metrics = DailyMetrics(
            user_id=sample_user.user_id,
            date=current_date,
            steps=8000 + (day * 50),
        )
        test_db_session.add(metrics)
        test_db_session.flush()

        # Training load pattern: gradual increase over 30 days
        # Week 1: 90-100, Week 2: 100-110, Week 3: 110-120, Week 4+: 115-125
        if day < 7:
            daily_load = 90 + (day % 7) * 2
        elif day < 14:
            daily_load = 100 + ((day - 7) % 7) * 2
        elif day < 21:
            daily_load = 110 + ((day - 14) % 7) * 2
        else:
            daily_load = 115 + ((day - 21) % 7) * 2

        # Calculate acute (last 7 days avg) and chronic (last 28 days avg)
        acute_load = 100 if day < 7 else 105 if day < 14 else 110 if day < 21 else 115
        chronic_load = 100
        acwr = acute_load / chronic_load if chronic_load > 0 else 1.0

        training_load = TrainingLoadTracking(
            user_id=sample_user.user_id,
            daily_metric_id=metrics.id,
            tracking_date=current_date,
            daily_training_load=daily_load,
            acute_training_load=acute_load,
            chronic_training_load=chronic_load,
            acwr=round(acwr, 2),
            acwr_status="optimal" if 0.8 <= acwr <= 1.3 else "moderate",
            fitness=float(90 + day),
            fatigue=float(40 + (day % 15)),
            form=float(50 + (day % 20)),
            recovery_score=max(60, 80 - (day % 25)),
        )
        test_db_session.add(training_load)
        training_loads.append(training_load)

    test_db_session.commit()
    return training_loads
