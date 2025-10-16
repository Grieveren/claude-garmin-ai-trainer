# Garmin Integration Quick Start Guide

## 1. Prerequisites

- Python 3.12+ installed
- Garmin Connect account with credentials
- Internet connection

## 2. Installation

```bash
# Navigate to project directory
cd /Users/brettgray/Coding/Garmin\ AI

# Install dependencies
pip install -r requirements.txt
```

## 3. Configuration

Create `.env` file in project root:

```env
# Garmin Connect Credentials
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Database
DATABASE_URL=sqlite:///./data/training_data.db

# Claude AI
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Security
SECRET_KEY=generate-a-32-character-secret-key-here

# Athlete Profile
ATHLETE_NAME=Your Name
ATHLETE_AGE=30
ATHLETE_GENDER=male
MAX_HEART_RATE=190
RESTING_HEART_RATE=50
TRAINING_GOAL=Your training goal
```

## 4. Initialize Database

```bash
python scripts/init_database.py
```

## 5. Sync Your Data

### Sync Last 7 Days
```bash
python scripts/sync_garmin_data.py --days 7
```

### Sync Specific Date Range
```bash
python scripts/sync_garmin_data.py \
  --start-date 2025-01-01 \
  --end-date 2025-01-15
```

### Sync Today Only
```bash
python scripts/sync_garmin_data.py --today
```

### Fast Sync (Skip Activities)
```bash
python scripts/sync_garmin_data.py --days 7 --skip-activities
```

## 6. Verify Data

```python
from app.database import get_db_context
from app.models.database_models import DailyMetrics
from datetime import date

with get_db_context() as db:
    # Get today's metrics
    metrics = db.query(DailyMetrics).filter_by(
        date=date.today()
    ).first()

    if metrics:
        print(f"Steps: {metrics.steps}")
        print(f"Resting HR: {metrics.resting_heart_rate}")
        print(f"HRV: {metrics.hrv_sdnn}")
        print(f"Sleep Score: {metrics.sleep_score}")
    else:
        print("No data found for today")
```

## 7. Programmatic Usage

```python
from app.services.garmin_service import GarminService
from app.core.config import get_settings
from datetime import date, timedelta

settings = get_settings()

# Use as context manager
with GarminService(settings) as garmin:
    # Fetch today's metrics
    metrics = garmin.fetch_daily_metrics(date.today())
    print(f"Steps today: {metrics.steps}")

    # Fetch last 7 days of activities
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    activities = garmin.fetch_activities(start_date, end_date)
    print(f"Activities this week: {len(activities)}")

    # Fetch HRV readings
    hrv_readings = garmin.fetch_hrv_readings(date.today())
    for reading in hrv_readings:
        print(f"HRV ({reading.reading_type}): {reading.hrv_sdnn}")
```

## 8. Common Tasks

### Check Sync History
```python
from app.database import get_db_context
from app.models.database_models import SyncHistory

with get_db_context() as db:
    recent_syncs = db.query(SyncHistory).order_by(
        SyncHistory.sync_started_at.desc()
    ).limit(5).all()

    for sync in recent_syncs:
        print(f"{sync.sync_started_at}: {sync.records_synced} records")
```

### Clear Token Cache
```bash
rm -rf ~/.garmin_tokens/
```

### View Logs
```bash
tail -f logs/training_optimizer.log
```

## 9. Testing

```bash
# Run all tests
pytest tests/test_garmin_service.py -v

# Run unit tests only
pytest tests/test_garmin_service.py -v -m unit
```

## 10. Troubleshooting

### Authentication Issues
```bash
# Clear token cache and try again
rm -rf ~/.garmin_tokens/
python scripts/sync_garmin_data.py --today
```

### Rate Limit Errors
- Wait 1 hour
- Use `--skip-activities` flag
- Reduce sync frequency

### Missing Data
- Check Garmin Connect app
- Try syncing previous day
- Wait for Garmin to sync from device

## Example Output

```
Starting Garmin data sync
Date range: 2025-01-10 to 2025-01-16
Skip activities: False

✓ Connected to Garmin Connect

Creating new user profile...
Created user profile for test@example.com

Syncing 7 days... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

Sync Summary
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric          ┃ Count ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Daily Metrics   │     7 │
│ Sleep Sessions  │     7 │
│ Activities      │    12 │
│ HRV Readings    │    14 │
│ Total Records   │     7 │
│ Failed          │     0 │
└─────────────────┴───────┘

✓ Sync completed successfully!
```

## Next Steps

1. Set up automated daily sync (Phase 2 Track 2B)
2. Integrate with AI analysis (Phase 3)
3. Build training recommendations
4. Create visualization dashboard

## Support

- Full Documentation: `docs/PHASE2_GARMIN_INTEGRATION.md`
- Completion Summary: `PHASE2_COMPLETION_SUMMARY.md`
- Test Suite: `tests/test_garmin_service.py`

## Quick Reference

| Command | Description |
|---------|-------------|
| `--days N` | Sync last N days |
| `--start-date YYYY-MM-DD` | Start of date range |
| `--end-date YYYY-MM-DD` | End of date range |
| `--today` | Sync today only |
| `--skip-activities` | Skip activities (faster) |
| `--verbose` | Enable debug logging |

---

**Status**: ✅ Ready to use
**Version**: Phase 2 Track 2A Complete
