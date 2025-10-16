"""
Main FastAPI application entry point.

Initializes the application, loads configuration, sets up logging,
and defines API routes.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings, Settings
from app.core.security import EncryptionManager, generate_secret_key
from app.models.user_profile import UserProfile, TrainingGoal, TrainingGoalType, Gender
from pydantic import ValidationError


# Initialize logger
logger = logging.getLogger(__name__)


def setup_logging(settings: Settings) -> None:
    """
    Configure application logging.

    Args:
        settings: Application settings
    """
    # Ensure log directory exists
    settings.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=settings.log_format,
        handlers=[
            # File handler
            logging.handlers.RotatingFileHandler(
                filename=settings.log_file,
                maxBytes=settings.log_max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8",
            ),
            # Console handler
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger.info("Logging configured successfully")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Log file: {settings.log_file}")


def validate_configuration(settings: Settings) -> None:
    """
    Validate application configuration on startup.

    Args:
        settings: Application settings to validate

    Raises:
        RuntimeError: If configuration is invalid
    """
    logger.info("Validating application configuration...")

    # Check required directories
    required_dirs = []
    if settings.database_path:
        required_dirs.append(settings.database_path.parent)

    for directory in required_dirs:
        if not directory.exists():
            logger.info(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)

    # Validate API keys (not empty, not default)
    if not settings.anthropic_api_key or len(settings.anthropic_api_key) < 20:
        raise RuntimeError(
            "Invalid Anthropic API key. Please set ANTHROPIC_API_KEY environment variable."
        )

    # Validate Garmin credentials
    if not settings.garmin_email or not settings.garmin_password:
        raise RuntimeError(
            "Missing Garmin credentials. Please set GARMIN_EMAIL and GARMIN_PASSWORD."
        )

    # Warn if using default secret key
    if settings.secret_key == "CHANGE_ME_IN_PRODUCTION" and settings.environment == "production":
        raise RuntimeError(
            "Cannot use default secret key in production. Generate a secure key."
        )

    logger.info("Configuration validation completed successfully")


def log_configuration_summary(settings: Settings) -> None:
    """
    Log configuration summary (with sensitive data masked).

    Args:
        settings: Application settings
    """
    logger.info("=" * 60)
    logger.info("AI-Powered Training Optimization System")
    logger.info("=" * 60)
    logger.info(f"Application: {settings.app_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Host: {settings.app_host}:{settings.app_port}")
    logger.info("-" * 60)

    # Database
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Pool Size: {settings.database_pool_size}")

    # AI Configuration
    logger.info(f"AI Model: {settings.ai_model}")
    logger.info(f"Max Tokens: {settings.ai_max_tokens}")
    logger.info(f"Temperature: {settings.ai_temperature}")

    # User Profile
    logger.info("-" * 60)
    logger.info(f"Athlete: {settings.athlete_name}")
    logger.info(f"Age: {settings.athlete_age}, Gender: {settings.athlete_gender}")
    logger.info(f"Max HR: {settings.max_heart_rate} bpm")
    logger.info(f"Resting HR: {settings.resting_heart_rate} bpm")
    logger.info(f"HR Reserve: {settings.hr_reserve} bpm")

    # Training Configuration
    logger.info(f"Training Goal: {settings.training_goal}")
    if settings.target_race_date:
        days_to_race = (settings.target_race_date - datetime.now().date()).days
        logger.info(f"Target Date: {settings.target_race_date} ({days_to_race} days)")
    logger.info(f"Weekly Training Days: {settings.weekly_training_days}")

    # Feature Flags
    logger.info("-" * 60)
    logger.info(f"AI Analysis: {'Enabled' if settings.enable_ai_analysis else 'Disabled'}")
    logger.info(f"Fatigue Monitoring: {'Enabled' if settings.enable_fatigue_monitoring else 'Disabled'}")
    logger.info(f"Workout Recommendations: {'Enabled' if settings.enable_workout_recommendations else 'Disabled'}")

    logger.info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up AI Training Optimizer...")

    try:
        settings = get_settings()

        # Setup logging
        setup_logging(settings)

        # Validate configuration
        validate_configuration(settings)

        # Ensure directories exist
        settings.ensure_directories_exist()

        # Log configuration summary
        log_configuration_summary(settings)

        logger.info("Application startup completed successfully")

    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        logger.error("Please check your .env file and environment variables")
        raise RuntimeError("Configuration validation failed") from e

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Training Optimizer...")
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="AI-Powered Training Optimization System",
    description="Intelligent training analysis and optimization using Garmin data and Claude AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API Routes ====================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    settings = get_settings()
    return {
        "application": settings.app_name,
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.environment,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/config", tags=["Configuration"])
async def get_config():
    """
    Get current configuration (sensitive data masked).

    Returns:
        dict: Configuration with masked sensitive values
    """
    settings = get_settings()
    return settings.get_safe_config_dict()


@app.get("/profile", tags=["User Profile"])
async def get_user_profile():
    """
    Get current user profile with heart rate zones.

    Returns:
        UserProfile: Complete user profile
    """
    settings = get_settings()

    try:
        # Create training goal
        goal = TrainingGoal(
            goal_type=TrainingGoalType.RACE if settings.target_race_date else TrainingGoalType.FITNESS,
            description=settings.training_goal,
            target_date=settings.target_race_date,
            priority=1,
        )

        # Create user profile
        profile = UserProfile(
            athlete_name=settings.athlete_name,
            email=settings.garmin_email,
            age=settings.athlete_age,
            gender=Gender(settings.athlete_gender),
            weight=settings.athlete_weight,
            height=settings.athlete_height,
            max_heart_rate=settings.max_heart_rate,
            resting_heart_rate=settings.resting_heart_rate,
            lactate_threshold_hr=settings.lactate_threshold_hr,
            weekly_training_days=settings.weekly_training_days,
            weekly_training_hours=settings.weekly_training_hours,
            preferred_training_types=settings.training_types_list,
            primary_goal=goal,
            injury_history=settings.injury_history,
        )

        return profile

    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user profile: {str(e)}"
        )


@app.get("/profile/zones", tags=["User Profile"])
async def get_heart_rate_zones():
    """
    Get heart rate training zones.

    Returns:
        dict: Heart rate zones with descriptions
    """
    settings = get_settings()

    from app.models.user_profile import HeartRateZones

    zones = HeartRateZones(
        max_heart_rate=settings.max_heart_rate,
        resting_heart_rate=settings.resting_heart_rate,
    )

    return zones.to_dict()


@app.get("/profile/summary", tags=["User Profile"])
async def get_profile_summary():
    """
    Get user profile summary.

    Returns:
        dict: Profile summary
    """
    profile = await get_user_profile()
    return profile.to_summary_dict()


@app.get("/security/generate-key", tags=["Security"])
async def generate_new_secret_key():
    """
    Generate a new secret key for configuration.

    WARNING: Only use in development. In production, use environment variables.

    Returns:
        dict: New secret key
    """
    settings = get_settings()

    if settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot generate keys in production environment"
        )

    new_key = generate_secret_key()

    return {
        "secret_key": new_key,
        "warning": "Store this securely in your .env file as SECRET_KEY",
        "note": "Never commit this to version control",
    }


# Error handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc),
        },
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
