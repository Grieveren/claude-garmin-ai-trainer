#!/usr/bin/env python3
"""
Database initialization script for Garmin AI Training System.

This script:
1. Creates all database tables
2. Sets up proper indexes and constraints
3. Optionally creates sample data for testing

Usage:
    python scripts/init_database.py              # Create empty database
    python scripts/init_database.py --sample     # Create database with sample data
    python scripts/init_database.py --reset      # Reset database (WARNING: deletes all data)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import init_db, reset_db, get_db_context, engine
from app.models.database_models import (
    UserProfile, DailyMetrics, SleepSession, Activity,
    HeartRateSample, HRVReading, TrainingPlan, PlannedWorkout,
    DailyReadiness, TrainingLoadTracking, SyncHistory,
    ActivityType, WorkoutIntensity, ReadinessRecommendation
)
from app.services.data_access import (
    bulk_insert_daily_metrics, bulk_insert_activities,
    get_dashboard_summary
)
from app.utils.database_utils import (
    ensure_user_exists, get_or_create
)
from sqlalchemy import inspect


def create_sample_user(db):
    """Create a sample user profile."""
    user = UserProfile(
        user_id="test_user_001",
        name="John Doe",
        email="john.doe@example.com",
        date_of_birth=date(1990, 5, 15),
        gender="male",
        height_cm=180.0,
        weight_kg=75.0,
        resting_heart_rate=55,
        max_heart_rate=185,
        training_preferences={
            "preferred_activities": ["running", "cycling"],
            "available_days": ["monday", "tuesday", "thursday", "saturday", "sunday"],
            "goals": ["Improve 5K time", "Build endurance"],
            "experience_level": "intermediate"
        },
        timezone="America/New_York",
        units_system="metric"
    )
    db.add(user)
    db.flush()
    return user


def create_sample_daily_metrics(db, user_id: str, days_back: int = 30):
    """Create sample daily metrics for the past N days."""
    metrics_list = []

    for i in range(days_back):
        metric_date = date.today() - timedelta(days=i)

        # Create realistic varying metrics
        base_hrv = 65 + random.randint(-15, 15)
        base_rhr = 55 + random.randint(-5, 5)
        sleep_quality = random.randint(70, 95)

        metrics = DailyMetrics(
            user_id=user_id,
            date=metric_date,
            steps=8000 + random.randint(-2000, 4000),
            distance_meters=6000 + random.randint(-1000, 3000),
            calories=2200 + random.randint(-300, 500),
            active_minutes=45 + random.randint(-15, 30),
            floors_climbed=10 + random.randint(0, 10),
            resting_heart_rate=base_rhr,
            max_heart_rate=165 + random.randint(-10, 20),
            avg_heart_rate=85 + random.randint(-10, 10),
            hrv_sdnn=base_hrv,
            hrv_rmssd=base_hrv * 1.2,
            stress_score=30 + random.randint(-15, 25),
            body_battery_charged=85 + random.randint(-10, 15),
            body_battery_drained=75 + random.randint(-10, 10),
            body_battery_max=95 + random.randint(-5, 5),
            body_battery_min=20 + random.randint(-10, 15),
            sleep_score=sleep_quality,
            total_sleep_minutes=420 + random.randint(-60, 60),
            deep_sleep_minutes=90 + random.randint(-20, 20),
            light_sleep_minutes=240 + random.randint(-40, 40),
            rem_sleep_minutes=90 + random.randint(-20, 20),
            awake_minutes=15 + random.randint(0, 15),
            vo2_max=52.0 + random.uniform(-2, 2),
            weight_kg=75.0 + random.uniform(-0.5, 0.5),
            body_fat_percent=15.0 + random.uniform(-0.3, 0.3),
            hydration_ml=2000 + random.randint(-500, 500),
        )
        db.add(metrics)
        metrics_list.append(metrics)

    db.flush()
    return metrics_list


def create_sample_activities(db, user_id: str, days_back: int = 14):
    """Create sample workout activities."""
    activities = []
    activity_types = [ActivityType.RUNNING, ActivityType.CYCLING, ActivityType.STRENGTH_TRAINING]

    # Create 3-4 workouts per week
    for i in range(days_back):
        metric_date = date.today() - timedelta(days=i)

        # Skip some days to simulate rest days
        if random.random() < 0.4:  # 40% chance of rest day
            continue

        activity_type = random.choice(activity_types)

        if activity_type == ActivityType.RUNNING:
            distance = 5000 + random.randint(-1000, 5000)
            duration = int(distance / 3.33)  # ~5:00 min/km pace
            activity = Activity(
                user_id=user_id,
                garmin_activity_id=f"activity_{metric_date}_{random.randint(1000, 9999)}",
                activity_date=metric_date,
                start_time=datetime.combine(metric_date, datetime.min.time().replace(hour=7)),
                activity_type=activity_type,
                activity_name="Morning Run",
                duration_seconds=duration,
                duration_minutes=duration / 60,
                distance_meters=distance,
                avg_heart_rate=150 + random.randint(-10, 15),
                max_heart_rate=175 + random.randint(-5, 10),
                avg_pace_per_km=5.0 + random.uniform(-0.5, 0.5),
                calories=int(distance / 10),
                elevation_gain_meters=50 + random.randint(0, 150),
                training_effect_aerobic=2.5 + random.uniform(-0.5, 1.5),
                training_effect_anaerobic=1.0 + random.uniform(0, 1.0),
                training_load=120 + random.randint(-30, 50),
                recovery_time_hours=24 + random.randint(0, 24),
                avg_cadence=170 + random.randint(-10, 10),
            )
        elif activity_type == ActivityType.CYCLING:
            distance = 20000 + random.randint(-5000, 15000)
            duration = int(distance / 8.33)  # ~30 km/h
            activity = Activity(
                user_id=user_id,
                garmin_activity_id=f"activity_{metric_date}_{random.randint(1000, 9999)}",
                activity_date=metric_date,
                start_time=datetime.combine(metric_date, datetime.min.time().replace(hour=8)),
                activity_type=activity_type,
                activity_name="Cycling Workout",
                duration_seconds=duration,
                duration_minutes=duration / 60,
                distance_meters=distance,
                avg_heart_rate=140 + random.randint(-10, 15),
                max_heart_rate=165 + random.randint(-5, 10),
                calories=int(distance / 20),
                elevation_gain_meters=200 + random.randint(0, 300),
                training_effect_aerobic=3.0 + random.uniform(-0.5, 1.0),
                training_effect_anaerobic=1.5 + random.uniform(0, 1.0),
                training_load=150 + random.randint(-30, 50),
                recovery_time_hours=36 + random.randint(0, 12),
                avg_power=200 + random.randint(-30, 50),
                avg_cadence=85 + random.randint(-10, 10),
            )
        else:  # STRENGTH_TRAINING
            duration = 45 * 60 + random.randint(-600, 600)
            activity = Activity(
                user_id=user_id,
                garmin_activity_id=f"activity_{metric_date}_{random.randint(1000, 9999)}",
                activity_date=metric_date,
                start_time=datetime.combine(metric_date, datetime.min.time().replace(hour=18)),
                activity_type=activity_type,
                activity_name="Strength Training",
                duration_seconds=duration,
                duration_minutes=duration / 60,
                avg_heart_rate=110 + random.randint(-10, 20),
                max_heart_rate=145 + random.randint(-5, 15),
                calories=300 + random.randint(-50, 100),
                training_effect_aerobic=1.0 + random.uniform(0, 0.5),
                training_effect_anaerobic=2.0 + random.uniform(-0.5, 1.0),
                training_load=80 + random.randint(-20, 40),
                recovery_time_hours=48 + random.randint(0, 24),
            )

        db.add(activity)
        activities.append(activity)

    db.flush()
    return activities


def create_sample_training_plan(db, user_id: str):
    """Create a sample training plan with planned workouts."""
    plan = TrainingPlan(
        user_id=user_id,
        name="5K Training Plan",
        goal="Run 5K in under 25 minutes",
        description="8-week progressive training plan to improve 5K performance",
        start_date=date.today(),
        target_date=date.today() + timedelta(days=56),
        is_active=True,
        created_by_ai=True,
        ai_model_version="claude-3-5-sonnet-20241022",
        weekly_structure={
            "week_1": {"easy_runs": 2, "tempo_run": 1, "long_run": 1, "rest_days": 3},
            "week_2": {"easy_runs": 2, "intervals": 1, "long_run": 1, "rest_days": 3},
        },
    )
    db.add(plan)
    db.flush()

    # Create planned workouts for the next 2 weeks
    workouts = []
    workout_schedule = [
        (0, "Easy Run", ActivityType.RUNNING, WorkoutIntensity.EASY, 3, 4000),
        (2, "Tempo Run", ActivityType.RUNNING, WorkoutIntensity.MODERATE, 6, 5000),
        (4, "Easy Run", ActivityType.RUNNING, WorkoutIntensity.EASY, 3, 4000),
        (6, "Long Run", ActivityType.RUNNING, WorkoutIntensity.MODERATE, 5, 8000),
        (7, "Rest Day", ActivityType.RUNNING, WorkoutIntensity.REST, 1, 0),
        (9, "Interval Training", ActivityType.RUNNING, WorkoutIntensity.HIGH_INTENSITY, 8, 6000),
        (11, "Easy Run", ActivityType.RUNNING, WorkoutIntensity.EASY, 3, 4000),
        (13, "Long Run", ActivityType.RUNNING, WorkoutIntensity.MODERATE, 5, 10000),
    ]

    for days_ahead, name, w_type, intensity, level, distance in workout_schedule:
        workout = PlannedWorkout(
            user_id=user_id,
            training_plan_id=plan.id,
            workout_date=date.today() + timedelta(days=days_ahead),
            workout_type=w_type,
            workout_name=name,
            description=f"{name} - Part of 5K training progression",
            target_duration_minutes=30 if distance < 5000 else 45 if distance < 8000 else 60,
            target_distance_meters=distance if distance > 0 else None,
            target_heart_rate_zone="Z2" if intensity == WorkoutIntensity.EASY else "Z3-Z4",
            intensity_level=level,
            intensity_category=intensity,
            was_completed=False,
            ai_reasoning=f"This {name} helps build {'endurance' if intensity == WorkoutIntensity.EASY else 'speed and lactate threshold'}",
        )
        db.add(workout)
        workouts.append(workout)

    db.flush()
    return plan, workouts


def create_sample_readiness(db, user_id: str, metrics_list):
    """Create sample daily readiness assessments."""
    for metrics in metrics_list[:7]:  # Only for the last week
        # Calculate readiness score based on metrics
        readiness_score = min(100, int(
            (metrics.hrv_sdnn / 80 * 30) +
            (metrics.sleep_score / 100 * 40) +
            ((100 - metrics.stress_score) / 100 * 30)
        ))

        if readiness_score >= 80:
            recommendation = ReadinessRecommendation.HIGH_INTENSITY
        elif readiness_score >= 60:
            recommendation = ReadinessRecommendation.MODERATE
        elif readiness_score >= 40:
            recommendation = ReadinessRecommendation.EASY
        else:
            recommendation = ReadinessRecommendation.REST

        readiness = DailyReadiness(
            user_id=user_id,
            daily_metric_id=metrics.id,
            readiness_date=metrics.date,
            readiness_score=readiness_score,
            recommendation=recommendation,
            key_factors={
                "good_hrv": metrics.hrv_sdnn > 60,
                "good_sleep": metrics.sleep_score > 75,
                "low_stress": metrics.stress_score < 40,
            },
            red_flags={
                "low_hrv": metrics.hrv_sdnn < 50,
                "poor_sleep": metrics.sleep_score < 70,
            } if readiness_score < 60 else {},
            recovery_tips={
                "sleep": "Aim for 8 hours of quality sleep",
                "hydration": "Drink 2-3 liters of water today",
                "nutrition": "Focus on whole foods and protein",
            },
            ai_analysis=f"Your readiness score is {readiness_score}. " +
                       f"Your HRV is {metrics.hrv_sdnn:.1f} and sleep score is {metrics.sleep_score}. " +
                       f"Recommendation: {recommendation.value}",
            ai_model_version="claude-3-5-sonnet-20241022",
            ai_confidence_score=0.85,
        )
        db.add(readiness)

    db.flush()


def create_sample_training_load(db, user_id: str, metrics_list):
    """Create sample training load tracking data."""
    for i, metrics in enumerate(metrics_list):
        # Simulate progressive training load
        daily_load = random.randint(80, 150) if i % 4 != 0 else 0  # Rest day every 4 days

        # Calculate rolling averages (simplified)
        acute_load = daily_load  # In reality, this would be 7-day average
        chronic_load = daily_load * 0.85  # In reality, this would be 28-day average
        acwr = acute_load / chronic_load if chronic_load > 0 else 1.0

        if acwr < 0.8:
            acwr_status = "low"
            injury_risk = "low"
        elif acwr <= 1.3:
            acwr_status = "optimal"
            injury_risk = "low"
        elif acwr <= 1.5:
            acwr_status = "moderate"
            injury_risk = "moderate"
        else:
            acwr_status = "high_risk"
            injury_risk = "high"

        tracking = TrainingLoadTracking(
            user_id=user_id,
            daily_metric_id=metrics.id,
            tracking_date=metrics.date,
            daily_training_load=daily_load,
            acute_training_load=acute_load,
            chronic_training_load=chronic_load,
            acwr=acwr,
            acwr_status=acwr_status,
            fitness=chronic_load,
            fatigue=acute_load,
            form=chronic_load - acute_load,
            recovery_score=metrics.sleep_score,
            injury_risk=injury_risk,
        )
        db.add(tracking)

    db.flush()


def create_sample_data(db):
    """Create a complete set of sample data."""
    print("Creating sample user...")
    user = create_sample_user(db)

    print("Creating 30 days of daily metrics...")
    metrics_list = create_sample_daily_metrics(db, user.user_id, days_back=30)

    print("Creating workout activities...")
    activities = create_sample_activities(db, user.user_id, days_back=14)

    print("Creating training plan with workouts...")
    plan, workouts = create_sample_training_plan(db, user.user_id)

    print("Creating daily readiness assessments...")
    create_sample_readiness(db, user.user_id, metrics_list)

    print("Creating training load tracking...")
    create_sample_training_load(db, user.user_id, metrics_list)

    print("\nSample data created successfully!")
    print(f"  User: {user.name} ({user.email})")
    print(f"  Daily metrics: {len(metrics_list)} days")
    print(f"  Activities: {len(activities)} workouts")
    print(f"  Training plan: {plan.name}")
    print(f"  Planned workouts: {len(workouts)}")


def verify_database_schema(db):
    """Verify database schema and indexes."""
    print("\nVerifying database schema...")

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = [
        'user_profile', 'daily_metrics', 'sleep_sessions', 'activities',
        'heart_rate_samples', 'hrv_readings', 'training_plans',
        'planned_workouts', 'daily_readiness', 'ai_analysis_cache',
        'training_load_tracking', 'sync_history'
    ]

    print(f"\n📊 Database Schema Verification:")
    print(f"  Expected tables: {len(expected_tables)}")
    print(f"  Found tables: {len(tables)}")

    missing_tables = set(expected_tables) - set(tables)
    if missing_tables:
        print(f"  ⚠️  Missing tables: {missing_tables}")
    else:
        print(f"  ✅ All tables present")

    # Verify indexes for performance
    print(f"\n📈 Index Verification:")
    total_indexes = 0
    for table in expected_tables:
        if table in tables:
            indexes = inspector.get_indexes(table)
            total_indexes += len(indexes)
            print(f"  {table}: {len(indexes)} indexes")

    print(f"\n  Total indexes: {total_indexes}")

    return len(missing_tables) == 0


def test_data_access_queries(db, user_id: str):
    """Test data access layer with sample queries."""
    print("\n🧪 Testing Data Access Layer...")

    # Test daily metrics query
    today = date.today()
    metrics = db.query(DailyMetrics).filter(
        DailyMetrics.user_id == user_id,
        DailyMetrics.date == today
    ).first()

    if metrics:
        print(f"  ✅ Daily metrics query: Found metrics for {today}")
    else:
        print(f"  ⚠️  Daily metrics query: No metrics for {today}")

    # Test activity query
    activities = db.query(Activity).filter(
        Activity.user_id == user_id
    ).order_by(Activity.activity_date.desc()).limit(5).all()

    print(f"  ✅ Activity query: Found {len(activities)} activities")

    # Test dashboard summary (comprehensive query)
    try:
        import time
        start_time = time.time()
        summary = get_dashboard_summary(db, user_id)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        print(f"  ✅ Dashboard summary: Retrieved in {elapsed:.1f}ms")

        if summary.get('latest_metrics'):
            print(f"     - Latest metrics: {summary['latest_metrics'].date}")
        if summary.get('training_load'):
            print(f"     - ACWR: {summary['training_load'].get('acwr')}")
        if summary.get('upcoming_workouts'):
            print(f"     - Upcoming workouts: {len(summary['upcoming_workouts'])}")

    except Exception as e:
        print(f"  ⚠️  Dashboard summary failed: {e}")


def show_database_stats(db):
    """Show database statistics."""
    print("\n📊 Database Statistics:")

    stats = {}
    tables = [
        ('Users', UserProfile),
        ('Daily Metrics', DailyMetrics),
        ('Sleep Sessions', SleepSession),
        ('Activities', Activity),
        ('HRV Readings', HRVReading),
        ('Training Plans', TrainingPlan),
        ('Planned Workouts', PlannedWorkout),
        ('Daily Readiness', DailyReadiness),
        ('Training Load', TrainingLoadTracking),
        ('Sync History', SyncHistory),
    ]

    for name, model in tables:
        count = db.query(model).count()
        stats[name] = count
        print(f"  {name}: {count:,} records")

    return stats


def main():
    """Main function to initialize database."""
    parser = argparse.ArgumentParser(description="Initialize Garmin AI Training System database")
    parser.add_argument("--sample", action="store_true", help="Create sample data for testing")
    parser.add_argument("--reset", action="store_true", help="Reset database (WARNING: deletes all data)")
    parser.add_argument("--verify", action="store_true", help="Verify database schema and indexes")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--test", action="store_true", help="Test data access layer queries")
    args = parser.parse_args()

    if args.reset:
        confirm = input("⚠️  WARNING: This will DELETE ALL DATA. Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        print("Resetting database...")
        reset_db()
        print("✅ Database reset complete.")
    else:
        print("Initializing database...")
        init_db()
        print("✅ Database tables created successfully.")

    # Verify schema if requested
    with get_db_context() as db:
        if args.verify or args.sample:
            verify_database_schema(db)

    if args.sample:
        print("\nCreating sample data...")
        with get_db_context() as db:
            create_sample_data(db)
        print("✅ Sample data created successfully.")

    # Show stats if requested
    if args.stats or args.sample:
        with get_db_context() as db:
            show_database_stats(db)

    # Test queries if requested
    if args.test and args.sample:
        with get_db_context() as db:
            test_data_access_queries(db, "test_user_001")

    print("\n🎉 Database initialization complete!")
    print("\nYou can now:")
    print("  - Start the API server")
    print("  - Run sync operations to fetch Garmin data")
    print("  - Generate AI training recommendations")
    print("\nUseful commands:")
    print("  python scripts/init_database.py --verify     # Verify schema")
    print("  python scripts/init_database.py --stats      # Show statistics")
    print("  python scripts/init_database.py --test       # Test queries")


if __name__ == "__main__":
    main()
