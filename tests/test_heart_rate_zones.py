"""
Tests for heart rate zone calculations.
"""

import pytest
import numpy as np

from app.utils.heart_rate_zones import (
    HeartRateZoneCalculator,
    calculate_hr_zones,
    determine_zone,
    calculate_time_in_zones,
    calculate_time_in_zones_from_series,
    get_zone_name,
    get_zone_description,
    analyze_workout_zones,
    format_zone_summary,
)


class TestHeartRateZoneCalculator:
    """Test HR zone calculator class"""

    def test_calculate_zones_percentage(self):
        """Test percentage-based zone calculation"""
        max_hr = 180
        zones = HeartRateZoneCalculator.calculate_zones_percentage(max_hr)

        assert len(zones) == 5

        # Zone 1: 50-60%
        assert zones[1] == (90, 108)

        # Zone 2: 60-70%
        assert zones[2] == (108, 126)

        # Zone 5: 90-100%
        assert zones[5] == (162, 180)

    def test_calculate_zones_karvonen(self):
        """Test Karvonen method zone calculation"""
        max_hr = 180
        resting_hr = 60

        zones = HeartRateZoneCalculator.calculate_zones_karvonen(max_hr, resting_hr)

        assert len(zones) == 5

        # Karvonen should give higher zones than percentage
        # Zone 2: 60-70% of HR reserve + resting
        expected_min = int((120 * 0.60) + 60)  # 132
        expected_max = int((120 * 0.70) + 60)  # 144
        assert zones[2] == (expected_min, expected_max)

    def test_determine_zone(self):
        """Test zone determination"""
        max_hr = 180
        zones = HeartRateZoneCalculator.calculate_zones_percentage(max_hr)

        # Test each zone
        assert HeartRateZoneCalculator.determine_zone(95, zones) == 1
        assert HeartRateZoneCalculator.determine_zone(115, zones) == 2
        assert HeartRateZoneCalculator.determine_zone(135, zones) == 3
        assert HeartRateZoneCalculator.determine_zone(155, zones) == 4
        assert HeartRateZoneCalculator.determine_zone(175, zones) == 5

        # Below all zones
        assert HeartRateZoneCalculator.determine_zone(50, zones) == 0

        # Above all zones (should cap at zone 5)
        assert HeartRateZoneCalculator.determine_zone(200, zones) == 5


class TestCalculateHRZones:
    """Test calculate_hr_zones function"""

    def test_percentage_method(self):
        """Test percentage method"""
        zones = calculate_hr_zones(180, method="percentage")

        assert len(zones) == 5
        assert zones[1]["name"] == "Recovery"
        assert zones[2]["name"] == "Easy Aerobic"
        assert zones[5]["name"] == "VO2 Max"

        # Check structure
        assert "range" in zones[1]
        assert "min_hr" in zones[1]
        assert "max_hr" in zones[1]
        assert "percentage" in zones[1]
        assert "description" in zones[1]

    def test_karvonen_method(self):
        """Test Karvonen method"""
        zones = calculate_hr_zones(180, resting_heart_rate=60, method="karvonen")

        assert len(zones) == 5

        # Karvonen should give different ranges than percentage
        zone2 = zones[2]
        assert zone2["min_hr"] > 108  # Higher than percentage method
        assert zone2["max_hr"] > 126

    def test_default_method(self):
        """Test default method is percentage"""
        zones1 = calculate_hr_zones(180)
        zones2 = calculate_hr_zones(180, method="percentage")

        assert zones1 == zones2


class TestDetermineZone:
    """Test determine_zone function"""

    def test_percentage_method(self):
        """Test zone determination with percentage method"""
        assert determine_zone(95, 180) == 1
        assert determine_zone(115, 180) == 2
        assert determine_zone(135, 180) == 3
        assert determine_zone(155, 180) == 4
        assert determine_zone(175, 180) == 5

    def test_karvonen_method(self):
        """Test zone determination with Karvonen method"""
        zone = determine_zone(140, 180, resting_heart_rate=60, method="karvonen")
        assert zone in [2, 3]  # Should be in easy/moderate range

    def test_edge_cases(self):
        """Test edge cases"""
        assert determine_zone(50, 180) == 0  # Below zone 1
        assert determine_zone(200, 180) == 5  # Above zone 5


