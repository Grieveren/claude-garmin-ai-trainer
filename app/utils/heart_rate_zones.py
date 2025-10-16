"""
Heart rate zone calculation utilities.

Provides functions for calculating 5-zone heart rate training zones,
determining which zone a heart rate falls into, and analyzing time spent
in each zone during workouts.

Zone definitions:
- Zone 1 (Recovery): 50-60% max HR - Active recovery, warm-up
- Zone 2 (Easy): 60-70% max HR - Base aerobic training
- Zone 3 (Moderate): 70-80% max HR - Aerobic endurance
- Zone 4 (Threshold): 80-90% max HR - Lactate threshold
- Zone 5 (Max): 90-100% max HR - VO2 max intervals
"""

from typing import Dict, List, Tuple, Optional
import numpy as np


class HeartRateZoneCalculator:
    """
    Calculator for heart rate training zones.

    Supports both percentage-based (% of max HR) and Karvonen method
    (using heart rate reserve).
    """

    # Zone boundaries as percentages of max HR
    ZONE_PERCENTAGES = {
        1: (0.50, 0.60),  # Recovery
        2: (0.60, 0.70),  # Easy aerobic
        3: (0.70, 0.80),  # Moderate aerobic
        4: (0.80, 0.90),  # Threshold
        5: (0.90, 1.00),  # VO2 max
    }

    ZONE_NAMES = {
        0: "Below Zone 1",
        1: "Zone 1 - Recovery",
        2: "Zone 2 - Easy Aerobic",
        3: "Zone 3 - Moderate Aerobic",
        4: "Zone 4 - Threshold",
        5: "Zone 5 - VO2 Max",
    }

    ZONE_DESCRIPTIONS = {
        1: "Active recovery, warm-up, cool-down. Very comfortable pace. Can easily hold conversation.",
        2: "Base aerobic training. Comfortable, conversational pace. Builds endurance foundation.",
        3: "Aerobic endurance. Moderate effort, can talk in short sentences. Improves aerobic capacity.",
        4: "Lactate threshold training. Hard effort, minimal talking. Increases speed and performance.",
        5: "VO2 max intervals. Maximum effort, very hard breathing. Boosts maximum performance.",
    }

    @staticmethod
    def calculate_zones_percentage(
        max_heart_rate: int,
        method: str = "percentage"
    ) -> Dict[int, Tuple[int, int]]:
        """
        Calculate heart rate zones using percentage of max HR.

        Args:
            max_heart_rate: Maximum heart rate in bpm
            method: Calculation method ('percentage' or 'simple')

        Returns:
            dict: Zone number -> (min_hr, max_hr) tuple

        Example:
            >>> zones = HeartRateZoneCalculator.calculate_zones_percentage(180)
            >>> zones[2]  # Zone 2
            (108, 126)
        """
        zones = {}

        for zone, (min_pct, max_pct) in HeartRateZoneCalculator.ZONE_PERCENTAGES.items():
            min_hr = round(max_heart_rate * min_pct)
            max_hr = round(max_heart_rate * max_pct)
            zones[zone] = (min_hr, max_hr)

        return zones

    @staticmethod
    def calculate_zones_karvonen(
        max_heart_rate: int,
        resting_heart_rate: int
    ) -> Dict[int, Tuple[int, int]]:
        """
        Calculate heart rate zones using Karvonen method (heart rate reserve).

        The Karvonen method uses heart rate reserve (max HR - resting HR) to
        calculate zones, which can be more accurate for individual athletes.

        Formula: Target HR = ((max HR - resting HR) × intensity%) + resting HR

        Args:
            max_heart_rate: Maximum heart rate in bpm
            resting_heart_rate: Resting heart rate in bpm

        Returns:
            dict: Zone number -> (min_hr, max_hr) tuple

        Example:
            >>> zones = HeartRateZoneCalculator.calculate_zones_karvonen(180, 60)
            >>> zones[2]  # Zone 2
            (132, 144)
        """
        hr_reserve = max_heart_rate - resting_heart_rate
        zones = {}

        for zone, (min_pct, max_pct) in HeartRateZoneCalculator.ZONE_PERCENTAGES.items():
            min_hr = round((hr_reserve * min_pct) + resting_heart_rate)
            max_hr = round((hr_reserve * max_pct) + resting_heart_rate)
            zones[zone] = (min_hr, max_hr)

        return zones

    @staticmethod
    def determine_zone(
        heart_rate: int,
        zones: Dict[int, Tuple[int, int]]
    ) -> int:
        """
        Determine which zone a heart rate value falls into.

        Args:
            heart_rate: Heart rate value in bpm
            zones: Zone definitions from calculate_zones_*

        Returns:
            int: Zone number (1-5), or 0 if below zone 1

        Example:
            >>> zones = HeartRateZoneCalculator.calculate_zones_percentage(180)
            >>> HeartRateZoneCalculator.determine_zone(120, zones)
            2
        """
        for zone in range(1, 6):
            min_hr, max_hr = zones[zone]
            if min_hr <= heart_rate <= max_hr:
                return zone

        # Check if above all zones
        if heart_rate > zones[5][1]:
            return 5

        # Below all zones
        return 0


