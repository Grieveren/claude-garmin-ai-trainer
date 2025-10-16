# Configuration and Environment Management

This document explains the configuration system for the AI-Powered Training Optimization System.

## Overview

The application uses a robust configuration management system built on:
- **Pydantic Settings**: Type-safe configuration with validation
- **Environment Variables**: Flexible configuration via `.env` files
- **Security**: Encrypted storage of sensitive credentials
- **Validation**: Comprehensive validation on startup with helpful error messages

## Quick Start

### 1. Copy Environment File

```bash
cp .env.example .env
```

### 2. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add this to your `.env` file as `SECRET_KEY`.

### 3. Configure Required Settings

Edit `.env` and set:
- `GARMIN_EMAIL`: Your Garmin Connect email
- `GARMIN_PASSWORD`: Your Garmin Connect password
- `ANTHROPIC_API_KEY`: Your Claude API key from https://console.anthropic.com/
- `SECRET_KEY`: Generated secret key from step 2

### 4. Configure Your Profile

Set your athlete data in `.env`:
```bash
ATHLETE_NAME=Your Name
ATHLETE_AGE=35
ATHLETE_GENDER=male
MAX_HEART_RATE=185
RESTING_HEART_RATE=55
TRAINING_GOAL=Complete marathon in under 3:30:00
```

### 5. Test Configuration

```bash
python -m app.main
```

Visit http://localhost:8000/config to see your configuration (sensitive data masked).

## Configuration Structure

### Database Settings

```bash
DATABASE_URL=sqlite:///./data/training_data.db
DATABASE_POOL_SIZE=5
DATABASE_POOL_TIMEOUT=30
```

### Garmin Settings (Sensitive)

```bash
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password
GARMIN_SYNC_ENABLED=true
```

**Security Note**: Garmin password is encrypted at rest using the application secret key.

### Claude AI Settings (Sensitive)

```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
AI_MODEL=claude-sonnet-4-5-20250929
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.7
```

**Available Models**:
- `claude-sonnet-4-5-20250929` (recommended)
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### User Profile Settings

```bash
ATHLETE_NAME=Your Name
ATHLETE_AGE=35
ATHLETE_GENDER=male  # male, female, or other
ATHLETE_WEIGHT=75.0  # kg
ATHLETE_HEIGHT=180.0  # cm

# Heart Rate
MAX_HEART_RATE=185
RESTING_HEART_RATE=55
LACTATE_THRESHOLD_HR=165  # optional
VO2_MAX=52.0  # optional
```

### Training Settings

```bash
TRAINING_GOAL=Complete marathon in under 3:30:00
TARGET_RACE_DATE=2025-10-15  # optional, format: YYYY-MM-DD
WEEKLY_TRAINING_DAYS=6
WEEKLY_TRAINING_HOURS=12.0
PREFERRED_TRAINING_TYPES=running,cycling
```

## Heart Rate Zones

The system automatically calculates 5 heart rate training zones:

### Zone Definitions

Based on your max heart rate, the system calculates:

| Zone | Name | % Max HR | Purpose |
|------|------|----------|---------|
| 1 | Recovery | 50-60% | Active recovery, warm-up, cool-down |
| 2 | Easy Aerobic | 60-70% | Base building, long runs |
| 3 | Moderate Aerobic | 70-80% | Tempo runs, aerobic endurance |
| 4 | Threshold | 80-90% | Lactate threshold, speed work |
| 5 | VO2 Max | 90-100% | Intervals, maximum effort |

### Example Calculation

For an athlete with max HR = 185 bpm:

- **Zone 1**: 93-111 bpm (Recovery)
- **Zone 2**: 111-130 bpm (Easy)
- **Zone 3**: 130-148 bpm (Moderate)
- **Zone 4**: 148-167 bpm (Threshold)
- **Zone 5**: 167-185 bpm (Max)

### Accessing Your Zones

```bash
# Start the application
python -m app.main

# In another terminal
curl http://localhost:8000/profile/zones
```

## Security Features

### Credential Encryption

Sensitive credentials (passwords, API keys) are encrypted using:
- **Algorithm**: Fernet (symmetric encryption)
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Base**: Application secret key

### Password Hashing

For user authentication (future feature):
- **Algorithm**: PBKDF2-SHA256
- **Iterations**: 100,000
- **Salt**: Randomly generated per password

### Token Generation

Secure tokens for sessions:
- **Source**: `secrets.token_urlsafe()`
- **Length**: 32-48 bytes
- **Encoding**: URL-safe base64

## Validation Rules

The configuration system enforces these rules:

### Email Validation
- Must be valid email format
- Used for Garmin login

### Heart Rate Validation
- Max HR: 100-220 bpm
- Resting HR: 30-100 bpm
- Resting HR < Max HR
- HR Reserve > 50 bpm (warns if lower)
- Lactate threshold: between resting and max

### Age Validation
- Must be 10-100 years
- Used for estimated max HR comparison

### Training Goal Validation
- Target date cannot be in past
- Warns if race < 4 weeks away

### Secret Key Validation
- Minimum 32 characters
- Cannot be default value in production

## Environment-Specific Configuration

### Development Environment

Use `.env.development`:
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
APP_HOST=127.0.0.1
```

### Production Environment

Use `.env.production`:
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
# Must have secure SECRET_KEY
# Must have real credentials
```

