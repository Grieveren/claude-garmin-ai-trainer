"""Initial database schema for Garmin AI Training System

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-10-15

This migration creates the complete database schema including:
- User profiles and Garmin integration
- Daily health metrics and sleep tracking
- Activities and heart rate data
- Training plans and scheduled workouts
- AI analysis and readiness scores
- Training load monitoring
- Sync history tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables with proper indexes and constraints."""

    # 1. user_profile
    op.create_table(
        'user_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('resting_heart_rate', sa.Integer(), nullable=True),
        sa.Column('max_heart_rate', sa.Integer(), nullable=True),
        sa.Column('training_preferences', sa.JSON(), nullable=True),
        sa.Column('garmin_user_id', sa.String(length=100), nullable=True),
        sa.Column('garmin_access_token', sa.Text(), nullable=True),
        sa.Column('garmin_refresh_token', sa.Text(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('units_system', sa.String(length=10), nullable=False, server_default='metric'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_profile_id', 'user_profile', ['id'])
    op.create_index('ix_user_profile_user_id', 'user_profile', ['user_id'], unique=True)
    op.create_index('ix_user_profile_email', 'user_profile', ['email'], unique=True)
    op.create_index('ix_user_profile_garmin_user_id', 'user_profile', ['garmin_user_id'], unique=True)

    # 2. daily_metrics
    op.create_table(
        'daily_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('steps', sa.Integer(), nullable=True),
        sa.Column('distance_meters', sa.Float(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('active_minutes', sa.Integer(), nullable=True),
        sa.Column('floors_climbed', sa.Integer(), nullable=True),
        sa.Column('resting_heart_rate', sa.Integer(), nullable=True),
        sa.Column('max_heart_rate', sa.Integer(), nullable=True),
        sa.Column('avg_heart_rate', sa.Integer(), nullable=True),
        sa.Column('hrv_sdnn', sa.Float(), nullable=True),
        sa.Column('hrv_rmssd', sa.Float(), nullable=True),
        sa.Column('stress_score', sa.Integer(), nullable=True),
        sa.Column('body_battery_charged', sa.Integer(), nullable=True),
        sa.Column('body_battery_drained', sa.Integer(), nullable=True),
        sa.Column('body_battery_max', sa.Integer(), nullable=True),
        sa.Column('body_battery_min', sa.Integer(), nullable=True),
        sa.Column('sleep_score', sa.Integer(), nullable=True),
        sa.Column('total_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('deep_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('light_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('rem_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('awake_minutes', sa.Integer(), nullable=True),
        sa.Column('vo2_max', sa.Float(), nullable=True),
        sa.Column('fitness_age', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('body_fat_percent', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('hydration_ml', sa.Integer(), nullable=True),
        sa.Column('avg_respiration_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_user_date')
    )
    op.create_index('ix_daily_metrics_id', 'daily_metrics', ['id'])
    op.create_index('ix_daily_metrics_user_id', 'daily_metrics', ['user_id'])
    op.create_index('ix_daily_metrics_date', 'daily_metrics', ['date'])
    op.create_index('idx_daily_metrics_user_date', 'daily_metrics', ['user_id', 'date'])

    # 3. sleep_sessions
    op.create_table(
        'sleep_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('daily_metric_id', sa.Integer(), nullable=False),
        sa.Column('sleep_date', sa.Date(), nullable=False),
        sa.Column('sleep_start_time', sa.DateTime(), nullable=False),
        sa.Column('sleep_end_time', sa.DateTime(), nullable=False),
        sa.Column('total_sleep_minutes', sa.Integer(), nullable=False),
        sa.Column('deep_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('light_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('rem_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('awake_minutes', sa.Integer(), nullable=True),
        sa.Column('sleep_score', sa.Integer(), nullable=True),
        sa.Column('sleep_quality', sa.String(length=20), nullable=True),
        sa.Column('restlessness', sa.Float(), nullable=True),
        sa.Column('avg_heart_rate', sa.Integer(), nullable=True),
        sa.Column('min_heart_rate', sa.Integer(), nullable=True),
        sa.Column('max_heart_rate', sa.Integer(), nullable=True),
        sa.Column('avg_hrv', sa.Float(), nullable=True),
        sa.Column('avg_respiration_rate', sa.Float(), nullable=True),
        sa.Column('awakenings_count', sa.Integer(), nullable=True),
        sa.Column('sleep_stages_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['daily_metric_id'], ['daily_metrics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sleep_sessions_id', 'sleep_sessions', ['id'])
    op.create_index('ix_sleep_sessions_user_id', 'sleep_sessions', ['user_id'])
    op.create_index('ix_sleep_sessions_daily_metric_id', 'sleep_sessions', ['daily_metric_id'], unique=True)
    op.create_index('idx_sleep_user_date', 'sleep_sessions', ['user_id', 'sleep_date'])
    op.create_index('idx_sleep_start_time', 'sleep_sessions', ['sleep_start_time'])

    # 4. activities
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('garmin_activity_id', sa.String(length=100), nullable=False),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('activity_type', sa.Enum('RUNNING', 'CYCLING', 'SWIMMING', 'WALKING', 'HIKING',
                                           'STRENGTH_TRAINING', 'YOGA', 'CARDIO', 'OTHER',
                                           name='activitytype'), nullable=False),
        sa.Column('activity_name', sa.String(length=200), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Float(), nullable=True),
        sa.Column('distance_meters', sa.Float(), nullable=True),
        sa.Column('avg_heart_rate', sa.Integer(), nullable=True),
        sa.Column('max_heart_rate', sa.Integer(), nullable=True),
        sa.Column('avg_pace_per_km', sa.Float(), nullable=True),
        sa.Column('avg_speed_kmh', sa.Float(), nullable=True),
        sa.Column('max_speed_kmh', sa.Float(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('elevation_gain_meters', sa.Float(), nullable=True),
        sa.Column('elevation_loss_meters', sa.Float(), nullable=True),
        sa.Column('training_effect_aerobic', sa.Float(), nullable=True),
        sa.Column('training_effect_anaerobic', sa.Float(), nullable=True),
        sa.Column('training_load', sa.Integer(), nullable=True),
        sa.Column('recovery_time_hours', sa.Integer(), nullable=True),
        sa.Column('avg_power', sa.Integer(), nullable=True),
        sa.Column('max_power', sa.Integer(), nullable=True),
        sa.Column('normalized_power', sa.Integer(), nullable=True),
        sa.Column('avg_cadence', sa.Integer(), nullable=True),
        sa.Column('max_cadence', sa.Integer(), nullable=True),
        sa.Column('avg_stride_length', sa.Float(), nullable=True),
        sa.Column('avg_vertical_oscillation', sa.Float(), nullable=True),
        sa.Column('avg_ground_contact_time', sa.Integer(), nullable=True),
        sa.Column('intensity_factor', sa.Float(), nullable=True),
        sa.Column('hr_zones_data', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('perceived_exertion', sa.Integer(), nullable=True),
        sa.Column('temperature_celsius', sa.Float(), nullable=True),
        sa.Column('weather_condition', sa.String(length=50), nullable=True),
        sa.Column('raw_activity_data', sa.JSON(), nullable=True),
        sa.Column('planned_workout_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activities_id', 'activities', ['id'])
    op.create_index('ix_activities_user_id', 'activities', ['user_id'])
    op.create_index('ix_activities_garmin_activity_id', 'activities', ['garmin_activity_id'], unique=True)
    op.create_index('ix_activities_activity_type', 'activities', ['activity_type'])
    op.create_index('idx_activity_user_date', 'activities', ['user_id', 'activity_date'])
    op.create_index('idx_activity_date', 'activities', ['activity_date'])

    # 5. heart_rate_samples
    op.create_table(
        'heart_rate_samples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activity_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('heart_rate', sa.Integer(), nullable=False),
        sa.Column('elapsed_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heart_rate_samples_id', 'heart_rate_samples', ['id'])
    op.create_index('ix_heart_rate_samples_activity_id', 'heart_rate_samples', ['activity_id'])
    op.create_index('idx_hr_timestamp', 'heart_rate_samples', ['timestamp'])

    # 6. hrv_readings
    op.create_table(
        'hrv_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('daily_metric_id', sa.Integer(), nullable=False),
        sa.Column('reading_date', sa.Date(), nullable=False),
        sa.Column('reading_time', sa.DateTime(), nullable=False),
        sa.Column('reading_type', sa.String(length=20), nullable=False),
        sa.Column('hrv_sdnn', sa.Float(), nullable=False),
        sa.Column('hrv_rmssd', sa.Float(), nullable=True),
        sa.Column('hrv_pnn50', sa.Float(), nullable=True),
        sa.Column('avg_heart_rate', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['daily_metric_id'], ['daily_metrics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_hrv_readings_id', 'hrv_readings', ['id'])
    op.create_index('ix_hrv_readings_user_id', 'hrv_readings', ['user_id'])
    op.create_index('idx_hrv_user_date', 'hrv_readings', ['user_id', 'reading_date'])
    op.create_index('idx_hrv_type', 'hrv_readings', ['reading_type'])

    # 7. training_plans
    op.create_table(
        'training_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('completion_percent', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_by_ai', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('ai_model_version', sa.String(length=50), nullable=True),
        sa.Column('ai_generation_prompt', sa.Text(), nullable=True),
        sa.Column('weekly_structure', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_plans_id', 'training_plans', ['id'])
    op.create_index('ix_training_plans_user_id', 'training_plans', ['user_id'])
    op.create_index('idx_plan_user_active', 'training_plans', ['user_id', 'is_active'])
    op.create_index('idx_plan_dates', 'training_plans', ['start_date', 'target_date'])

    # 8. planned_workouts
    op.create_table(
        'planned_workouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('training_plan_id', sa.Integer(), nullable=True),
        sa.Column('workout_date', sa.Date(), nullable=False),
        sa.Column('workout_type', sa.Enum('RUNNING', 'CYCLING', 'SWIMMING', 'WALKING', 'HIKING',
                                          'STRENGTH_TRAINING', 'YOGA', 'CARDIO', 'OTHER',
                                          name='activitytype'), nullable=False),
        sa.Column('workout_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('target_distance_meters', sa.Float(), nullable=True),
        sa.Column('target_heart_rate_zone', sa.String(length=20), nullable=True),
        sa.Column('target_pace_per_km', sa.Float(), nullable=True),
        sa.Column('target_power', sa.Integer(), nullable=True),
        sa.Column('intensity_level', sa.Integer(), nullable=False),
        sa.Column('intensity_category', sa.Enum('REST', 'EASY', 'MODERATE', 'HIGH_INTENSITY', 'MAXIMUM',
                                                 name='workoutintensity'), nullable=False),
        sa.Column('was_completed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('actual_activity_id', sa.Integer(), nullable=True),
        sa.Column('workout_structure', sa.JSON(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('ai_adaptations', sa.JSON(), nullable=True),
        sa.Column('coach_notes', sa.Text(), nullable=True),
        sa.Column('athlete_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['training_plan_id'], ['training_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actual_activity_id'], ['activities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_planned_workouts_id', 'planned_workouts', ['id'])
    op.create_index('ix_planned_workouts_user_id', 'planned_workouts', ['user_id'])
    op.create_index('idx_planned_user_date', 'planned_workouts', ['user_id', 'workout_date'])
    op.create_index('idx_planned_plan', 'planned_workouts', ['training_plan_id'])
    op.create_index('idx_planned_completed', 'planned_workouts', ['was_completed'])

    # Add foreign key from activities to planned_workouts (circular reference handled after both tables exist)
    op.create_foreign_key(
        'fk_activities_planned_workout_id',
        'activities', 'planned_workouts',
        ['planned_workout_id'], ['id'],
        ondelete='SET NULL'
    )

    # 9. daily_readiness
    op.create_table(
        'daily_readiness',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('daily_metric_id', sa.Integer(), nullable=False),
        sa.Column('readiness_date', sa.Date(), nullable=False),
        sa.Column('readiness_score', sa.Integer(), nullable=False),
        sa.Column('recommendation', sa.Enum('HIGH_INTENSITY', 'MODERATE', 'EASY', 'REST', 'RECOVERY',
                                            name='readinessrecommendation'), nullable=False),
        sa.Column('recommended_intensity', sa.String(length=50), nullable=True),
        sa.Column('key_factors', sa.JSON(), nullable=False),
        sa.Column('red_flags', sa.JSON(), nullable=True),
        sa.Column('recovery_tips', sa.JSON(), nullable=True),
        sa.Column('suggested_workout_id', sa.Integer(), nullable=True),
        sa.Column('suggested_workout_description', sa.Text(), nullable=True),
        sa.Column('ai_analysis', sa.Text(), nullable=False),
        sa.Column('ai_model_version', sa.String(length=50), nullable=True),
        sa.Column('ai_confidence_score', sa.Float(), nullable=True),
        sa.Column('training_load_7d', sa.Integer(), nullable=True),
        sa.Column('training_load_28d', sa.Integer(), nullable=True),
        sa.Column('acwr', sa.Float(), nullable=True),
        sa.Column('user_agreement', sa.Boolean(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['daily_metric_id'], ['daily_metrics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['suggested_workout_id'], ['planned_workouts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'readiness_date', name='uq_user_readiness_date')
    )
    op.create_index('ix_daily_readiness_id', 'daily_readiness', ['id'])
    op.create_index('ix_daily_readiness_user_id', 'daily_readiness', ['user_id'])
    op.create_index('ix_daily_readiness_daily_metric_id', 'daily_readiness', ['daily_metric_id'], unique=True)
    op.create_index('idx_readiness_user_date', 'daily_readiness', ['user_id', 'readiness_date'])
    op.create_index('idx_readiness_score', 'daily_readiness', ['readiness_score'])

    # 10. ai_analysis_cache
    op.create_table(
        'ai_analysis_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('analysis_type', sa.String(length=50), nullable=False),
        sa.Column('input_context', sa.JSON(), nullable=False),
        sa.Column('ai_response', sa.Text(), nullable=False),
        sa.Column('ai_model_version', sa.String(length=50), nullable=False),
        sa.Column('structured_output', sa.JSON(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_analysis_cache_id', 'ai_analysis_cache', ['id'])
    op.create_index('idx_cache_hash', 'ai_analysis_cache', ['content_hash'], unique=True)
    op.create_index('idx_cache_created', 'ai_analysis_cache', ['created_at'])
    op.create_index('idx_cache_type', 'ai_analysis_cache', ['analysis_type'])

    # 11. training_load_tracking
    op.create_table(
        'training_load_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('daily_metric_id', sa.Integer(), nullable=False),
        sa.Column('tracking_date', sa.Date(), nullable=False),
        sa.Column('daily_training_load', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('acute_training_load', sa.Integer(), nullable=True),
        sa.Column('chronic_training_load', sa.Integer(), nullable=True),
        sa.Column('acwr', sa.Float(), nullable=True),
        sa.Column('acwr_status', sa.String(length=20), nullable=True),
        sa.Column('fitness', sa.Float(), nullable=True),
        sa.Column('fatigue', sa.Float(), nullable=True),
        sa.Column('form', sa.Float(), nullable=True),
        sa.Column('training_monotony', sa.Float(), nullable=True),
        sa.Column('training_strain', sa.Float(), nullable=True),
        sa.Column('weekly_ramp_rate', sa.Float(), nullable=True),
        sa.Column('recovery_score', sa.Integer(), nullable=True),
        sa.Column('overtraining_risk', sa.String(length=20), nullable=True),
        sa.Column('injury_risk', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['daily_metric_id'], ['daily_metrics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tracking_date', name='uq_user_tracking_date')
    )
    op.create_index('ix_training_load_tracking_id', 'training_load_tracking', ['id'])
    op.create_index('ix_training_load_tracking_user_id', 'training_load_tracking', ['user_id'])
    op.create_index('ix_training_load_tracking_daily_metric_id', 'training_load_tracking', ['daily_metric_id'], unique=True)
    op.create_index('idx_load_user_date', 'training_load_tracking', ['user_id', 'tracking_date'])

    # 12. sync_history
    op.create_table(
        'sync_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('sync_status', sa.String(length=20), nullable=False),
        sa.Column('data_start_date', sa.Date(), nullable=True),
        sa.Column('data_end_date', sa.Date(), nullable=True),
        sa.Column('sync_started_at', sa.DateTime(), nullable=False),
        sa.Column('sync_completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('records_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('synced_data_types', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('api_calls_made', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('api_rate_limit_hit', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sync_history_id', 'sync_history', ['id'])
    op.create_index('ix_sync_history_user_id', 'sync_history', ['user_id'])
    op.create_index('idx_sync_user_status', 'sync_history', ['user_id', 'sync_status'])
    op.create_index('idx_sync_time', 'sync_history', ['sync_started_at'])
    op.create_index('idx_sync_type', 'sync_history', ['sync_type'])


def downgrade():
    """Drop all tables in reverse order."""

    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table('sync_history')
    op.drop_table('training_load_tracking')
    op.drop_table('ai_analysis_cache')
    op.drop_table('daily_readiness')
    op.drop_table('planned_workouts')
    op.drop_table('training_plans')
    op.drop_table('hrv_readings')
    op.drop_table('heart_rate_samples')
    op.drop_table('activities')
    op.drop_table('sleep_sessions')
    op.drop_table('daily_metrics')
    op.drop_table('user_profile')

    # Drop enums (if using PostgreSQL)
    try:
        sa.Enum(name='activitytype').drop(op.get_bind(), checkfirst=True)
        sa.Enum(name='workoutintensity').drop(op.get_bind(), checkfirst=True)
        sa.Enum(name='readinessrecommendation').drop(op.get_bind(), checkfirst=True)
    except:
        # SQLite doesn't have native enums, so this will fail gracefully
        pass