def calculate_hr_zones(
    max_heart_rate: int,
    resting_heart_rate: Optional[int] = None,
    method: str = "percentage"
) -> Dict[int, Dict[str, any]]:
    """
    Calculate heart rate training zones with detailed information.

    Args:
        max_heart_rate: Maximum heart rate in bpm
        resting_heart_rate: Resting heart rate (optional, for Karvonen method)
        method: 'percentage' (default) or 'karvonen'

    Returns:
        dict: Zone information including ranges, names, and descriptions

    Example:
        >>> zones = calculate_hr_zones(180, 60, method='karvonen')
        >>> zones[2]['name']
        'Easy Aerobic'
        >>> zones[2]['range']
        (132, 144)
    """
    if method == "karvonen" and resting_heart_rate:
        zone_ranges = HeartRateZoneCalculator.calculate_zones_karvonen(
            max_heart_rate, resting_heart_rate
        )
    else:
        zone_ranges = HeartRateZoneCalculator.calculate_zones_percentage(
            max_heart_rate
        )

    zones = {}
    zone_info = {
        1: ("Recovery", "50-60%"),
        2: ("Easy Aerobic", "60-70%"),
        3: ("Moderate Aerobic", "70-80%"),
        4: ("Threshold", "80-90%"),
        5: ("VO2 Max", "90-100%"),
    }

    for zone_num in range(1, 6):
        min_hr, max_hr = zone_ranges[zone_num]
        name, percentage = zone_info[zone_num]

        zones[zone_num] = {
            "zone": zone_num,
            "name": name,
            "range": (min_hr, max_hr),
            "min_hr": min_hr,
            "max_hr": max_hr,
            "percentage": percentage,
            "description": HeartRateZoneCalculator.ZONE_DESCRIPTIONS[zone_num],
        }

    return zones


def determine_zone(
    heart_rate: int,
    max_heart_rate: int,
    resting_heart_rate: Optional[int] = None,
    method: str = "percentage"
) -> int:
    """
    Determine which training zone a heart rate value falls into.

    Args:
        heart_rate: Heart rate value to classify
        max_heart_rate: Maximum heart rate
        resting_heart_rate: Resting heart rate (optional)
        method: 'percentage' or 'karvonen'

    Returns:
        int: Zone number (0-5, where 0 is below zone 1)

    Example:
        >>> determine_zone(140, 180, 60, method='karvonen')
        2
    """
    zones_detail = calculate_hr_zones(max_heart_rate, resting_heart_rate, method)

    for zone_num, zone_info in zones_detail.items():
        min_hr, max_hr = zone_info["range"]
        if min_hr <= heart_rate <= max_hr:
            return zone_num

    # Check if above all zones
    if heart_rate > zones_detail[5]["max_hr"]:
        return 5

    # Below all zones
    return 0


