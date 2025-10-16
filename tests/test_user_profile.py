"""
Tests for user profile models.
"""

import pytest
from datetime import date, datetime

from app.models.user_profile import (
    UserProfile,
    HeartRateZones,
    TrainingGoal,
    AthleteMetrics,
    Gender,
    TrainingGoalType,
)


class TestHeartRateZones:
    """Test heart rate zones model"""

    def test_zone_calculation(self):
        """Test automatic zone calculation"""
        zones = HeartRateZones(
            max_heart_rate=180,
            resting_heart_rate=60
        )

        # Zone 1: 50-60% of 180
        assert zones.zone1_min == 90
        assert zones.zone1_max == 108

        # Zone 2: 60-70%
        assert zones.zone2_min == 109
        assert zones.zone2_max == 126

        # Zone 5: 90-100%
        assert zones.zone5_min == 163
        assert zones.zone5_max == 180

    def test_hr_reserve(self):
        """Test heart rate reserve calculation"""
        zones = HeartRateZones(max_heart_rate=185, resting_heart_rate=55)
        assert zones.hr_reserve == 130

    def test_get_zone(self):
        """Test zone determination"""
        zones = HeartRateZones(max_heart_rate=180, resting_heart_rate=60)

        assert zones.get_zone(100) == 1
        assert zones.get_zone(115) == 2
        assert zones.get_zone(135) == 3
        assert zones.get_zone(155) == 4
        assert zones.get_zone(170) == 5
        assert zones.get_zone(50) == 0  # Below zone 1

    def test_get_zone_range(self):
        """Test zone range retrieval"""
        zones = HeartRateZones(max_heart_rate=180, resting_heart_rate=60)

        min_hr, max_hr = zones.get_zone_range(2)
        assert min_hr == 109
        assert max_hr == 126

        with pytest.raises(ValueError):
            zones.get_zone_range(6)  # Invalid zone

    def test_get_zone_name(self):
        """Test zone name retrieval"""
        zones = HeartRateZones(max_heart_rate=180, resting_heart_rate=60)

        assert "Recovery" in zones.get_zone_name(1)
        assert "Easy" in zones.get_zone_name(2)
        assert "Threshold" in zones.get_zone_name(4)

    def test_to_dict(self):
        """Test dictionary conversion"""
        zones = HeartRateZones(max_heart_rate=180, resting_heart_rate=60)
        d = zones.to_dict()

        assert "max_heart_rate" in d
        assert "zones" in d
        assert len(d["zones"]) == 5

        # Check zone structure
        zone1 = d["zones"][0]
        assert zone1["zone"] == 1
        assert zone1["name"] == "Recovery"
        assert "description" in zone1


