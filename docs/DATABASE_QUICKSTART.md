# Database Quick Start Guide

## Overview

This guide will help you set up and start using the Garmin AI Training System database.

## Prerequisites

- Python 3.10+
- SQLAlchemy 2.0+
- Alembic (for migrations)

## Installation

```bash
# Install dependencies
pip install sqlalchemy alembic psycopg2-binary  # For PostgreSQL
# OR
pip install sqlalchemy alembic  # For SQLite (default)
```

## Quick Start

### 1. Initialize Empty Database

```bash
# Create all tables
python scripts/init_database.py
```

This creates an empty database with all 12 tables and proper indexes.

### 2. Initialize with Sample Data

```bash
# Create tables AND sample data for testing
python scripts/init_database.py --sample
```

This creates:
- 1 sample user (John Doe)
- 30 days of daily health metrics
- 14 days of workout activities
- 1 training plan with 8 planned workouts
- Daily readiness assessments
- Training load tracking

### 3. Reset Database (Development Only)

```bash
# Delete all data and recreate tables
python scripts/init_database.py --reset
```

**⚠️ WARNING**: This deletes ALL data. Use only in development!

## Database Configuration

### SQLite (Default)

The default configuration uses SQLite with the database file at:
```
./garmin_training.db
```

No additional setup required!

### PostgreSQL (Production)

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost/garmin_training"
```

Or create a `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost/garmin_training
```

## Usage Examples

### Python Code

```python
from app.database import get_db_context
from app.models import UserProfile, DailyMetrics
from datetime import date

# Create a new user
with get_db_context() as db:
    user = UserProfile(
        user_id="user123",
        name="Jane Smith",
        email="jane@example.com",
        height_cm=165.0,
        weight_kg=60.0
    )
    db.add(user)

# Query data
with get_db_context() as db:
    # Get user
    user = db.query(UserProfile).filter_by(user_id="user123").first()

    # Get today's metrics
    today_metrics = db.query(DailyMetrics).filter_by(
        user_id="user123",
        date=date.today()
    ).first()

    # Get recent activities
    activities = db.query(Activity).filter(
        Activity.user_id == "user123",
        Activity.activity_date >= date.today() - timedelta(days=7)
    ).order_by(Activity.activity_date.desc()).all()
```

### FastAPI Integration

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

@app.get("/metrics/today")
def get_today_metrics(db: Session = Depends(get_db)):
    metrics = db.query(DailyMetrics).filter_by(
        user_id="user123",
        date=date.today()
    ).first()
    return metrics
```

## Database Migrations with Alembic

### Setup Alembic

```bash
# Initialize Alembic (already done)
alembic init alembic
```

### Apply Initial Migration

```bash
# Apply the initial schema migration
alembic upgrade head
```

### Create New Migration

When you modify models:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to activities"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Schema Overview

### Core Tables

1. **user_profile** - User accounts and Garmin integration
2. **daily_metrics** - Daily health metrics (HRV, sleep, steps, etc.)
3. **sleep_sessions** - Detailed sleep data with stages
4. **activities** - Workout activities from Garmin
5. **heart_rate_samples** - Intra-workout HR time-series
6. **hrv_readings** - HRV measurements throughout the day
7. **training_plans** - Goal-based training programs
8. **planned_workouts** - Daily workout prescriptions
9. **daily_readiness** - AI-generated readiness scores
10. **ai_analysis_cache** - Cached AI responses
11. **training_load_tracking** - ACWR and training load monitoring
12. **sync_history** - Garmin sync audit trail

See [database_schema.md](database_schema.md) for complete documentation.

## Common Queries

### Get User Dashboard Data

```python
from sqlalchemy.orm import joinedload

with get_db_context() as db:
    metrics = db.query(DailyMetrics).options(
        joinedload(DailyMetrics.sleep_session),
        joinedload(DailyMetrics.daily_readiness),
        joinedload(DailyMetrics.training_load)
    ).filter_by(
        user_id="user123",
        date=date.today()
    ).first()

    print(f"HRV: {metrics.hrv_sdnn}")
    print(f"Sleep Score: {metrics.sleep_score}")
    print(f"Readiness: {metrics.daily_readiness.readiness_score}")
    print(f"ACWR: {metrics.training_load.acwr}")
```

### Get Weekly Training Summary

```python
from sqlalchemy import func
from datetime import date, timedelta

with get_db_context() as db:
    week_start = date.today() - timedelta(days=7)

    summary = db.query(
        func.count(Activity.id).label('workouts'),
        func.sum(Activity.duration_minutes).label('total_minutes'),
        func.sum(Activity.distance_meters).label('total_distance'),
        func.sum(Activity.training_load).label('total_load')
    ).filter(
        Activity.user_id == "user123",
        Activity.activity_date >= week_start
    ).first()

    print(f"This week: {summary.workouts} workouts, "
          f"{summary.total_minutes:.0f} minutes, "
          f"{summary.total_distance/1000:.1f} km")
```

