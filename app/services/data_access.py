"""
Comprehensive Data Access Layer for Garmin AI Training Optimizer.

This module provides high-performance CRUD operations, query builders,
bulk operations, and common query functions for all database models.

Performance targets:
- Single record queries: <10ms
- Range queries (30 days): <100ms
- Bulk inserts (100 records): <500ms
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from contextlib import contextmanager

from app.models.database_models import (
    UserProfile, DailyMetrics, SleepSession, Activity,
    HeartRateSample, HRVReading, TrainingPlan, PlannedWorkout,
    DailyReadiness, AIAnalysisCache, TrainingLoadTracking, SyncHistory,
    ActivityType, WorkoutIntensity, ReadinessRecommendation
)


# ============================================================================
# USER PROFILE OPERATIONS
# ============================================================================

def get_user_by_id(db: Session, user_id: str) -> Optional[UserProfile]:
    """Get user profile by user_id."""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[UserProfile]:
    """Get user profile by email."""
    return db.query(UserProfile).filter(UserProfile.email == email).first()


def create_user(db: Session, user_data: Dict[str, Any]) -> UserProfile:
    """Create a new user profile."""
    user = UserProfile(**user_data)
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, user_id: str, user_data: Dict[str, Any]) -> Optional[UserProfile]:
    """Update user profile."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.flush()
    return user