class TestTrainingGoal:
    """Test training goal model"""

    def test_basic_goal(self):
        """Test basic goal creation"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.RACE,
            description="Marathon under 3 hours",
            target_date=date(2026, 10, 15),
            priority=1
        )

        assert goal.goal_type == TrainingGoalType.RACE
        assert goal.description == "Marathon under 3 hours"
        assert goal.is_active
        assert not goal.completed

    def test_race_goal_with_details(self):
        """Test race goal with additional details"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.RACE,
            description="Berlin Marathon",
            target_date=date(2026, 9, 27),
            race_name="BMW Berlin Marathon",
            race_distance=42.195,
            target_time="02:59:59"
        )

        assert goal.race_name == "BMW Berlin Marathon"
        assert goal.race_distance == 42.195
        assert goal.target_time == "02:59:59"

    def test_past_date_validation(self):
        """Test that past dates are rejected"""
        with pytest.raises(ValueError):
            TrainingGoal(
                goal_type=TrainingGoalType.RACE,
                description="Past race",
                target_date=date(2020, 1, 1)
            )

    def test_completed_goal(self):
        """Test completed goal validation"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Improve fitness",
            completed=True,
            completed_date=date.today()
        )

        assert goal.completed
        assert goal.completed_date is not None


class TestAthleteMetrics:
    """Test athlete metrics model"""

    def test_basic_metrics(self):
        """Test basic metrics creation"""
        metrics = AthleteMetrics(
            resting_hr=55,
            max_hr=185,
            vo2_max=52.0,
            weight=75.0
        )

        assert metrics.resting_hr == 55
        assert metrics.max_hr == 185
        assert isinstance(metrics.recorded_at, datetime)

    def test_recovery_metrics(self):
        """Test recovery-related metrics"""
        metrics = AthleteMetrics(
            hrv=65.0,
            sleep_hours=7.5,
            fatigue_level=3,
            stress_level=4
        )

        assert metrics.hrv == 65.0
        assert metrics.sleep_hours == 7.5
        assert 1 <= metrics.fatigue_level <= 10
        assert 1 <= metrics.stress_level <= 10

    def test_performance_metrics(self):
        """Test performance metrics"""
        metrics = AthleteMetrics(
            ftp=250,
            lactate_threshold_hr=165,
            vo2_max=55.0
        )

        assert metrics.ftp == 250
        assert metrics.lactate_threshold_hr == 165


class TestUserProfile:
    """Test user profile model"""

    def test_basic_profile(self):
        """Test basic profile creation"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Improve fitness"
        )

        profile = UserProfile(
            athlete_name="John Doe",
            email="john@example.com",
            age=35,
            gender=Gender.MALE,
            max_heart_rate=185,
            resting_heart_rate=55,
            primary_goal=goal
        )

        assert profile.athlete_name == "John Doe"
        assert profile.age == 35
        assert profile.gender == Gender.MALE

    def test_zones_auto_calculation(self):
        """Test that zones are calculated automatically"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test"
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        assert profile.heart_rate_zones is not None
        assert profile.heart_rate_zones.max_heart_rate == 180

    def test_get_zone_for_hr(self):
        """Test zone determination from profile"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test"
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        assert profile.get_zone_for_hr(115) == 2
        assert profile.get_zone_for_hr(155) == 4

    def test_bmi_calculation(self):
        """Test BMI calculation"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test"
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            weight=75.0,
            height=180.0,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        assert profile.bmi is not None
        assert 20 <= profile.bmi <= 25  # Normal range

    def test_days_to_goal(self):
        """Test days to goal calculation"""
        future_date = date(2026, 12, 31)
        goal = TrainingGoal(
            goal_type=TrainingGoalType.RACE,
            description="Test race",
            target_date=future_date
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        assert profile.days_to_goal is not None
        assert profile.days_to_goal > 0

    def test_estimated_max_hr(self):
        """Test estimated max HR formula"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test"
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        # 220 - 30 = 190
        assert profile.estimated_max_hr == 190

    def test_update_metrics(self):
        """Test updating athlete metrics"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test"
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=goal
        )

        new_metrics = AthleteMetrics(
            resting_hr=58,
            max_hr=182,
            vo2_max=55.0
        )

        profile.update_metrics(new_metrics)

        assert profile.current_metrics is not None
        assert profile.current_metrics.vo2_max == 55.0

        # Should update HR and recalculate zones
        assert profile.max_heart_rate == 182
        assert profile.resting_heart_rate == 58

    def test_to_summary_dict(self):
        """Test summary dictionary creation"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.RACE,
            description="Marathon under 3 hours",
            target_date=date(2026, 10, 15)
        )

        profile = UserProfile(
            athlete_name="John Doe",
            email="john@example.com",
            age=35,
            gender=Gender.MALE,
            weight=75.0,
            height=180.0,
            max_heart_rate=185,
            resting_heart_rate=55,
            primary_goal=goal
        )

        summary = profile.to_summary_dict()

        assert "name" in summary
        assert "age" in summary
        assert "primary_goal" in summary
        assert "max_hr" in summary
        assert summary["name"] == "John Doe"

    def test_multiple_goals(self):
        """Test profile with multiple goals"""
        primary = TrainingGoal(
            goal_type=TrainingGoalType.RACE,
            description="Marathon",
            priority=1
        )

        secondary1 = TrainingGoal(
            goal_type=TrainingGoalType.SPEED,
            description="Improve 5K time",
            priority=2
        )

        secondary2 = TrainingGoal(
            goal_type=TrainingGoalType.ENDURANCE,
            description="Build base",
            priority=3
        )

        profile = UserProfile(
            athlete_name="Test",
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            max_heart_rate=180,
            resting_heart_rate=60,
            primary_goal=primary,
            secondary_goals=[secondary1, secondary2]
        )

        assert len(profile.secondary_goals) == 2
        assert profile.secondary_goals[0].description == "Improve 5K time"


class TestProfileValidation:
    """Test profile validation"""

    def test_max_hr_warning(self):
        """Test max HR validation warning"""
        goal = TrainingGoal(
            goal_type=TrainingGoalType.FITNESS,
            description="Test"
        )

        # Max HR very different from age estimate should warn
        # Age 30 -> estimated 190, actual 150 (difference > 30)
        with pytest.warns(UserWarning):
            profile = UserProfile(
                athlete_name="Test",
                email="test@example.com",
                age=30,
                gender=Gender.MALE,
                max_heart_rate=150,  # Much lower than 220-30=190
                resting_heart_rate=50,
                primary_goal=goal
            )
