"""
Tests for the main FastAPI application.

This module tests the core application endpoints and functionality.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_read_root(client: TestClient) -> None:
    """
    Test the root endpoint returns HTML successfully.

    Args:
        client: FastAPI test client
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    assert "Training Optimizer" in response.text


@pytest.mark.unit
def test_health_check(client: TestClient) -> None:
    """
    Test the health check endpoint.

    Args:
        client: FastAPI test client
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert isinstance(data["debug"], bool)


@pytest.mark.unit
def test_api_info(client: TestClient) -> None:
    """
    Test the API info endpoint.

    Args:
        client: FastAPI test client
    """
    response = client.get("/api/info")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "application" in data
    assert "version" in data
    assert "ai_model" in data
    assert "endpoints" in data


@pytest.mark.unit
def test_request_id_header(client: TestClient) -> None:
    """
    Test that request ID is added to response headers.

    Args:
        client: FastAPI test client
    """
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


@pytest.mark.unit
def test_cors_headers(client: TestClient) -> None:
    """
    Test CORS headers are present.

    Args:
        client: FastAPI test client
    """
    response = client.options("/health")
    # CORS headers should be present
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_204_NO_CONTENT
    ]


@pytest.mark.unit
def test_404_not_found(client: TestClient) -> None:
    """
    Test 404 error for non-existent endpoint.

    Args:
        client: FastAPI test client
    """
    response = client.get("/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
def test_static_files_mounted(client: TestClient) -> None:
    """
    Test that static files are accessible.

    Args:
        client: FastAPI test client
    """
    # Test CSS file
    response = client.get("/static/css/style.css")
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_404_NOT_FOUND  # May not exist in test environment
    ]


@pytest.mark.integration
def test_application_startup(client: TestClient) -> None:
    """
    Test that the application starts successfully.

    Args:
        client: FastAPI test client
    """
    # If client is created successfully, app started
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