### Get Training Plan Progress

```python
with get_db_context() as db:
    plan = db.query(TrainingPlan).filter_by(
        user_id="user123",
        is_active=True
    ).first()

    total_workouts = len(plan.planned_workouts)
    completed = sum(1 for w in plan.planned_workouts if w.was_completed)

    print(f"{plan.name}: {completed}/{total_workouts} completed "
          f"({completed/total_workouts*100:.1f}%)")
```

### Check Overtraining Risk

```python
with get_db_context() as db:
    recent_load = db.query(TrainingLoadTracking).filter(
        TrainingLoadTracking.user_id == "user123",
        TrainingLoadTracking.tracking_date >= date.today() - timedelta(days=14)
    ).order_by(TrainingLoadTracking.tracking_date.desc()).all()

    high_risk_days = [
        load for load in recent_load
        if load.acwr and load.acwr > 1.5
    ]

    if high_risk_days:
        print(f"⚠️ High injury risk detected on {len(high_risk_days)} days")
        print(f"Latest ACWR: {recent_load[0].acwr:.2f}")
```

## Database Performance Tips

### 1. Use Indexes Efficiently

All foreign keys and date columns are indexed. Always filter by these fields:

```python
# Good - Uses indexes
db.query(DailyMetrics).filter_by(user_id="user123", date=today)

# Bad - Doesn't use indexes efficiently
db.query(DailyMetrics).filter(DailyMetrics.steps > 10000)
```

### 2. Eager Loading for Relationships

Use `joinedload` to avoid N+1 queries:

```python
# Good - Single query with joins
db.query(DailyMetrics).options(
    joinedload(DailyMetrics.sleep_session),
    joinedload(DailyMetrics.daily_readiness)
).filter_by(user_id="user123")

# Bad - N+1 queries
metrics = db.query(DailyMetrics).filter_by(user_id="user123").all()
for m in metrics:
    print(m.sleep_session.sleep_score)  # Separate query each time!
```

### 3. Batch Operations

Use bulk operations for multiple inserts:

```python
# Good - Single transaction
with get_db_context() as db:
    samples = [
        HeartRateSample(activity_id=1, timestamp=t, heart_rate=hr)
        for t, hr in hr_data
    ]
    db.bulk_save_objects(samples)

# Bad - Multiple transactions
for t, hr in hr_data:
    with get_db_context() as db:
        db.add(HeartRateSample(activity_id=1, timestamp=t, heart_rate=hr))
```

### 4. Limit Result Sets

Always use `LIMIT` for pagination:

```python
# Good - Limits results
db.query(Activity).filter_by(user_id="user123")\
    .order_by(Activity.activity_date.desc())\
    .limit(20).all()
```

### 5. Cache Expensive Queries

Use the `ai_analysis_cache` table for AI responses and expensive computations.

## Backup and Restore

### SQLite Backup

```bash
# Backup
cp garmin_training.db garmin_training_backup_$(date +%Y%m%d).db

# Restore
cp garmin_training_backup_20251015.db garmin_training.db
```

### PostgreSQL Backup

```bash
# Backup
pg_dump -U user garmin_training > backup_$(date +%Y%m%d).sql

# Restore
psql -U user garmin_training < backup_20251015.sql
```

## Troubleshooting

### "Table already exists" Error

```bash
# Option 1: Drop and recreate (development only)
python scripts/init_database.py --reset

# Option 2: Use Alembic to manage schema
alembic stamp head  # Mark current state
```

### Foreign Key Constraint Violations

Ensure parent records exist before creating child records:

```python
# Create user first
user = UserProfile(user_id="user123", name="John")
db.add(user)
db.flush()  # Get user.id

# Then create dependent record
metrics = DailyMetrics(user_id=user.user_id, date=date.today())
db.add(metrics)
```

### Slow Queries

Enable SQL logging to identify slow queries:

```bash
export SQL_ECHO=true
```

Or in code:
```python
from app.database import engine
engine.echo = True
```

Then use `EXPLAIN ANALYZE`:
```sql
EXPLAIN QUERY PLAN
SELECT * FROM daily_metrics WHERE user_id = 'user123' AND date = '2025-10-15';
```

### Database Locked (SQLite)

SQLite doesn't support high concurrency. Consider PostgreSQL for production:

```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt install postgresql  # Linux

# Create database
createdb garmin_training

# Set DATABASE_URL
export DATABASE_URL="postgresql://localhost/garmin_training"
```

## Next Steps

1. ✅ Database created and initialized
2. 📊 Create data repositories (see `docs/repositories.md`)
3. 🔄 Implement Garmin sync service
4. 🤖 Build AI analysis engine
5. 🚀 Create REST API endpoints

## Resources

- [Database Schema Documentation](database_schema.md)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI Database Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)

## Support

For issues or questions:
1. Check the [database_schema.md](database_schema.md) for detailed schema documentation
2. Review query examples in this guide
3. Enable SQL logging to debug queries
4. Check SQLAlchemy documentation for advanced features