def update_garmin_tokens(
    db: Session,
    user_id: str,
    access_token: str,
    refresh_token: str
) -> Optional[UserProfile]:
    """Update Garmin OAuth tokens."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.garmin_access_token = access_token
    user.garmin_refresh_token = refresh_token
    user.last_sync_at = datetime.utcnow()
    db.flush()
    return user


# ============================================================================
# DAILY METRICS OPERATIONS
# ============================================================================

def get_daily_metrics(db: Session, user_id: str, metric_date: date) -> Optional[DailyMetrics]:
    """
    Get daily metrics for a specific date.

    Performance: <5ms (uses composite index on user_id + date)
    """
    return db.query(DailyMetrics).filter(
        DailyMetrics.user_id == user_id,
        DailyMetrics.date == metric_date
    ).first()


def get_metrics_range(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date
) -> List[DailyMetrics]:
    """
    Get daily metrics for a date range.

    Performance: <50ms for 30 days (uses composite index)
    """
    return db.query(DailyMetrics).filter(
        DailyMetrics.user_id == user_id,
        DailyMetrics.date >= start_date,
        DailyMetrics.date <= end_date
    ).order_by(DailyMetrics.date.desc()).all()


def get_latest_metrics(db: Session, user_id: str, limit: int = 30) -> List[DailyMetrics]:
    """Get the most recent N days of metrics."""
    return db.query(DailyMetrics).filter(
        DailyMetrics.user_id == user_id
    ).order_by(DailyMetrics.date.desc()).limit(limit).all()


def create_daily_metrics(db: Session, metrics_data: Dict[str, Any]) -> DailyMetrics:
    """Create daily metrics record."""
    metrics = DailyMetrics(**metrics_data)
    db.add(metrics)
    db.flush()
    return metrics


def upsert_daily_metrics(db: Session, metrics_data: Dict[str, Any]) -> DailyMetrics:
    """
    Insert or update daily metrics (handles duplicates).

    Uses upsert logic to avoid constraint violations.
    """
    existing = get_daily_metrics(
        db,
        metrics_data["user_id"],
        metrics_data["date"]
    )

    if existing:
        # Update existing record
        for key, value in metrics_data.items():
            if hasattr(existing, key) and key not in ["id", "created_at"]:
                setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        db.flush()
        return existing
    else:
        # Create new record
        return create_daily_metrics(db, metrics_data)


def update_daily_metrics(
    db: Session,
    user_id: str,
    metric_date: date,
    updates: Dict[str, Any]
) -> Optional[DailyMetrics]:
    """Update daily metrics for a specific date."""
    metrics = get_daily_metrics(db, user_id, metric_date)
    if not metrics:
        return None

    for key, value in updates.items():
        if hasattr(metrics, key) and key not in ["id", "created_at", "user_id", "date"]:
            setattr(metrics, key, value)

    metrics.updated_at = datetime.utcnow()
    db.flush()
    return metrics


def bulk_insert_daily_metrics(
    db: Session,
    metrics_list: List[Dict[str, Any]],
    upsert: bool = True
) -> int:
    """
    Bulk insert daily metrics with optional upsert.

    Performance: <500ms for 100 records

    Args:
        db: Database session
        metrics_list: List of metrics dictionaries
        upsert: If True, update existing records; if False, skip duplicates

    Returns:
        Number of records inserted/updated
    """
    if not metrics_list:
        return 0

    if upsert:
        # Use individual upserts for SQLite (doesn't support ON CONFLICT DO UPDATE efficiently)
        count = 0
        for metrics_data in metrics_list:
            upsert_daily_metrics(db, metrics_data)
            count += 1
        return count
    else:
        # Bulk insert, ignoring duplicates
        db.bulk_insert_mappings(DailyMetrics, metrics_list)
        return len(metrics_list)


def bulk_update_daily_metrics(
    db: Session,
    updates_list: List[Dict[str, Any]]
) -> int:
    """
    Bulk update daily metrics.

    Performance: <3s for 90 records

    Args:
        db: Database session
        updates_list: List of update dictionaries with 'id' and fields to update

    Returns:
        Number of records updated
    """
    if not updates_list:
        return 0

    count = 0
    for update_data in updates_list:
        metric_id = update_data.get('id')
        if not metric_id:
            continue

        metric = db.query(DailyMetrics).filter(DailyMetrics.id == metric_id).first()
        if metric:
            for key, value in update_data.items():
                if key != 'id' and hasattr(metric, key):
                    setattr(metric, key, value)
            metric.updated_at = datetime.utcnow()
            count += 1

    db.flush()
    return count


# ============================================================================
# ACTIVITY OPERATIONS
# ============================================================================

def get_activity_by_id(db: Session, activity_id: int) -> Optional[Activity]:
    """Get activity by internal ID."""
    return db.query(Activity).filter(Activity.id == activity_id).first()


def get_activity_by_garmin_id(db: Session, garmin_activity_id: str) -> Optional[Activity]:
    """Get activity by Garmin activity ID."""
    return db.query(Activity).filter(
        Activity.garmin_activity_id == garmin_activity_id
    ).first()


def get_recent_activities(
    db: Session,
    user_id: str,
    limit: int = 10,
    activity_type: Optional[ActivityType] = None
) -> List[Activity]:
    """
    Get recent activities for a user.

    Performance: <20ms for 10 records
    """
    query = db.query(Activity).filter(Activity.user_id == user_id)

    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)

    return query.order_by(Activity.start_time.desc()).limit(limit).all()


def get_activities_range(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date,
    activity_type: Optional[ActivityType] = None
) -> List[Activity]:
    """Get activities for a date range."""
    query = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.activity_date >= start_date,
        Activity.activity_date <= end_date
    )

    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)

    return query.order_by(Activity.start_time.desc()).all()


def create_activity(db: Session, activity_data: Dict[str, Any]) -> Activity:
    """Create new activity."""
    activity = Activity(**activity_data)
    db.add(activity)
    db.flush()
    return activity


def bulk_insert_activities(
    db: Session,
    activities_list: List[Dict[str, Any]],
    upsert: bool = True
) -> int:
    """
    Bulk insert activities with duplicate handling.

    Performance: <500ms for 100 records
    """
    if not activities_list:
        return 0

    count = 0
    for activity_data in activities_list:
        # Check if activity already exists
        existing = get_activity_by_garmin_id(db, activity_data["garmin_activity_id"])

        if existing:
            if upsert:
                # Update existing
                for key, value in activity_data.items():
                    if hasattr(existing, key) and key not in ["id", "created_at"]:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                count += 1
        else:
            # Create new
            create_activity(db, activity_data)
            count += 1

    db.flush()
    return count


# ============================================================================
# SLEEP OPERATIONS
# ============================================================================

def get_sleep_session(db: Session, user_id: str, sleep_date: date) -> Optional[SleepSession]:
    """Get sleep session for a specific date."""
    return db.query(SleepSession).filter(
        SleepSession.user_id == user_id,
        SleepSession.sleep_date == sleep_date
    ).first()


def get_sleep_range(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date
) -> List[SleepSession]:
    """Get sleep sessions for a date range."""
    return db.query(SleepSession).filter(
        SleepSession.user_id == user_id,
        SleepSession.sleep_date >= start_date,
        SleepSession.sleep_date <= end_date
    ).order_by(SleepSession.sleep_date.desc()).all()


def get_sleep_stats(db: Session, user_id: str, days: int = 7) -> Dict[str, float]:
    """
    Get aggregated sleep statistics.

    Returns average sleep duration, deep sleep, REM, etc.
    Performance: <50ms
    """
    start_date = date.today() - timedelta(days=days)

    stats = db.query(
        func.avg(SleepSession.total_sleep_minutes).label("avg_total_sleep"),
        func.avg(SleepSession.deep_sleep_minutes).label("avg_deep_sleep"),
        func.avg(SleepSession.light_sleep_minutes).label("avg_light_sleep"),
        func.avg(SleepSession.rem_sleep_minutes).label("avg_rem_sleep"),
        func.avg(SleepSession.awake_minutes).label("avg_awake"),
        func.avg(SleepSession.sleep_score).label("avg_sleep_score"),
        func.avg(SleepSession.avg_heart_rate).label("avg_hr_during_sleep"),
    ).filter(
        SleepSession.user_id == user_id,
        SleepSession.sleep_date >= start_date
    ).first()

    if not stats or stats.avg_total_sleep is None:
        return {}

    return {
        "avg_total_sleep_minutes": float(stats.avg_total_sleep or 0),
        "avg_deep_sleep_minutes": float(stats.avg_deep_sleep or 0),
        "avg_light_sleep_minutes": float(stats.avg_light_sleep or 0),
        "avg_rem_sleep_minutes": float(stats.avg_rem_sleep or 0),
        "avg_awake_minutes": float(stats.avg_awake or 0),
        "avg_sleep_score": float(stats.avg_sleep_score or 0),
        "avg_hr_during_sleep": float(stats.avg_hr_during_sleep or 0),
    }


# ============================================================================
# HRV OPERATIONS
# ============================================================================

def get_hrv_readings(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date,
    reading_type: Optional[str] = "morning"
) -> List[HRVReading]:
    """Get HRV readings for a date range."""
    query = db.query(HRVReading).filter(
        HRVReading.user_id == user_id,
        HRVReading.reading_date >= start_date,
        HRVReading.reading_date <= end_date
    )

    if reading_type:
        query = query.filter(HRVReading.reading_type == reading_type)

    return query.order_by(HRVReading.reading_date.desc()).all()


def get_hrv_baseline(db: Session, user_id: str, days: int = 30) -> Optional[Dict[str, float]]:
    """
    Calculate HRV baseline (average and standard deviation).

    Performance: <50ms for 30 days
    """
    start_date = date.today() - timedelta(days=days)

    # Get all HRV readings
    readings = db.query(HRVReading).filter(
        HRVReading.user_id == user_id,
        HRVReading.reading_date >= start_date,
        HRVReading.reading_type == "morning"
    ).all()

    if not readings:
        return None

    # Extract values for calculation
    sdnn_values = [r.hrv_sdnn for r in readings if r.hrv_sdnn is not None]
    rmssd_values = [r.hrv_rmssd for r in readings if r.hrv_rmssd is not None]

    if not sdnn_values:
        return None

    # Calculate statistics using Python
    import numpy as np

    return {
        "avg_hrv_sdnn": float(np.mean(sdnn_values)),
        "avg_hrv_rmssd": float(np.mean(rmssd_values)) if rmssd_values else 0.0,
        "stddev_hrv_sdnn": float(np.std(sdnn_values, ddof=1)) if len(sdnn_values) > 1 else 0.0,
        "stddev_hrv_rmssd": float(np.std(rmssd_values, ddof=1)) if len(rmssd_values) > 1 else 0.0,
        "min_hrv_sdnn": float(min(sdnn_values)),
        "max_hrv_sdnn": float(max(sdnn_values)),
        "days_analyzed": days,
    }


# ============================================================================
# TRAINING LOAD OPERATIONS
# ============================================================================

def get_training_load(db: Session, user_id: str, tracking_date: date) -> Optional[TrainingLoadTracking]:
    """Get training load for a specific date."""
    return db.query(TrainingLoadTracking).filter(
        TrainingLoadTracking.user_id == user_id,
        TrainingLoadTracking.tracking_date == tracking_date
    ).first()


def get_training_load_range(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date
) -> List[TrainingLoadTracking]:
    """Get training load for a date range."""
    return db.query(TrainingLoadTracking).filter(
        TrainingLoadTracking.user_id == user_id,
        TrainingLoadTracking.tracking_date >= start_date,
        TrainingLoadTracking.tracking_date <= end_date
    ).order_by(TrainingLoadTracking.tracking_date.desc()).all()


def get_acute_training_load(db: Session, user_id: str, days: int = 7) -> Optional[int]:
    """
    Calculate acute training load (7-day average).

    Performance: <50ms
    """
    start_date = date.today() - timedelta(days=days)

    result = db.query(
        func.avg(TrainingLoadTracking.daily_training_load).label("avg_load")
    ).filter(
        TrainingLoadTracking.user_id == user_id,
        TrainingLoadTracking.tracking_date >= start_date
    ).first()

    if result and result.avg_load is not None:
        return int(result.avg_load)
    return None


def get_chronic_training_load(db: Session, user_id: str, days: int = 28) -> Optional[int]:
    """
    Calculate chronic training load (28-day average).

    Performance: <50ms
    """
    start_date = date.today() - timedelta(days=days)

    result = db.query(
        func.avg(TrainingLoadTracking.daily_training_load).label("avg_load")
    ).filter(
        TrainingLoadTracking.user_id == user_id,
        TrainingLoadTracking.tracking_date >= start_date
    ).first()

    if result and result.avg_load is not None:
        return int(result.avg_load)
    return None


def calculate_acwr(db: Session, user_id: str) -> Optional[float]:
    """
    Calculate Acute:Chronic Workload Ratio.

    Performance: <100ms
    """
    acute = get_acute_training_load(db, user_id, days=7)
    chronic = get_chronic_training_load(db, user_id, days=28)

    if acute is not None and chronic is not None and chronic > 0:
        return round(acute / chronic, 2)
    return None


def create_training_load_tracking(
    db: Session,
    tracking_data: Dict[str, Any]
) -> TrainingLoadTracking:
    """Create a new training load tracking record."""
    tracking = TrainingLoadTracking(**tracking_data)
    db.add(tracking)
    db.flush()
    return tracking


# ============================================================================
# TRAINING PLAN OPERATIONS
# ============================================================================

def get_active_training_plan(db: Session, user_id: str) -> Optional[TrainingPlan]:
    """Get the user's currently active training plan."""
    return db.query(TrainingPlan).filter(
        TrainingPlan.user_id == user_id,
        TrainingPlan.is_active == True
    ).order_by(TrainingPlan.created_at.desc()).first()


