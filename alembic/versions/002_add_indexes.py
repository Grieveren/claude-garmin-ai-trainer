"""Add performance indexes for common query patterns

Revision ID: 002_add_indexes
Revises: 001_initial_schema
Create Date: 2025-10-16

This migration adds additional indexes to optimize common query patterns:
- Composite indexes for range queries
- Indexes for aggregation queries
- Indexes for filtering and sorting operations
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_indexes'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes."""

    # ========================================================================
    # DAILY METRICS INDEXES
    # ========================================================================

    # Index for HRV queries (filtering by HRV values)
    op.create_index(
        'idx_daily_metrics_hrv_sdnn',
        'daily_metrics',
        ['hrv_sdnn'],
        postgresql_where=sa.text('hrv_sdnn IS NOT NULL')
    )

    # Index for sleep quality queries
    op.create_index(
        'idx_daily_metrics_sleep_score',
        'daily_metrics',
        ['sleep_score'],
        postgresql_where=sa.text('sleep_score IS NOT NULL')
    )

    # Index for body battery queries
    op.create_index(
        'idx_daily_metrics_body_battery',
        'daily_metrics',
        ['body_battery_max', 'body_battery_min']
    )

    # Composite index for stress analysis
    op.create_index(
        'idx_daily_metrics_stress_date',
        'daily_metrics',
        ['user_id', 'stress_score', 'date']
    )

    # ========================================================================
    # ACTIVITY INDEXES
    # ========================================================================

    # Index for activity type + date queries (common filter pattern)
    op.create_index(
        'idx_activity_type_date',
        'activities',
        ['activity_type', 'activity_date', 'user_id']
    )

    # Index for training load queries
    op.create_index(
        'idx_activity_training_load',
        'activities',
        ['user_id', 'training_load'],
        postgresql_where=sa.text('training_load IS NOT NULL')
    )

    # Index for distance-based queries (e.g., long runs)
    op.create_index(
        'idx_activity_distance',
        'activities',
        ['user_id', 'distance_meters', 'activity_type']
    )

    # Index for duration-based queries
    op.create_index(
        'idx_activity_duration',
        'activities',
        ['user_id', 'duration_minutes', 'activity_type']
    )

    # ========================================================================
    # SLEEP SESSION INDEXES
    # ========================================================================

    # Index for sleep duration queries
    op.create_index(
        'idx_sleep_duration',
        'sleep_sessions',
        ['user_id', 'total_sleep_minutes', 'sleep_date']
    )

    # Index for sleep quality filtering
    op.create_index(
        'idx_sleep_quality',
        'sleep_sessions',
        ['user_id', 'sleep_quality', 'sleep_score']
    )

    # Index for sleep time range queries
    op.create_index(
        'idx_sleep_time_range',
        'sleep_sessions',
        ['sleep_start_time', 'sleep_end_time']
    )

    # ========================================================================
    # HRV READING INDEXES
    # ========================================================================

    # Composite index for HRV trend analysis
    op.create_index(
        'idx_hrv_user_type_date',
        'hrv_readings',
        ['user_id', 'reading_type', 'reading_date', 'hrv_sdnn']
    )

    # Index for HRV status queries
    op.create_index(
        'idx_hrv_status',
        'hrv_readings',
        ['user_id', 'status'],
        postgresql_where=sa.text('status IS NOT NULL')
    )

    # ========================================================================
    # TRAINING LOAD TRACKING INDEXES
    # ========================================================================

    # Index for ACWR queries
    op.create_index(
        'idx_load_acwr',
        'training_load_tracking',
        ['user_id', 'acwr', 'tracking_date']
    )

    # Index for injury risk queries
    op.create_index(
        'idx_load_injury_risk',
        'training_load_tracking',
        ['user_id', 'injury_risk', 'tracking_date'],
        postgresql_where=sa.text('injury_risk IS NOT NULL')
    )

    # Index for form/fitness queries
    op.create_index(
        'idx_load_form',
        'training_load_tracking',
        ['user_id', 'form', 'tracking_date']
    )

    # Index for overtraining risk
    op.create_index(
        'idx_load_overtraining',
        'training_load_tracking',
        ['user_id', 'overtraining_risk'],
        postgresql_where=sa.text('overtraining_risk IS NOT NULL')
    )

    # ========================================================================
    # DAILY READINESS INDEXES
    # ========================================================================

    # Index for readiness recommendation queries
    op.create_index(
        'idx_readiness_recommendation',
        'daily_readiness',
        ['user_id', 'recommendation', 'readiness_date']
    )

    # Index for readiness score range queries
    op.create_index(
        'idx_readiness_score_date',
        'daily_readiness',
        ['user_id', 'readiness_score', 'readiness_date']
    )

    # Index for AI confidence filtering
    op.create_index(
        'idx_readiness_confidence',
        'daily_readiness',
        ['ai_confidence_score'],
        postgresql_where=sa.text('ai_confidence_score IS NOT NULL')
    )

    # ========================================================================
    # PLANNED WORKOUT INDEXES
    # ========================================================================

    # Index for intensity-based queries
    op.create_index(
        'idx_planned_intensity',
        'planned_workouts',
        ['user_id', 'intensity_category', 'workout_date']
    )

    # Index for workout type queries
    op.create_index(
        'idx_planned_type_date',
        'planned_workouts',
        ['workout_type', 'workout_date', 'was_completed']
    )

    # Index for completion status + plan queries
    op.create_index(
        'idx_planned_plan_completion',
        'planned_workouts',
        ['training_plan_id', 'was_completed', 'workout_date']
    )

    # ========================================================================
    # TRAINING PLAN INDEXES
    # ========================================================================

    # Index for active plan queries with date range
    op.create_index(
        'idx_plan_active_dates',
        'training_plans',
        ['user_id', 'is_active', 'start_date', 'target_date']
    )

    # Index for AI-generated plans
    op.create_index(
        'idx_plan_ai_generated',
        'training_plans',
        ['created_by_ai', 'created_at']
    )

    # ========================================================================
    # AI ANALYSIS CACHE INDEXES
    # ========================================================================

    # Composite index for cache lookup by type and hash
    op.create_index(
        'idx_cache_type_hash',
        'ai_analysis_cache',
        ['analysis_type', 'content_hash']
    )

    # Index for cache cleanup based on hit count
    op.create_index(
        'idx_cache_hits',
        'ai_analysis_cache',
        ['hit_count', 'last_accessed_at']
    )

    # Index for expiration queries
    op.create_index(
        'idx_cache_expiration',
        'ai_analysis_cache',
        ['expires_at'],
        postgresql_where=sa.text('expires_at IS NOT NULL')
    )

    # ========================================================================
    # SYNC HISTORY INDEXES
    # ========================================================================

    # Composite index for sync status + type queries
    op.create_index(
        'idx_sync_status_type',
        'sync_history',
        ['user_id', 'sync_status', 'sync_type', 'sync_started_at']
    )

    # Index for data range queries
    op.create_index(
        'idx_sync_data_range',
        'sync_history',
        ['data_start_date', 'data_end_date'],
        postgresql_where=sa.text('data_start_date IS NOT NULL')
    )

    # Index for failed syncs
    op.create_index(
        'idx_sync_failed',
        'sync_history',
        ['sync_status', 'sync_started_at'],
        postgresql_where=sa.text("sync_status = 'failed'")
    )

    # ========================================================================
    # USER PROFILE INDEXES
    # ========================================================================

    # Index for last sync time queries
    op.create_index(
        'idx_user_last_sync',
        'user_profile',
        ['last_sync_at'],
        postgresql_where=sa.text('last_sync_at IS NOT NULL')
    )

    # Index for Garmin integration status
    op.create_index(
        'idx_user_garmin_integration',
        'user_profile',
        ['garmin_user_id', 'last_sync_at'],
        postgresql_where=sa.text('garmin_user_id IS NOT NULL')
    )


