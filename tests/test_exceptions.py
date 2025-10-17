"""
Tests for custom exception hierarchy and error handlers.

This module tests all custom exceptions defined in app/core/exceptions.py including:
- Exception creation and properties
- Exception serialization to API responses
- Exception handlers for FastAPI
- Error logging and request tracking
"""

import pytest
from datetime import datetime
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from app.core.exceptions import (
    # Base exceptions
    AppException,

    # External API errors
    ExternalAPIError,

    # Garmin API errors
    GarminAPIError,
    GarminAuthenticationError,
    GarminConnectionError,
    GarminRateLimitError,
    GarminDataNotFoundError,

    # AI Analysis errors
    AIAnalysisError,
    ClaudeAPIError,
    ClaudeTokenLimitError,
    ClaudeParsingError,
    ClaudeRateLimitError,

    # Data errors
    DataError,
    DataValidationError,
    DataProcessingError,
    DataNotFoundError,
    InsufficientDataError,

    # Database errors
    DatabaseError,
    DatabaseConnectionError,
    DatabaseIntegrityError,
    DatabaseQueryError,

    # Auth errors
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError,

    # Business logic errors
    TrainingPlanError,
    InvalidTrainingPlanError,
    TrainingPlanConflictError,

    # Rate limiting
    RateLimitError,

    # Background jobs
    BackgroundJobError,
    JobNotFoundError,
    JobExecutionError,

    # Exception handlers
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
    register_exception_handlers,
)