def get_training_plans(
    db: Session,
    user_id: str,
    include_inactive: bool = False
) -> List[TrainingPlan]:
    """Get all training plans for a user."""
    query = db.query(TrainingPlan).filter(TrainingPlan.user_id == user_id)

    if not include_inactive:
        query = query.filter(TrainingPlan.is_active == True)

    return query.order_by(TrainingPlan.created_at.desc()).all()


def create_training_plan(db: Session, plan_data: Dict[str, Any]) -> TrainingPlan:
    """Create a new training plan."""
    plan = TrainingPlan(**plan_data)
    db.add(plan)
    db.flush()
    return plan


def deactivate_training_plans(db: Session, user_id: str) -> int:
    """Deactivate all training plans for a user."""
    count = db.query(TrainingPlan).filter(
        TrainingPlan.user_id == user_id,
        TrainingPlan.is_active == True
    ).update({"is_active": False})

    db.flush()
    return count


# ============================================================================
# PLANNED WORKOUT OPERATIONS
# ============================================================================

def get_planned_workout(db: Session, workout_id: int) -> Optional[PlannedWorkout]:
    """Get planned workout by ID."""
    return db.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()


def get_planned_workouts_for_date(
    db: Session,
    user_id: str,
    workout_date: date
) -> List[PlannedWorkout]:
    """Get planned workouts for a specific date."""
    return db.query(PlannedWorkout).filter(
        PlannedWorkout.user_id == user_id,
        PlannedWorkout.workout_date == workout_date
    ).all()