def downgrade():
    """Remove performance indexes."""

    # Drop indexes in reverse order
    op.drop_index('idx_user_garmin_integration', 'user_profile')
    op.drop_index('idx_user_last_sync', 'user_profile')

    op.drop_index('idx_sync_failed', 'sync_history')
    op.drop_index('idx_sync_data_range', 'sync_history')
    op.drop_index('idx_sync_status_type', 'sync_history')

    op.drop_index('idx_cache_expiration', 'ai_analysis_cache')
    op.drop_index('idx_cache_hits', 'ai_analysis_cache')
    op.drop_index('idx_cache_type_hash', 'ai_analysis_cache')

    op.drop_index('idx_plan_ai_generated', 'training_plans')
    op.drop_index('idx_plan_active_dates', 'training_plans')

    op.drop_index('idx_planned_plan_completion', 'planned_workouts')
    op.drop_index('idx_planned_type_date', 'planned_workouts')
    op.drop_index('idx_planned_intensity', 'planned_workouts')

    op.drop_index('idx_readiness_confidence', 'daily_readiness')
    op.drop_index('idx_readiness_score_date', 'daily_readiness')
    op.drop_index('idx_readiness_recommendation', 'daily_readiness')

    op.drop_index('idx_load_overtraining', 'training_load_tracking')
    op.drop_index('idx_load_form', 'training_load_tracking')
    op.drop_index('idx_load_injury_risk', 'training_load_tracking')
    op.drop_index('idx_load_acwr', 'training_load_tracking')

    op.drop_index('idx_hrv_status', 'hrv_readings')
    op.drop_index('idx_hrv_user_type_date', 'hrv_readings')

    op.drop_index('idx_sleep_time_range', 'sleep_sessions')
    op.drop_index('idx_sleep_quality', 'sleep_sessions')
    op.drop_index('idx_sleep_duration', 'sleep_sessions')

    op.drop_index('idx_activity_duration', 'activities')
    op.drop_index('idx_activity_distance', 'activities')
    op.drop_index('idx_activity_training_load', 'activities')
    op.drop_index('idx_activity_type_date', 'activities')

    op.drop_index('idx_daily_metrics_stress_date', 'daily_metrics')
    op.drop_index('idx_daily_metrics_body_battery', 'daily_metrics')
    op.drop_index('idx_daily_metrics_sleep_score', 'daily_metrics')
    op.drop_index('idx_daily_metrics_hrv_sdnn', 'daily_metrics')
