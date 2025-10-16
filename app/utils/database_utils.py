"""
Database utility functions for Garmin AI Training Optimizer.

Provides helper functions for common database operations:
- User management (get or create)
- Generic get_or_create patterns
- Data validation
- Cleanup operations
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.database_models import (
    UserProfile, DailyMetrics, Base
)

T = TypeVar('T', bound=Base)


def ensure_user_exists(
    db: Session,
    user_id: str,
    default_data: Optional[Dict[str, Any]] = None
) -> UserProfile:
    """
    Get existing user or create a new one.

    Args:
        db: Database session
        user_id: User ID to look up
        default_data: Optional default data for new users

    Returns:
        UserProfile instance (existing or newly created)

    Example:
        user = ensure_user_exists(db, "user_123", {
            "name": "John Doe",
            "email": "john@example.com"
        })
    """
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        # Create new user with defaults
        user_data = default_data or {}
        user_data["user_id"] = user_id

        # Set sensible defaults if not provided
        user_data.setdefault("timezone", "UTC")
        user_data.setdefault("units_system", "metric")

        user = UserProfile(**user_data)
        db.add(user)
        db.flush()

    return user


def get_or_create(
    db: Session,
    model: Type[T],
    defaults: Optional[Dict[str, Any]] = None,
    **kwargs
) -> tuple[T, bool]:
    """
    Generic get_or_create helper for any model.

    Args:
        db: Database session
        model: SQLAlchemy model class
        defaults: Dictionary of default values for creation
        **kwargs: Filter criteria for lookup

    Returns:
        Tuple of (instance, created) where created is True if newly created

    Example:
        metrics, created = get_or_create(
            db,
            DailyMetrics,
            defaults={"steps": 10000, "calories": 2200},
            user_id="user_123",
            date=date.today()
        )
    """
    instance = db.query(model).filter_by(**kwargs).first()

    if instance:
        return instance, False

    # Create new instance
    params = kwargs.copy()
    if defaults:
        params.update(defaults)

    instance = model(**params)
    db.add(instance)

    try:
        db.flush()
        return instance, True
    except IntegrityError:
        # Another transaction created it; fetch it
        db.rollback()
        instance = db.query(model).filter_by(**kwargs).first()
        return instance, False


def update_or_create(
    db: Session,
    model: Type[T],
    lookup_fields: Dict[str, Any],
    update_data: Dict[str, Any]
) -> tuple[T, bool]:
    """
    Update existing record or create new one (upsert).

    Args:
        db: Database session
        model: SQLAlchemy model class
        lookup_fields: Fields to use for lookup
        update_data: Data to update or use for creation

    Returns:
        Tuple of (instance, created) where created is True if newly created

    Example:
        metrics, created = update_or_create(
            db,
            DailyMetrics,
            lookup_fields={"user_id": "user_123", "date": date.today()},
            update_data={"steps": 12000, "calories": 2400}
        )
    """
    instance = db.query(model).filter_by(**lookup_fields).first()

    if instance:
        # Update existing
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        # Update timestamp if available
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()

        db.flush()
        return instance, False
    else:
        # Create new
        params = lookup_fields.copy()
        params.update(update_data)
        instance = model(**params)
        db.add(instance)
        db.flush()
        return instance, True


def bulk_get_or_create(
    db: Session,
    model: Type[T],
    records: list[Dict[str, Any]],
    lookup_fields: list[str],
    batch_size: int = 100
) -> tuple[int, int]:
    """
    Bulk get_or_create operation for efficient batch processing.

    Args:
        db: Database session
        model: SQLAlchemy model class
        records: List of dictionaries with record data
        lookup_fields: Fields to use for duplicate detection
        batch_size: Number of records to process per batch

    Returns:
        Tuple of (created_count, updated_count)

    Example:
        created, updated = bulk_get_or_create(
            db,
            DailyMetrics,
            records=[
                {"user_id": "u1", "date": date(2025, 1, 1), "steps": 10000},
                {"user_id": "u1", "date": date(2025, 1, 2), "steps": 12000},
            ],
            lookup_fields=["user_id", "date"]
        )
    """
    created_count = 0
    updated_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        for record in batch:
            # Build lookup filter
            lookup = {field: record[field] for field in lookup_fields if field in record}

            instance = db.query(model).filter_by(**lookup).first()

            if instance:
                # Update existing
                for key, value in record.items():
                    if hasattr(instance, key) and key not in lookup_fields:
                        setattr(instance, key, value)
                if hasattr(instance, 'updated_at'):
                    instance.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new
                instance = model(**record)
                db.add(instance)
                created_count += 1

        db.flush()

    return created_count, updated_count


def delete_user_data(db: Session, user_id: str) -> Dict[str, int]:
    """
    Delete all data for a user (cascade delete).

    WARNING: This permanently deletes all user data!

    Args:
        db: Database session
        user_id: User ID to delete

    Returns:
        Dictionary with count of deleted records per table

    Example:
        deleted = delete_user_data(db, "user_123")
        print(f"Deleted {deleted['total']} total records")
    """
    counts = {}

    # Deleting user will cascade to all related records
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if user:
        # Count related records before deletion
        counts["daily_metrics"] = len(user.daily_metrics)
        counts["activities"] = len(user.activities)
        counts["training_plans"] = len(user.training_plans)
        counts["sync_history"] = len(user.sync_history)

        # Delete user (cascades to all related records)
        db.delete(user)
        db.flush()

        counts["total"] = sum(counts.values())
    else:
        counts["total"] = 0

    return counts


def validate_date_range(start_date: date, end_date: date, max_days: int = 365) -> bool:
    """
    Validate that a date range is reasonable.

    Args:
        start_date: Start date
        end_date: End date
        max_days: Maximum allowed days in range

    Returns:
        True if valid, False otherwise
    """
    if start_date > end_date:
        return False

    days_diff = (end_date - start_date).days
    if days_diff > max_days:
        return False

    return True


def get_date_range_for_period(
    period: str,
    reference_date: Optional[date] = None
) -> tuple[date, date]:
    """
    Get start and end dates for common time periods.

    Args:
        period: One of 'today', 'yesterday', 'week', 'month', 'year'
        reference_date: Reference date (defaults to today)

    Returns:
        Tuple of (start_date, end_date)

    Example:
        start, end = get_date_range_for_period('week')
        # Returns Monday to Sunday of current week
    """
    ref = reference_date or date.today()

    if period == 'today':
        return ref, ref

    elif period == 'yesterday':
        yesterday = ref - timedelta(days=1)
        return yesterday, yesterday

    elif period == 'week':
        # Monday to Sunday of current week
        monday = ref - timedelta(days=ref.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    elif period == 'last_week':
        # Previous week (Monday to Sunday)
        last_monday = ref - timedelta(days=ref.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return last_monday, last_sunday

    elif period == 'month':
        # Current month (1st to last day)
        first_day = ref.replace(day=1)
        if ref.month == 12:
            last_day = ref.replace(day=31)
        else:
            next_month = ref.replace(month=ref.month + 1, day=1)
            last_day = next_month - timedelta(days=1)
        return first_day, last_day

    elif period == 'year':
        # Current year (Jan 1 to Dec 31)
        first_day = ref.replace(month=1, day=1)
        last_day = ref.replace(month=12, day=31)
        return first_day, last_day

    elif period == 'last_7_days':
        return ref - timedelta(days=7), ref

    elif period == 'last_30_days':
        return ref - timedelta(days=30), ref

    elif period == 'last_90_days':
        return ref - timedelta(days=90), ref

    else:
        raise ValueError(f"Unknown period: {period}")


def calculate_pagination(
    total_count: int,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Calculate pagination metadata.

    Args:
        total_count: Total number of records
        page: Current page number (1-indexed)
        page_size: Number of records per page

    Returns:
        Dictionary with pagination metadata

    Example:
        pagination = calculate_pagination(total_count=100, page=2, page_size=20)
        # Returns: {
        #     "page": 2,
        #     "page_size": 20,
        #     "total_pages": 5,
        #     "total_count": 100,
        #     "has_next": True,
        #     "has_prev": True,
        #     "offset": 20
        # }
    """
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    offset = (page - 1) * page_size

    return {
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "offset": offset
    }


