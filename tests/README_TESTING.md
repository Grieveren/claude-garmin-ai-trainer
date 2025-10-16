# Phase 2 Testing Infrastructure

Comprehensive testing infrastructure for Garmin AI Training Optimization System Phase 2.

## Overview

This testing infrastructure provides:
- **In-memory test database** (SQLite) for fast, isolated tests
- **Realistic test data generators** with proper statistical distributions
- **Mock Garmin service** simulating real API behavior
- **Fixtures** for common test scenarios
- **Utilities** for database state assertions

## Test Organization

```
tests/
├── conftest.py                  # Pytest fixtures
├── test_*.py                    # Unit tests
├── integration/                 # Integration tests
│   └── test_data_pipeline.py
├── mocks/                       # Mock services
│   └── mock_garmin.py
├── generators/                  # Test data generators
│   └── metric_generator.py
└── utils/                       # Testing utilities
    └── db_test_utils.py
```

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest -m unit
```

### Integration Tests Only
```bash
pytest -m integration
```

### Fast Tests (<1s)
```bash
pytest -m "not slow"
```

### Specific Test File
```bash
pytest tests/test_garmin_service.py
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Markers

Tests are organized with markers:
- `unit` - Fast unit tests (no external dependencies)
- `integration` - Integration tests (database, services)
- `slow` - Slow-running tests (>1s)
- `db` - Database tests
- `garmin` - Garmin integration tests
- `async` - Async/await tests
- `mock` - Mock service tests

## Key Fixtures

### Database Fixtures
- `test_db_session` - In-memory SQLite session
- `sample_user` - Test user with realistic data
- `sample_daily_metrics` - Single day of metrics
- `daily_metrics_7_days` - 7 days of metrics
- `daily_metrics_30_days` - 30 days of metrics

### User Scenario Fixtures
- `sample_user_well_rested` - Well-recovered athlete
- `sample_user_tired` - Fatigued athlete
- `sample_user_overtrained` - Overtrained state

### Activity Fixtures
- `sample_activity` - Single workout
- `sample_activities` - Multiple workouts (5 types)

### Sleep Fixtures
- `sample_sleep_data` - Single night
- `sleep_data_30_days` - 30 nights

### HRV Fixtures
- `sample_hrv_reading` - Single reading
- `hrv_readings_30_days` - 30 days showing recovery trend

## Mock Garmin Service

Simulate Garmin Connect API:

```python
from tests.mocks.mock_garmin import MockGarminConnect, UserScenario

# Create mock with scenario
config = MockGarminConfig(user_scenario=UserScenario.WELL_RESTED)
mock_garmin = MockGarminConnect(config)

# Authenticate
result = mock_garmin.authenticate("user@test.com", "password")

# Get data
metrics = mock_garmin.get_daily_metrics("user_123", date.today())
activities = mock_garmin.get_activities("user_123", start_date, end_date)
sleep = mock_garmin.get_sleep_data("user_123", date.today())
hrv = mock_garmin.get_hrv_data("user_123", date.today())
```

### Error Simulation

```python
# Simulate rate limiting
config = MockGarminConfig(fail_on_rate_limit=True)

# Simulate network errors
config = MockGarminConfig(fail_on_network=True)

# Simulate auth errors
config = MockGarminConfig(fail_on_auth=True)
```

## Test Data Generators

Generate realistic metrics with statistical distributions:

```python
from tests.generators.metric_generator import MetricGenerator

# Generate single day
metrics = MetricGenerator.generate_daily_metrics(
    user_id="user_123",
    date_obj=date.today(),
    recovery_factor=0.8,  # Well-rested
    fatigue_factor=0.2,   # Slightly fatigued
)

# Generate sequence with trend
metrics_list = MetricGenerator.generate_daily_metrics_sequence(
    user_id="user_123",
    start_date=date.today() - timedelta(days=30),
    num_days=30,
    recovery_trend="recovering",  # or "fatiguing", "cycling", "normal"
)
```

## Database Utilities

### Populate Test Data