class TestCalculateTimeInZones:
    """Test time in zones calculation"""

    def test_basic_calculation(self):
        """Test basic time in zones calculation"""
        heart_rates = [100, 110, 120, 130, 140, 150, 160]
        time_in_zones = calculate_time_in_zones(heart_rates, 180)

        # Should have entries for all zones
        assert len(time_in_zones) == 6  # 0-5

        # Total time should equal number of samples (in minutes)
        total = sum(time_in_zones.values())
        assert abs(total - (len(heart_rates) / 60)) < 0.01

    def test_sampling_interval(self):
        """Test with different sampling intervals"""
        heart_rates = [120, 120, 120]  # 3 samples

        # 1 second intervals
        time1 = calculate_time_in_zones(heart_rates, 180, sampling_interval=1.0)
        assert abs(sum(time1.values()) - 0.05) < 0.01  # 3 seconds = 0.05 min

        # 60 second intervals
        time60 = calculate_time_in_zones(heart_rates, 180, sampling_interval=60.0)
        assert abs(sum(time60.values()) - 3.0) < 0.01  # 3 minutes

    def test_empty_list(self):
        """Test with empty heart rate list"""
        time_in_zones = calculate_time_in_zones([], 180)

        assert all(time == 0.0 for time in time_in_zones.values())


class TestCalculateTimeInZonesFromSeries:
    """Test time in zones from time series"""

    def test_with_timestamps(self):
        """Test with timestamp data"""
        hrs = np.array([120, 130, 140, 150, 160])
        times = np.array([0, 60, 120, 180, 240])  # Every 60 seconds

        time_in_zones = calculate_time_in_zones_from_series(hrs, times, 180)

        # Each sample represents 1 minute (60 seconds)
        # Total time should be ~4 minutes (intervals between 5 points)
        total = sum(time_in_zones.values())
        assert abs(total - 4.0) < 0.1

    def test_irregular_intervals(self):
        """Test with irregular time intervals"""
        hrs = np.array([120, 130, 140])
        times = np.array([0, 30, 90])  # 30s, then 60s

        time_in_zones = calculate_time_in_zones_from_series(hrs, times, 180)

        total = sum(time_in_zones.values())
        assert abs(total - 1.5) < 0.01  # (30 + 60) / 60 = 1.5 min

    def test_mismatched_lengths(self):
        """Test error on mismatched array lengths"""
        hrs = np.array([120, 130, 140])
        times = np.array([0, 60])  # Wrong length

        with pytest.raises(ValueError):
            calculate_time_in_zones_from_series(hrs, times, 180)

    def test_empty_arrays(self):
        """Test with empty arrays"""
        hrs = np.array([])
        times = np.array([])

        time_in_zones = calculate_time_in_zones_from_series(hrs, times, 180)

        assert all(time == 0.0 for time in time_in_zones.values())


class TestZoneUtilities:
    """Test utility functions"""

    def test_get_zone_name(self):
        """Test zone name retrieval"""
        assert "Recovery" in get_zone_name(1)
        assert "Easy" in get_zone_name(2)
        assert "Moderate" in get_zone_name(3)
        assert "Threshold" in get_zone_name(4)
        assert "VO2" in get_zone_name(5)
        assert "Below" in get_zone_name(0)

    def test_get_zone_description(self):
        """Test zone description retrieval"""
        desc1 = get_zone_description(1)
        assert len(desc1) > 0
        assert "recovery" in desc1.lower()

        desc5 = get_zone_description(5)
        assert "maximum" in desc5.lower() or "VO2" in desc5


