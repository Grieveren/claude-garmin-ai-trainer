# Configuration Management Implementation

## Complete Implementation of Configuration and Environment Management

This document provides a comprehensive overview of the configuration management system implemented for the AI-Powered Training Optimization System.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Components](#components)
4. [Configuration](#configuration)
5. [Security](#security)
6. [Heart Rate Zones](#heart-rate-zones)
7. [User Profiles](#user-profiles)
8. [Testing](#testing)
9. [API](#api)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What Was Implemented

A complete configuration and environment management system featuring:

- **Type-safe configuration** with Pydantic Settings
- **Secure credential management** with encryption
- **Heart rate zone calculations** (5 zones, multiple methods)
- **User profile models** with automatic zone calculation
- **FastAPI application** with health checks and configuration endpoints
- **Comprehensive test suite** with 60+ tests
- **Complete documentation** for setup and usage

### Key Features

✅ **60+ validated configuration parameters**
✅ **Automatic heart rate zone calculation**
✅ **Credential encryption at rest**
✅ **Environment-specific configurations**
✅ **RESTful API with interactive docs**
✅ **Comprehensive error handling**
✅ **Production-ready security**

---

## Quick Start

### 1. Verify Setup

```bash
# Run verification script
python verify_setup.py
```

This checks:
- Python version (3.12+)
- Dependencies installed
- Environment file exists
- Configuration valid
- All components working

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env with your values
# Required: GARMIN_EMAIL, GARMIN_PASSWORD, ANTHROPIC_API_KEY, SECRET_KEY
# Required: ATHLETE_NAME, ATHLETE_AGE, ATHLETE_GENDER
# Required: MAX_HEART_RATE, RESTING_HEART_RATE, TRAINING_GOAL
```

### 4. Start Application

```bash
python -m app.main
```

Visit:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Config**: http://localhost:8000/config
- **Profile**: http://localhost:8000/profile

---

## Components

### 1. Configuration (`app/core/config.py`)

**Purpose**: Type-safe application configuration with validation

**Features**:
- 60+ configuration parameters
- Environment variable loading
- Comprehensive validation
- Sensitive data masking
- Computed properties

**Usage**:
```python
from app.core.config import get_settings

settings = get_settings()
print(f"Max HR: {settings.max_heart_rate}")
print(f"HR Reserve: {settings.hr_reserve}")
```

### 2. Security (`app/core/security.py`)

**Purpose**: Secure credential management

**Components**:
- `EncryptionManager`: Encrypt/decrypt credentials
- `PasswordHasher`: Secure password hashing
- `TokenGenerator`: Cryptographic token generation
- `SecureStorage`: High-level credential management

**Usage**:
```python
from app.core.security import EncryptionManager, generate_secret_key

secret = generate_secret_key()
em = EncryptionManager(secret)

encrypted = em.encrypt("my-password")
decrypted = em.decrypt(encrypted)
```

### 3. Heart Rate Zones (`app/utils/heart_rate_zones.py`)

**Purpose**: Calculate and analyze training zones

**Functions**:
- `calculate_hr_zones()`: Calculate 5 zones
- `determine_zone()`: Find zone for HR value
- `calculate_time_in_zones()`: Time distribution
- `analyze_workout_zones()`: Complete workout analysis

**Usage**:
```python
from app.utils.heart_rate_zones import calculate_hr_zones

zones = calculate_hr_zones(185, 55, method='karvonen')

for zone_num, zone_data in zones.items():
    print(f"Zone {zone_num}: {zone_data['min_hr']}-{zone_data['max_hr']} bpm")
```

### 4. User Profile (`app/models/user_profile.py`)

**Purpose**: Complete athlete data model

**Models**:
- `HeartRateZones`: Automatic zone calculation
- `TrainingGoal`: Goal tracking
- `AthleteMetrics`: Performance metrics
- `UserProfile`: Complete athlete profile

**Usage**:
```python
from app.models.user_profile import UserProfile, TrainingGoal, Gender

profile = UserProfile(
    athlete_name="John Doe",
    email="john@example.com",
    age=35,
    gender=Gender.MALE,
    max_heart_rate=185,
    resting_heart_rate=55,
    primary_goal=TrainingGoal(
        goal_type="race",
        description="Marathon under 3 hours"
    )
)

# Automatically calculates zones
zones = profile.heart_rate_zones
```

### 5. FastAPI Application (`app/main.py`)

**Purpose**: RESTful API with configuration endpoints

**Endpoints**:
- `GET /`: API information
- `GET /health`: Health check
- `GET /config`: Configuration (masked)
- `GET /profile`: User profile
- `GET /profile/zones`: Heart rate zones
- `GET /profile/summary`: Profile summary

**Features**:
- Lifespan management
- Configuration validation on startup
- Logging setup
- Error handling
- CORS support

---

## Configuration

### Configuration Groups

1. **Database**: Connection, pool settings
2. **Garmin**: Email, password (encrypted)
3. **Claude AI**: API key, model, parameters
4. **Application**: Host, port, debug, secret key
5. **Scheduling**: Sync time, timezone
6. **Notifications**: Email/SMS settings
7. **User Profile**: Athlete data
8. **Training**: Goals, preferences
9. **Logging**: Level, file path
10. **Features**: Feature flags

### Required Settings

```bash
# Garmin (required)
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password

# Claude AI (required)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Application (required)
SECRET_KEY=your-32-char-secret-key

# Athlete (required)
ATHLETE_NAME=Your Name
ATHLETE_AGE=35
ATHLETE_GENDER=male
MAX_HEART_RATE=185
RESTING_HEART_RATE=55
TRAINING_GOAL=Your training goal
```

### Optional Settings

See `.env.example` for all optional settings with defaults.

### Validation Rules

- **Email**: Valid email format
- **Age**: 10-100 years
- **Max HR**: 100-220 bpm
- **Resting HR**: 30-100 bpm
- **Max > Resting**: Must have HR reserve
- **Secret Key**: Minimum 32 characters
- **API Key**: Minimum 20 characters
- **Target Date**: Cannot be past

---

## Security

### Encryption

**Algorithm**: Fernet (symmetric encryption)
**Key Derivation**: PBKDF2 with 100,000 iterations
**Usage**: Encrypt Garmin password and API keys

```python
from app.core.security import encrypt_password, decrypt_password

secret_key = "your-secret-key"
encrypted = encrypt_password("my-password", secret_key)
decrypted = decrypt_password(encrypted, secret_key)
```

### Password Hashing

**Algorithm**: PBKDF2-SHA256
**Iterations**: 100,000
**Usage**: User authentication (future feature)

```python
from app.core.security import PasswordHasher

hashed, salt = PasswordHasher.hash_password("password")
is_valid = PasswordHasher.verify_password("password", hashed, salt)
```

### Token Generation

**Source**: `secrets` module (cryptographically secure)
**Usage**: Session IDs, API keys

```python
from app.core.security import TokenGenerator

session_id = TokenGenerator.generate_session_id()
api_key = TokenGenerator.generate_api_key()
```

### Best Practices

1. ✅ Never commit `.env` to version control
2. ✅ Use different keys for dev/prod
3. ✅ Rotate credentials regularly
4. ✅ Monitor access logs
5. ✅ Use HTTPS in production

---

## Heart Rate Zones

### Zone Definitions

Based on percentage of maximum heart rate:

| Zone | Name | % Max HR | Purpose |
|------|------|----------|---------|
| 1 | Recovery | 50-60% | Active recovery, warm-up |
| 2 | Easy Aerobic | 60-70% | Base building, long runs |
| 3 | Moderate Aerobic | 70-80% | Tempo, aerobic endurance |
| 4 | Threshold | 80-90% | Lactate threshold, speed |
| 5 | VO2 Max | 90-100% | Intervals, max effort |

### Calculation Methods

#### 1. Percentage Method (Simple)

```
Zone X = (min% × max HR) to (max% × max HR)
```

**Example**: Max HR = 180 bpm
- Zone 2 = (0.60 × 180) to (0.70 × 180) = 108-126 bpm

#### 2. Karvonen Method (HR Reserve)

```
Zone X = ((HRR × min%) + resting HR) to ((HRR × max%) + resting HR)
where HRR = max HR - resting HR
```

**Example**: Max HR = 180, Resting HR = 60
- HRR = 120 bpm
- Zone 2 = ((120 × 0.60) + 60) to ((120 × 0.70) + 60) = 132-144 bpm

### Usage Examples

```python
from app.utils.heart_rate_zones import calculate_hr_zones, determine_zone

# Calculate zones
zones = calculate_hr_zones(185, 55, method='karvonen')

# Determine zone for HR value
zone = determine_zone(140, 185, 55, method='karvonen')
print(f"HR 140 is in Zone {zone}")

# Analyze workout
from app.utils.heart_rate_zones import analyze_workout_zones

heart_rates = [120, 130, 140, 150, 160, 155, 145, 135]
analysis = analyze_workout_zones(heart_rates, 185, 55)

print(f"Total time: {analysis['total_time']} minutes")
print(f"Dominant zone: {analysis['statistics']['dominant_zone']}")
print(f"Recommendation: {analysis['recommendation']}")
```

---

## User Profiles

### Profile Structure

```python
UserProfile(
    # Basic info
    athlete_name: str
    email: str
    age: int
    gender: Gender  # male, female, other

    # Physical data
    weight: float  # kg
    height: float  # cm

    # Heart rate
    max_heart_rate: int
    resting_heart_rate: int
    lactate_threshold_hr: int  # optional

    # Training
    weekly_training_days: int
    primary_goal: TrainingGoal
    secondary_goals: list[TrainingGoal]

    # Automatically calculated
    heart_rate_zones: HeartRateZones
    bmi: float
    estimated_max_hr: int
)
```

### Creating a Profile

```python
from app.models.user_profile import (
    UserProfile, TrainingGoal, TrainingGoalType, Gender
)

goal = TrainingGoal(
    goal_type=TrainingGoalType.RACE,
    description="Marathon under 3 hours",
    target_date=date(2026, 10, 15),
    race_distance=42.195
)

profile = UserProfile(
    athlete_name="John Doe",
    email="john@example.com",
    age=35,
    gender=Gender.MALE,
    weight=75.0,
    height=180.0,
    max_heart_rate=185,
    resting_heart_rate=55,
    weekly_training_days=6,
    primary_goal=goal
)

# Access calculated zones
print(profile.heart_rate_zones.to_dict())
print(f"BMI: {profile.bmi}")
print(f"Days to goal: {profile.days_to_goal}")
```

---

## Testing

### Test Suite

4 comprehensive test files with 60+ tests:

1. **test_config.py**: Configuration validation
2. **test_security.py**: Security utilities
3. **test_heart_rate_zones.py**: Zone calculations
4. **test_user_profile.py**: Profile models

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_config.py

# With coverage
pytest --cov=app tests/

# Verbose output
pytest -v

# Specific test
pytest tests/test_config.py::TestConfigValidation::test_valid_config
```

### Test Coverage

- Configuration validation: 15+ tests
- Security utilities: 20+ tests
- Heart rate zones: 25+ tests
- User profiles: 15+ tests
- Edge cases and real-world scenarios

---

## API

### Endpoints

#### GET /

API information and status

```bash
curl http://localhost:8000/
```

#### GET /health

Health check endpoint

```bash
curl http://localhost:8000/health
```

#### GET /config

Configuration with sensitive data masked

```bash
curl http://localhost:8000/config
```

#### GET /profile

Complete user profile with zones

```bash
curl http://localhost:8000/profile | python -m json.tool
```

#### GET /profile/zones

Heart rate training zones

```bash
curl http://localhost:8000/profile/zones | python -m json.tool
```

#### GET /profile/summary

Profile summary

```bash
curl http://localhost:8000/profile/summary
```

### Interactive Documentation

Visit http://localhost:8000/docs for:
- Interactive API testing
- Request/response schemas
- Authentication details
- Error codes

---

## Troubleshooting

### Configuration Issues

**Problem**: `ValidationError: X validation errors`

**Solution**:
1. Check `.env` file exists
2. Verify all required fields set
3. Check value ranges (age, HR, etc.)
4. Run `python verify_setup.py`

### Dependency Issues

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
pip install -r requirements.txt
```

### Heart Rate Issues

**Problem**: HR reserve warning

**Solution**:
1. Verify max HR (test or estimate)
2. Measure resting HR when fully rested
3. Ensure max > resting by at least 50 bpm

### API Key Issues

**Problem**: Invalid API key error

**Solution**:
1. Get key from https://console.anthropic.com/
2. Check key starts with `sk-ant-api03-`
3. Verify no extra spaces in `.env`
4. Ensure key has sufficient credits

### Port Issues

**Problem**: Port already in use

**Solution**:
Change port in `.env`:
```bash
APP_PORT=8001
```

---

## Documentation

### Available Guides

1. **QUICKSTART.md**: 5-minute setup guide
2. **README_CONFIGURATION.md**: Complete configuration reference
3. **IMPLEMENTATION_SUMMARY.md**: Technical implementation details
4. **This file**: Overview and usage guide

### Code Documentation

All code includes:
- Comprehensive docstrings
- Type hints
- Usage examples
- Parameter descriptions
- Return value specifications

---

## Next Steps

### Immediate

1. ✅ Verify setup: `python verify_setup.py`
2. ✅ Configure environment: Edit `.env`
3. ✅ Start application: `python -m app.main`
4. ✅ Test API: Visit http://localhost:8000/docs

### Integration

1. Garmin data synchronization
2. Claude AI analysis integration
3. Database setup
4. Workout analysis pipeline
5. Training plan generation

### Enhancement

1. WebSocket support
2. Background task scheduling
3. Email/SMS notifications
4. Data visualization
5. Mobile app API

---

## Support

### Getting Help

- **Configuration**: See `README_CONFIGURATION.md`
- **Quick Start**: See `QUICKSTART.md`
- **API Docs**: http://localhost:8000/docs
- **Tests**: Check `tests/` directory
- **Logs**: `logs/training_optimizer.log`

### Common Commands

```bash
# Verify setup
python verify_setup.py

# Start application
python -m app.main

# Run tests
pytest

# Check configuration
python -c "from app.core.config import get_settings; print(get_settings().get_safe_config_dict())"

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Summary

You now have a complete, production-ready configuration and environment management system with:

✅ Type-safe configuration (60+ parameters)
✅ Secure credential management
✅ Heart rate zone calculations (5 zones)
✅ User profile models
✅ RESTful API with docs
✅ Comprehensive test suite
✅ Complete documentation

**Status**: Ready for integration with Garmin data sync and Claude AI analysis.

---

**Questions?** Check the documentation files or run `python verify_setup.py` to diagnose issues.
