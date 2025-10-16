#!/usr/bin/env python3
"""
Setup verification script for AI-Powered Training Optimization System.

This script verifies that all components are properly configured and working.
"""

import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗{RESET} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠{RESET} {text}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ{RESET} {text}")


def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version_info

    if version.major >= 3 and version.minor >= 12:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} (✓ >= 3.12)")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (✗ < 3.12)")
        print_warning("Python 3.12 or higher is recommended")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("Checking Dependencies")

    dependencies = [
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
        ("cryptography", "Cryptography"),
        ("uvicorn", "Uvicorn"),
    ]

    all_installed = True

    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print_success(f"{display_name} installed")
        except ImportError:
            print_error(f"{display_name} not installed")
            all_installed = False

    if not all_installed:
        print_info("\nInstall dependencies with: pip install -r requirements.txt")

    return all_installed


def check_env_file():
    """Check if .env file exists"""
    print_header("Checking Environment Configuration")

    env_path = Path(".env")

    if env_path.exists():
        print_success(".env file exists")
        return True
    else:
        print_error(".env file not found")
        print_info("Create .env file with: cp .env.example .env")
        return False


def check_configuration():
    """Check if configuration is valid"""
    print_header("Validating Configuration")

    try:
        from app.core.config import get_settings

        settings = get_settings()

        # Check required fields
        checks = [
            (settings.garmin_email, "Garmin email"),
            (settings.garmin_password, "Garmin password"),
            (settings.anthropic_api_key, "Anthropic API key"),
            (settings.secret_key, "Secret key"),
            (settings.athlete_name, "Athlete name"),
            (settings.max_heart_rate, "Max heart rate"),
            (settings.resting_heart_rate, "Resting heart rate"),
        ]

        all_valid = True
        for value, name in checks:
            if value:
                print_success(f"{name} configured")
            else:
                print_error(f"{name} not configured")
                all_valid = False

        # Check HR values
        if settings.max_heart_rate and settings.resting_heart_rate:
            hr_reserve = settings.max_heart_rate - settings.resting_heart_rate
            print_info(f"Heart Rate Reserve: {hr_reserve} bpm")

            if hr_reserve < 50:
                print_warning("HR reserve seems low - verify your heart rates")

        return all_valid

    except Exception as e:
        print_error(f"Configuration error: {e}")
        print_info("Check your .env file for errors")
        return False


def check_heart_rate_zones():
    """Check heart rate zone calculations"""
    print_header("Testing Heart Rate Zone Calculations")

    try:
        from app.utils.heart_rate_zones import calculate_hr_zones

        zones = calculate_hr_zones(180, 60, method='karvonen')

        print_success("Zone calculation successful")
        print_info("\nYour Heart Rate Zones (example with 180 max, 60 resting):")

        for zone_num, zone_data in zones.items():
            print(f"  Zone {zone_num} ({zone_data['name']}): "
                  f"{zone_data['min_hr']}-{zone_data['max_hr']} bpm "
                  f"({zone_data['percentage']})")

        return True

    except Exception as e:
        print_error(f"Zone calculation error: {e}")
        return False


def check_user_profile():
    """Check user profile creation"""
    print_header("Testing User Profile")

    try:
        from app.models.user_profile import (
            UserProfile, TrainingGoal, TrainingGoalType, Gender
        )

        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test goal"
        )

        profile = UserProfile(
            athlete_name="Test Athlete",
            email="test@example.com",
            age=35,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        print_success("User profile created successfully")
        print_info(f"Profile: {profile.athlete_name}, Age {profile.age}")
        print_info(f"HR Zones: {len(profile.heart_rate_zones.to_dict()['zones'])} zones calculated")

        return True

    except Exception as e:
        print_error(f"Profile creation error: {e}")
        return False


def check_security():
    """Check security utilities"""
    print_header("Testing Security Utilities")

    try:
        from app.core.security import (
            EncryptionManager,
            PasswordHasher,
            TokenGenerator,
            generate_secret_key
        )

        # Test encryption
        secret = generate_secret_key()
        em = EncryptionManager(secret)
        encrypted = em.encrypt("test-password")
        decrypted = em.decrypt(encrypted)

        if decrypted == "test-password":
            print_success("Encryption/decryption working")
        else:
            print_error("Encryption/decryption failed")
            return False

        # Test password hashing
        hashed, salt = PasswordHasher.hash_password("test-password")
        if PasswordHasher.verify_password("test-password", hashed, salt):
            print_success("Password hashing working")
        else:
            print_error("Password hashing failed")
            return False

        # Test token generation
        token = TokenGenerator.generate_token()
        if len(token) >= 32:
            print_success("Token generation working")
        else:
            print_error("Token generation failed")
            return False

        return True

    except Exception as e:
        print_error(f"Security test error: {e}")
        return False


def check_directories():
    """Check if required directories exist"""
    print_header("Checking Directories")

    directories = [
        Path("logs"),
        Path("data"),
        Path("app"),
        Path("tests"),
    ]

    all_exist = True
    for directory in directories:
        if directory.exists():
            print_success(f"{directory}/ directory exists")
        else:
            print_error(f"{directory}/ directory missing")
            all_exist = False

    return all_exist


def main():
    """Run all verification checks"""
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║  AI-Powered Training Optimization System - Setup Check    ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════╝{RESET}")

    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Environment File": check_env_file(),
        "Configuration": check_configuration(),
        "Heart Rate Zones": check_heart_rate_zones(),
        "User Profile": check_user_profile(),
        "Security": check_security(),
        "Directories": check_directories(),
    }

    # Summary
    print_header("Verification Summary")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for check_name, result in results.items():
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")

    print(f"\n{BLUE}{'─' * 60}{RESET}")

    if passed == total:
        print(f"\n{GREEN}✓ All checks passed! ({passed}/{total}){RESET}")
        print(f"{GREEN}Your system is ready to use.{RESET}\n")
        print_info("Start the application with: python -m app.main")
        print_info("Visit http://localhost:8000/docs for API documentation")
        return 0
    else:
        print(f"\n{RED}✗ Some checks failed ({passed}/{total} passed){RESET}")
        print(f"{YELLOW}Please fix the errors above before proceeding.{RESET}\n")

        if not results["Dependencies"]:
            print_info("Install dependencies: pip install -r requirements.txt")

        if not results["Environment File"]:
            print_info("Create .env file: cp .env.example .env")

        if not results["Configuration"]:
            print_info("Edit .env and configure required settings")

        return 1


if __name__ == "__main__":
    sys.exit(main())
