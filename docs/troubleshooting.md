# Troubleshooting Guide

Common issues and solutions for the AI Training Optimizer.

---

## Table of Contents

1. [Garmin Connection Issues](#garmin-connection-issues)
2. [Database Errors](#database-errors)
3. [API Errors](#api-errors)
4. [Configuration Issues](#configuration-issues)
5. [Performance Issues](#performance-issues)
6. [Notification Issues](#notification-issues)
7. [AI Analysis Issues](#ai-analysis-issues)

---

## Garmin Connection Issues

### Issue 1: Garmin Login Fails

**Symptoms**:
```
GarminConnectAuthenticationError: Authentication failed
```

**Possible Causes**:
- Incorrect credentials
- 2FA enabled on account
- Account locked or suspended
- Garmin API changed (library broken)
- Network connectivity issues

**Solutions**:

1. **Verify credentials**:
   ```bash
   # Check .env file
   cat .env | grep GARMIN

   # Ensure no extra spaces or quotes
   GARMIN_EMAIL=email@example.com  # CORRECT
   GARMIN_EMAIL="email@example.com"  # WRONG (remove quotes)
   ```

2. **Disable 2FA**:
   - Go to: https://connect.garmin.com/modern/settings/security
   - Disable two-factor authentication
   - Library doesn't support 2FA

3. **Test login manually**:
   - Try logging into https://connect.garmin.com
   - If manual login works, library issue
   - If manual login fails, account issue

4. **Check library status**:
   ```bash
   # Update to latest version
   pip install --upgrade garminconnect

   # Check GitHub issues
   # Visit: https://github.com/cyberjunky/python-garminconnect/issues
   ```

5. **Try test script**:
   ```bash
   python scripts/test_garmin_connection.py
   # Shows detailed error messages
   ```

**Workaround - Manual Data Export**:
If Garmin API is broken:
1. Go to https://connect.garmin.com
2. Export activities as FIT files
3. Import manually:
   ```bash
   python scripts/import_fit_files.py --dir ~/Downloads/garmin_export
   ```

---

### Issue 2: garminconnect Library Broken

**Symptoms**:
```
CloudFlare protection detected
KeyError: 'activityId'
Unexpected JSON response
```

**What Happened**:
Garmin changed their API, breaking the unofficial library.

**Immediate Solutions**:

1. **Check for library updates**:
   ```bash
   pip install --upgrade garminconnect
   ```

2. **Check GitHub for fixes**:
   - Visit: https://github.com/cyberjunky/python-garminconnect
   - Look for recent issues/PRs addressing your error
   - Community often has quick fixes

3. **Try community forks**:
   ```bash
   # Example (check GitHub for current recommended fork)
   pip uninstall garminconnect
   pip install git+https://github.com/USER/python-garminconnect@fix-branch
   ```

**Long-term Solutions**:

1. **Switch to manual export workflow**:
   - Export FIT files weekly from Garmin
   - Import using: `scripts/import_fit_files.py`
   - Less convenient but reliable

2. **Use Garmin API Health Snapshots**:
   - Garmin offers data export feature
   - Download ZIP files periodically
   - Import into system

3. **Consider alternative data sources**:
   - Apple HealthKit (iOS only)
   - Strava API (if you sync Garmin → Strava)
   - Manual entry

---

### Issue 3: Data Sync Incomplete

**Symptoms**:
- Some activities missing
- HRV data not syncing
- Sleep data incomplete

**Solutions**:

1. **Check Garmin device sync**:
   - Ensure device synced to Garmin Connect
   - Open Garmin Connect app on phone
   - Verify data visible in app

2. **Run manual sync with logs**:
   ```bash
   python scripts/sync_data.py --verbose --date 2025-10-15
   # Check logs for specific errors
   ```

3. **Verify data exists in Garmin**:
   - Log into connect.garmin.com
   - Check if data visible there
   - If not in Garmin, can't sync it

4. **Re-sync specific date**:
   ```bash
   python scripts/sync_data.py --date 2025-10-15 --force
   # --force overwrites existing data
   ```

---

## Database Errors

### Issue 1: Database Locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Causes**:
- Another process accessing database
- Previous query didn't complete
- Database file permissions issue

**Solutions**:

1. **Check for running processes**:
   ```bash
   # Find processes using database
   lsof data/training_data.db  # macOS/Linux

   # Kill if needed
   kill -9 <PID>
   ```

2. **Restart application**:
   ```bash
   # Stop uvicorn (Ctrl+C)
   # Wait 5 seconds
   # Start again
   uvicorn app.main:app --reload
   ```

3. **Check file permissions**:
   ```bash
   ls -l data/training_data.db
   # Should be writable by your user

   # Fix if needed
   chmod 644 data/training_data.db
   ```

4. **Last resort - reset database**:
   ```bash
   # BACKUP FIRST
   cp data/training_data.db data/training_data.db.backup

   # Reset
   rm data/training_data.db
   python scripts/initial_setup.py
   python scripts/backfill_data.py --days 30
   ```

---

### Issue 2: Migration Errors

**Symptoms**:
```
alembic.util.exc.CommandError: Can't locate revision
sqlalchemy.exc.OperationalError: no such table
```

**Solutions**:

1. **Check current migration version**:
   ```bash
   alembic current
   ```

2. **Run pending migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Reset migrations** (destructive):
   ```bash
   # Backup data
   python scripts/export_data.py --output backup.json

   # Delete database and migrations
   rm data/training_data.db
   rm alembic/versions/*.py

   # Recreate
   alembic revision --autogenerate -m "initial schema"
   alembic upgrade head

   # Restore data
   python scripts/import_data.py --input backup.json
   ```

---

### Issue 3: Data Validation Errors

**Symptoms**:
```
IntegrityError: UNIQUE constraint failed
IntegrityError: NOT NULL constraint failed
```

**Solutions**:

1. **Check data before insert**:
   ```python
   # Example validation
   if daily_metrics.date is None:
       logger.error("Date cannot be null")
       return

   # Check for duplicates
   existing = session.query(DailyMetrics).filter_by(date=date).first()
   if existing:
       # Update instead of insert
       existing.update(new_data)
   ```

2. **Clean invalid data**:
   ```bash
   python scripts/clean_database.py --fix-duplicates --remove-nulls
   ```

3. **Re-import with validation**:
   ```bash
   python scripts/sync_data.py --validate --date 2025-10-15
   ```

---

## API Errors

### Issue 1: Claude API Authentication Error

**Symptoms**:
```
anthropic.AuthenticationError: invalid x-api-key
anthropic.PermissionDeniedError: credit balance too low
```

**Solutions**:

1. **Verify API key**:
   ```bash
   cat .env | grep ANTHROPIC_API_KEY
   # Should start with: sk-ant-

   # Get new key from: https://console.anthropic.com/settings/keys
   ```

2. **Check billing**:
   - Visit: https://console.anthropic.com/settings/billing
   - Add payment method if missing
   - Check credit balance
   - Review spending limits

3. **Test API key**:
   ```bash
   python scripts/test_claude_connection.py
   # Will show specific error
   ```

4. **Check API status**:
   - Visit: https://status.anthropic.com
   - Ensure no outages

---

### Issue 2: Claude API Rate Limiting

**Symptoms**:
```
anthropic.RateLimitError: rate_limit_exceeded
429 Too Many Requests
```

**Solutions**:

1. **Implement backoff**:
   Already built-in, but you can adjust:
   ```bash
   # In .env
   AI_MAX_RETRIES=5
   AI_RETRY_DELAY=2  # seconds
   ```

2. **Enable caching**:
   ```bash
   # Increase cache duration
   AI_CACHE_HOURS=48  # Default is 24
   ```

3. **Reduce analysis frequency**:
   ```bash
   # Run sync less often
   SYNC_HOUR=8
   # Don't run on demand frequently
   ```

4. **Check rate limits**:
   - Visit: https://console.anthropic.com/settings/limits
   - Request higher limits if needed

---

### Issue 3: Claude API Costs Too High

**Symptoms**:
- Monthly bill exceeds $15
- Unexpected charges

**Solutions**:

1. **Enable aggressive caching**:
   ```bash
   # In .env
   AI_CACHE_HOURS=72  # Cache for 3 days
   ENABLE_PROMPT_CACHING=True  # Uses Claude's built-in caching
   ```

2. **Reduce data context**:
   ```bash
   # Limit historical data sent to AI
   AI_CONTEXT_DAYS=7  # Only send last 7 days (default: 14)
   ```

3. **Monitor usage**:
   ```bash
   # View token usage
   curl http://localhost:8000/api/analysis/token-usage

   # Check logs
   grep "Token usage" logs/training_optimizer.log
   ```

4. **Set spending alerts**:
   - Anthropic console: https://console.anthropic.com/settings/billing
   - Set monthly budget alert

5. **Reduce analysis frequency**:
   ```bash
   # Analyze every other day instead of daily
   ENABLE_DAILY_ANALYSIS=False
   # Run manually when needed
   ```

---

## Configuration Issues

### Issue 1: Environment Variables Not Loading

**Symptoms**:
- Settings use default values
- API keys not recognized
- Application can't find config

**Solutions**:

1. **Check .env file exists**:
   ```bash
   ls -la .env
   # Should be in project root
   ```

2. **Verify file is loaded**:
   ```python
   # In Python shell
   from dotenv import load_dotenv
   import os
   load_dotenv()
   print(os.getenv('ANTHROPIC_API_KEY'))
   # Should print your key
   ```

3. **Check for syntax errors**:
   ```bash
   # No spaces around =
   GOOD=value
   BAD = value  # This won't work

   # No quotes needed
   GOOD=my_value
   BAD="my_value"  # Quotes included in value
   ```

4. **Restart application**:
   Changes to .env require restart:
   ```bash
   # Ctrl+C to stop
   uvicorn app.main:app --reload
   ```

---

### Issue 2: Heart Rate Zones Incorrect

**Symptoms**:
- Zones seem too high/low
- Workout recommendations use wrong HR

**Solutions**:

1. **Recalculate max HR**:
   ```bash
   # Don't use age formula (220 - age)
   # Instead: Run hard 5K, note your max HR

   # Update .env
   MAX_HEART_RATE=<your actual max>
   ```

2. **Update resting HR**:
   ```bash
   # Measure for 7 days, average them
   RESTING_HEART_RATE=<your 7-day average>
   ```

3. **Recalculate zones**:
   ```bash
   python scripts/recalculate_zones.py
   # Updates database with new zones
   ```

4. **Manual zone override**:
   ```bash
   # In .env, set custom zones
   HR_ZONE_1_MAX=120
   HR_ZONE_2_MAX=140
   HR_ZONE_3_MAX=160
   HR_ZONE_4_MAX=175
   HR_ZONE_5_MAX=188
   ```

---

## Performance Issues

### Issue 1: Slow Data Sync

**Symptoms**:
- Sync takes >10 minutes
- Times out frequently

**Solutions**:

1. **Sync smaller date ranges**:
   ```bash
   # Instead of 90 days at once
   python scripts/backfill_data.py --days 30

   # Or one day at a time
   python scripts/sync_data.py --date 2025-10-15
   ```

2. **Check network**:
   ```bash
   # Test Garmin API speed
   time curl https://connect.garmin.com
   # Should be <2 seconds
   ```

3. **Reduce retry attempts**:
   ```bash
   # In .env
   GARMIN_MAX_RETRIES=2  # Default: 3
   GARMIN_TIMEOUT=30  # seconds
   ```

4. **Sync during off-peak**:
   - Schedule for early morning
   - Avoid peak hours (6-9 AM, 5-8 PM)

---

### Issue 2: Slow AI Analysis

**Symptoms**:
- Readiness analysis takes >60 seconds
- Dashboard loads slowly

**Solutions**:

1. **Enable caching**:
   ```bash
   AI_CACHE_HOURS=24
   ENABLE_PROMPT_CACHING=True
   ```

2. **Reduce context window**:
   ```bash
   AI_CONTEXT_DAYS=7  # Send less historical data
   ```

3. **Optimize database queries**:
   ```bash
   # Rebuild indexes
   python scripts/optimize_database.py
   ```

4. **Use faster model** (if available):
   ```bash
   AI_MODEL=claude-3-haiku-20240307  # Faster, cheaper, less accurate
   # Default: claude-sonnet-4-5-20250929
   ```

---

### Issue 3: High Memory Usage

**Symptoms**:
- System uses >2GB RAM
- Slow performance
- Out of memory errors

**Solutions**:

1. **Limit data processing**:
   ```bash
   # Process in batches
   python scripts/process_data.py --batch-size 100
   ```

2. **Clean up old data**:
   ```bash
   # Archive data older than 1 year
   python scripts/archive_old_data.py --days 365
   ```

3. **Optimize pandas usage**:
   ```python
   # Use dtype optimization
   df = pd.read_sql(..., dtype={'heart_rate': 'int16'})

   # Free memory after use
   del df
   import gc
   gc.collect()
   ```

4. **Increase system memory**:
   - Close other applications
   - Add swap space (Linux)
   - Upgrade RAM if possible

---

## Notification Issues

### Issue 1: Email Notifications Not Sending

**Symptoms**:
- No morning emails received
- Notification logs show errors

**Solutions**:

1. **Verify SMTP settings**:
   ```bash
   cat .env | grep SMTP

   # For Gmail
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

2. **Use App Password**:
   Gmail requires app-specific password:
   - Visit: https://myaccount.google.com/apppasswords
   - Create app password
   - Use that, not your regular password

3. **Test email sending**:
   ```bash
   python scripts/test_email.py --to your@email.com
   ```

4. **Check spam folder**:
   - Emails might be filtered
   - Add to safe senders list

5. **Try different SMTP**:
   ```bash
   # For Outlook/Hotmail
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587

   # For Yahoo
   SMTP_SERVER=smtp.mail.yahoo.com
   SMTP_PORT=587
   ```

---

### Issue 2: Notifications Wrong Time

**Symptoms**:
- Receive notifications at wrong time
- Timezone seems off

**Solutions**:

1. **Set correct timezone**:
   ```bash
   # In .env
   TIMEZONE=America/New_York
   # Or: Europe/London, Asia/Tokyo, etc.

   # List timezones
   python -c "import pytz; print('\n'.join(pytz.all_timezones))"
   ```

2. **Adjust notification time**:
   ```bash
   SYNC_HOUR=8  # 8 AM
   SYNC_MINUTE=0
   NOTIFICATION_DELAY_MINUTES=10  # Send 10 min after sync
   ```

3. **Check server time**:
   ```bash
   date
   # Should show correct time

   # If wrong, sync system time
   sudo ntpdate time.apple.com  # macOS
   ```

---

## AI Analysis Issues

### Issue 1: Recommendations Don't Make Sense

**Symptoms**:
- AI suggests hard workout when clearly fatigued
- Inconsistent with data
- Generic responses

**Solutions**:

1. **Check baseline calculation**:
   ```bash
   # Need 7+ days for HRV baseline
   python scripts/check_baselines.py
   # Shows if enough data
   ```

2. **Review input data**:
   ```bash
   # View what AI receives
   curl http://localhost:8000/api/analysis/debug/readiness-input?date=2025-10-15
   # Check if data looks correct
   ```

3. **Adjust AI temperature**:
   ```bash
   # In .env
   AI_TEMPERATURE=0.3  # More consistent (default: 0.7)
   ```

4. **Provide more context**:
   ```bash
   # Increase historical context
   AI_CONTEXT_DAYS=14  # More data for patterns
   ```

5. **Update user profile**:
   - Ensure goals are specific
   - Add injury history
   - Set preferences clearly

---

### Issue 2: AI Analysis Fails

**Symptoms**:
```
Error parsing AI response
JSONDecodeError
Unexpected response format
```

**Solutions**:

1. **Check prompt format**:
   ```bash
   # View actual prompt sent
   curl http://localhost:8000/api/analysis/debug/last-prompt
   ```

2. **Validate response**:
   ```bash
   # Check logs for full AI response
   tail -f logs/training_optimizer.log | grep "AI response"
   ```

3. **Retry with different model**:
   ```bash
   AI_MODEL=claude-3-opus-20240229  # Most capable
   # Or
   AI_MODEL=claude-3-sonnet-20240229  # Balanced
   ```

4. **Simplify request**:
   - Reduce context sent to AI
   - Ask for simpler output format
   - Break complex analysis into steps

---

### Issue 3: Overtraining Not Detected

**Symptoms**:
- AI suggests hard workout despite clear fatigue
- Doesn't recognize overtraining signs

**Solutions**:

1. **Check HRV trend**:
   ```bash
   curl http://localhost:8000/api/health/hrv?start_date=2025-10-01&end_date=2025-10-15
   # Verify HRV data exists and is dropping
   ```

2. **Verify detection thresholds**:
   ```bash
   # In .env
   HRV_DROP_THRESHOLD=15  # % drop that triggers warning
   RHR_ELEVATION_THRESHOLD=5  # bpm above baseline
   OVERTRAINING_SENSITIVITY=medium  # low, medium, high
   ```

3. **Manual override**:
   If AI misses it, you can:
   ```bash
   # Force rest day
   curl -X POST http://localhost:8000/api/training/force-rest?date=2025-10-15
   ```

4. **Improve prompt**:
   Add explicit overtraining detection instructions to prompt template

---

## Getting More Help

If your issue isn't covered here:

1. **Check logs**:
   ```bash
   tail -100 logs/training_optimizer.log
   # Look for error messages
   ```

2. **Search GitHub Issues**:
   - https://github.com/yourusername/training-optimizer/issues
   - Search for error message

3. **Open new issue** with:
   - Error message (full stack trace)
   - Steps to reproduce
   - Your environment (OS, Python version)
   - Relevant config (with secrets removed)
   - Log file excerpt

4. **Community help**:
   - GitHub Discussions
   - Discord/Slack channel
   - Email support

---

## Emergency Recovery

If system is completely broken:

```bash
# 1. Backup everything
cp -r data data_backup
cp .env .env.backup

# 2. Full reset
rm -rf venv
rm data/training_data.db
git reset --hard  # If you made code changes

# 3. Clean reinstall
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Reconfigure
cp .env.backup .env

# 5. Reinitialize
python scripts/initial_setup.py

# 6. Restore data if possible
cp data_backup/training_data.db data/
# Or re-backfill
python scripts/backfill_data.py --days 30
```

---

**Remember**: Most issues are configuration-related. Double-check .env file first!
