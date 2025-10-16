"""
Pytest configuration and fixtures for testing.

This module provides common fixtures and configuration for all tests.
"""

import os
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["GARMIN_EMAIL"] = "test@example.com"
os.environ["GARMIN_PASSWORD"] = "test_password"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_training_data.db"
os.environ["DEBUG"] = "True"

from app.main import app


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> Path:
    """
    Create a temporary directory for test data.

    Args:
        tmp_path_factory: Pytest temporary path factory

    Returns:
        Path to temporary data directory
    """
    data_dir = tmp_path_factory.mktemp("test_data")
    return data_dir


@pytest.fixture(scope="session")
def test_logs_dir(tmp_path_factory) -> Path:
    """
    Create a temporary directory for test logs.

    Args:
        tmp_path_factory: Pytest temporary path factory

    Returns:
        Path to temporary logs directory
    """
    logs_dir = tmp_path_factory.mktemp("test_logs")
    return logs_dir


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client for the FastAPI application.

    Yields:
        TestClient instance for making test requests
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_activity_data() -> dict:
    """
    Provide sample activity data for testing.

    Returns:
        Dictionary with sample activity data
    """
    return {
        "activity_id": "test_activity_123",
        "activity_type": "running",
        "start_time": "2025-01-15T08:00:00Z",
        "duration": 3600,  # 1 hour
        "distance": 10000,  # 10 km
        "avg_heart_rate": 150,
        "max_heart_rate": 175,
        "calories": 650,
    }


@pytest.fixture
def sample_athlete_profile() -> dict:
    """
    Provide sample athlete profile for testing.

    Returns:
        Dictionary with sample athlete profile
    """
    return {
        "name": "Test Athlete",
        "age": 30,
        "max_heart_rate": 188,
        "resting_heart_rate": 48,
        "training_goal": {
            "goal_type": "marathon",
            "target_race_date": "2025-12-01",
            "target_distance": 42195,  # Marathon distance in meters
            "target_time": 14400,  # 4 hours in seconds
        }
    }


@pytest.fixture
def mock_garmin_response() -> dict:
    """
    Provide mock Garmin API response data.

    Returns:
        Dictionary with mock Garmin data
    """
    return {
        "activityId": 123456789,
        "activityName": "Morning Run",
        "activityType": {
            "typeKey": "running"
        },
        "startTimeLocal": "2025-01-15 08:00:00",
        "duration": 3600.0,
        "distance": 10000.0,
        "averageHR": 150,
        "maxHR": 175,
        "calories": 650,
    }


@pytest.fixture
def mock_claude_response() -> dict:
    """
    Provide mock Claude AI response data.

    Returns:
        Dictionary with mock Claude response
    """
    return {
        "analysis": "Your recent training shows consistent effort...",
        "recommendations": [
            "Increase weekly mileage by 10%",
            "Add one speed workout per week",
            "Focus on recovery after long runs"
        ],
        "insights": {
            "weekly_distance": 50.0,
            "avg_pace": "5:30",
            "training_load": "moderate",
            "recovery_status": "good"
        }
    }


@pytest.fixture(autouse=True)
def cleanup_test_database():
    """
    Clean up test database after each test.

    This fixture automatically runs after each test to ensure
    a clean state for the next test.
    """
    yield
    # Cleanup code here (will be implemented with database setup)
    test_db_path = Path("./data/test_training_data.db")
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def auth_headers() -> dict:
    """
    Provide authentication headers for testing protected endpoints.

    Returns:
        Dictionary with authentication headers
    """
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }
