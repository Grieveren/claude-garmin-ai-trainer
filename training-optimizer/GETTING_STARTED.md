# Getting Started with AI-Powered Training Optimizer

## Quick Setup (5 Minutes)

### 1. Verify Python Version

This project requires **Python 3.10 or higher**.

```bash
python3 --version
```

If you have Python 3.9, the project will still work but with an older version of garminconnect.

### 2. Create Virtual Environment

```bash
cd training-optimizer
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI & Uvicorn (web framework)
- Garmin Connect (activity data)
- Anthropic (Claude AI)
- SQLAlchemy (database)
- And many more...

### 4. Run Verification Script

```bash
python verify_setup.py
```

This script checks that:
- All packages are installed correctly
- Project structure is complete
- Application can be imported

### 5. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required settings:**
```bash
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_garmin_password
ANTHROPIC_API_KEY=sk-ant-your-key-here
SECRET_KEY=generate-random-secret-key
```

**Optional but recommended:**
```bash
ATHLETE_NAME=Your Name
ATHLETE_AGE=30
MAX_HEART_RATE=188
RESTING_HEART_RATE=48
TRAINING_GOAL=marathon
TARGET_RACE_DATE=2025-12-01
```

### 6. Run Setup Wizard

```bash
python scripts/initial_setup.py
```

The wizard will:
- Create necessary directories
- Verify your configuration
- Test Garmin connection
- Test Claude AI connection
- Initialize the database

### 7. Start the Application

```bash
uvicorn app.main:app --reload
```

Or simply:
```bash
python -m app.main
```

### 8. Access the Dashboard

Open your browser to: **http://localhost:8000**

**API Documentation:**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Next Steps

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific tests
pytest tests/test_main.py

# Run only unit tests
pytest -m unit
```

### Explore the Code

```
app/
├── main.py              # Start here - FastAPI application
├── core/
│   ├── config.py        # Configuration management
│   └── logger.py        # Logging setup
└── models/
    └── schemas.py       # Data models
```

### Manual Data Sync

```bash
# Sync last 7 days of activities
python scripts/sync_data.py

# Sync last 30 days
python scripts/sync_data.py 30
```

(Note: Full sync functionality will be available after Garmin service implementation)

### Jupyter Notebook

Explore your data with Jupyter:

```bash
pip install jupyter
jupyter notebook notebooks/exploratory_analysis.ipynb
```

## Troubleshooting

### Issue: Python version too old

**Solution:** Install Python 3.10+ from python.org or use pyenv:
```bash
pyenv install 3.10.0
pyenv local 3.10.0
```

### Issue: Package installation fails

**Solution:** Upgrade pip and try again:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Issue: Garmin connection fails

**Possible causes:**
1. Incorrect credentials in .env
2. Garmin service is down
3. Need to enable third-party access in Garmin settings

**Solution:** Run the setup wizard and verify credentials:
```bash
python scripts/initial_setup.py
```

### Issue: Port 8000 already in use

**Solution:** Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

Or update APP_PORT in .env file.

### Issue: Database errors

**Solution:** Delete and recreate the database:
```bash
rm data/training_data.db
python scripts/initial_setup.py
```

## Development Workflow

### Daily Development

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Start dev server:**
   ```bash
   uvicorn app.main:app --reload --log-level debug
   ```

3. **Make changes to code**

4. **Test your changes:**
   ```bash
   pytest
   ```

### Code Quality

**Format code:**
```bash
black app/ tests/ scripts/
```

**Lint code:**
```bash
ruff check app/ tests/ scripts/
```

**Fix linting issues:**
```bash
ruff check --fix app/ tests/ scripts/
```

### Adding Features

1. **Create a new branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**

3. **Add tests**

4. **Run tests:**
   ```bash
   pytest
   ```

5. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   git push origin feature/my-feature
   ```

## Project Status

✅ **Completed:**
- Project scaffolding
- Configuration management
- Logging system
- FastAPI application
- Basic templates and static files
- Test infrastructure
- Setup wizard
- Documentation

🚧 **In Progress / Next Phase:**
- Database models (pending)
- Garmin service implementation (pending)
- Claude AI service (pending)
- API routes (pending)
- Full dashboard (pending)

## Getting Help

### Check Logs

```bash
tail -f logs/training_optimizer.log
```

### Run Diagnostics

```bash
python verify_setup.py
python scripts/initial_setup.py
```

### Common Commands

```bash
# List all installed packages
pip list

# Check Python version
python --version

# View environment variables
cat .env

# Test database connection (coming soon)
# python scripts/test_db.py

# Clear cache
rm -rf __pycache__ app/__pycache__ tests/__pycache__
```

## Resources

- **FastAPI Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **Garmin Connect API:** https://github.com/cyberjunky/python-garminconnect
- **Claude AI Docs:** https://docs.anthropic.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Pytest Docs:** https://docs.pytest.org/

## What's Included

### Core Application
- ✅ FastAPI web framework
- ✅ Configuration management with Pydantic
- ✅ Structured logging with Loguru
- ✅ CORS middleware
- ✅ Request tracking

### Frontend
- ✅ Jinja2 templates
- ✅ Tailwind CSS integration
- ✅ Custom CSS and JavaScript
- ✅ Responsive design

### Testing
- ✅ Pytest setup
- ✅ Test fixtures
- ✅ Async test support
- ✅ Mock data

### DevOps
- ✅ Requirements.txt
- ✅ .gitignore
- ✅ Environment variables
- ✅ Setup scripts

### Documentation
- ✅ README.md
- ✅ This getting started guide
- ✅ API documentation (auto-generated)
- ✅ Code docstrings

## Success Criteria

You'll know the setup is complete when:

1. ✓ Virtual environment created
2. ✓ All dependencies installed
3. ✓ Configuration file (.env) created
4. ✓ Setup wizard runs successfully
5. ✓ Application starts without errors
6. ✓ Health check endpoint returns 200 OK
7. ✓ Tests pass

## Ready to Build!

Your project is now fully scaffolded and ready for development. The foundation is solid, following modern Python best practices.

**Start building by:**
1. Implementing database models
2. Creating the Garmin service
3. Building the Claude AI integration
4. Adding API routes
5. Expanding the dashboard

Happy coding! 🚀
