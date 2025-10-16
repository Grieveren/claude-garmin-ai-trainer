#!/usr/bin/env python3
"""
Initial Setup Wizard for AI-Powered Training Optimization System.

This script guides users through the initial setup process, including:
- Creating necessary directories
- Validating configuration
- Testing Garmin connection
- Testing Claude AI connection
- Initializing the database
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"✓ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"✗ {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"ℹ {text}")


def create_directories() -> bool:
    """
    Create necessary directories for the application.

    Returns:
        True if successful, False otherwise
    """
    print_header("Step 1: Creating Directories")

    base_dir = Path(__file__).parent.parent
    directories = [
        base_dir / "data",
        base_dir / "logs",
        base_dir / "data" / "cache",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
    ]

    try:
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print_success(f"Created/verified: {directory.relative_to(base_dir)}")
        return True
    except Exception as e:
        print_error(f"Failed to create directories: {e}")
        return False


def check_env_file() -> bool:
    """
    Check if .env file exists and has required variables.

    Returns:
        True if .env file is properly configured, False otherwise
    """
    print_header("Step 2: Checking Configuration")

    base_dir = Path(__file__).parent.parent
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"

    if not env_file.exists():
        print_error(".env file not found")
        print_info(f"Please copy {env_example.name} to .env and configure it")

        if env_example.exists():
            print_info("\nYou can do this by running:")
            print_info(f"  cp {env_example} {env_file}")

        return False

    # Check for required variables
    required_vars = [
        "GARMIN_EMAIL",
        "GARMIN_PASSWORD",
        "ANTHROPIC_API_KEY",
        "SECRET_KEY",
    ]

    missing_vars = []
    with open(env_file, 'r') as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content or f"{var}=your" in env_content:
                missing_vars.append(var)

    if missing_vars:
        print_error("Missing or incomplete configuration variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return False

    print_success(".env file configured")
    return True


def test_imports() -> bool:
    """
    Test that required packages are installed.

    Returns:
        True if all imports succeed, False otherwise
    """
    print_header("Step 3: Checking Dependencies")

    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("garminconnect", "Garmin Connect"),
        ("anthropic", "Anthropic (Claude AI)"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pandas", "Pandas"),
        ("loguru", "Loguru"),
    ]

    all_imported = True
    for package, name in required_packages:
        try:
            __import__(package)
            print_success(f"{name} installed")
        except ImportError:
            print_error(f"{name} NOT installed")
            all_imported = False

    if not all_imported:
        print_info("\nInstall missing packages with:")
        print_info("  pip install -r requirements.txt")

    return all_imported


def test_garmin_connection() -> bool:
    """
    Test connection to Garmin Connect.

    Returns:
        True if connection successful, False otherwise
    """
    print_header("Step 4: Testing Garmin Connection")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        if not email or not password or "your" in email.lower():
            print_error("Garmin credentials not configured in .env file")
            return False

        print_info("Attempting to connect to Garmin Connect...")
        print_info("(This may take a moment)")

        from garminconnect import Garmin

        garmin = Garmin(email, password)
        garmin.login()

        print_success("Successfully connected to Garmin Connect")

        # Get user info
        user_info = garmin.get_full_name()
        print_info(f"Connected as: {user_info}")

        return True

    except ImportError:
        print_error("garminconnect package not installed")
        return False
    except Exception as e:
        print_error(f"Failed to connect to Garmin: {e}")
        print_info("Please verify your credentials in .env file")
        return False


def test_claude_connection() -> bool:
    """
    Test connection to Claude AI API.

    Returns:
        True if connection successful, False otherwise
    """
    print_header("Step 5: Testing Claude AI Connection")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key or "your" in api_key.lower():
            print_error("Anthropic API key not configured in .env file")
            return False

        print_info("Testing Claude AI API connection...")

        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Simple test message
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Respond with 'OK' if you receive this message."
            }]
        )

        print_success("Successfully connected to Claude AI")
        print_info(f"Model: {message.model}")

        return True

    except ImportError:
        print_error("anthropic package not installed")
        return False
    except Exception as e:
        print_error(f"Failed to connect to Claude AI: {e}")
        print_info("Please verify your API key in .env file")
        return False


def initialize_database() -> bool:
    """
    Initialize the database.

    Returns:
        True if successful, False otherwise
    """
    print_header("Step 6: Initializing Database")

    try:
        print_info("Database initialization will be implemented by DB architect")
        print_success("Database setup pending (placeholder)")
        return True

    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        return False


def create_env_file_interactive() -> None:
    """Create .env file interactively."""
    print_header("Interactive Configuration Setup")

    base_dir = Path(__file__).parent.parent
    env_file = base_dir / ".env"

    print_info("Let's set up your configuration file.")
    print_info("Press Enter to skip optional fields.\n")

    # Garmin credentials
    print("Garmin Connect Credentials:")
    garmin_email = input("  Email: ").strip()
    garmin_password = input("  Password: ").strip()

    # Claude API
    print("\nClaude AI Configuration:")
    anthropic_key = input("  API Key: ").strip()

    # Athlete profile
    print("\nAthlete Profile:")
    athlete_name = input("  Name [Athlete]: ").strip() or "Athlete"
    athlete_age = input("  Age [30]: ").strip() or "30"
    max_hr = input("  Max Heart Rate [188]: ").strip() or "188"
    rest_hr = input("  Resting Heart Rate [48]: ").strip() or "48"

    # Training goal
    print("\nTraining Goal:")
    print("  Options: marathon, half_marathon, 5k, 10k, general_fitness")
    training_goal = input("  Goal [general_fitness]: ").strip() or "general_fitness"
    target_date = input("  Target Race Date (YYYY-MM-DD) [optional]: ").strip()

    # Generate secret key
    import secrets
    secret_key = secrets.token_urlsafe(32)

    # Create .env content
    env_content = f"""# Garmin Credentials
