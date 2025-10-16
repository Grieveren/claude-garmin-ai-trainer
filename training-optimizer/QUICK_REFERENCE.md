# Quick Reference Card

## Essential Commands

### Setup
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python scripts/initial_setup.py

# Verify setup
python verify_setup.py
```

### Running the Application
```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Alternative way
python -m app.main

# With debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Testing
```bash
# Run all tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_main.py

# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Watch mode (requires pytest-watch)
ptw
```

### Code Quality
```bash
# Format code
black app/ tests/ scripts/

# Check formatting
black --check app/ tests/ scripts/

# Lint with ruff
ruff check app/ tests/ scripts/

# Auto-fix linting issues
ruff check --fix app/ tests/ scripts/

# Type checking (if mypy added)
mypy app/
```

### Database
```bash
# Initialize Alembic (when ready)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Data Management
```bash
# Manual sync (placeholder)
python scripts/sync_data.py

# Sync last 30 days
python scripts/sync_data.py 30
```

### Jupyter Notebooks
```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
jupyter notebook

# Open analysis notebook
jupyter notebook notebooks/exploratory_analysis.ipynb
```

### Logs & Debugging
```bash
# View logs
tail -f logs/training_optimizer.log

# Clear logs
rm logs/*.log

# View last 100 lines
tail -n 100 logs/training_optimizer.log

# Search logs
grep "ERROR" logs/training_optimizer.log
```

### Environment Management
```bash
# Create .env from example
cp .env.example .env

# Edit .env
nano .env

# Load environment variables
export $(cat .env | xargs)

# Show environment
env | grep -E "GARMIN|ANTHROPIC|APP_"
```

## Important URLs

```
Dashboard:           http://localhost:8000
Health Check:        http://localhost:8000/health
API Info:            http://localhost:8000/api/info
Swagger Docs:        http://localhost:8000/api/docs
ReDoc:               http://localhost:8000/api/redoc
```

## Directory Structure
```
app/              → Application code
├── core/         → Configuration, logging
├── models/       → Data models
├── services/     → Business logic
├── routers/      → API endpoints
├── templates/    → HTML templates
└── static/       → CSS, JS, images

scripts/          → Utility scripts
tests/            → Test suite
notebooks/        → Jupyter notebooks
data/             → Local data storage
logs/             → Application logs
docs/             → Documentation
```

## Key Files
```
app/main.py              → FastAPI app entry point
app/core/config.py       → Configuration
app/core/logger.py       → Logging setup
app/models/schemas.py    → Pydantic models
tests/conftest.py        → Pytest fixtures
requirements.txt         → Dependencies
.env                     → Environment variables (create from .env.example)
pytest.ini              → Pytest configuration
```

## Common Tasks

### Add New Dependency
```bash
pip install package_name
pip freeze > requirements.txt
```

### Create New Test
```python
# tests/test_feature.py
import pytest

@pytest.mark.unit
def test_feature(client):
    response = client.get("/endpoint")
    assert response.status_code == 200
```

### Add New API Endpoint
```python
# app/routers/feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
async def get_items():
    return {"items": []}
```

### Add New Config Variable
```python
# app/core/config.py
class Settings(BaseSettings):
    new_setting: str = Field(default="value")
```

## Troubleshooting Quick Fixes

### Port already in use
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 PID

# Use different port
uvicorn app.main:app --port 8001
```

### Import errors
```bash
# Activate venv
source venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### Database locked
```bash
# Close all connections
# Delete database
rm data/training_data.db

# Re-run setup
python scripts/initial_setup.py
```

### Clear cache
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Git Workflow
```bash
# Create branch
git checkout -b feature/name

# Stage changes
git add .

# Commit
git commit -m "Description"

# Push
git push origin feature/name

# Pull latest
git pull origin main

# Merge main into branch
git merge main
```

## Python Version Management
```bash
# Check version
python --version

# Use specific version with pyenv
pyenv install 3.10.0
pyenv local 3.10.0

# Create venv with specific version
python3.10 -m venv venv
```

## Environment Variables (Required)
```bash
GARMIN_EMAIL=           # Garmin account email
GARMIN_PASSWORD=        # Garmin account password
ANTHROPIC_API_KEY=      # Claude AI API key
SECRET_KEY=             # App secret (random string)
DATABASE_URL=           # SQLite path
```

## Status Markers
- ✅ Implemented
- 🚧 In Progress
- 📋 Planned
- ❌ Not Started

## Get Help
```bash
# Application help
python -m app.main --help

# Pytest help
pytest --help

# FastAPI help
uvicorn --help

# Check setup
python verify_setup.py

# Run setup wizard
python scripts/initial_setup.py
```

## Performance Tips
- Use `--reload` only in development
- Enable caching for AI responses
- Use database indexes
- Implement request rate limiting
- Monitor logs for slow queries

## Security Checklist
- [x] Environment variables for secrets
- [x] .env in .gitignore
- [x] Strong SECRET_KEY
- [ ] Rate limiting (todo)
- [ ] Authentication (todo)
- [ ] Input validation (partial)
- [x] XSS prevention in frontend

---

**Quick Start:** `source venv/bin/activate && uvicorn app.main:app --reload`