def calculate_time_in_zones(
    heart_rates: List[int],
    max_heart_rate: int,
    resting_heart_rate: Optional[int] = None,
    method: str = "percentage",
    sampling_interval: float = 1.0
) -> Dict[int, float]:
    """
    Calculate time spent in each heart rate zone during a workout.

    Args:
        heart_rates: List of heart rate measurements
        max_heart_rate: Maximum heart rate
        resting_heart_rate: Resting heart rate (optional)
        method: 'percentage' or 'karvonen'
        sampling_interval: Time between measurements in seconds (default 1.0)

    Returns:
        dict: Zone number -> time in minutes

    Example:
        >>> hrs = [120, 125, 130, 140, 145, 150, 155]
        >>> time_in_zones = calculate_time_in_zones(hrs, 180, 60)
        >>> time_in_zones[2]  # Minutes in zone 2
        0.05
    """
    if not heart_rates:
        return {zone: 0.0 for zone in range(0, 6)}

    zones_detail = calculate_hr_zones(max_heart_rate, resting_heart_rate, method)

    # Count samples in each zone
    zone_counts = {zone: 0 for zone in range(0, 6)}

    for hr in heart_rates:
        zone = determine_zone(hr, max_heart_rate, resting_heart_rate, method)
        zone_counts[zone] += 1

    # Convert counts to minutes
    time_in_zones = {}
    for zone, count in zone_counts.items():
        time_in_zones[zone] = (count * sampling_interval) / 60.0

    return time_in_zones


def calculate_time_in_zones_from_series(
    heart_rate_series: np.ndarray,
    timestamps: np.ndarray,
    max_heart_rate: int,
    resting_heart_rate: Optional[int] = None,
    method: str = "percentage"
) -> Dict[int, float]:
    """
    Calculate time in zones from time-series data with timestamps.

    Args:
        heart_rate_series: NumPy array of heart rate values
        timestamps: NumPy array of timestamps (seconds since start)
        max_heart_rate: Maximum heart rate
        resting_heart_rate: Resting heart rate (optional)
        method: 'percentage' or 'karvonen'

    Returns:
        dict: Zone number -> time in minutes

    Example:
        >>> hrs = np.array([120, 125, 130, 140, 145])
        >>> times = np.array([0, 60, 120, 180, 240])  # Every 60 seconds
        >>> result = calculate_time_in_zones_from_series(hrs, times, 180, 60)
    """
    if len(heart_rate_series) != len(timestamps):
        raise ValueError("heart_rate_series and timestamps must have same length")

    if len(heart_rate_series) == 0:
        return {zone: 0.0 for zone in range(0, 6)}

    # Calculate time intervals
    intervals = np.diff(timestamps, prepend=0)

    # Determine zone for each measurement
    zones_detail = calculate_hr_zones(max_heart_rate, resting_heart_rate, method)
    zones_array = np.array([
        determine_zone(hr, max_heart_rate, resting_heart_rate, method)
        for hr in heart_rate_series
    ])

    # Sum time in each zone
    time_in_zones = {}
    for zone in range(0, 6):
        mask = zones_array == zone
        time_in_zones[zone] = float(np.sum(intervals[mask]) / 60.0)

    return time_in_zones


def get_zone_name(zone: int) -> str:
    """
    Get descriptive name for a zone.

    Args:
        zone: Zone number (0-5)

    Returns:
        str: Zone name

    Example:
        >>> get_zone_name(2)
        'Zone 2 - Easy Aerobic'
    """
    return HeartRateZoneCalculator.ZONE_NAMES.get(zone, "Unknown")


def get_zone_description(zone: int) -> str:
    """
    Get detailed description for a zone.

    Args:
        zone: Zone number (1-5)

    Returns:
        str: Zone description

    Example:
        >>> desc = get_zone_description(2)
        >>> 'conversational' in desc.lower()
        True
    """
    return HeartRateZoneCalculator.ZONE_DESCRIPTIONS.get(zone, "")