def safe_divide(numerator: Optional[float], denominator: Optional[float], default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling None and division by zero.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division fails

    Returns:
        Division result or default value
    """
    if numerator is None or denominator is None or denominator == 0:
        return default
    return numerator / denominator


def safe_percentage(value: Optional[float], total: Optional[float], decimals: int = 1) -> Optional[float]:
    """
    Calculate percentage safely.

    Args:
        value: Part value
        total: Total value
        decimals: Number of decimal places

    Returns:
        Percentage or None if calculation not possible
    """
    if value is None or total is None or total == 0:
        return None
    return round((value / total) * 100, decimals)


def sanitize_for_json(data: Any) -> Any:
    """
    Sanitize data for JSON serialization.

    Converts date, datetime, and other non-JSON types to strings.

    Args:
        data: Data to sanitize

    Returns:
        JSON-serializable version of data
    """
    if isinstance(data, (date, datetime)):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: sanitize_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif hasattr(data, '__dict__'):
        # SQLAlchemy model instance
        return {key: sanitize_for_json(value)
                for key, value in data.__dict__.items()
                if not key.startswith('_')}
    else:
        return data


def create_content_hash(data: Dict[str, Any]) -> str:
    """
    Create SHA-256 hash of data for caching.

    Args:
        data: Dictionary to hash

    Returns:
        Hexadecimal hash string
    """
    import hashlib
    import json

    # Sort keys for consistent hashing
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


def chunk_list(items: list, chunk_size: int):
    """
    Split a list into chunks of specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Yields:
        Chunks of the original list

    Example:
        for chunk in chunk_list(range(100), 20):
            process_batch(chunk)
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def format_duration(minutes: Optional[float]) -> str:
    """
    Format duration in minutes to human-readable string.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string (e.g., "1h 30m")

    Example:
        format_duration(90)  # "1h 30m"
        format_duration(45)  # "45m"
    """
    if minutes is None:
        return "N/A"

    hours = int(minutes // 60)
    mins = int(minutes % 60)

    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"


def format_pace(pace_per_km: Optional[float]) -> str:
    """
    Format pace in minutes per km to MM:SS format.

    Args:
        pace_per_km: Pace in minutes per kilometer

    Returns:
        Formatted string (e.g., "5:30")

    Example:
        format_pace(5.5)  # "5:30"
    """
    if pace_per_km is None:
        return "N/A"

    minutes = int(pace_per_km)
    seconds = int((pace_per_km - minutes) * 60)

    return f"{minutes}:{seconds:02d}"


def meters_to_km(meters: Optional[float], decimals: int = 2) -> Optional[float]:
    """Convert meters to kilometers."""
    if meters is None:
        return None
    return round(meters / 1000, decimals)


def seconds_to_minutes(seconds: Optional[int], decimals: int = 1) -> Optional[float]:
    """Convert seconds to minutes."""
    if seconds is None:
        return None
    return round(seconds / 60, decimals)
