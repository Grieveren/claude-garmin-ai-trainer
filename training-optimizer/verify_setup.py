#!/usr/bin/env python3
"""
Quick verification script to test the basic setup.

Run this after installing dependencies to verify everything is working.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all critical packages can be imported."""
    print("Testing package imports...")

    tests = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("loguru", "Loguru"),
        ("anthropic", "Anthropic"),
        ("garminconnect", "Garmin Connect"),
        ("pandas", "Pandas"),
        ("pytest", "Pytest"),
    ]

    success = 0
    for module, name in tests:
        try:
            __import__(module)
            print(f"  ✓ {name}")
            success += 1
        except ImportError as e:
            print(f"  ✗ {name}: {e}")

    print(f"\n{success}/{len(tests)} packages imported successfully\n")
    return success == len(tests)


def test_app_structure():
    """Test that the application structure is correct."""
    print("Testing project structure...")

    required_paths = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/core/logger.py",
        "app/models/schemas.py",
        "app/templates/base.html",
        "app/static/css/style.css",
        "app/static/js/main.js",
        "scripts/initial_setup.py",
        "tests/conftest.py",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]

    base_dir = Path(__file__).parent
    success = 0

    for path in required_paths:
        full_path = base_dir / path
        if full_path.exists():
            print(f"  ✓ {path}")
            success += 1
        else:
            print(f"  ✗ {path} (missing)")

    print(f"\n{success}/{len(required_paths)} files found\n")
    return success == len(required_paths)


def test_app_import():
    """Test that the main app can be imported."""
    print("Testing application import...")

    try:
        # Set minimal environment variables
        import os
        os.environ.setdefault("GARMIN_EMAIL", "test@example.com")
        os.environ.setdefault("GARMIN_PASSWORD", "test_password")
        os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
        os.environ.setdefault("SECRET_KEY", "test-secret")

        from app.main import app
        print("  ✓ FastAPI app imported successfully")

        # Check app attributes
        print(f"  ✓ App title: {app.title}")
        print(f"  ✓ App version: {app.version}")

        return True
    except Exception as e:
        print(f"  ✗ Failed to import app: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        import os
        os.environ.setdefault("GARMIN_EMAIL", "test@example.com")
        os.environ.setdefault("GARMIN_PASSWORD", "test_password")
        os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
        os.environ.setdefault("SECRET_KEY", "test-secret")

        from app.core.config import settings

        print(f"  ✓ Settings loaded")
        print(f"  ✓ Log level: {settings.log_level}")
        print(f"  ✓ AI model: {settings.ai_model}")
        print(f"  ✓ Database URL: {settings.database_url}")

        return True
    except Exception as e:
        print(f"  ✗ Failed to load config: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("  AI-Powered Training Optimizer - Setup Verification")
    print("=" * 70)
    print()

    results = []

    # Run tests
    results.append(("Package Imports", test_imports()))
    results.append(("Project Structure", test_app_structure()))
    results.append(("Configuration", test_config()))
    results.append(("Application Import", test_app_import()))

    # Summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print()

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n✓ All tests passed! Setup is complete.")
        print("\nNext steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Run: python scripts/initial_setup.py")
        print("  3. Start app: uvicorn app.main:app --reload")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
