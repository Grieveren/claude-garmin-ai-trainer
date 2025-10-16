"""
Custom exception hierarchy for the Garmin AI Training Optimization System.

This module defines all custom exceptions used throughout the application,
organized in a clear hierarchy for granular error handling.
"""

from typing import Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
from datetime import datetime

logger = structlog.get_logger()


# ============================================================================
# Base Exception
# ============================================================================

class AppException(Exception):
    """
    Base exception for all application-specific exceptions.

    All custom exceptions should inherit from this base class.
    """

    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        **extra_data
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        self.extra_data = extra_data
        super().__init__(self.message)

    def to_dict(self, request_id: Optional[str] = None) -> dict[str, Any]:
        """Convert exception to dictionary format for API response."""
        error_dict = {
            "code": self.code,
            "message": self.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if self.details:
            error_dict["details"] = self.details

        if request_id:
            error_dict["request_id"] = request_id

        if self.extra_data:
            error_dict["extra"] = self.extra_data

        return {"success": False, "error": error_dict}


# ============================================================================
# External API Errors
# ============================================================================

class ExternalAPIError(AppException):
    """Base exception for external API errors."""

    def __init__(
        self,
        message: str,
        code: str = "EXTERNAL_API_ERROR",
        service_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            service_name=service_name,
            **kwargs
        )


# ============================================================================
# Garmin API Errors
# ============================================================================

class GarminAPIError(ExternalAPIError):
    """Base exception for Garmin Connect API errors."""

    def __init__(
        self,
        message: str,
        code: str = "GARMIN_API_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            service_name="Garmin Connect",
            **kwargs
        )


class GarminAuthenticationError(GarminAPIError):
    """
    Exception raised when Garmin authentication fails.

    This could be due to:
    - Invalid credentials
    - Expired session
    - Account locked
    - Two-factor authentication required
    """

    def __init__(
        self,
        message: str = "Failed to authenticate with Garmin Connect",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="GARMIN_AUTH_FAILED",
            details="Please verify your Garmin credentials and try again",
            **kwargs
        )


class GarminConnectionError(GarminAPIError):
    """
    Exception raised when unable to connect to Garmin API.

    This could be due to:
    - Network connectivity issues
    - Garmin service outage
    - DNS resolution failure
    - Timeout
    """

    def __init__(
        self,
        message: str = "Unable to connect to Garmin Connect",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="GARMIN_CONNECTION_ERROR",
            details="Please check your internet connection and try again later",
            **kwargs
        )


class GarminRateLimitError(GarminAPIError):
    """
    Exception raised when Garmin API rate limit is exceeded.

    Includes retry_after information for backoff logic.
    """

    def __init__(
        self,
        message: str = "Garmin API rate limit exceeded",
        retry_after_seconds: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="GARMIN_RATE_LIMITED",
            details=f"Please try again in {retry_after_seconds} seconds" if retry_after_seconds else "Please try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after_seconds=retry_after_seconds,
            **kwargs
        )


class GarminDataNotFoundError(GarminAPIError):
    """
    Exception raised when requested data is not available from Garmin.

    This could be due to:
    - No data for requested date range
    - Device not synced
    - Data not yet available
    """

    def __init__(
        self,
        message: str = "Requested data not found on Garmin Connect",
        data_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="GARMIN_DATA_NOT_FOUND",
            details="The requested data may not be available yet. Please sync your Garmin device and try again.",
            status_code=status.HTTP_404_NOT_FOUND,
            data_type=data_type,
            **kwargs
        )


# ============================================================================
# AI Analysis Errors
# ============================================================================

class AIAnalysisError(ExternalAPIError):
    """Base exception for AI analysis errors."""

    def __init__(
        self,
        message: str,
        code: str = "AI_ANALYSIS_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            service_name="Claude AI",
            **kwargs
        )


class ClaudeAPIError(AIAnalysisError):
    """
    Exception raised when Claude API request fails.

    This could be due to:
    - API service outage
    - Invalid API key
    - Network connectivity issues
    """

    def __init__(
        self,
        message: str = "Claude AI API request failed",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="CLAUDE_API_ERROR",
            details="Unable to generate AI analysis at this time",
            **kwargs
        )


class ClaudeTokenLimitError(AIAnalysisError):
    """
    Exception raised when Claude API token limit is exceeded.

    This happens when the input or output exceeds Claude's token limits.
    """

    def __init__(
        self,
        message: str = "Input data exceeds Claude AI token limit",
        token_count: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="CLAUDE_TOKEN_LIMIT",
            details="Please reduce the date range or data scope for analysis",
            status_code=status.HTTP_400_BAD_REQUEST,
            token_count=token_count,
            **kwargs
        )


class ClaudeParsingError(AIAnalysisError):
    """
    Exception raised when Claude API response cannot be parsed.

    This could be due to:
    - Unexpected response format
    - Malformed JSON
    - Missing required fields
    """

    def __init__(
        self,
        message: str = "Failed to parse Claude AI response",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="CLAUDE_PARSING_ERROR",
            details="AI analysis generated unexpected response format",
            **kwargs
        )


class ClaudeRateLimitError(AIAnalysisError):
    """
    Exception raised when Claude API rate limit is exceeded.
    """

    def __init__(
        self,
        message: str = "Claude AI API rate limit exceeded",
        retry_after_seconds: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="CLAUDE_RATE_LIMITED",
            details=f"Please try again in {retry_after_seconds} seconds" if retry_after_seconds else "Please try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after_seconds=retry_after_seconds,
            **kwargs
        )


# ============================================================================
# Data Errors
# ============================================================================

class DataError(AppException):
    """Base exception for data-related errors."""

    def __init__(
        self,
        message: str,
        code: str = "DATA_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            **kwargs
        )


class DataValidationError(DataError):
    """
    Exception raised when data validation fails.

    This could be due to:
    - Invalid date range
    - Missing required fields
    - Out of range values
    - Type mismatches
    """

    def __init__(
        self,
        message: str = "Data validation failed",
        field_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="DATA_VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            field_name=field_name,
            **kwargs
        )


class DataProcessingError(DataError):
    """
    Exception raised when data processing fails.

    This could be due to:
    - Calculation errors
    - Invalid data transformations
    - Aggregation failures
    """

    def __init__(
        self,
        message: str = "Data processing failed",
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="DATA_PROCESSING_ERROR",
            details="Unable to process the requested data",
            operation=operation,
            **kwargs
        )


class DataNotFoundError(DataError):
    """
    Exception raised when requested data is not found in database.
    """

    def __init__(
        self,
        message: str = "Requested data not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="DATA_NOT_FOUND",
            details="The requested resource does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )


class InsufficientDataError(DataError):
    """
    Exception raised when insufficient data is available for analysis.

    This could be due to:
    - Not enough historical data
    - Missing required metrics
    - Sparse data coverage
    """

    def __init__(
        self,
        message: str = "Insufficient data for analysis",
        required_days: Optional[int] = None,
        available_days: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="INSUFFICIENT_DATA",
            details=f"Need at least {required_days} days of data, but only {available_days} days available" if required_days and available_days else None,
            status_code=status.HTTP_400_BAD_REQUEST,
            required_days=required_days,
            available_days=available_days,
            **kwargs
        )


# ============================================================================
# Database Errors
# ============================================================================

class DatabaseError(AppException):
    """Base exception for database-related errors."""

    def __init__(
        self,
        message: str,
        code: str = "DATABASE_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            details="Database operation failed",
            **kwargs
        )


class DatabaseConnectionError(DatabaseError):
    """
    Exception raised when database connection fails.

    This could be due to:
    - Database server down
    - Connection timeout
    - Invalid connection parameters
    """

    def __init__(
        self,
        message: str = "Failed to connect to database",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="DATABASE_CONNECTION_ERROR",
            details="Please try again later",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            **kwargs
        )


class DatabaseIntegrityError(DatabaseError):
    """
    Exception raised when database integrity constraint is violated.

    This could be due to:
    - Duplicate key violation
    - Foreign key violation
    - NOT NULL constraint violation
    """

    def __init__(
        self,
        message: str = "Database integrity constraint violated",
        constraint_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="DATABASE_INTEGRITY_ERROR",
            details="The operation violates database constraints",
            status_code=status.HTTP_409_CONFLICT,
            constraint_name=constraint_name,
            **kwargs
        )


class DatabaseQueryError(DatabaseError):
    """
    Exception raised when database query fails.
    """

    def __init__(
        self,
        message: str = "Database query failed",
        query_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="DATABASE_QUERY_ERROR",
            query_type=query_type,
            **kwargs
        )


# ============================================================================
# Authentication & Authorization Errors
# ============================================================================

class AuthenticationError(AppException):
    """
    Exception raised when authentication fails.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            details="Invalid credentials or session expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )


class AuthorizationError(AppException):
    """
    Exception raised when user is not authorized to perform an action.
    """

    def __init__(
        self,
        message: str = "Insufficient permissions",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_FAILED",
            details="You do not have permission to perform this action",
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs
        )


class TokenExpiredError(AppException):
    """
    Exception raised when JWT token has expired.
    """

    def __init__(
        self,
        message: str = "Token has expired",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="TOKEN_EXPIRED",
            details="Please refresh your access token",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )


class InvalidTokenError(AppException):
    """
    Exception raised when JWT token is invalid.
    """

    def __init__(
        self,
        message: str = "Invalid token",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="INVALID_TOKEN",
            details="Please log in again",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )


# ============================================================================
# Business Logic Errors
# ============================================================================

class TrainingPlanError(AppException):
    """Base exception for training plan errors."""

    def __init__(
        self,
        message: str,
        code: str = "TRAINING_PLAN_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            **kwargs
        )


class InvalidTrainingPlanError(TrainingPlanError):
    """
    Exception raised when training plan parameters are invalid.
    """

    def __init__(
        self,
        message: str = "Invalid training plan parameters",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="INVALID_TRAINING_PLAN",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs
        )


class TrainingPlanConflictError(TrainingPlanError):
    """
    Exception raised when training plan conflicts with existing plan.
    """

    def __init__(
        self,
        message: str = "Training plan conflicts with existing plan",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="TRAINING_PLAN_CONFLICT",
            details="You already have an active training plan for this period",
            status_code=status.HTTP_409_CONFLICT,
            **kwargs
        )


# ============================================================================
# Rate Limiting Errors
# ============================================================================

class RateLimitError(AppException):
    """
    Exception raised when API rate limit is exceeded.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after_seconds: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details=f"Please try again in {retry_after_seconds} seconds" if retry_after_seconds else "Please try again later",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after_seconds=retry_after_seconds,
            **kwargs
        )


# ============================================================================
# Background Job Errors
# ============================================================================

class BackgroundJobError(AppException):
    """Base exception for background job errors."""

    def __init__(
        self,
        message: str,
        code: str = "BACKGROUND_JOB_ERROR",
        job_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            job_id=job_id,
            **kwargs
        )


class JobNotFoundError(BackgroundJobError):
    """
    Exception raised when background job is not found.
    """

    def __init__(
        self,
        message: str = "Background job not found",
        job_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            job_id=job_id,
            **kwargs
        )


class JobExecutionError(BackgroundJobError):
    """
    Exception raised when background job execution fails.
    """

    def __init__(
        self,
        message: str = "Background job execution failed",
        job_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="JOB_EXECUTION_FAILED",
            job_id=job_id,
            **kwargs
        )


# ============================================================================
# Exception Handlers for FastAPI
# ============================================================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Global exception handler for AppException and its subclasses.

    Logs the error and returns a standardized JSON response.
    """
    request_id = getattr(request.state, "request_id", None)

    # Log the exception
    logger.error(
        "application_error",
        error_code=exc.code,
        error_message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        **exc.extra_data
    )

    # Return JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=request_id),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Exception handler for FastAPI HTTPException.

    Converts HTTPException to standardized error format.
    """
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
            },
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Exception handler for Pydantic validation errors.

    Formats validation errors in a user-friendly way.
    """
    request_id = getattr(request.state, "request_id", None)

    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        "validation_error",
        errors=errors,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": "One or more fields have invalid values",
                "validation_errors": errors,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for unhandled exceptions.

    Catches all unexpected errors and logs them for debugging.
    """
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": "Our team has been notified and will investigate",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
            },
        },
    )


# ============================================================================
# Register Exception Handlers
# ============================================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.

    Usage:
        from fastapi import FastAPI
        from app.core.exceptions import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
    """
    from fastapi import FastAPI
    from fastapi.exceptions import RequestValidationError

    # Custom exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info("exception_handlers_registered")
