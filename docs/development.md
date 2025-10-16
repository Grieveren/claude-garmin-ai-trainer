# Development Guide

Guide for developers contributing to or extending the AI Training Optimizer.

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Code Organization](#code-organization)
3. [Adding New Features](#adding-new-features)
4. [Running Tests](#running-tests)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Git Workflow](#git-workflow)
7. [Debugging Tips](#debugging-tips)
8. [Database Migrations](#database-migrations)

---

## Development Environment Setup

### Prerequisites

- Python 3.10+
- Git
- IDE with Python support (VS Code, PyCharm recommended)
- Docker (optional, for containerized development)

### Initial Setup

```bash
# 1. Fork and clone repository
git clone https://github.com/YOUR_USERNAME/training-optimizer.git
cd training-optimizer

# 2. Create development branch
git checkout -b dev

# 3. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 4. Install dependencies including dev tools
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Install pre-commit hooks
pre-commit install

# 6. Copy environment template
cp .env.example .env.dev

# 7. Configure for development
# Edit .env.dev with test credentials
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./data/training_data_dev.db

# 8. Initialize dev database
python scripts/initial_setup.py --env dev

# 9. Run tests to verify setup
pytest
```

### IDE Configuration

#### VS Code

Install extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- autoDocstring
- GitLens

`.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.analysis.typeCheckingMode": "basic"
}
```

#### PyCharm

1. Open project directory
2. Configure Python interpreter: Settings → Project → Python Interpreter
3. Select virtual environment: `./venv`
4. Enable pytest: Settings → Tools → Python Integrated Tools → Testing → pytest
5. Configure Black: Settings → Tools → External Tools → Add Black

---

## Code Organization

### Project Structure

```
training-optimizer/
├── app/
│   ├── main.py                     # FastAPI application entry
│   ├── config.py                   # Configuration management
│   ├── database.py                 # Database connection
│   │
│   ├── core/                       # Core utilities
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── logger.py               # Logging configuration
│   │   └── security.py             # Security utilities
│   │
│   ├── models/                     # Data models
│   │   ├── database_models.py      # SQLAlchemy models
│   │   ├── schemas.py              # Pydantic schemas
│   │   └── workout_library.py      # Workout definitions
│   │
│   ├── services/                   # Business logic
│   │   ├── garmin_service.py       # Garmin data fetching
│   │   ├── ai_analyzer.py          # AI analysis engine
│   │   ├── training_planner.py     # Training plan generation
│   │   ├── data_processor.py       # Data aggregation
│   │   └── notification_service.py # Notifications
│   │
│   ├── routers/                    # API endpoints
│   │   ├── health.py               # Health data endpoints
│   │   ├── analysis.py             # AI analysis endpoints
│   │   ├── training.py             # Training plan endpoints
│   │   └── chat.py                 # AI chat interface
│   │
│   ├── templates/                  # Jinja2 templates
│   └── static/                     # CSS, JS, images
│
├── scripts/                        # Utility scripts
├── tests/                          # Test suite
├── docs/                           # Documentation
└── alembic/                        # Database migrations
```

### Module Responsibilities

**app/services/** - Business logic layer:
- No direct FastAPI dependencies
- Reusable across different interfaces
- Contains core algorithms and processing
- Well-tested with unit tests

**app/routers/** - API layer:
- FastAPI route handlers
- Request validation with Pydantic
- Response formatting
- Error handling
- Delegates to services

**app/models/** - Data layer:
- Database models (SQLAlchemy)
- API schemas (Pydantic)
- Data validation
- No business logic

**app/core/** - Shared utilities:
- Configuration
- Logging
- Exceptions
- Security functions

---

## Adding New Features

### Feature Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write failing test first** (TDD):
   ```python
   # tests/test_your_feature.py
   def test_new_feature():
       result = your_new_function()
       assert result == expected_value
   ```

3. **Implement feature**:
   ```python
   # app/services/your_service.py
   def your_new_function():
       # Implementation
       return result
   ```

4. **Add API endpoint** (if needed):
   ```python
   # app/routers/your_router.py
   @router.get("/new-endpoint")
   async def new_endpoint():
       result = await your_service.your_new_function()
       return result
   ```

5. **Update documentation**:
   - Add docstrings
   - Update API docs
   - Add usage examples

6. **Run tests**:
   ```bash
   pytest tests/test_your_feature.py -v
   ```

7. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   git push origin feature/your-feature-name
   ```

### Example: Adding a New Metric

Let's add "Running Power" tracking:

**Step 1 - Database Model**:
```python
# app/models/database_models.py
class Activity(Base):
    __tablename__ = "activities"

    # Existing fields...
    avg_power = Column(Integer, nullable=True)  # Add this
    normalized_power = Column(Integer, nullable=True)  # Add this
```

**Step 2 - Create Migration**:
```bash
alembic revision --autogenerate -m "add running power fields"
alembic upgrade head
```

**Step 3 - Service Layer**:
```python
# app/services/garmin_service.py
def fetch_activity_details(self, activity_id: str):
    # Existing code...

    # Add power data
    activity_data['avg_power'] = garmin_data.get('avgPower')
    activity_data['normalized_power'] = garmin_data.get('normalizedPower')

    return activity_data
```

**Step 4 - API Schema**:
```python
# app/models/schemas.py
class ActivityResponse(BaseModel):
    # Existing fields...
    avg_power: Optional[int] = None
    normalized_power: Optional[int] = None
```

**Step 5 - Tests**:
```python
# tests/test_garmin_service.py
def test_fetch_activity_with_power():
    activity = garmin_service.fetch_activity_details("12345")
    assert activity.avg_power is not None
    assert activity.normalized_power is not None
```

**Step 6 - Documentation**:
```python
def fetch_activity_details(self, activity_id: str):
    """
    Fetch detailed activity data from Garmin.

    Args:
        activity_id: Garmin activity ID

    Returns:
        ActivityData with all metrics including power data

    Raises:
        GarminConnectionError: If fetch fails
    """
```

---

## Running Tests

### Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── test_garmin_service.py      # Garmin integration tests
├── test_ai_analyzer.py         # AI analysis tests
├── test_training_planner.py    # Training plan tests
├── test_database.py            # Database tests
├── test_api/                   # API endpoint tests
│   ├── test_health_api.py
│   ├── test_training_api.py
│   └── test_analysis_api.py
├── integration/                # Integration tests
│   └── test_workflows.py
└── fixtures/                   # Test data
    ├── sample_garmin_data.json
    └── sample_ai_responses.json
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_garmin_service.py

# Run specific test
pytest tests/test_garmin_service.py::test_authentication

# Run with coverage
pytest --cov=app --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"

# Run in verbose mode
pytest -v

# Run with output (don't capture print statements)
pytest -s

# Run and stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run tests matching pattern
pytest -k "test_garmin"
```

### Writing Tests

#### Unit Test Example

```python
# tests/test_data_processor.py
import pytest
from app.services.data_processor import DataProcessor

@pytest.fixture
def data_processor():
    return DataProcessor()

@pytest.fixture
def sample_hrv_data():
    return [
        {"date": "2025-10-01", "hrv": 60},
        {"date": "2025-10-02", "hrv": 58},
        {"date": "2025-10-03", "hrv": 62},
        # ... more data
    ]

def test_calculate_hrv_baseline(data_processor, sample_hrv_data):
    baseline = data_processor.calculate_hrv_baseline(
        sample_hrv_data,
        days=7
    )

    assert baseline == 60.0  # Expected average
    assert isinstance(baseline, float)

def test_calculate_hrv_baseline_insufficient_data(data_processor):
    with pytest.raises(ValueError, match="Insufficient data"):
        data_processor.calculate_hrv_baseline([], days=7)
```

#### Integration Test Example

```python
# tests/integration/test_daily_workflow.py
import pytest
from datetime import date

@pytest.mark.slow
@pytest.mark.integration
async def test_complete_daily_workflow(test_client, test_db):
    """Test complete daily workflow from sync to recommendation."""

    # 1. Sync data
    response = await test_client.post("/api/sync/manual")
    assert response.status_code == 200

    # 2. Generate readiness analysis
    response = await test_client.get("/api/recommendations/today")
    assert response.status_code == 200

    data = response.json()
    assert "readiness_score" in data
    assert 0 <= data["readiness_score"] <= 100
    assert data["recommendation"] in ["high_intensity", "moderate", "easy", "rest"]

    # 3. Verify database updated
    from app.models.database_models import DailyReadiness
    readiness = test_db.query(DailyReadiness).filter_by(
        date=date.today()
    ).first()

    assert readiness is not None
    assert readiness.readiness_score == data["readiness_score"]
```

#### API Test Example

```python
# tests/test_api/test_health_api.py
def test_get_daily_summary(test_client, test_db, sample_daily_metrics):
    """Test GET /api/health/summary endpoint."""

    # Setup test data
    test_db.add(sample_daily_metrics)
    test_db.commit()

    # Make request
    response = test_client.get("/api/health/summary?date=2025-10-15")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["date"] == "2025-10-15"
    assert data["steps"] == 10500
    assert data["resting_heart_rate"] == 48
    assert data["hrv_sdnn"] == 62.0

def test_get_daily_summary_missing_date(test_client):
    """Test error handling for missing date."""
    response = test_client.get("/api/health/summary")
    assert response.status_code == 422  # Validation error
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    """Create test database for each test."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_client(test_db):
    """Create test client with test database."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_daily_metrics():
    """Sample daily metrics for testing."""
    from app.models.database_models import DailyMetrics
    from datetime import date

    return DailyMetrics(
        date=date(2025, 10, 15),
        steps=10500,
        resting_heart_rate=48,
        hrv_sdnn=62.0,
        sleep_score=85
    )
```

---

## Code Style Guidelines

### Python Style (PEP 8 + Black)

```bash
# Format code with Black
black app/ tests/ scripts/

# Check code style
flake8 app/ tests/

# Type checking
mypy app/
```

### Naming Conventions

```python
# Classes: PascalCase
class DataProcessor:
    pass

# Functions/methods: snake_case
def calculate_hrv_baseline():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Variables: snake_case
user_profile = get_profile()
```

### Docstrings

Use Google style docstrings:

```python
def analyze_daily_readiness(
    self,
    date: str,
    include_alternatives: bool = True
) -> DailyReadinessResponse:
    """
    Analyze athlete's readiness to train for a specific date.

    Examines sleep quality, HRV trends, training load, and recovery status
    to generate a readiness score and workout recommendation.

    Args:
        date: Date to analyze in YYYY-MM-DD format
        include_alternatives: Whether to include alternative workout options

    Returns:
        DailyReadinessResponse containing:
            - readiness_score: 0-100 score
            - recommendation: high_intensity|moderate|easy|rest
            - suggested_workout: Specific workout details
            - key_factors: List of influencing factors
            - red_flags: Any concerning patterns

    Raises:
        ValueError: If date format is invalid
        InsufficientDataError: If not enough data for analysis

    Example:
        >>> analyzer = AIAnalyzer()
        >>> result = analyzer.analyze_daily_readiness("2025-10-15")
        >>> print(result.readiness_score)
        82
    """
    pass
```

### Type Hints

Always use type hints:

```python
from typing import List, Optional, Dict, Any
from datetime import date

def fetch_activities(
    start_date: date,
    end_date: date,
    activity_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Fetch activities in date range."""
    pass
```

### Error Handling

```python
# Use specific exceptions
from app.core.exceptions import GarminConnectionError, InsufficientDataError

def fetch_data(date: str) -> dict:
    try:
        data = garmin_api.get_data(date)
    except RequestException as e:
        raise GarminConnectionError(
            f"Failed to fetch data for {date}: {str(e)}"
        ) from e

    if not data:
        raise InsufficientDataError(
            f"No data available for {date}"
        )

    return data
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: dict):
    logger.info(f"Processing data for {data['date']}")

    try:
        result = perform_calculation(data)
        logger.debug(f"Calculation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise
```

---

## Git Workflow

### Branch Strategy

```bash
main          # Production-ready code
├── dev       # Development branch
│   ├── feature/new-feature
│   ├── fix/bug-fix
│   └── refactor/improve-code
```

### Commit Messages

Follow conventional commits:

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat: Add new feature
fix: Bug fix
docs: Documentation changes
style: Code formatting (no logic change)
refactor: Code restructuring
test: Add or update tests
chore: Maintenance tasks

# Examples:
git commit -m "feat(ai): add overtraining detection algorithm"
git commit -m "fix(garmin): handle missing HRV data gracefully"
git commit -m "docs: update setup guide with troubleshooting"
git commit -m "test: add integration tests for daily workflow"
git commit -m "refactor(database): optimize query performance"
```

### Pull Request Process

1. **Update your branch**:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout feature/your-feature
   git rebase dev
   ```

2. **Run tests**:
   ```bash
   pytest
   black app/ tests/
   flake8 app/ tests/
   ```

3. **Push to GitHub**:
   ```bash
   git push origin feature/your-feature
   ```

4. **Create PR on GitHub**:
   - Title: Clear description of change
   - Description: What changed and why
   - Link related issues
   - Add screenshots if UI changes

5. **Code review**:
   - Address reviewer comments
   - Make requested changes
   - Push updates

6. **Merge**:
   - Squash and merge to keep history clean
   - Delete branch after merge

---

## Debugging Tips

### Enable Debug Logging

```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Run with verbose logging
uvicorn app.main:app --reload --log-level debug
```

### Use Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with VS Code, add breakpoint in editor and press F5
```

### Debug API Requests

```bash
# Use curl with verbose output
curl -v http://localhost:8000/api/recommendations/today

# Or use httpie (more readable)
http :8000/api/recommendations/today

# Debug with Postman or Insomnia GUI
```

### Database Debugging

```bash
# Open SQLite database
sqlite3 data/training_data.db

# Run queries
SELECT * FROM daily_readiness ORDER BY date DESC LIMIT 5;

# Check table structure
.schema daily_readiness

# Enable query logging
# In app/database.py
engine = create_engine(
    DATABASE_URL,
    echo=True  # Logs all SQL queries
)
```

### Profile Performance

```python
# Use cProfile
python -m cProfile -o profile.stats scripts/sync_data.py

# Analyze results
python -m pstats profile.stats
# Then: sort cumtime, stats 20

# Or use line_profiler for line-by-line
@profile  # Requires kernprof
def slow_function():
    pass
```

---

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add new column"

# Create empty migration (for data migrations)
alembic revision -m "migrate old data format"

# Review generated migration
cat alembic/versions/xxxx_add_new_column.py
```

### Running Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history

# Upgrade to specific version
alembic upgrade abc123
```

### Example Migration

```python
# alembic/versions/001_add_power_fields.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('activities',
        sa.Column('avg_power', sa.Integer(), nullable=True)
    )
    op.add_column('activities',
        sa.Column('normalized_power', sa.Integer(), nullable=True)
    )

def downgrade():
    op.drop_column('activities', 'normalized_power')
    op.drop_column('activities', 'avg_power')
```

---

## Development Best Practices

1. **Write tests first** (TDD when possible)
2. **Keep functions small** (< 50 lines)
3. **One responsibility per function**
4. **Use type hints** everywhere
5. **Document complex logic**
6. **Handle errors gracefully**
7. **Log important events**
8. **Validate input data**
9. **Don't repeat yourself (DRY)**
10. **Commit often** with clear messages

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Anthropic API Reference](https://docs.anthropic.com)
- [pytest Documentation](https://docs.pytest.org)
- [PEP 8 Style Guide](https://pep8.org)

---

**Happy coding! Let's build amazing training tools together.**