class TestAppException:
    """Test base AppException class."""

    def test_app_exception_initialization(self):
        """Test that AppException can be created with all parameters."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR",
            details="Additional details",
            status_code=400,
            extra_field="extra_value"
        )

        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.details == "Additional details"
        assert exc.status_code == 400
        assert exc.extra_data["extra_field"] == "extra_value"

    def test_app_exception_to_dict_basic(self):
        """Test exception serialization to dictionary."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR"
        )

        result = exc.to_dict()

        assert result["success"] is False
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error"
        assert "timestamp" in result["error"]

    def test_app_exception_to_dict_with_details(self):
        """Test exception serialization includes details."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR",
            details="Detailed explanation"
        )

        result = exc.to_dict()

        assert result["error"]["details"] == "Detailed explanation"

    def test_app_exception_to_dict_with_request_id(self):
        """Test exception serialization includes request ID."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR"
        )

        result = exc.to_dict(request_id="req-123")

        assert result["error"]["request_id"] == "req-123"

    def test_app_exception_to_dict_with_extra_data(self):
        """Test exception serialization includes extra data."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR",
            user_id="user-123",
            action="test_action"
        )

        result = exc.to_dict()

        assert result["error"]["extra"]["user_id"] == "user-123"
        assert result["error"]["extra"]["action"] == "test_action"


class TestGarminExceptions:
    """Test Garmin API exception classes."""

    def test_garmin_authentication_error_defaults(self):
        """Test GarminAuthenticationError has correct defaults."""
        exc = GarminAuthenticationError()

        assert exc.code == "GARMIN_AUTH_FAILED"
        assert "authenticate" in exc.message.lower()
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.extra_data["service_name"] == "Garmin Connect"

    def test_garmin_connection_error_defaults(self):
        """Test GarminConnectionError has correct defaults."""
        exc = GarminConnectionError()

        assert exc.code == "GARMIN_CONNECTION_ERROR"
        assert "connect" in exc.message.lower()
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY

    def test_garmin_rate_limit_error_with_retry_after(self):
        """Test GarminRateLimitError includes retry_after."""
        exc = GarminRateLimitError(retry_after_seconds=60)

        assert exc.code == "GARMIN_RATE_LIMITED"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.extra_data["retry_after_seconds"] == 60
        assert "60 seconds" in exc.details

    def test_garmin_data_not_found_error(self):
        """Test GarminDataNotFoundError."""
        exc = GarminDataNotFoundError(data_type="sleep_data")

        assert exc.code == "GARMIN_DATA_NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.extra_data["data_type"] == "sleep_data"


class TestClaudeExceptions:
    """Test Claude AI exception classes."""

    def test_claude_api_error_defaults(self):
        """Test ClaudeAPIError has correct defaults."""
        exc = ClaudeAPIError()

        assert exc.code == "CLAUDE_API_ERROR"
        assert exc.extra_data["service_name"] == "Claude AI"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY

    def test_claude_token_limit_error_with_count(self):
        """Test ClaudeTokenLimitError includes token count."""
        exc = ClaudeTokenLimitError(token_count=50000)

        assert exc.code == "CLAUDE_TOKEN_LIMIT"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.extra_data["token_count"] == 50000

    def test_claude_parsing_error(self):
        """Test ClaudeParsingError."""
        exc = ClaudeParsingError()

        assert exc.code == "CLAUDE_PARSING_ERROR"
        assert "parse" in exc.message.lower()

    def test_claude_rate_limit_error(self):
        """Test ClaudeRateLimitError."""
        exc = ClaudeRateLimitError(retry_after_seconds=30)

        assert exc.code == "CLAUDE_RATE_LIMITED"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestDataExceptions:
    """Test data-related exception classes."""

    def test_data_validation_error_with_field(self):
        """Test DataValidationError includes field name."""
        exc = DataValidationError(
            message="Invalid email format",
            field_name="email"
        )

        assert exc.code == "DATA_VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.extra_data["field_name"] == "email"

    def test_data_processing_error_with_operation(self):
        """Test DataProcessingError includes operation."""
        exc = DataProcessingError(operation="calculate_average")

        assert exc.code == "DATA_PROCESSING_ERROR"
        assert exc.extra_data["operation"] == "calculate_average"

    def test_data_not_found_error(self):
        """Test DataNotFoundError."""
        exc = DataNotFoundError(
            resource_type="user",
            resource_id="123"
        )

        assert exc.code == "DATA_NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.extra_data["resource_type"] == "user"
        assert exc.extra_data["resource_id"] == "123"

    def test_insufficient_data_error_with_days(self):
        """Test InsufficientDataError includes day counts."""
        exc = InsufficientDataError(
            required_days=30,
            available_days=15
        )

        assert exc.code == "INSUFFICIENT_DATA"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "30 days" in exc.details
        assert "15 days" in exc.details


class TestDatabaseExceptions:
    """Test database exception classes."""

    def test_database_connection_error(self):
        """Test DatabaseConnectionError."""
        exc = DatabaseConnectionError()

        assert exc.code == "DATABASE_CONNECTION_ERROR"
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_database_integrity_error_with_constraint(self):
        """Test DatabaseIntegrityError includes constraint name."""
        exc = DatabaseIntegrityError(constraint_name="unique_email")

        assert exc.code == "DATABASE_INTEGRITY_ERROR"
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert exc.extra_data["constraint_name"] == "unique_email"

    def test_database_query_error(self):
        """Test DatabaseQueryError."""
        exc = DatabaseQueryError(query_type="SELECT")

        assert exc.code == "DATABASE_QUERY_ERROR"
        assert exc.extra_data["query_type"] == "SELECT"


class TestAuthenticationExceptions:
    """Test authentication and authorization exceptions."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError()

        assert exc.code == "AUTHENTICATION_FAILED"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError()

        assert exc.code == "AUTHORIZATION_FAILED"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_token_expired_error(self):
        """Test TokenExpiredError."""
        exc = TokenExpiredError()

        assert exc.code == "TOKEN_EXPIRED"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_error(self):
        """Test InvalidTokenError."""
        exc = InvalidTokenError()

        assert exc.code == "INVALID_TOKEN"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED


class TestBusinessLogicExceptions:
    """Test business logic exception classes."""

    def test_invalid_training_plan_error(self):
        """Test InvalidTrainingPlanError."""
        exc = InvalidTrainingPlanError()

        assert exc.code == "INVALID_TRAINING_PLAN"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_training_plan_conflict_error(self):
        """Test TrainingPlanConflictError."""
        exc = TrainingPlanConflictError()

        assert exc.code == "TRAINING_PLAN_CONFLICT"
        assert exc.status_code == status.HTTP_409_CONFLICT


class TestRateLimitingExceptions:
    """Test rate limiting exception."""

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        exc = RateLimitError(retry_after_seconds=120)

        assert exc.code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.extra_data["retry_after_seconds"] == 120