```python
from tests.utils.db_test_utils import DatabaseTestUtils

# Populate 30 days of complete data
user = DatabaseTestUtils.populate_test_data(
    session=test_db_session,
    user_id="test_user",
    user_name="Test Athlete",
    days=30,
    include_activities=True,
    include_sleep=True,
    include_hrv=True,
)
```

### Assert Database State

```python
from tests.utils.db_test_utils import DatabaseTestUtils

# Check record counts
DatabaseTestUtils.assert_db_state(
    test_db_session,
    {
        "users": 1,
        "daily_metrics": 30,
        "activities": 15,
        "sleep_sessions": 30,
        "hrv_readings": 30,
    },
)
```

### Query Test Data

```python
# Get metrics for date range
metrics = DatabaseTestUtils.get_user_metrics_range(
    test_db_session,
    user_id="test_user",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
)

# Get activities
activities = DatabaseTestUtils.get_user_activities(
    test_db_session,
    user_id="test_user",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
)
```

## Writing New Tests

### Example Unit Test

```python
import pytest
from datetime import date

@pytest.mark.unit
def test_hrv_analysis(test_db_session, sample_user, hrv_readings_30_days):
    """Test HRV analysis logic."""
    # Test logic here
    assert len(hrv_readings_30_days) == 30
    
    # Check HRV values are realistic
    for reading in hrv_readings_30_days:
        assert 30 <= reading.hrv_sdnn <= 100
```

### Example Integration Test

```python
import pytest
from datetime import date, timedelta

@pytest.mark.integration
@pytest.mark.db
def test_data_pipeline_end_to_end(test_db_session):
    """Test complete data pipeline."""
    # Setup
    user = DatabaseTestUtils.populate_test_data(
        test_db_session, "user_123", days=30
    )
    
    # Run pipeline
    # ... pipeline logic ...
    
    # Assert results
    DatabaseTestUtils.assert_db_state(
        test_db_session,
        {"daily_metrics": 30, "activities": 15}
    )
```

## Coverage Requirements

- **Minimum coverage**: 80% (enforced in CI)
- **Target coverage**: 90%
- Run: `pytest --cov=app --cov-report=html`
- View: `open htmlcov/index.html`

## Performance Requirements

- Unit tests should run in <5 seconds total
- Integration tests should run in <10 seconds total
- Individual tests should be <1s (mark with `@pytest.mark.slow` if longer)

## Best Practices

1. **Use fixtures** - Don't create data manually
2. **Test isolation** - Each test gets fresh database
3. **Realistic data** - Use generators for proper distributions
4. **Mark appropriately** - Use `@pytest.mark.unit`, etc.
5. **Fast tests** - Keep tests fast for quick feedback
6. **Clear names** - Use descriptive test names
7. **Arrange-Act-Assert** - Follow AAA pattern

## TDD Workflow

Phase 2 follows Test-Driven Development:

1. **Write failing test** - Define expected behavior
2. **Verify failure** - Ensure test fails for right reason
3. **Implement minimum code** - Make test pass
4. **Refactor** - Clean up while tests pass
5. **Repeat** - Next feature

Example:
```python
# 1. Write failing test
@pytest.mark.unit
def test_calculate_readiness_score():
    """Test readiness score calculation."""
    score = calculate_readiness_score(hrv=60, sleep=480, stress=25)
    assert score >= 80  # High readiness
    
# 2. Run test - should fail (function doesn't exist)

# 3. Implement
def calculate_readiness_score(hrv, sleep, stress):
    return int(hrv * 0.5 + sleep/6 + (100-stress) * 0.3)

# 4. Run test - should pass

# 5. Refactor if needed
```

## Troubleshooting

### Tests Not Found
```bash
# Ensure pytest can find tests
python -m pytest --collect-only
```

### Import Errors
```bash
# Install package in editable mode
pip install -e .
```

### Database Errors
```bash
# Clean test database
rm -rf __pycache__ .pytest_cache
```

### Coverage Not Working
```bash
# Install coverage plugin
pip install pytest-cov
```

## CI/CD Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before deployment

GitHub Actions config: `.github/workflows/test.yml`

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)
