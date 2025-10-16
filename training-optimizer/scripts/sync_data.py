#!/usr/bin/env python3
"""
Manual Data Synchronization Script.

This script manually syncs training data from Garmin Connect.
It will be fully implemented after the Garmin service is built.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def sync_activities(days: int = 7) -> None:
    """
    Sync activities from Garmin Connect.

    Args:
        days: Number of days of activities to sync
    """
    print(f"Syncing activities from the last {days} days...")
    print("This functionality will be implemented after the Garmin service is built.")

    # Placeholder for future implementation
    # from app.services.garmin import GarminService
    # from app.core.config import settings
    #
    # garmin_service = GarminService(
    #     email=settings.garmin_email,
    #     password=settings.garmin_password
    # )
    #
    # start_date = datetime.now() - timedelta(days=days)
    # activities = garmin_service.get_activities(start_date)
    #
    # for activity in activities:
    #     # Save to database
    #     pass


def main() -> int:
    """
    Run manual sync.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 70)
    print("  Manual Data Synchronization")
    print("=" * 70)
    print()

    try:
        # Default to last 7 days
        days = 7

        # Check for command line argument
        if len(sys.argv) > 1:
            try:
                days = int(sys.argv[1])
            except ValueError:
                print(f"Invalid number of days: {sys.argv[1]}")
                return 1

        sync_activities(days)

        print("\nSync completed successfully!")
        return 0

    except Exception as e:
        print(f"\nSync failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
