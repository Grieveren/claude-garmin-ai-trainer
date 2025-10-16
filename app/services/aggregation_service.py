"""
Data aggregation service for creating daily, weekly, and monthly summaries.

This service aggregates raw health and activity data into summarized views that
are useful for analysis, reporting, and trend visualization.

Aggregation Levels:
1. Daily Summary: Single day overview of all metrics
2. Weekly Summary: 7-day aggregated view with trends
3. Monthly Summary: 30-day overview with performance trends
"""

from datetime import date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import numpy as np

from app.models.database_models import (
    DailyMetrics,
    Activity,
    SleepSession,
    ActivityType
)
from app.utils import hrv_analysis, training_load, sleep_analysis, statistics


class AggregationService:
    """Service for aggregating health and training data at various time scales."""

    def __init__(self, db: Session):
        """
        Initialize aggregation service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def aggregate_daily_summary(
        self,
        user_id: str,
        target_date: date
    ) -> Dict[str, any]:
        """
        Create comprehensive daily summary for a single day.

        Aggregates all metrics for one day including:
        - Daily health metrics (HRV, sleep, body battery)
        - Activities performed
        - Training load
        - Recovery status
        - Readiness assessment

        Args:
            user_id: User identifier
            target_date: Date to summarize

        Returns:
            Dictionary containing complete daily summary

        Example:
            >>> service = AggregationService(db)
            >>> summary = service.aggregate_daily_summary("user123", date.today())
            >>> print(f"Readiness: {summary['readiness_score']}/100")
        """
        # Get base daily metrics
        daily_metric = self.db.query(DailyMetrics).filter(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.date == target_date
            )
        ).first()

        if not daily_metric:
            return {
                'date': target_date.isoformat(),
                'status': 'no_data',
                'message': 'No data available for this date'
            }

        # Get activities for the day
        activities = self.db.query(Activity).filter(
            and_(
                Activity.user_id == user_id,
                Activity.activity_date == target_date
            )
        ).all()

        # Calculate activity summary
        activity_summary = {
            'count': len(activities),
            'types': list(set([a.activity_type.value for a in activities])),
            'total_duration_minutes': sum([a.duration_minutes or 0 for a in activities]),
            'total_distance_km': sum([a.distance_meters or 0 for a in activities]) / 1000,
            'total_training_load': sum([a.training_load or 0 for a in activities]),
            'activities': [
                {
                    'type': a.activity_type.value,
                    'name': a.activity_name,
                    'duration_minutes': a.duration_minutes,
                    'distance_meters': a.distance_meters,
                    'training_load': a.training_load
                }
                for a in activities
            ]
        }

        # Get HRV status
        hrv_status = hrv_analysis.get_hrv_status(
            self.db,
            user_id,
            target_date
        )

        # Get sleep status
        sleep_status = sleep_analysis.get_sleep_status(
            self.db,
            user_id,
            target_date
        )

        # Get training load status
        load_status = training_load.get_training_load_status(
            self.db,
            user_id,
            target_date
        )

        # Calculate overall readiness score (weighted combination)
        readiness_components = {
            'hrv': hrv_analysis.get_hrv_score(hrv_status),
            'sleep': sleep_analysis.get_sleep_score(sleep_status),
            'training_load': self._calculate_load_score(load_status)
        }

        # Weighted average: HRV 40%, Sleep 35%, Load 25%
        readiness_score = (
            readiness_components['hrv'] * 0.40 +
            readiness_components['sleep'] * 0.35 +
            readiness_components['training_load'] * 0.25
        )

        return {
            'date': target_date.isoformat(),
            'status': 'success',

            # Basic metrics
            'metrics': {
                'steps': daily_metric.steps,
                'resting_heart_rate': daily_metric.resting_heart_rate,
                'hrv_rmssd': daily_metric.hrv_rmssd,
                'body_battery_max': daily_metric.body_battery_max,
                'body_battery_min': daily_metric.body_battery_min,
                'stress_score': daily_metric.stress_score,
                'calories': daily_metric.calories
            },

            # Sleep summary
            'sleep': {
                'total_minutes': daily_metric.total_sleep_minutes,
                'quality_score': sleep_status['last_night']['score'] if sleep_status.get('last_night') else None,
                'deep_minutes': daily_metric.deep_sleep_minutes,
                'rem_minutes': daily_metric.rem_sleep_minutes,
                'status': sleep_status['status']
            },

            # Activity summary
            'activities': activity_summary,

            # Recovery and readiness
            'hrv_status': {
                'current': hrv_status.get('current_hrv'),
                'baseline_7d': hrv_status.get('baseline_7d'),
                'status': hrv_status.get('status'),
                'score': readiness_components['hrv']
            },

            'training_load': {
                'daily': activity_summary['total_training_load'],
                'acute_7d': load_status.get('acute_load'),
                'chronic_28d': load_status.get('chronic_load'),
                'acwr': load_status['acwr']['acwr'] if load_status.get('acwr') else None,
                'form': load_status['fitness_fatigue']['form'] if load_status.get('fitness_fatigue') else None,
                'status': load_status.get('overall_status')
            },

            # Overall readiness
            'readiness': {
                'score': round(readiness_score, 1),
                'components': readiness_components,
                'status': self._get_readiness_status(readiness_score),
                'recommendation': self._get_daily_recommendation(
                    readiness_score,
                    hrv_status,
                    sleep_status,
                    load_status
                )
            }
        }

    def aggregate_weekly_summary(
        self,
        user_id: str,
        week_start: date
    ) -> Dict[str, any]:
        """
        Create weekly aggregated summary (7 days).

        Provides overview of:
        - Training volume and intensity
        - Average sleep and recovery metrics
        - HRV trends
        - Training load progression
        - Weekly performance highlights

        Args:
            user_id: User identifier
            week_start: Start date of the week (typically Monday)

        Returns:
            Dictionary containing weekly summary

        Example:
            >>> service = AggregationService(db)
            >>> monday = date.today() - timedelta(days=date.today().weekday())
            >>> summary = service.aggregate_weekly_summary("user123", monday)
            >>> print(f"Weekly volume: {summary['training']['total_duration_hours']} hours")
        """
        week_end = week_start + timedelta(days=6)

        # Get all daily metrics for the week
        daily_metrics = self.db.query(DailyMetrics).filter(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.date >= week_start,
                DailyMetrics.date <= week_end
            )
        ).order_by(DailyMetrics.date).all()

        if not daily_metrics:
            return {
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'status': 'no_data'
            }

        # Get all activities for the week
        activities = self.db.query(Activity).filter(
            and_(
                Activity.user_id == user_id,
                Activity.activity_date >= week_start,
                Activity.activity_date <= week_end
            )
        ).all()

        # Training summary
        training_summary = self._calculate_training_summary(activities)

        # Sleep summary
        sleep_summary = self._calculate_sleep_summary(daily_metrics)

        # HRV summary
        hrv_summary = self._calculate_hrv_summary(daily_metrics)

        # Recovery summary
        recovery_summary = self._calculate_recovery_summary(daily_metrics)

        # Load progression
        load_progression = self._calculate_load_progression(user_id, week_start)

        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'status': 'success',
            'days_with_data': len(daily_metrics),

            'training': training_summary,
            'sleep': sleep_summary,
            'hrv': hrv_summary,
            'recovery': recovery_summary,
            'load_progression': load_progression,

            'highlights': self._generate_weekly_highlights(
                training_summary,
                sleep_summary,
                hrv_summary,
                load_progression
            )
        }

    def aggregate_monthly_summary(
        self,
        user_id: str,
        month: date  # First day of the month
    ) -> Dict[str, any]:
        """
        Create monthly aggregated summary (30 days).

        Provides long-term overview of:
        - Training volume trends
        - Fitness progression
        - Recovery patterns
        - Performance achievements
        - Monthly goals and progress

        Args:
            user_id: User identifier
            month: First day of the month to summarize

        Returns:
            Dictionary containing monthly summary

        Example:
            >>> service = AggregationService(db)
            >>> first_of_month = date.today().replace(day=1)
            >>> summary = service.aggregate_monthly_summary("user123", first_of_month)
        """
        # Calculate month boundaries
        if month.month == 12:
            month_end = date(month.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month.year, month.month + 1, 1) - timedelta(days=1)

        # Get all daily metrics for the month
        daily_metrics = self.db.query(DailyMetrics).filter(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.date >= month,
                DailyMetrics.date <= month_end
            )
        ).order_by(DailyMetrics.date).all()

        if not daily_metrics:
            return {
                'month_start': month.isoformat(),
                'month_end': month_end.isoformat(),
                'status': 'no_data'
            }

        # Get all activities for the month
        activities = self.db.query(Activity).filter(
            and_(
                Activity.user_id == user_id,
                Activity.activity_date >= month,
                Activity.activity_date <= month_end
            )
        ).all()

        # Monthly training summary
        training_summary = self._calculate_monthly_training_summary(activities)

        # Monthly averages
        monthly_averages = self._calculate_monthly_averages(daily_metrics)

        # Trends analysis
        trends = self._calculate_monthly_trends(daily_metrics)

        # Personal records and achievements
        achievements = self._identify_monthly_achievements(activities)

        return {
            'month_start': month.isoformat(),
            'month_end': month_end.isoformat(),
            'status': 'success',
            'days_with_data': len(daily_metrics),

            'training': training_summary,
            'averages': monthly_averages,
            'trends': trends,
            'achievements': achievements,

            'summary': self._generate_monthly_summary_text(
                training_summary,
                trends,
                achievements
            )
        }

    # Helper methods for calculations

    def _calculate_load_score(self, load_status: Dict) -> int:
        """Calculate readiness score from training load status (0-100)."""
        if not load_status or load_status.get('overall_status') == 'no_data':
            return 50  # Neutral

        status_scores = {
            'optimal': 90,
            'caution': 70,
            'warning': 40
        }

        return status_scores.get(load_status.get('overall_status', 'optimal'), 50)

    def _get_readiness_status(self, score: float) -> str:
        """Convert readiness score to status label."""
        if score >= 85:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 55:
            return 'fair'
        else:
            return 'poor'

    def _get_daily_recommendation(
        self,
        readiness_score: float,
        hrv_status: Dict,
        sleep_status: Dict,
        load_status: Dict
    ) -> str:
        """Generate daily training recommendation based on all factors."""
        if readiness_score >= 85:
            return "Excellent readiness. Ready for high-intensity training or competition."
        elif readiness_score >= 70:
            return "Good readiness. Suitable for quality training sessions."
        elif readiness_score >= 55:
            return "Moderate readiness. Consider easy to moderate training."
        else:
            return "Low readiness. Prioritize recovery: easy training or rest day."

    def _calculate_training_summary(self, activities: List[Activity]) -> Dict:
        """Calculate weekly training summary from activities."""
        if not activities:
            return {
                'total_activities': 0,
                'total_duration_hours': 0,
                'total_distance_km': 0,
                'total_training_load': 0
            }

        by_type = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            if activity_type not in by_type:
                by_type[activity_type] = {
                    'count': 0,
                    'duration_minutes': 0,
                    'distance_meters': 0
                }

            by_type[activity_type]['count'] += 1
            by_type[activity_type]['duration_minutes'] += activity.duration_minutes or 0
            by_type[activity_type]['distance_meters'] += activity.distance_meters or 0

        return {
            'total_activities': len(activities),
            'total_duration_hours': round(sum([a.duration_minutes or 0 for a in activities]) / 60, 1),
            'total_distance_km': round(sum([a.distance_meters or 0 for a in activities]) / 1000, 1),
            'total_training_load': sum([a.training_load or 0 for a in activities]),
            'by_type': by_type,
            'longest_activity_minutes': max([a.duration_minutes or 0 for a in activities]) if activities else 0
        }

    def _calculate_sleep_summary(self, daily_metrics: List[DailyMetrics]) -> Dict:
        """Calculate weekly sleep summary."""
        sleep_durations = [m.total_sleep_minutes for m in daily_metrics if m.total_sleep_minutes]

        if not sleep_durations:
            return {'status': 'no_data'}

        return {
            'avg_duration_hours': round(np.mean(sleep_durations) / 60, 1),
            'min_duration_hours': round(min(sleep_durations) / 60, 1),
            'max_duration_hours': round(max(sleep_durations) / 60, 1),
            'consistency_score': round(100 - (statistics.standard_deviation(sleep_durations) / np.mean(sleep_durations) * 100), 1),
            'nights_tracked': len(sleep_durations)
        }

    def _calculate_hrv_summary(self, daily_metrics: List[DailyMetrics]) -> Dict:
        """Calculate weekly HRV summary."""
        hrv_values = [m.hrv_rmssd for m in daily_metrics if m.hrv_rmssd]

        if not hrv_values:
            return {'status': 'no_data'}

        return {
            'avg_hrv': round(np.mean(hrv_values), 1),
            'min_hrv': round(min(hrv_values), 1),
            'max_hrv': round(max(hrv_values), 1),
            'cv': round(statistics.coefficient_of_variation(hrv_values), 1),
            'readings': len(hrv_values)
        }

    def _calculate_recovery_summary(self, daily_metrics: List[DailyMetrics]) -> Dict:
        """Calculate weekly recovery metrics summary."""
        rhr_values = [m.resting_heart_rate for m in daily_metrics if m.resting_heart_rate]
        stress_values = [m.stress_score for m in daily_metrics if m.stress_score]

        return {
            'avg_resting_hr': round(np.mean(rhr_values), 0) if rhr_values else None,
            'avg_stress': round(np.mean(stress_values), 0) if stress_values else None
        }

    def _calculate_load_progression(self, user_id: str, week_start: date) -> Dict:
        """Calculate training load progression compared to previous week."""
        current_load = training_load.calculate_acute_load(self.db, user_id, week_start + timedelta(days=6))
        previous_load = training_load.calculate_acute_load(self.db, user_id, week_start - timedelta(days=1))

        if not current_load or not previous_load:
            return {'status': 'insufficient_data'}

        change_percent = ((current_load - previous_load) / previous_load) * 100

        return {
            'current_week_load': round(current_load, 1),
            'previous_week_load': round(previous_load, 1),
            'change_percent': round(change_percent, 1),
            'trend': 'increasing' if change_percent > 5 else 'decreasing' if change_percent < -5 else 'stable'
        }

    def _generate_weekly_highlights(self, training, sleep, hrv, load_progression) -> List[str]:
        """Generate text highlights for the week."""
        highlights = []

        if training['total_activities'] > 0:
            highlights.append(f"Completed {training['total_activities']} workouts totaling {training['total_duration_hours']} hours")

        if sleep.get('avg_duration_hours'):
            highlights.append(f"Average sleep: {sleep['avg_duration_hours']} hours/night")

        if load_progression.get('trend'):
            highlights.append(f"Training load {load_progression['trend']}")

        return highlights

    def _calculate_monthly_training_summary(self, activities: List[Activity]) -> Dict:
        """Calculate monthly training summary."""
        return self._calculate_training_summary(activities)  # Same logic, longer period

    def _calculate_monthly_averages(self, daily_metrics: List[DailyMetrics]) -> Dict:
        """Calculate monthly metric averages."""
        return {
            'avg_steps': round(np.mean([m.steps for m in daily_metrics if m.steps]), 0),
            'avg_sleep_hours': round(np.mean([m.total_sleep_minutes for m in daily_metrics if m.total_sleep_minutes]) / 60, 1),
            'avg_hrv': round(np.mean([m.hrv_rmssd for m in daily_metrics if m.hrv_rmssd]), 1),
            'avg_resting_hr': round(np.mean([m.resting_heart_rate for m in daily_metrics if m.resting_heart_rate]), 0)
        }

    def _calculate_monthly_trends(self, daily_metrics: List[DailyMetrics]) -> Dict:
        """Calculate trends over the month using linear regression."""
        # This would use statistics.linear_regression on time-series data
        return {
            'hrv_trend': 'improving',  # Placeholder
            'sleep_trend': 'stable',
            'fitness_trend': 'improving'
        }

    def _identify_monthly_achievements(self, activities: List[Activity]) -> List[str]:
        """Identify notable achievements for the month."""
        achievements = []

        if activities:
            longest_run = max([a for a in activities if a.activity_type == ActivityType.RUNNING],
                             key=lambda x: x.distance_meters or 0, default=None)
            if longest_run and longest_run.distance_meters:
                achievements.append(f"Longest run: {longest_run.distance_meters/1000:.1f} km")

        return achievements

    def _generate_monthly_summary_text(self, training, trends, achievements) -> str:
        """Generate human-readable monthly summary."""
        parts = []

        if training['total_activities'] > 0:
            parts.append(f"Completed {training['total_activities']} workouts this month")

        if achievements:
            parts.append(f"Achievements: {', '.join(achievements)}")

        return ". ".join(parts) if parts else "No significant activity this month."