def get_upcoming_workouts(
    db: Session,
    user_id: str,
    days_ahead: int = 7
) -> List[PlannedWorkout]:
    """Get upcoming planned workouts."""
    end_date = date.today() + timedelta(days=days_ahead)

    return db.query(PlannedWorkout).filter(
        PlannedWorkout.user_id == user_id,
        PlannedWorkout.workout_date >= date.today(),
        PlannedWorkout.workout_date <= end_date,
        PlannedWorkout.was_completed == False
    ).order_by(PlannedWorkout.workout_date.asc()).all()


def create_planned_workout(db: Session, workout_data: Dict[str, Any]) -> PlannedWorkout:
    """Create a new planned workout."""
    workout = PlannedWorkout(**workout_data)
    db.add(workout)
    db.flush()
    return workout


def bulk_create_planned_workouts(
    db: Session,
    workouts_list: List[Dict[str, Any]]
) -> List[PlannedWorkout]:
    """Bulk create planned workouts."""
    workouts = [PlannedWorkout(**data) for data in workouts_list]
    db.bulk_save_objects(workouts, return_defaults=True)
    db.flush()
    return workouts


def mark_workout_completed(
    db: Session,
    workout_id: int,
    activity_id: Optional[int] = None
) -> Optional[PlannedWorkout]:
    """Mark a planned workout as completed."""
    workout = get_planned_workout(db, workout_id)
    if not workout:
        return None

    workout.was_completed = True
    workout.completion_date = datetime.utcnow()
    if activity_id:
        workout.actual_activity_id = activity_id

    db.flush()
    return workout


