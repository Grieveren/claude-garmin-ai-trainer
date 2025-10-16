"""
Logging configuration using loguru.

This module sets up structured logging with console and file handlers,
log rotation, and request ID tracking for debugging.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure logging for the application.

    Sets up loguru with:
    - Console handler for development
    - File handler with rotation
    - Structured format with timestamps
    - Request ID tracking support
    """
    # Remove default handler
    logger.remove()

    # Console handler - pretty format for development
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
    )

    # Ensure logs directory exists
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler - JSON format for production
    logger.add(
        settings.log_file,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        level=settings.log_level,
        rotation="10 MB",  # Rotate when file reaches 10 MB
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress rotated logs
        enqueue=True,  # Async logging
        backtrace=True,  # Show full traceback
        diagnose=True,  # Show variable values in traceback
    )

    logger.info("Logging configured successfully")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Log file: {settings.log_file}")


def log_request(request_id: str, method: str, path: str) -> None:
    """
    Log an incoming HTTP request.

    Args:
        request_id: Unique identifier for the request
        method: HTTP method (GET, POST, etc.)
        path: Request path
    """
    logger.info(f"[{request_id}] {method} {path}")


def log_response(
    request_id: str,
    status_code: int,
    duration_ms: float
) -> None:
    """
    Log an HTTP response.

    Args:
        request_id: Unique identifier for the request
        status_code: HTTP status code
        duration_ms: Request processing duration in milliseconds
    """
    logger.info(
        f"[{request_id}] Response: {status_code} "
        f"(took {duration_ms:.2f}ms)"
    )


def log_garmin_sync(
    success: bool,
    activities_count: int = 0,
    error: Optional[str] = None
) -> None:
    """
    Log Garmin data synchronization results.

    Args:
        success: Whether the sync was successful
        activities_count: Number of activities synced
        error: Error message if sync failed
    """
    if success:
        logger.info(f"Garmin sync successful: {activities_count} activities")
    else:
        logger.error(f"Garmin sync failed: {error}")


def log_ai_request(
    request_type: str,
    tokens_used: Optional[int] = None
) -> None:
    """
    Log AI API request.

    Args:
        request_type: Type of AI request (analysis, recommendation, etc.)
        tokens_used: Number of tokens used (if available)
    """
    if tokens_used:
        logger.info(f"AI request ({request_type}): {tokens_used} tokens")
    else:
        logger.info(f"AI request: {request_type}")


def log_database_operation(
    operation: str,
    table: str,
    records_affected: int = 0
) -> None:
    """
    Log database operations.

    Args:
        operation: Type of operation (INSERT, UPDATE, DELETE, SELECT)
        table: Database table name
        records_affected: Number of records affected
    """
    logger.debug(
        f"Database {operation} on {table}: {records_affected} records"
    )


def log_scheduler_task(task_name: str, status: str) -> None:
    """
    Log scheduled task execution.

    Args:
        task_name: Name of the scheduled task
        status: Task status (started, completed, failed)
    """
    logger.info(f"Scheduled task '{task_name}': {status}")


# Context manager for request logging
class RequestLogger:
    """Context manager for logging HTTP requests with timing."""

    def __init__(self, request_id: str, method: str, path: str):
        """
        Initialize request logger.

        Args:
            request_id: Unique identifier for the request
            method: HTTP method
            path: Request path
        """
        self.request_id = request_id
        self.method = method
        self.path = path
        self.start_time: Optional[float] = None

    def __enter__(self) -> "RequestLogger":
        """Start timing the request."""
        import time
        self.start_time = time.time()
        log_request(self.request_id, self.method, self.path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Log the request completion and duration."""
        import time
        duration_ms = (time.time() - self.start_time) * 1000
        if exc_type is None:
            log_response(self.request_id, 200, duration_ms)
        else:
            logger.error(
                f"[{self.request_id}] Request failed: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )


# Initialize logging on module import
setup_logging()