def analyze_workout_zones(
    heart_rates: List[int],
    max_heart_rate: int,
    resting_heart_rate: Optional[int] = None,
    method: str = "percentage",
    sampling_interval: float = 1.0
) -> Dict[str, any]:
    """
    Complete analysis of heart rate zones for a workout.

    Args:
        heart_rates: List of heart rate measurements
        max_heart_rate: Maximum heart rate
        resting_heart_rate: Resting heart rate (optional)
        method: 'percentage' or 'karvonen'
        sampling_interval: Time between measurements in seconds

    Returns:
        dict: Complete zone analysis with time, percentages, and recommendations

    Example:
        >>> hrs = [120, 130, 140, 150, 160, 155, 145, 135, 125]
        >>> analysis = analyze_workout_zones(hrs, 180, 60)
        >>> analysis['total_time']
        0.15
    """
    if not heart_rates:
        return {
            "error": "No heart rate data provided",
            "total_time": 0.0,
        }

    # Calculate time in zones
    time_in_zones = calculate_time_in_zones(
        heart_rates, max_heart_rate, resting_heart_rate, method, sampling_interval
    )

    total_time = sum(time_in_zones.values())

    # Calculate percentages
    percentages = {}
    for zone, time in time_in_zones.items():
        percentages[zone] = (time / total_time * 100) if total_time > 0 else 0.0

    # Get zone details
    zones_detail = calculate_hr_zones(max_heart_rate, resting_heart_rate, method)

    # Build analysis
    analysis = {
        "total_time": total_time,
        "time_in_zones": time_in_zones,
        "percentage_in_zones": percentages,
        "zones": zones_detail,
        "statistics": {
            "avg_hr": np.mean(heart_rates),
            "max_hr": np.max(heart_rates),
            "min_hr": np.min(heart_rates),
            "dominant_zone": max(
                [(z, t) for z, t in time_in_zones.items() if z > 0],
                key=lambda x: x[1],
                default=(0, 0)
            )[0],
        },
    }

    # Add training recommendations
    dominant_zone = analysis["statistics"]["dominant_zone"]
    if dominant_zone == 1:
        analysis["recommendation"] = "Recovery workout - great for active recovery days."
    elif dominant_zone == 2:
        analysis["recommendation"] = "Base-building workout - excellent for aerobic foundation."
    elif dominant_zone == 3:
        analysis["recommendation"] = "Tempo workout - good for aerobic endurance."
    elif dominant_zone == 4:
        analysis["recommendation"] = "Threshold workout - improves lactate clearance and speed."
    elif dominant_zone == 5:
        analysis["recommendation"] = "High-intensity workout - boosts VO2 max. Ensure adequate recovery."
    else:
        analysis["recommendation"] = "Incomplete data or very low intensity."

    return analysis


def format_zone_summary(
    time_in_zones: Dict[int, float],
    zones_detail: Dict[int, Dict[str, any]]
) -> str:
    """
    Format zone time distribution as readable text.

    Args:
        time_in_zones: Time spent in each zone (minutes)
        zones_detail: Zone details from calculate_hr_zones()

    Returns:
        str: Formatted summary

    Example:
        >>> zones = calculate_hr_zones(180, 60)
        >>> times = {1: 5.0, 2: 20.0, 3: 10.0, 4: 5.0, 5: 0.0}
        >>> print(format_zone_summary(times, zones))
    """
    lines = ["Heart Rate Zone Distribution:", "=" * 40]

    total_time = sum(t for z, t in time_in_zones.items() if z > 0)

    for zone in range(1, 6):
        time = time_in_zones.get(zone, 0.0)
        if time > 0:
            zone_info = zones_detail[zone]
            percentage = (time / total_time * 100) if total_time > 0 else 0
            lines.append(
                f"Zone {zone} ({zone_info['name']}): "
                f"{time:.1f} min ({percentage:.1f}%) "
                f"[{zone_info['min_hr']}-{zone_info['max_hr']} bpm]"
            )

    lines.append("=" * 40)
    lines.append(f"Total: {total_time:.1f} minutes")

    return "\n".join(lines)
