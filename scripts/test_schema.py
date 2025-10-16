#!/usr/bin/env python3
"""
Quick test script to validate database schema.

This script:
1. Imports all models
2. Creates tables
3. Verifies table creation
4. Tests basic CRUD operations

Usage:
    python scripts/test_schema.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, datetime, timedelta
from app.database import Base, engine, get_db_context
from app.models import (
    UserProfile, DailyMetrics, SleepSession, Activity,
    HeartRateSample, HRVReading, TrainingPlan, PlannedWorkout,
    DailyReadiness, AIAnalysisCache, TrainingLoadTracking, SyncHistory,
    ActivityType, WorkoutIntensity, ReadinessRecommendation
)


def test_imports():
    """Test that all models can be imported."""
    print("✓ All models imported successfully")
    return True


def test_table_creation():
    """Test that all tables can be created."""
    try:
        # Drop all tables first
        Base.metadata.drop_all(bind=engine)
        print("✓ Dropped existing tables")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ Created all tables")

        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            'user_profile', 'daily_metrics', 'sleep_sessions', 'activities',
            'heart_rate_samples', 'hrv_readings', 'training_plans',
            'planned_workouts', 'daily_readiness', 'ai_analysis_cache',
            'training_load_tracking', 'sync_history'
        ]

        for table in expected_tables:
            if table in tables:
                print(f"  ✓ Table '{table}' exists")
            else:
                print(f"  ✗ Table '{table}' MISSING")
                return False

        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False


def test_basic_crud():
    """Test basic CRUD operations."""
    try:
        with get_db_context() as db:
            # CREATE - User
            user = UserProfile(
                user_id="test_user_001",
                name="Test User",
                email="test@example.com",
                height_cm=175.0,
                weight_kg=70.0,
            )
            db.add(user)
            db.flush()
            print("✓ Created user")

            # CREATE - Daily Metrics
            metrics = DailyMetrics(
                user_id=user.user_id,
                date=date.today(),
                steps=10000,
                distance_meters=7500.0,
                resting_heart_rate=60,
                hrv_sdnn=65.0,
                sleep_score=85,
            )
            db.add(metrics)
            db.flush()
            print("✓ Created daily metrics")

            # CREATE - Activity
            activity = Activity(
                user_id=user.user_id,
                garmin_activity_id="test_activity_001",
                activity_date=date.today(),
                start_time=datetime.now(),
                activity_type=ActivityType.RUNNING,
                activity_name="Morning Run",
                duration_seconds=1800,
                duration_minutes=30.0,
                distance_meters=5000.0,
                avg_heart_rate=150,
            )
            db.add(activity)
            db.flush()
            print("✓ Created activity")

            # CREATE - Training Plan
            plan = TrainingPlan(
                user_id=user.user_id,
                name="Test Plan",
                goal="Test goal",
                start_date=date.today(),
                target_date=date.today() + timedelta(days=30),
                is_active=True,
            )
            db.add(plan)
            db.flush()
            print("✓ Created training plan")

            # CREATE - Planned Workout
            workout = PlannedWorkout(
                user_id=user.user_id,
                training_plan_id=plan.id,
                workout_date=date.today() + timedelta(days=1),
                workout_type=ActivityType.RUNNING,
                workout_name="Easy Run",
                description="Recovery run",
                intensity_level=3,
                intensity_category=WorkoutIntensity.EASY,
            )
            db.add(workout)
            db.flush()
            print("✓ Created planned workout")

            # CREATE - Daily Readiness
            readiness = DailyReadiness(
                user_id=user.user_id,
                daily_metric_id=metrics.id,
                readiness_date=date.today(),
                readiness_score=80,
                recommendation=ReadinessRecommendation.MODERATE,
                key_factors={"good_hrv": True, "good_sleep": True},
                ai_analysis="Test analysis",
            )
            db.add(readiness)
            db.flush()
            print("✓ Created daily readiness")

            # CREATE - Training Load
            load = TrainingLoadTracking(
                user_id=user.user_id,
                daily_metric_id=metrics.id,
                tracking_date=date.today(),
                daily_training_load=100,
                acute_training_load=100,
                chronic_training_load=85,
                acwr=1.18,
                acwr_status="optimal",
            )
            db.add(load)
            db.flush()
            print("✓ Created training load tracking")

            # CREATE - HRV Reading
            hrv = HRVReading(
                user_id=user.user_id,
                daily_metric_id=metrics.id,
                reading_date=date.today(),
                reading_time=datetime.now(),
                reading_type="morning",
                hrv_sdnn=65.0,
            )
            db.add(hrv)
            db.flush()
            print("✓ Created HRV reading")

            # CREATE - Sleep Session
            sleep = SleepSession(
                user_id=user.user_id,
                daily_metric_id=metrics.id,
                sleep_date=date.today(),
                sleep_start_time=datetime.now() - timedelta(hours=8),
                sleep_end_time=datetime.now(),
                total_sleep_minutes=480,
                deep_sleep_minutes=120,
                light_sleep_minutes=240,
                rem_sleep_minutes=90,
                sleep_score=85,
            )
            db.add(sleep)
            db.flush()
            print("✓ Created sleep session")

            # CREATE - Heart Rate Sample
            hr_sample = HeartRateSample(
                activity_id=activity.id,
                timestamp=datetime.now(),
                heart_rate=150,
                elapsed_seconds=60,
            )
            db.add(hr_sample)
            db.flush()
            print("✓ Created heart rate sample")

            # CREATE - AI Analysis Cache
            cache = AIAnalysisCache(
                content_hash="test_hash_123",
                analysis_type="readiness",
                input_context={"test": "data"},
                ai_response="Test AI response",
                ai_model_version="claude-3-5-sonnet-20241022",
            )
            db.add(cache)
            db.flush()
            print("✓ Created AI analysis cache")

            # CREATE - Sync History
            sync = SyncHistory(
                user_id=user.user_id,
                sync_type="full",
                sync_status="completed",
                sync_started_at=datetime.now(),
                records_synced=10,
            )
            db.add(sync)
            db.flush()
            print("✓ Created sync history")

            # Commit all changes
            db.commit()
            print("\n✓ All records committed successfully")

            # READ - Verify data with relationships
            user_check = db.query(UserProfile).filter_by(user_id="test_user_001").first()
            assert user_check is not None, "User not found"
            assert len(user_check.daily_metrics) == 1, "Metrics not linked"
            assert len(user_check.activities) == 1, "Activities not linked"
            print("✓ Relationships working correctly")

            return True

    except Exception as e:
        print(f"✗ Error in CRUD operations: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_queries():
    """Test common query patterns."""
    try:
        with get_db_context() as db:
            # Test user query
            user = db.query(UserProfile).filter_by(user_id="test_user_001").first()
            assert user is not None
            print("✓ User query successful")

            # Test metrics with joins
            from sqlalchemy.orm import joinedload
            metrics = db.query(DailyMetrics).options(
                joinedload(DailyMetrics.sleep_session),
                joinedload(DailyMetrics.daily_readiness),
                joinedload(DailyMetrics.training_load)
            ).filter_by(user_id="test_user_001", date=date.today()).first()

            assert metrics is not None
            assert metrics.sleep_session is not None
            assert metrics.daily_readiness is not None
            assert metrics.training_load is not None
            print("✓ Joined query successful")

            # Test activity query
            activities = db.query(Activity).filter(
                Activity.user_id == "test_user_001",
                Activity.activity_type == ActivityType.RUNNING
            ).all()
            assert len(activities) == 1
            print("✓ Activity filter query successful")

            return True

    except Exception as e:
        print(f"✗ Error in queries: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING DATABASE SCHEMA")
    print("=" * 60)
    print()

    tests = [
        ("Imports", test_imports),
        ("Table Creation", test_table_creation),
        ("CRUD Operations", test_basic_crud),
        ("Query Patterns", test_queries),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"TEST: {name}")
        print('=' * 60)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