# ============================================================================
# DAILY READINESS OPERATIONS
# ============================================================================

def get_daily_readiness(db: Session, user_id: str, readiness_date: date) -> Optional[DailyReadiness]:
    """Get daily readiness for a specific date."""
    return db.query(DailyReadiness).filter(
        DailyReadiness.user_id == user_id,
        DailyReadiness.readiness_date == readiness_date
    ).first()


def get_recent_readiness(db: Session, user_id: str, days: int = 7) -> List[DailyReadiness]:
    """Get recent readiness assessments."""
    start_date = date.today() - timedelta(days=days)

    return db.query(DailyReadiness).filter(
        DailyReadiness.user_id == user_id,
        DailyReadiness.readiness_date >= start_date
    ).order_by(DailyReadiness.readiness_date.desc()).all()


def create_daily_readiness(db: Session, readiness_data: Dict[str, Any]) -> DailyReadiness:
    """Create daily readiness assessment."""
    readiness = DailyReadiness(**readiness_data)
    db.add(readiness)
    db.flush()
    return readiness


# ============================================================================
# AI ANALYSIS CACHE OPERATIONS
# ============================================================================

def get_cached_analysis(
    db: Session,
    content_hash: str,
    max_age_hours: int = 24
) -> Optional[AIAnalysisCache]:
    """
    Get cached AI analysis by content hash.

    Returns None if cache is expired or doesn't exist.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    cache = db.query(AIAnalysisCache).filter(
        AIAnalysisCache.content_hash == content_hash,
        AIAnalysisCache.created_at >= cutoff_time
    ).first()

    if cache:
        # Update hit count and last accessed
        cache.hit_count += 1
        cache.last_accessed_at = datetime.utcnow()
        db.flush()

    return cache


def create_analysis_cache(db: Session, cache_data: Dict[str, Any]) -> AIAnalysisCache:
    """Create new AI analysis cache entry."""
    cache = AIAnalysisCache(**cache_data)
    db.add(cache)
    db.flush()
    return cache


def cleanup_old_cache(db: Session, days_to_keep: int = 30) -> int:
    """Delete cache entries older than specified days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

    count = db.query(AIAnalysisCache).filter(
        AIAnalysisCache.created_at < cutoff_date
    ).delete()

    db.flush()
    return count


# ============================================================================
# SYNC HISTORY OPERATIONS
# ============================================================================

def get_last_sync(db: Session, user_id: str, sync_type: Optional[str] = None) -> Optional[SyncHistory]:
    """Get the most recent successful sync for a user."""
    query = db.query(SyncHistory).filter(
        SyncHistory.user_id == user_id,
        SyncHistory.sync_status == "completed"
    )

    if sync_type:
        query = query.filter(SyncHistory.sync_type == sync_type)

    return query.order_by(SyncHistory.sync_completed_at.desc()).first()


def create_sync_history(db: Session, sync_data: Dict[str, Any]) -> SyncHistory:
    """Create sync history record."""
    sync = SyncHistory(**sync_data)
    db.add(sync)
    db.flush()
    return sync


def update_sync_status(
    db: Session,
    sync_id: int,
    status: str,
    **kwargs
) -> Optional[SyncHistory]:
    """Update sync history status."""
    sync = db.query(SyncHistory).filter(SyncHistory.id == sync_id).first()
    if not sync:
        return None

    sync.sync_status = status
    for key, value in kwargs.items():
        if hasattr(sync, key):
            setattr(sync, key, value)

    db.flush()
    return sync


