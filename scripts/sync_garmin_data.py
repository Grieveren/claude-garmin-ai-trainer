#!/usr/bin/env python3
"""
Manual Garmin data synchronization script.

This CLI tool allows manual fetching and storing of Garmin Connect data
for a specified date range. Useful for:
- Initial data backfill
- Re-syncing specific date ranges
- Testing data pipeline
- Manual data updates

Usage:
    python scripts/sync_garmin_data.py --start-date 2025-01-01 --end-date 2025-01-15
    python scripts/sync_garmin_data.py --days 7  # Last 7 days
    python scripts/sync_garmin_data.py --today    # Today only
"""

import sys
import argparse
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import print as rprint

from app.core.config import get_settings
from app.database import get_db_context, init_db
from app.services.garmin_service import GarminService, GarminServiceError
from app.models.database_models import (
    DailyMetrics,
    SleepSession,
    Activity,
    HRVReading,
    SyncHistory,
    UserProfile,
)
from app.models.garmin_schemas import GarminSyncResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()


def get_or_create_user(db: Session, settings) -> UserProfile:
    """
    Get or create user profile.

    Args:
        db: Database session
        settings: Application settings

    Returns:
        UserProfile instance
    """
    # Use email as user_id
    user_id = settings.garmin_email

    user = db.query(UserProfile).filter_by(user_id=user_id).first()

    if not user:
        console.print("[yellow]Creating new user profile...[/yellow]")
        user = UserProfile(
            user_id=user_id,
            email=settings.garmin_email,
            name=settings.athlete_name,
            resting_heart_rate=settings.resting_heart_rate,
            max_heart_rate=settings.max_heart_rate,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        console.print(f"[green]Created user profile for {user.email}[/green]")

    return user


def store_daily_metrics(
    db: Session,
    user: UserProfile,
    metrics_data,
) -> Optional[DailyMetrics]:
    """
    Store daily metrics in database.

    Args:
        db: Database session
        user: User profile
        metrics_data: GarminDailyMetrics object

    Returns:
        DailyMetrics instance or None if no data
    """
    if not metrics_data:
        return None

    # Check if already exists
    existing = db.query(DailyMetrics).filter_by(
        user_id=user.user_id,
        date=metrics_data.date
    ).first()

    if existing:
        # Update existing record
        for key, value in metrics_data.model_dump(exclude={'date', 'raw_data'}).items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        daily_metric = DailyMetrics(
            user_id=user.user_id,
            date=metrics_data.date,
            steps=metrics_data.steps,
            distance_meters=metrics_data.distance_meters,
            calories=metrics_data.calories,
            active_minutes=metrics_data.active_minutes,
            floors_climbed=metrics_data.floors_climbed,
            resting_heart_rate=metrics_data.resting_heart_rate,
            max_heart_rate=metrics_data.max_heart_rate,
            avg_heart_rate=metrics_data.avg_heart_rate,
            hrv_sdnn=metrics_data.hrv_sdnn,
            hrv_rmssd=metrics_data.hrv_rmssd,
            stress_score=metrics_data.stress_score,
            body_battery_charged=metrics_data.body_battery_charged,
            body_battery_drained=metrics_data.body_battery_drained,
            body_battery_max=metrics_data.body_battery_max,
            body_battery_min=metrics_data.body_battery_min,
            sleep_score=metrics_data.sleep_score,
            total_sleep_minutes=metrics_data.total_sleep_minutes,
            deep_sleep_minutes=metrics_data.deep_sleep_minutes,
            light_sleep_minutes=metrics_data.light_sleep_minutes,
            rem_sleep_minutes=metrics_data.rem_sleep_minutes,
            awake_minutes=metrics_data.awake_minutes,
            vo2_max=metrics_data.vo2_max,
            fitness_age=metrics_data.fitness_age,
            weight_kg=metrics_data.weight_kg,
            body_fat_percent=metrics_data.body_fat_percent,
            bmi=metrics_data.bmi,
            hydration_ml=metrics_data.hydration_ml,
            avg_respiration_rate=metrics_data.avg_respiration_rate,
        )
        db.add(daily_metric)
        db.commit()
        db.refresh(daily_metric)
        return daily_metric


def store_sleep_data(
    db: Session,
    user: UserProfile,
    daily_metric: DailyMetrics,
    sleep_data,
) -> Optional[SleepSession]:
    """
    Store sleep session in database.

    Args:
        db: Database session
        user: User profile
        daily_metric: Associated daily metrics
        sleep_data: GarminSleepData object

    Returns:
        SleepSession instance or None if no data
    """
    if not sleep_data:
        return None

    # Check if already exists
    existing = db.query(SleepSession).filter_by(
        daily_metric_id=daily_metric.id
    ).first()

    if existing:
        # Update existing
        for key, value in sleep_data.model_dump(
            exclude={'sleep_date', 'sleep_stages_data', 'raw_data'}
        ).items():
            if value is not None:
                setattr(existing, key, value)
        existing.sleep_stages_data = sleep_data.sleep_stages_data
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        sleep_session = SleepSession(
            user_id=user.user_id,
            daily_metric_id=daily_metric.id,
            sleep_date=sleep_data.sleep_date,
            sleep_start_time=sleep_data.sleep_start_time,
            sleep_end_time=sleep_data.sleep_end_time,
            total_sleep_minutes=sleep_data.total_sleep_minutes,
            deep_sleep_minutes=sleep_data.deep_sleep_minutes,
            light_sleep_minutes=sleep_data.light_sleep_minutes,
            rem_sleep_minutes=sleep_data.rem_sleep_minutes,
            awake_minutes=sleep_data.awake_minutes,
            sleep_score=sleep_data.sleep_score,
            sleep_quality=sleep_data.sleep_quality.value if sleep_data.sleep_quality else None,
            restlessness=sleep_data.restlessness,
            avg_heart_rate=sleep_data.avg_heart_rate,
            min_heart_rate=sleep_data.min_heart_rate,
            max_heart_rate=sleep_data.max_heart_rate,
            avg_hrv=sleep_data.avg_hrv,
            avg_respiration_rate=sleep_data.avg_respiration_rate,
            awakenings_count=sleep_data.awakenings_count,
            sleep_stages_data=sleep_data.sleep_stages_data,
        )
        db.add(sleep_session)
        db.commit()
        db.refresh(sleep_session)
        return sleep_session


def store_activity(
    db: Session,
    user: UserProfile,
    activity_data,
) -> Optional[Activity]:
    """
    Store activity in database.

    Args:
        db: Database session
        user: User profile
        activity_data: GarminActivity object

    Returns:
        Activity instance or None if no data
    """
    if not activity_data:
        return None

    # Check if already exists
    existing = db.query(Activity).filter_by(
        garmin_activity_id=activity_data.garmin_activity_id
    ).first()

    if existing:
        # Update existing
        for key, value in activity_data.model_dump(
            exclude={'garmin_activity_id', 'raw_data', 'hr_zones_data'}
        ).items():
            if value is not None:
                setattr(existing, key, value)
        existing.hr_zones_data = activity_data.hr_zones_data
        existing.raw_activity_data = activity_data.raw_data
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        activity = Activity(
            user_id=user.user_id,
            garmin_activity_id=activity_data.garmin_activity_id,
            activity_date=activity_data.activity_date,
            start_time=activity_data.start_time,
            activity_type=activity_data.activity_type,
            activity_name=activity_data.activity_name,
            duration_seconds=activity_data.duration_seconds,
            duration_minutes=activity_data.duration_minutes,
            distance_meters=activity_data.distance_meters,
            avg_heart_rate=activity_data.avg_heart_rate,
            max_heart_rate=activity_data.max_heart_rate,
            avg_pace_per_km=activity_data.avg_pace_per_km,
            avg_speed_kmh=activity_data.avg_speed_kmh,
            max_speed_kmh=activity_data.max_speed_kmh,
            calories=activity_data.calories,
            elevation_gain_meters=activity_data.elevation_gain_meters,
            elevation_loss_meters=activity_data.elevation_loss_meters,
            training_effect_aerobic=activity_data.training_effect_aerobic,
            training_effect_anaerobic=activity_data.training_effect_anaerobic,
            training_load=activity_data.training_load,
            recovery_time_hours=activity_data.recovery_time_hours,
            avg_power=activity_data.avg_power,
            max_power=activity_data.max_power,
            normalized_power=activity_data.normalized_power,
            avg_cadence=activity_data.avg_cadence,
            max_cadence=activity_data.max_cadence,
            avg_stride_length=activity_data.avg_stride_length,
            avg_vertical_oscillation=activity_data.avg_vertical_oscillation,
            avg_ground_contact_time=activity_data.avg_ground_contact_time,
            intensity_factor=activity_data.intensity_factor,
            hr_zones_data=activity_data.hr_zones_data,
            notes=activity_data.notes,
            perceived_exertion=activity_data.perceived_exertion,
            temperature_celsius=activity_data.temperature_celsius,
            weather_condition=activity_data.weather_condition,
            raw_activity_data=activity_data.raw_data,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity


def store_hrv_readings(
    db: Session,
    user: UserProfile,
    daily_metric: DailyMetrics,
    hrv_readings: list,
) -> int:
    """
    Store HRV readings in database.

    Args:
        db: Database session
        user: User profile
        daily_metric: Associated daily metrics
        hrv_readings: List of GarminHRVReading objects

    Returns:
        Number of readings stored
    """
    count = 0
    for hrv_data in hrv_readings:
        # Check if already exists
        existing = db.query(HRVReading).filter_by(
            user_id=user.user_id,
            reading_date=hrv_data.reading_date,
            reading_time=hrv_data.reading_time,
        ).first()

        if not existing:
            hrv_reading = HRVReading(
                user_id=user.user_id,
                daily_metric_id=daily_metric.id,
                reading_date=hrv_data.reading_date,
                reading_time=hrv_data.reading_time,
                reading_type=hrv_data.reading_type,
                hrv_sdnn=hrv_data.hrv_sdnn,
                hrv_rmssd=hrv_data.hrv_rmssd,
                hrv_pnn50=hrv_data.hrv_pnn50,
                avg_heart_rate=hrv_data.avg_heart_rate,
                status=hrv_data.status.value if hrv_data.status else None,
            )
            db.add(hrv_reading)
            count += 1

    if count > 0:
        db.commit()

    return count


def sync_date_range(
    start_date: date,
    end_date: date,
    skip_activities: bool = False,
) -> GarminSyncResult:
    """
    Sync Garmin data for a date range.

    Args:
        start_date: Start date
        end_date: End date
        skip_activities: Skip activity sync (faster)

    Returns:
        GarminSyncResult with sync statistics
    """
    settings = get_settings()
    sync_started = datetime.utcnow()

    result = GarminSyncResult(
        sync_type="manual",
        start_date=start_date,
        end_date=end_date,
        sync_started_at=sync_started,
    )

    console.print(f"\n[bold blue]Starting Garmin data sync[/bold blue]")
    console.print(f"Date range: {start_date} to {end_date}")
    console.print(f"Skip activities: {skip_activities}\n")

    try:
        # Initialize database
        init_db()

        # Connect to Garmin
        with GarminService(settings) as garmin:
            console.print("[green]✓[/green] Connected to Garmin Connect\n")

            # Get database session
            with get_db_context() as db:
                user = get_or_create_user(db, settings)

                # Calculate total days
                total_days = (end_date - start_date).days + 1

                # Progress tracking
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        f"Syncing {total_days} days...",
                        total=total_days
                    )

                    # Sync each day
                    current_date = start_date
                    while current_date <= end_date:
                        progress.update(
                            task,
                            description=f"Syncing {current_date.isoformat()}..."
                        )

                        try:
                            # Fetch daily metrics
                            metrics = garmin.fetch_daily_metrics(current_date)
                            if metrics:
                                daily_metric = store_daily_metrics(db, user, metrics)
                                result.daily_metrics_synced += 1

                                # Fetch sleep data
                                sleep_data = garmin.fetch_sleep_data(current_date)
                                if sleep_data:
                                    store_sleep_data(db, user, daily_metric, sleep_data)
                                    result.sleep_sessions_synced += 1

                                # Fetch HRV readings
                                hrv_readings = garmin.fetch_hrv_readings(current_date)
                                if hrv_readings:
                                    count = store_hrv_readings(
                                        db, user, daily_metric, hrv_readings
                                    )
                                    result.hrv_readings_synced += count

                            # Fetch activities if not skipped
                            if not skip_activities:
                                activities = garmin.fetch_activities(
                                    current_date,
                                    current_date
                                )
                                for activity_data in activities:
                                    store_activity(db, user, activity_data)
                                    result.activities_synced += 1

                            result.records_synced += 1

                        except Exception as e:
                            error_msg = f"Error syncing {current_date}: {str(e)}"
                            result.errors.append(error_msg)
                            result.records_failed += 1
                            logger.error(error_msg)

                        # Move to next day
                        current_date += timedelta(days=1)
                        progress.update(task, advance=1)

                # Update user sync time
                user.last_sync_at = datetime.utcnow()
                db.commit()

        result.sync_completed_at = datetime.utcnow()
        result.success = result.records_failed == 0

        # Store sync history
        with get_db_context() as db:
            sync_history = SyncHistory(
                user_id=user.user_id,
                sync_type=result.sync_type,
                sync_status="completed" if result.success else "partial",
                data_start_date=start_date,
                data_end_date=end_date,
                sync_started_at=result.sync_started_at,
                sync_completed_at=result.sync_completed_at,
                duration_seconds=int(
                    (result.sync_completed_at - result.sync_started_at).total_seconds()
                ),
                records_synced=result.records_synced,
                records_failed=result.records_failed,
                synced_data_types={
                    "daily_metrics": result.daily_metrics_synced,
                    "sleep_sessions": result.sleep_sessions_synced,
                    "activities": result.activities_synced,
                    "hrv_readings": result.hrv_readings_synced,
                },
                error_message="; ".join(result.errors) if result.errors else None,
            )
            db.add(sync_history)
            db.commit()

    except GarminServiceError as e:
        result.success = False
        result.errors.append(str(e))
        console.print(f"\n[bold red]Sync failed:[/bold red] {e}")
    except Exception as e:
        result.success = False
        result.errors.append(str(e))
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}")
        logger.exception("Sync failed with unexpected error")

    return result