## API Endpoints

### Configuration Endpoints

**GET /config**
```bash
curl http://localhost:8000/config
```
Returns configuration with sensitive data masked.

**GET /profile**
```bash
curl http://localhost:8000/profile
```
Returns complete user profile with zones.

**GET /profile/zones**
```bash
curl http://localhost:8000/profile/zones
```
Returns heart rate zones with descriptions.

**GET /profile/summary**
```bash
curl http://localhost:8000/profile/summary
```
Returns athlete summary.

## Python Usage

### Load Settings

```python
from app.core.config import get_settings

settings = get_settings()
print(f"Max HR: {settings.max_heart_rate}")
print(f"HR Reserve: {settings.hr_reserve}")
```

### Create User Profile

```python
from app.models.user_profile import UserProfile, TrainingGoal, TrainingGoalType, Gender

profile = UserProfile(
    athlete_name="John Doe",
    email="john@example.com",
    age=35,
    gender=Gender.MALE,
    max_heart_rate=185,
    resting_heart_rate=55,
    primary_goal=TrainingGoal(
        goal_type=TrainingGoalType.RACE,
        description="Marathon under 3 hours",
    )
)

# Access zones
zones = profile.heart_rate_zones
print(zones.to_dict())
```

### Calculate Heart Rate Zones

```python
from app.utils.heart_rate_zones import calculate_hr_zones, determine_zone

# Calculate zones
zones = calculate_hr_zones(
    max_heart_rate=185,
    resting_heart_rate=55,
    method='karvonen'  # or 'percentage'
)

# Determine zone for a heart rate
hr = 145
zone = determine_zone(hr, 185, 55, method='karvonen')
print(f"HR {hr} is in Zone {zone}")
```

### Analyze Workout

```python
from app.utils.heart_rate_zones import analyze_workout_zones

# Heart rates from a workout
heart_rates = [120, 130, 140, 150, 160, 155, 145, 135, 125]

analysis = analyze_workout_zones(
    heart_rates=heart_rates,
    max_heart_rate=185,
    resting_heart_rate=55,
    method='karvonen',
    sampling_interval=60.0  # 1 minute
)

print(f"Total time: {analysis['total_time']:.1f} minutes")
print(f"Dominant zone: {analysis['statistics']['dominant_zone']}")
print(f"Recommendation: {analysis['recommendation']}")
```

## Encryption Usage

### Encrypt Credentials

```python
from app.core.security import EncryptionManager

em = EncryptionManager(secret_key="your-secret-key")

# Encrypt
encrypted = em.encrypt("my-password")
print(f"Encrypted: {encrypted}")

# Decrypt
decrypted = em.decrypt(encrypted)
print(f"Decrypted: {decrypted}")
```

### Generate Secure Tokens

```python
from app.core.security import TokenGenerator

# Session ID
session_id = TokenGenerator.generate_session_id()

# API Key
api_key = TokenGenerator.generate_api_key()
```

## Troubleshooting

### Configuration Validation Failed

**Error**: `ValidationError: X validation errors for Settings`

**Solution**: Check your `.env` file for:
1. Missing required fields
2. Invalid email format
3. Out-of-range values (age, heart rates)
4. Incorrect data types

### Secret Key Error

**Error**: `Secret key must be changed from default value`

**Solution**: Generate a new key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Heart Rate Reserve Too Low

**Warning**: `Heart rate reserve (X bpm) seems too low`

**Solution**: Verify your max and resting heart rates:
- Max HR should be around 220 - age
- Resting HR measured when fully rested
- They should differ by at least 50 bpm

### Invalid Timezone

**Error**: `Invalid timezone 'XXX'`

**Solution**: Use valid IANA timezone:
- `UTC`
- `America/New_York`
- `Europe/London`
- `Asia/Tokyo`

### Missing API Key

**Error**: `Invalid Anthropic API key`

**Solution**:
1. Get API key from https://console.anthropic.com/
2. Set in `.env`: `ANTHROPIC_API_KEY=sk-ant-api03-xxxxx`
3. Ensure key is at least 20 characters

## Best Practices

### Security

1. **Never commit `.env`** to version control
2. Use different keys for dev/prod
3. Rotate credentials regularly
4. Use environment-specific configurations
5. Review configuration logs for leaks

### Configuration Management

1. Keep `.env.example` updated
2. Document all new settings
3. Provide sensible defaults
4. Validate early (fail fast)
5. Log configuration on startup

### Heart Rate Zones

1. Test your actual max HR (supervised)
2. Measure resting HR when fully recovered
3. Consider lactate threshold testing
4. Update zones as fitness improves
5. Use Karvonen method for accuracy

## Additional Resources

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [Cryptography Library](https://cryptography.io/en/latest/)
- [Heart Rate Training Zones](https://www.trainingpeaks.com/blog/power-training-levels/)

## Support

For configuration issues:
1. Check logs: `logs/training_optimizer.log`
2. Validate configuration: `curl http://localhost:8000/config`
3. Test profile: `curl http://localhost:8000/profile`
4. Review this document

## Next Steps

After configuration:
1. Test API endpoints
2. Verify Garmin connection
3. Test Claude AI integration
4. Review heart rate zones
5. Set up data synchronization

---

**Note**: Keep your `.env` file secure and never share sensitive credentials!