# ============================================================================
# AGGREGATED QUERY FUNCTIONS
# ============================================================================

def get_dashboard_summary(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive dashboard summary for a user.

    Includes:
    - Latest metrics
    - Recent readiness
    - Upcoming workouts
    - Training load summary
    - Sleep summary

    Performance: <200ms (optimized with single queries)
    """
    today = date.today()
    week_ago = today - timedelta(days=7)

    # Latest metrics
    latest_metrics = get_daily_metrics(db, user_id, today)

    # Latest readiness
    latest_readiness = get_daily_readiness(db, user_id, today)

    # Upcoming workouts
    upcoming = get_upcoming_workouts(db, user_id, days_ahead=7)

    # Training load
    acute_load = get_acute_training_load(db, user_id, days=7)
    chronic_load = get_chronic_training_load(db, user_id, days=28)
    acwr = calculate_acwr(db, user_id)

    # Sleep stats
    sleep_stats = get_sleep_stats(db, user_id, days=7)

    # HRV baseline
    hrv_baseline = get_hrv_baseline(db, user_id, days=30)

    return {
        "user_id": user_id,
        "date": today,
        "latest_metrics": latest_metrics,
        "latest_readiness": latest_readiness,
        "upcoming_workouts": upcoming,
        "training_load": {
            "acute": acute_load,
            "chronic": chronic_load,
            "acwr": acwr,
        },
        "sleep_summary": sleep_stats,
        "hrv_baseline": hrv_baseline,
    }


def get_weekly_summary(db: Session, user_id: str, weeks_back: int = 0) -> Dict[str, Any]:
    """
    Get weekly training summary.

    Args:
        user_id: User ID
        weeks_back: Number of weeks back (0 = current week)

    Returns:
        Dictionary with weekly totals and averages
    """
    week_start = date.today() - timedelta(days=date.today().weekday() + (weeks_back * 7))
    week_end = week_start + timedelta(days=6)

    # Get all activities for the week
    activities = get_activities_range(db, user_id, week_start, week_end)

    # Get metrics for the week
    metrics = get_metrics_range(db, user_id, week_start, week_end)

    # Calculate totals
    total_distance = sum(a.distance_meters or 0 for a in activities) / 1000  # km
    total_duration = sum(a.duration_minutes or 0 for a in activities)  # minutes
    total_activities = len(activities)

    # Calculate averages from metrics
    avg_hrv = sum(m.hrv_sdnn or 0 for m in metrics if m.hrv_sdnn) / len(metrics) if metrics else 0
    avg_sleep = sum(m.total_sleep_minutes or 0 for m in metrics if m.total_sleep_minutes) / len(metrics) if metrics else 0
    avg_stress = sum(m.stress_score or 0 for m in metrics if m.stress_score) / len(metrics) if metrics else 0

    return {
        "week_start": week_start,
        "week_end": week_end,
        "activities": {
            "total_count": total_activities,
            "total_distance_km": round(total_distance, 2),
            "total_duration_minutes": round(total_duration, 1),
            "avg_duration_minutes": round(total_duration / total_activities, 1) if total_activities > 0 else 0,
        },
        "health": {
            "avg_hrv_sdnn": round(avg_hrv, 1),
            "avg_sleep_minutes": round(avg_sleep, 0),
            "avg_stress_score": round(avg_stress, 0),
        },
    }


# ============================================================================
# DELETION OPERATIONS
# ============================================================================

def delete_old_data(db: Session, days_to_keep: int = 365) -> Dict[str, int]:
    """
    Delete data older than specified days.

    Used for data retention compliance and database cleanup.

    Returns:
        Dictionary with count of deleted records per table
    """
    cutoff_date = date.today() - timedelta(days=days_to_keep)

    results = {}

    # Delete old daily metrics (cascade deletes related data)
    results["daily_metrics"] = db.query(DailyMetrics).filter(
        DailyMetrics.date < cutoff_date
    ).delete()

    # Delete old activities
    results["activities"] = db.query(Activity).filter(
        Activity.activity_date < cutoff_date
    ).delete()

    # Delete old sync history
    results["sync_history"] = db.query(SyncHistory).filter(
        SyncHistory.sync_started_at < datetime.combine(cutoff_date, datetime.min.time())
    ).delete()

    # Delete old cache
    results["ai_cache"] = cleanup_old_cache(db, days_to_keep=90)

    db.flush()
    return results