def print_sync_summary(result: GarminSyncResult) -> None:
    """Print sync results summary."""
    console.print("\n[bold]Sync Summary[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("Daily Metrics", str(result.daily_metrics_synced))
    table.add_row("Sleep Sessions", str(result.sleep_sessions_synced))
    table.add_row("Activities", str(result.activities_synced))
    table.add_row("HRV Readings", str(result.hrv_readings_synced))
    table.add_row("Total Records", str(result.records_synced))
    table.add_row("Failed", str(result.records_failed), style="red" if result.records_failed > 0 else "green")

    console.print(table)

    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  - {error}")

    if result.success:
        console.print("\n[bold green]✓ Sync completed successfully![/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Sync completed with errors[/bold yellow]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manually sync Garmin Connect data to database"
    )

    # Date range options (mutually exclusive)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--start-date",
        type=date.fromisoformat,
        help="Start date (YYYY-MM-DD)",
    )
    date_group.add_argument(
        "--days",
        type=int,
        help="Number of days to sync (from today backwards)",
    )
    date_group.add_argument(
        "--today",
        action="store_true",
        help="Sync today only",
    )

    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        help="End date (YYYY-MM-DD, required with --start-date)",
    )

    parser.add_argument(
        "--skip-activities",
        action="store_true",
        help="Skip activity sync (faster)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine date range
    if args.today:
        start_date = end_date = date.today()
    elif args.days:
        end_date = date.today()
        start_date = end_date - timedelta(days=args.days - 1)
    else:
        start_date = args.start_date
        if not args.end_date:
            parser.error("--end-date is required when using --start-date")
        end_date = args.end_date

    # Validate date range
    if start_date > end_date:
        console.print("[bold red]Error:[/bold red] Start date must be before end date")
        sys.exit(1)

    if end_date > date.today():
        console.print("[bold red]Error:[/bold red] End date cannot be in the future")
        sys.exit(1)

    # Run sync
    try:
        result = sync_date_range(
            start_date=start_date,
            end_date=end_date,
            skip_activities=args.skip_activities,
        )
        print_sync_summary(result)

        # Exit with error code if sync failed
        sys.exit(0 if result.success else 1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Sync interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {e}")
        logger.exception("Fatal error in sync script")
        sys.exit(1)


if __name__ == "__main__":
    main()
