# Setup Guide - AI Training Optimizer

Complete step-by-step guide to set up the AI-Powered Training Optimization System.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [First Run](#first-run)
5. [Verification](#verification)
6. [Troubleshooting Setup](#troubleshooting-setup)

---

## Prerequisites

### Required Software

- [ ] **Python 3.10 or higher** installed
  - Check version: `python --version` or `python3 --version`
  - Download from: https://python.org/downloads

- [ ] **Git** installed (for cloning repository)
  - Check version: `git --version`
  - Download from: https://git-scm.com/downloads

- [ ] **Text editor or IDE** (VS Code, PyCharm, or any editor)

- [ ] **Terminal/Command prompt** access

### Required Accounts

- [ ] **Garmin Connect account** (active and syncing)
  - Create at: https://connect.garmin.com
  - Ensure your Garmin device is syncing properly
  - Note: 2FA must be disabled (not supported by library)

- [ ] **Claude API key** from Anthropic
  - Sign up at: https://console.anthropic.com
  - Get API key from: https://console.anthropic.com/settings/keys
  - Add payment method (costs ~$5-15/month)

### System Requirements

**Minimum**:
- 2GB RAM
- 500MB free disk space
- Internet connection

**Recommended**:
- 4GB RAM
- 2GB free disk space
- Stable broadband connection

---

## Installation Steps

### Step 1: Clone Repository

```bash
# Using HTTPS
git clone https://github.com/yourusername/training-optimizer.git
cd training-optimizer

# Or using SSH
git clone git@github.com:yourusername/training-optimizer.git
cd training-optimizer
```

**Verify**: You should see project files when you run `ls` or `dir`.

---

### Step 2: Create Virtual Environment

Virtual environments keep dependencies isolated from your system Python.

#### On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt
```

#### On Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your prompt
```

**Verify**: Your command prompt should now show `(venv)` at the beginning.

**Troubleshooting**:
- If `python3` doesn't work, try `python`
- On Windows, if activation fails, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will take 2-5 minutes
```

**What's being installed**:
- FastAPI (web framework)
- garminconnect (Garmin data fetching)
- anthropic (Claude AI SDK)
- SQLAlchemy (database)
- pandas (data processing)
- plotly (visualizations)
- And more...

**Verify**:
```bash
pip list
# Should show 30+ packages including fastapi, anthropic, garminconnect
```

**Troubleshooting**:
- If installation fails, ensure you're in the virtual environment
- On macOS, you may need: `xcode-select --install`
- On Windows, install Visual C++ Build Tools if needed

---

### Step 4: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

#### Required Configuration

Open `.env` file and fill in these critical variables:

```bash
# === GARMIN CREDENTIALS ===
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_secure_password

# === CLAUDE AI API ===
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# === USER PROFILE ===
ATHLETE_NAME=Your Name
ATHLETE_AGE=30
ATHLETE_GENDER=M  # M or F
ATHLETE_WEIGHT_KG=70.0

# === HEART RATE ZONES ===
MAX_HEART_RATE=188
RESTING_HEART_RATE=48
LACTATE_THRESHOLD_HR=175

# === TRAINING GOAL ===
TRAINING_GOAL=marathon
GOAL_DESCRIPTION=Sub-3:30 Marathon
TARGET_RACE_DATE=2025-12-01
WEEKLY_TRAINING_DAYS=6
MAX_WEEKLY_HOURS=10
```

#### How to Calculate Your Heart Rate Values

**Max Heart Rate**:
- **Estimated**: 220 - your age (e.g., 220 - 30 = 190)
- **Better**: Run a 5K race effort, your max HR during it
- **Best**: Professional VO2 max test

**Resting Heart Rate**:
- Measure first thing in morning, before getting out of bed
- Use Garmin device overnight measurement
- Average over 3-7 days for accuracy

**Lactate Threshold HR**:
- **Estimated**: Max HR × 0.85-0.90
- **Better**: 30-minute time trial, average HR of last 20 minutes
- **Best**: Professional lactate threshold test

**Training Zones** (calculated automatically from above):
- Zone 1 (Recovery): 50-60% max HR
- Zone 2 (Easy/Aerobic): 60-70% max HR
- Zone 3 (Tempo): 70-80% max HR
- Zone 4 (Threshold): 80-90% max HR
- Zone 5 (VO2 Max): 90-100% max HR

---

### Step 5: Configure Notifications (Optional)

If you want morning email notifications:

```bash
# === EMAIL NOTIFICATIONS ===
ENABLE_EMAIL_NOTIFICATIONS=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # NOT your regular password
NOTIFICATION_EMAIL=your_email@gmail.com
```

#### Getting Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Create app password for "Training Optimizer"
3. Copy the 16-character password
4. Use this as `SMTP_PASSWORD`

**Note**: Don't use your regular Gmail password!

---

### Step 6: Initialize Database

```bash
# Run initial setup script
python scripts/initial_setup.py
```

This script will:
1. Create SQLite database
2. Initialize all tables
3. Create your user profile
4. Set up heart rate zones
5. Run test queries

**Output should show**:
```
✓ Database created successfully
✓ Tables initialized (12 tables)
✓ User profile created
✓ Heart rate zones calculated:
  Zone 1 (Recovery): 94-113 bpm
  Zone 2 (Aerobic): 113-131 bpm
  Zone 3 (Tempo): 131-150 bpm
  Zone 4 (Threshold): 150-169 bpm
  Zone 5 (VO2 Max): 169-188 bpm
✓ Setup complete!
```

**Verify**:
```bash
# Check database was created
ls -lh data/training_data.db
# Should show file size ~20-50KB
```

---

### Step 7: Test Garmin Connection

Before proceeding, verify Garmin authentication works:

```bash
python scripts/test_garmin_connection.py
```

**Expected output**:
```
Testing Garmin connection...
✓ Authentication successful
✓ Fetching user profile...
  Name: Your Name
  Email: your_email@example.com
✓ Fetching latest activity...
  Latest: Running on 2025-10-14
✓ Garmin connection working!
```

**If this fails**:
- Double-check credentials in `.env`
- Ensure no 2FA on Garmin account
- Try logging into Garmin Connect web to verify account works
- See [Troubleshooting](#troubleshooting-setup) section

---

### Step 8: Backfill Historical Data (Recommended)

Backfill 30-90 days of historical data for AI baseline:

```bash
# Backfill last 30 days (takes ~5-10 minutes)
python scripts/backfill_data.py --days 30

# Or backfill last 90 days for better baseline
python scripts/backfill_data.py --days 90
```

This fetches:
- Daily health metrics (steps, calories, HR, HRV)
- Sleep data
- All activities
- Body composition data

**Output shows progress**:
```
Backfilling data for last 30 days...
[========================================] 100% (30/30 days)

Summary:
✓ Daily metrics: 30 days
✓ Sleep sessions: 28 nights
✓ Activities: 18 workouts
✓ HRV readings: 25 measurements

Data backfill complete!
```

**Note**: This is important for establishing HRV and RHR baselines.

---

### Step 9: Test Claude AI Connection

Verify AI integration works:

```bash
python scripts/test_claude_connection.py
```

**Expected output**:
```
Testing Claude AI connection...
✓ API key valid
✓ Making test request...
✓ Response received

Test query: "Explain what HRV is in 2 sentences."
Response: "Heart Rate Variability (HRV) measures the variation in time between heartbeats, indicating autonomic nervous system balance. Higher HRV typically indicates better recovery and readiness to train, while lower HRV suggests stress or fatigue."

✓ Claude AI working correctly!
Token usage: 145 tokens (~$0.001)
```

**If this fails**:
- Verify API key in `.env` is correct
- Check API key has not expired
- Verify payment method added to Anthropic account
- See [Troubleshooting](#troubleshooting-setup) section

---

### Step 10: Run Application

```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Or with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Access dashboard**:
- Open browser: http://localhost:8000
- You should see the dashboard

**API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## First Run

### Get Your First Recommendation

1. **Sync latest data**:
   ```bash
   curl -X POST http://localhost:8000/api/sync/manual
   ```

2. **Generate readiness analysis**:
   ```bash
   curl http://localhost:8000/api/recommendations/today
   ```

3. **View in dashboard**:
   - Open: http://localhost:8000
   - See today's workout recommendation
   - Review readiness score and key factors

### Understanding Your First Recommendation

The AI will analyze:
- Your recent training history (from backfilled data)
- Last night's sleep
- Morning HRV compared to baseline
- Training load and recovery status

And recommend:
- Readiness score (0-100)
- Workout type (high intensity, moderate, easy, or rest)
- Specific workout with structure
- Why this recommendation makes sense

---

## Verification

### System Health Checks

```bash
# 1. Check database
sqlite3 data/training_data.db "SELECT COUNT(*) FROM daily_metrics;"
# Should show number of days backfilled

# 2. Check API health
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# 3. Check sync status
curl http://localhost:8000/api/sync/status
# Should show last sync time

# 4. Run tests
pytest tests/ -v
# Should show passing tests
```

### Data Validation

```bash
# View your HRV baseline
curl http://localhost:8000/api/health/hrv?start_date=2025-09-15&end_date=2025-10-15

# View recent activities
curl http://localhost:8000/api/activities?start_date=2025-10-01

# Check training load
curl http://localhost:8000/api/analysis/training-load
```

---

## Troubleshooting Setup

### Python Version Issues

**Problem**: `python3` command not found

**Solution**:
```bash
# Try just 'python'
python --version

# Or install Python 3.10+
# macOS: brew install python@3.10
# Windows: Download from python.org
# Linux: sudo apt-get install python3.10
```

### Virtual Environment Issues

**Problem**: Can't activate virtual environment on Windows

**Solution**:
```bash
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\activate
```

### Dependency Installation Fails

**Problem**: Error installing packages

**Solution**:
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install packages one by one to identify issue
pip install fastapi
pip install anthropic
pip install garminconnect

# On macOS, install Xcode tools
xcode-select --install
```

### Garmin Authentication Fails

**Problem**: `GarminConnectAuthenticationError`

**Solutions**:
1. **Check credentials**: Verify email/password in `.env`
2. **Disable 2FA**: Library doesn't support two-factor auth
3. **Test manually**: Log into connect.garmin.com with same credentials
4. **Check account**: Ensure account is active and not locked
5. **Library issue**: Check https://github.com/cyberjunky/python-garminconnect/issues

**Temporary workaround**:
```bash
# Use manual FIT file export
# 1. Go to connect.garmin.com
# 2. Export activities as FIT files
# 3. Import: python scripts/import_fit_files.py --dir ~/Downloads/garmin_data
```

### Claude API Issues

**Problem**: `AuthenticationError` or `PermissionError`

**Solutions**:
1. **Verify API key**: Check https://console.anthropic.com/settings/keys
2. **Add payment**: API requires payment method: https://console.anthropic.com/settings/billing
3. **Check quota**: Ensure you haven't exceeded rate limits
4. **Key format**: Must start with `sk-ant-`

### Database Issues

**Problem**: Database locked or corrupted

**Solution**:
```bash
# Backup existing data
cp data/training_data.db data/training_data.db.backup

# Reset database
rm data/training_data.db
python scripts/initial_setup.py

# Re-backfill data
python scripts/backfill_data.py --days 30
```

### Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --port 8080
```

---

## Next Steps

After successful setup:

1. **Read the User Guide**: [docs/user_guide.md](user_guide.md)
2. **Set up automation**: Configure daily sync schedule
3. **Generate training plan**: Create your first AI training plan
4. **Explore analytics**: Review performance trends
5. **Customize settings**: Adjust preferences in `.env`

---

## Getting Help

If you encounter issues not covered here:

1. Check [Troubleshooting Guide](troubleshooting.md)
2. Review [FAQ](faq.md)
3. Search [GitHub Issues](https://github.com/yourusername/training-optimizer/issues)
4. Open new issue with:
   - Error message
   - Steps to reproduce
   - Your system info
   - Log files from `logs/`

---

## Security Reminders

- **Never commit `.env` file** to Git (it's in `.gitignore`)
- **Keep API keys secret** - don't share screenshots with keys
- **Use app passwords** for email (not your main password)
- **Backup your data** regularly
- **Update dependencies** periodically: `pip install --upgrade -r requirements.txt`

---

**Setup complete! You're ready to start training smarter with AI coaching.**
