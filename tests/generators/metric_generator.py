"""Test data generators for daily metrics and related data."""

import random
import math
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DistributionParams:
    """Parameters for statistical distributions."""

    mean: float
    std_dev: float
    min_val: float
    max_val: float


class RealisticDistribution:
    """Generate realistic metric distributions using normal and poisson distributions."""

    @staticmethod
    def normal(params: DistributionParams) -> float:
        """
        Generate value from normal distribution.

        Args:
            params: Distribution parameters

        Returns:
            float: Normally distributed value, clamped to min/max
        """
        value = random.gauss(params.mean, params.std_dev)
        return max(params.min_val, min(params.max_val, value))

    @staticmethod
    def poisson(mean: float, min_val: float = 0, max_val: float = float("inf")) -> int:
        """
        Generate value from poisson distribution.

        Args:
            mean: Mean of distribution
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            int: Poisson-distributed value
        """
        value = random.gauss(mean, math.sqrt(mean))
        return int(max(min_val, min(max_val, value)))

    @staticmethod
    def exponential(mean: float) -> float:
        """
        Generate value from exponential distribution.

        Args:
            mean: Mean of distribution

        Returns:
            float: Exponentially distributed value
        """
        return random.expovariate(1.0 / mean)


class MetricGenerator:
    """Generate realistic daily metrics with proper statistical distributions."""

    # Realistic ranges for different metrics
    HEART_RATE_PARAMS = DistributionParams(mean=95, std_dev=15, min_val=40, max_val=200)
    RESTING_HR_PARAMS = DistributionParams(mean=55, std_dev=5, min_val=40, max_val=80)
    MAX_HR_PARAMS = DistributionParams(mean=180, std_dev=8, min_val=160, max_val=200)

    # HRV parameters (SDNN in milliseconds)
    HRV_SDNN_NORMAL = DistributionParams(mean=48, std_dev=8, min_val=30, max_val=100)
    HRV_SDNN_TIRED = DistributionParams(mean=35, std_dev=5, min_val=25, max_val=45)
    HRV_SDNN_RECOVERED = DistributionParams(mean=60, std_dev=10, min_val=45, max_val=100)

    # Sleep parameters
    SLEEP_DURATION_PARAMS = DistributionParams(mean=420, std_dev=40, min_val=300, max_val=540)
    SLEEP_SCORE_PARAMS = DistributionParams(mean=75, std_dev=10, min_val=40, max_val=100)

    # Stress parameters
    STRESS_SCORE_PARAMS = DistributionParams(mean=45, std_dev=15, min_val=0, max_val=100)

    # Activity parameters
    STEPS_PARAMS = DistributionParams(mean=8500, std_dev=2500, min_val=2000, max_val=20000)
    ACTIVE_MINUTES_PARAMS = DistributionParams(mean=45, std_dev=15, min_val=10, max_val=120)

    # Body metrics
    WEIGHT_KG_PARAMS = DistributionParams(mean=75.0, std_dev=5.0, min_val=60.0, max_val=100.0)
    VO2_MAX_PARAMS = DistributionParams(mean=52.0, std_dev=3.0, min_val=40.0, max_val=65.0)

    @classmethod
    def generate_daily_metrics(
        cls,
        user_id: str,
        date_obj: date,
        recovery_factor: float = 1.0,
        fatigue_factor: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate realistic daily metrics.

        Args:
            user_id: User identifier
            date_obj: Date for metrics
            recovery_factor: 0-1 scale (1.0 = well-rested, 0.0 = normal)
            fatigue_factor: 0-1 scale (0.0 = normal, 1.0 = very fatigued)

        Returns:
            Dict with daily metrics
        """
        # Adjust parameters based on recovery/fatigue
        hrv_params = cls._adjust_hrv_params(recovery_factor, fatigue_factor)
        heart_rate_base = cls.HEART_RATE_PARAMS.mean + (fatigue_factor * 20)
        resting_hr = cls.RESTING_HR_PARAMS.mean + (fatigue_factor * 8)
        stress = cls.STRESS_SCORE_PARAMS.mean + (fatigue_factor * 30)

        # Calculate sleep based on fatigue (fatigue reduces sleep)
        sleep_minutes = int(
            cls.SLEEP_DURATION_PARAMS.mean * (1.0 - fatigue_factor * 0.3) +
            random.gauss(0, cls.SLEEP_DURATION_PARAMS.std_dev * 0.5)
        )

        metrics = {
            "user_id": user_id,
            "date": date_obj,
            # Heart rate metrics
            "resting_heart_rate": int(max(40, min(80, resting_hr))),
            "max_heart_rate": int(cls.normal(cls.MAX_HR_PARAMS)),
            "avg_heart_rate": int(
                max(40, min(200, heart_rate_base + random.gauss(0, 10)))
            ),
            # HRV metrics
            "hrv_sdnn": cls.normal(hrv_params),
            "hrv_rmssd": cls.normal(hrv_params) * 0.72,
            # Stress
            "stress_score": int(max(0, min(100, stress + random.gauss(0, 10)))),
            # Activity
            "steps": cls.poisson(cls.STEPS_PARAMS.mean, 2000, 20000),
            "distance_meters": cls.poisson(6000, 1000, 20000),
            "calories": cls.poisson(2100, 1000, 4000),
            "active_minutes": int(cls.normal(cls.ACTIVE_MINUTES_PARAMS)),
            "floors_climbed": cls.poisson(5, 0, 30),
            # Body battery
            "body_battery_charged": cls.poisson(35, 10, 60),
            "body_battery_drained": cls.poisson(40, 10, 80),
            "body_battery_max": 100,
            "body_battery_min": cls.poisson(20, 5, 40),
            # Sleep
            "sleep_score": int(
                max(40, min(100, cls.SLEEP_SCORE_PARAMS.mean - (fatigue_factor * 30)))
            ),
            "total_sleep_minutes": max(240, min(540, sleep_minutes)),
            "deep_sleep_minutes": int(sleep_minutes * 0.20),
            "light_sleep_minutes": int(sleep_minutes * 0.58),
            "rem_sleep_minutes": int(sleep_minutes * 0.18),
            "awake_minutes": int(sleep_minutes * 0.04),
            # Performance
            "vo2_max": cls.normal(cls.VO2_MAX_PARAMS),
            "fitness_age": cls.poisson(30, 20, 50),
            # Body composition
            "weight_kg": cls.normal(cls.WEIGHT_KG_PARAMS),
            "body_fat_percent": cls.normal(
                DistributionParams(mean=16.0, std_dev=2.0, min_val=8.0, max_val=30.0)
            ),
            "bmi": cls.normal(
                DistributionParams(mean=23.0, std_dev=1.5, min_val=18.0, max_val=30.0)
            ),
            # Hydration
            "hydration_ml": cls.poisson(2200, 1500, 3500),
            # Respiration
            "avg_respiration_rate": cls.normal(
                DistributionParams(mean=14.5, std_dev=1.0, min_val=12.0, max_val=20.0)
            ),
        }

        return metrics

    @classmethod
    def generate_daily_metrics_sequence(
        cls,
        user_id: str,
        start_date: date,
        num_days: int = 30,
        recovery_trend: str = "normal",
    ) -> List[Dict[str, Any]]:
        """
        Generate sequence of daily metrics showing realistic trends.

        Recovery trends:
        - 'normal': Stable metrics
        - 'recovering': Improving recovery over time
        - 'fatiguing': Worsening metrics (overtraining)
        - 'cycling': Cycling between recovery and fatigue

        Args:
            user_id: User identifier
            start_date: Starting date
            num_days: Number of days to generate
            recovery_trend: Type of trend

        Returns:
            List of daily metrics dicts
        """
        metrics_list = []

        for day in range(num_days):
            current_date = start_date + timedelta(days=day)

            # Calculate recovery and fatigue factors based on trend
            if recovery_trend == "normal":
                recovery_factor = 0.5  # Baseline
                fatigue_factor = 0.0

            elif recovery_trend == "recovering":
                recovery_factor = 0.5 + (day / num_days) * 0.5  # Improving
                fatigue_factor = max(0, 1.0 - (day / num_days))  # Decreasing

            elif recovery_trend == "fatiguing":
                recovery_factor = max(0, 0.5 - (day / num_days) * 0.5)  # Decreasing
                fatigue_factor = (day / num_days) * 0.8  # Increasing

            elif recovery_trend == "cycling":
                # 7-day cycle
                cycle_pos = (day % 7) / 7
                recovery_factor = 0.3 + 0.4 * math.sin(cycle_pos * 2 * math.pi)
                fatigue_factor = 0.3 + 0.4 * math.cos(cycle_pos * 2 * math.pi)

            else:
                recovery_factor = 0.5
                fatigue_factor = 0.0

            metrics = cls.generate_daily_metrics(
                user_id,
                current_date,
                recovery_factor=recovery_factor,
                fatigue_factor=fatigue_factor,
            )
            metrics_list.append(metrics)

        return metrics_list

    @classmethod
    def _adjust_hrv_params(cls, recovery_factor: float, fatigue_factor: float) -> DistributionParams:
        """
        Adjust HRV parameters based on recovery/fatigue state.

        Args:
            recovery_factor: Recovery level (0-1)
            fatigue_factor: Fatigue level (0-1)

        Returns:
            DistributionParams: Adjusted HRV parameters
        """
        # Interpolate between states
        if recovery_factor > 0.5:
            # Well-rested
            base_mean = cls.HRV_SDNN_RECOVERED.mean
            base_std = cls.HRV_SDNN_RECOVERED.std_dev
        elif fatigue_factor > 0.5:
            # Tired
            base_mean = cls.HRV_SDNN_TIRED.mean
            base_std = cls.HRV_SDNN_TIRED.std_dev
        else:
            # Normal
            base_mean = cls.HRV_SDNN_NORMAL.mean
            base_std = cls.HRV_SDNN_NORMAL.std_dev

        return DistributionParams(
            mean=base_mean,
            std_dev=base_std,
            min_val=30,
            max_val=100,
        )

    @classmethod
    def normal(cls, params: DistributionParams) -> float:
        """Generate normally distributed value."""
        return RealisticDistribution.normal(params)
