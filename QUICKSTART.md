# Quick Start Guide

Get up and running with the AI-Powered Training Optimization System in 5 minutes.

## Prerequisites

- Python 3.12 or higher
- pip or uv package manager
- Garmin Connect account
- Anthropic API key (get one at https://console.anthropic.com/)

## Step 1: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# OR using uv (faster)
uv pip install -r requirements.txt
```

## Step 2: Configure Environment

### Create .env file

```bash
cp .env.example .env
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and add it to your `.env` file as `SECRET_KEY`.

### Configure Required Settings

Edit `.env` and set these **required** values:

```bash
# Your Garmin Connect credentials
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password

# Your Claude API key from https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx

# Secret key from step above
SECRET_KEY=your-generated-secret-key

# Your athlete data
ATHLETE_NAME=Your Name
ATHLETE_AGE=35
ATHLETE_GENDER=male
MAX_HEART_RATE=185
RESTING_HEART_RATE=55

# Your training goal
TRAINING_GOAL=Complete marathon in under 3:30:00
```

## Step 3: Run the Application

```bash
python -m app.main
```

You should see:

```
INFO - AI-Powered Training Optimization System
INFO - Athlete: Your Name
INFO - Max HR: 185 bpm
INFO - Training Goal: Complete marathon in under 3:30:00
```

## Step 4: Test the API

Open your browser and visit:

- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Configuration**: http://localhost:8000/config
- **Your Profile**: http://localhost:8000/profile
- **Heart Rate Zones**: http://localhost:8000/profile/zones
- **API Docs**: http://localhost:8000/docs

### Using curl

```bash
# Check configuration
curl http://localhost:8000/config

# Get your profile
curl http://localhost:8000/profile

# Get heart rate zones
curl http://localhost:8000/profile/zones

# Get profile summary
curl http://localhost:8000/profile/summary
```

## Step 5: View Your Heart Rate Zones

```bash
curl http://localhost:8000/profile/zones | python -m json.tool
```

You'll see your personalized training zones:

```json
{
  "max_heart_rate": 185,
  "resting_heart_rate": 55,
  "hr_reserve": 130,
  "zones": [
    {
      "zone": 1,
      "name": "Recovery",
      "min_hr": 92,
      "max_hr": 111,
      "percentage": "50-60%",
      "description": "Active recovery, warm-up, cool-down..."
    },
    ...
  ]
}
```

## Common Commands

### Start the server in debug mode

```bash
# Set DEBUG=true in .env, then:
python -m app.main
```

### Run tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

### Generate a new secret key

```bash
curl http://localhost:8000/security/generate-key
```

## Troubleshooting

### Configuration validation failed

**Error**: `ValidationError: X validation errors for Settings`

**Solution**: Check your `.env` file. Common issues:
- Missing required fields
- Invalid email format
- Heart rates out of valid range (100-220 for max, 30-100 for resting)
- Age out of range (10-100)

Run this to see your current config:
```bash
python -c "from app.core.config import get_settings; print(get_settings().get_safe_config_dict())"
```

### Import errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Run from the project root directory:
```bash
cd "/Users/brettgray/Coding/Garmin AI"
python -m app.main
```

### API key not working

**Error**: `Invalid Anthropic API key`

**Solution**:
1. Get your API key from https://console.anthropic.com/
2. Ensure it starts with `sk-ant-api03-`
3. Check you've set it in `.env` correctly
4. No spaces before or after the key

### Port already in use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**: Change the port in `.env`:
```bash
APP_PORT=8001
```

## Next Steps

### 1. Understand Your Heart Rate Zones

Read about your training zones:
```bash
curl http://localhost:8000/profile/zones
```

### 2. Review Configuration Documentation

See [README_CONFIGURATION.md](README_CONFIGURATION.md) for:
- Detailed configuration options
- Security best practices
- Heart rate zone calculations
- Advanced usage examples

### 3. Explore the API

Visit http://localhost:8000/docs for interactive API documentation.

### 4. Run the Test Suite

```bash
pytest tests/ -v
```

### 5. Set Up Development Environment

```bash
# Install development dependencies
pip install ruff mypy pre-commit

# Set up pre-commit hooks
pre-commit install
```

## Example API Usage

### Get your training zones

```python
import requests

response = requests.get("http://localhost:8000/profile/zones")
zones = response.json()

print(f"Zone 2 (Easy): {zones['zones'][1]['min_hr']}-{zones['zones'][1]['max_hr']} bpm")
```

### Check your profile

```python
import requests

response = requests.get("http://localhost:8000/profile")
profile = response.json()

print(f"Athlete: {profile['athlete_name']}")
print(f"Goal: {profile['primary_goal']['description']}")
print(f"HR Reserve: {profile['heart_rate_zones']['hr_reserve']} bpm")
```

## Production Deployment

For production deployment:

1. **Use production environment file**:
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Set environment**:
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   ```

3. **Use strong secret key**:
   ```bash
   SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```

4. **Configure CORS** in `app/main.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

5. **Use production server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

6. **Set up HTTPS** with nginx/certbot or similar

## Getting Help

- **Configuration Issues**: See [README_CONFIGURATION.md](README_CONFIGURATION.md)
- **API Documentation**: Visit http://localhost:8000/docs
- **Test Examples**: Check `tests/` directory
- **Logs**: Check `logs/training_optimizer.log`

## Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Heart Rate Training Guide](https://www.trainingpeaks.com/blog/power-training-levels/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

**You're all set!** The system is ready to integrate with Garmin data and provide AI-powered training insights.

Next: Configure Garmin data synchronization and test Claude AI integration.