class TestAnalyzeWorkoutZones:
    """Test workout zone analysis"""

    def test_basic_analysis(self):
        """Test basic workout analysis"""
        hrs = [120, 130, 140, 150, 160, 155, 145, 135, 125]
        analysis = analyze_workout_zones(hrs, 180, 60)

        assert "total_time" in analysis
        assert "time_in_zones" in analysis
        assert "percentage_in_zones" in analysis
        assert "zones" in analysis
        assert "statistics" in analysis
        assert "recommendation" in analysis

        # Check statistics
        stats = analysis["statistics"]
        assert "avg_hr" in stats
        assert "max_hr" in stats
        assert "min_hr" in stats
        assert "dominant_zone" in stats

        assert stats["max_hr"] == 160
        assert stats["min_hr"] == 120

    def test_dominant_zone(self):
        """Test dominant zone identification"""
        # Mostly zone 2 heart rates
        hrs = [110] * 20 + [150] * 5
        analysis = analyze_workout_zones(hrs, 180, 60)

        assert analysis["statistics"]["dominant_zone"] == 2

    def test_recommendations(self):
        """Test workout recommendations"""
        # Zone 2 workout
        hrs = [115] * 10
        analysis = analyze_workout_zones(hrs, 180, 60)
        assert "base" in analysis["recommendation"].lower() or "aerobic" in analysis["recommendation"].lower()

        # Zone 5 workout
        hrs = [175] * 10
        analysis = analyze_workout_zones(hrs, 180, 60)
        assert "high" in analysis["recommendation"].lower() or "VO2" in analysis["recommendation"]

    def test_empty_data(self):
        """Test with empty data"""
        analysis = analyze_workout_zones([], 180, 60)

        assert "error" in analysis
        assert analysis["total_time"] == 0.0


class TestFormatZoneSummary:
    """Test zone summary formatting"""

    def test_format_summary(self):
        """Test summary formatting"""
        zones = calculate_hr_zones(180, 60)
        time_in_zones = {1: 5.0, 2: 20.0, 3: 10.0, 4: 5.0, 5: 0.0, 0: 0.0}

        summary = format_zone_summary(time_in_zones, zones)

        assert "Zone 1" in summary
        assert "Zone 2" in summary
        assert "20.0 min" in summary  # Zone 2 time
        assert "Total" in summary


class TestRealWorldScenarios:
    """Test with realistic workout scenarios"""

    def test_easy_run(self):
        """Test analysis of an easy run"""
        # 30-minute easy run, mostly zone 2
        hrs = [110, 115, 120, 125, 120, 115, 125, 120, 118, 122] * 18  # ~30 min

        analysis = analyze_workout_zones(hrs, 185, 55, sampling_interval=10.0)

        assert analysis["statistics"]["dominant_zone"] == 2
        assert analysis["total_time"] > 25  # At least 25 minutes

    def test_interval_workout(self):
        """Test analysis of interval workout"""
        # Warm-up, intervals, recovery, cool-down
        warmup = [110] * 10
        interval1 = [170] * 5
        recovery1 = [120] * 3
        interval2 = [175] * 5
        recovery2 = [120] * 3
        cooldown = [110] * 10

        hrs = warmup + interval1 + recovery1 + interval2 + recovery2 + cooldown

        analysis = analyze_workout_zones(hrs, 185, 55, sampling_interval=60.0)

        # Should have time in multiple zones
        time_zones = analysis["time_in_zones"]
        zones_used = sum(1 for t in time_zones.values() if t > 0)
        assert zones_used >= 3  # Multiple zones used

    def test_threshold_run(self):
        """Test threshold run analysis"""
        # 20-minute threshold run at zone 4
        warmup = [115] * 5
        threshold = [160] * 20
        cooldown = [110] * 5

        hrs = warmup + threshold + cooldown

        analysis = analyze_workout_zones(hrs, 185, 55, sampling_interval=60.0)

        assert analysis["statistics"]["dominant_zone"] == 4
        assert "threshold" in analysis["recommendation"].lower()