GARMIN_EMAIL={garmin_email}
GARMIN_PASSWORD={garmin_password}

# Claude AI API
ANTHROPIC_API_KEY={anthropic_key}

# Database
DATABASE_URL=sqlite:///./data/training_data.db

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY={secret_key}
DEBUG=True

# Scheduling
SYNC_HOUR=8
SYNC_MINUTE=0
TIMEZONE=America/New_York

# Notifications
ENABLE_EMAIL_NOTIFICATIONS=False
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# User Profile
ATHLETE_NAME={athlete_name}
ATHLETE_AGE={athlete_age}
MAX_HEART_RATE={max_hr}
RESTING_HEART_RATE={rest_hr}

# Training Goal
TRAINING_GOAL={training_goal}
TARGET_RACE_DATE={target_date}

# AI Settings
AI_MODEL=claude-sonnet-4-5-20250929
AI_CACHE_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/training_optimizer.log
"""

    with open(env_file, 'w') as f:
        f.write(env_content)

    print_success(f"\n.env file created at {env_file}")


def main() -> int:
    """
    Run the setup wizard.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_header("AI-Powered Training Optimization System - Setup Wizard")

    print("""
This wizard will help you set up the training optimizer system.

We will:
  1. Create necessary directories
  2. Check configuration
  3. Verify dependencies
  4. Test Garmin connection
  5. Test Claude AI connection
  6. Initialize database
    """)

    base_dir = Path(__file__).parent.parent
    env_file = base_dir / ".env"

    # Offer to create .env file if it doesn't exist
    if not env_file.exists():
        response = input("Would you like to create the .env file now? (y/n): ")
        if response.lower() == 'y':
            create_env_file_interactive()
            print()

    # Run setup steps
    steps = [
        ("Create directories", create_directories),
        ("Check configuration", check_env_file),
        ("Check dependencies", test_imports),
        ("Test Garmin connection", test_garmin_connection),
        ("Test Claude AI connection", test_claude_connection),
        ("Initialize database", initialize_database),
    ]

    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append(result)
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {e}")
            results.append(False)

    # Summary
    print_header("Setup Summary")

    for (step_name, _), result in zip(steps, results):
        if result:
            print_success(f"{step_name}")
        else:
            print_error(f"{step_name}")

    success_count = sum(results)
    total_count = len(results)

    print(f"\n{success_count}/{total_count} steps completed successfully")

    if all(results):
        print_success("\nSetup completed successfully!")
        print_info("\nYou can now start the application with:")
        print_info("  uvicorn app.main:app --reload")
        print_info("\nOr run:")
        print_info("  python -m app.main")
        return 0
    else:
        print_error("\nSetup incomplete. Please address the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