class TestBackgroundJobExceptions:
    """Test background job exception classes."""

    def test_job_not_found_error(self):
        """Test JobNotFoundError."""
        exc = JobNotFoundError(job_id="job-123")

        assert exc.code == "JOB_NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.extra_data["job_id"] == "job-123"

    def test_job_execution_error(self):
        """Test JobExecutionError."""
        exc = JobExecutionError(job_id="job-456")

        assert exc.code == "JOB_EXECUTION_FAILED"
        assert exc.extra_data["job_id"] == "job-456"


class TestExceptionHandlers:
    """Test FastAPI exception handlers."""

    @pytest.mark.asyncio
    async def test_app_exception_handler_returns_json(self):
        """Test that app_exception_handler returns proper JSON response."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR",
            status_code=400
        )

        # Mock request
        request = MagicMock(spec=Request)
        request.state.request_id = "req-123"
        request.url.path = "/test"
        request.method = "GET"

        response = await app_exception_handler(request, exc)

        assert response.status_code == 400
        # Note: Would need to parse response.body to check JSON content

    @pytest.mark.asyncio
    async def test_app_exception_handler_logs_error(self):
        """Test that app_exception_handler logs the error."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR"
        )

        request = MagicMock(spec=Request)
        request.state.request_id = "req-123"
        request.url.path = "/test"
        request.method = "GET"

        with patch("app.core.exceptions.logger") as mock_logger:
            await app_exception_handler(request, exc)
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_exception_handler_converts_to_standard_format(self):
        """Test that HTTPException is converted to standard error format."""
        exc = HTTPException(status_code=404, detail="Not found")

        request = MagicMock(spec=Request)
        request.state.request_id = None
        request.url.path = "/test"
        request.method = "GET"

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_exception_handler_formats_errors(self):
        """Test that validation errors are properly formatted."""
        # Create a mock validation error
        from pydantic_core import ValidationError as PydanticValidationError

        # This is a simplified test - actual ValidationError creation is complex
        # Would need to create proper Pydantic validation errors
        pass  # TODO: Implement with proper Pydantic error

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_catches_all(self):
        """Test that unhandled exception handler catches unexpected errors."""
        exc = Exception("Unexpected error")

        request = MagicMock(spec=Request)
        request.state.request_id = "req-123"
        request.url.path = "/test"
        request.method = "GET"

        with patch("app.core.exceptions.logger") as mock_logger:
            response = await unhandled_exception_handler(request, exc)

            assert response.status_code == 500
            mock_logger.error.assert_called_once()


class TestExceptionHandlerRegistration:
    """Test exception handler registration."""

    def test_register_exception_handlers_adds_all_handlers(self):
        """Test that all exception handlers are registered."""
        from fastapi import FastAPI

        app = FastAPI()

        # Get initial handler count
        initial_handlers = len(app.exception_handlers)

        register_exception_handlers(app)

        # Should have added handlers
        assert len(app.exception_handlers) > initial_handlers

    def test_register_exception_handlers_logs_registration(self):
        """Test that registration is logged."""
        from fastapi import FastAPI

        app = FastAPI()

        with patch("app.core.exceptions.logger") as mock_logger:
            register_exception_handlers(app)
            mock_logger.info.assert_called_with("exception_handlers_registered")


# ============================================================================
# Integration Tests with FastAPI
# ============================================================================

class TestExceptionHandlersIntegration:
    """Integration tests for exception handlers with FastAPI."""

    def test_app_exception_in_route_is_caught(self):
        """Test that AppException raised in route is properly handled."""
        # Would require setting up test FastAPI app with routes
        pass  # TODO: Implement integration test

    def test_database_error_returns_proper_status_code(self):
        """Test that DatabaseError returns 500 status."""
        pass  # TODO: Implement integration test

    def test_validation_error_returns_422(self):
        """Test that validation errors return 422 status."""
        pass  # TODO: Implement integration test


# ============================================================================
# Additional Test Cases to Add
# ============================================================================

"""
TODO: Add these additional test cases:

1. Exception Chaining:
   - test_exception_chain_preserved()
   - test_original_exception_logged()

2. Sensitive Data Protection:
   - test_exception_does_not_leak_credentials()
   - test_exception_masks_api_keys()
   - test_exception_sanitizes_sql_in_errors()

3. Localization:
   - test_exception_messages_localizable()
   - test_error_codes_consistent()

4. Performance:
   - test_exception_creation_performance()
   - test_exception_handler_overhead()

5. Error Recovery:
   - test_exception_allows_retry()
   - test_exception_includes_recovery_hints()
"""
