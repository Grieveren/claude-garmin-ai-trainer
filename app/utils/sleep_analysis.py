"""
Sleep analysis utilities for quality scoring and recovery assessment.

This module analyzes sleep data to:
1. Calculate sleep quality scores (0-100)
2. Track sleep averages and patterns
3. Detect sleep debt accumulation
4. Assess sleep's impact on recovery

Sleep is crucial for athletic recovery and performance. Poor sleep quality or
duration negatively impacts HRV, training adaptation, and injury risk.

Sleep Quality Components:
- Duration: Total sleep time vs. recommended (7-9 hours)
- Efficiency: Time asleep / time in bed
- Deep sleep: Percentage of total sleep (15-25% optimal)
- REM sleep: Percentage of total sleep (20-25% optimal)
- Consistency: Regular sleep/wake times
- Disruptions: Number of awakenings
"""

from datetime import date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np

from app.models.database_models import DailyMetrics, SleepSession
from app.utils.statistics import moving_average, standard_deviation


def calculate_sleep_quality_score(
    total_sleep_minutes: int,
    deep_sleep_minutes: Optional[int] = None,
    light_sleep_minutes: Optional[int] = None,
    rem_sleep_minutes: Optional[int] = None,
    awake_minutes: Optional[int] = None,
    awakenings_count: Optional[int] = None,
    target_sleep_minutes: int = 480  # 8 hours
) -> Dict[str, any]:
    """
    Calculate comprehensive sleep quality score (0-100).

    Combines multiple sleep metrics into a single quality score using weighted
    components: duration, sleep stages, and disruptions.

    Args:
        total_sleep_minutes: Total time asleep
        deep_sleep_minutes: Time in deep sleep
        light_sleep_minutes: Time in light sleep
        rem_sleep_minutes: Time in REM sleep
        awake_minutes: Time awake after sleep onset
        awakenings_count: Number of times awakened
        target_sleep_minutes: Individual's target sleep duration (default: 480 = 8 hours)

    Returns:
        Dictionary containing:
        - score: Overall quality score (0-100)
        - duration_score: Score for total duration (0-100)
        - stage_score: Score for sleep stages distribution (0-100)
        - disruption_score: Score for sleep disruptions (0-100)
        - quality_rating: 'excellent', 'good', 'fair', or 'poor'
        - recommendations: List of improvement suggestions

    Scoring:
        - 90-100: Excellent sleep
        - 75-89: Good sleep
        - 60-74: Fair sleep
        - <60: Poor sleep

    Example:
        >>> score = calculate_sleep_quality_score(
        >>>     total_sleep_minutes=450,
        >>>     deep_sleep_minutes=90,
        >>>     rem_sleep_minutes=100,
        >>>     awakenings_count=2
        >>> )
        >>> print(f"Sleep Quality: {score['score']}/100 - {score['quality_rating']}")

    Notes:
        - Duration is most important factor (40% weight)
        - Sleep stages composition (30% weight)
        - Disruptions/continuity (30% weight)
    """
    recommendations = []
    total_score = 0.0
    weights_used = 0.0

    # Component 1: Duration Score (40% weight)
    duration_score = 100.0

    if total_sleep_minutes < target_sleep_minutes * 0.7:  # < 70% of target
        duration_score = (total_sleep_minutes / (target_sleep_minutes * 0.7)) * 60
        recommendations.append("Increase sleep duration. Aim for 7-9 hours per night.")
    elif total_sleep_minutes < target_sleep_minutes * 0.9:  # 70-90% of target
        duration_score = 60 + ((total_sleep_minutes - target_sleep_minutes * 0.7) /
                               (target_sleep_minutes * 0.2)) * 30
        recommendations.append("Sleep duration slightly below optimal. Try to get 30-60 minutes more.")
    elif total_sleep_minutes <= target_sleep_minutes * 1.1:  # 90-110% of target
        duration_score = 90 + ((total_sleep_minutes - target_sleep_minutes * 0.9) /
                               (target_sleep_minutes * 0.2)) * 10
    else:  # > 110% of target
        duration_score = 95.0  # Slightly lower for oversleeping

    total_score += duration_score * 0.4
    weights_used += 0.4

    # Component 2: Sleep Stages Score (30% weight)
    if deep_sleep_minutes is not None and rem_sleep_minutes is not None:
        deep_percent = (deep_sleep_minutes / total_sleep_minutes) * 100
        rem_percent = (rem_sleep_minutes / total_sleep_minutes) * 100

        # Optimal: 15-25% deep, 20-25% REM
        stage_score = 100.0

        # Deep sleep scoring
        if deep_percent < 10:
            stage_score -= 25
            recommendations.append("Low deep sleep. Avoid caffeine/alcohol before bed, keep room cool.")
        elif deep_percent < 15:
            stage_score -= 10
        elif deep_percent > 25:
            stage_score -= 5

        # REM sleep scoring
        if rem_percent < 15:
            stage_score -= 25
            recommendations.append("Low REM sleep. Maintain consistent sleep schedule, manage stress.")
        elif rem_percent < 20:
            stage_score -= 10
        elif rem_percent > 30:
            stage_score -= 5

        total_score += max(0, stage_score) * 0.3
        weights_used += 0.3
    else:
        stage_score = None

    # Component 3: Disruption Score (30% weight)
    disruption_score = 100.0

    if awake_minutes is not None:
        wake_percent = (awake_minutes / total_sleep_minutes) * 100
        if wake_percent > 15:
            disruption_score -= 40
            recommendations.append("High wake time. Consider sleep environment improvements.")
        elif wake_percent > 10:
            disruption_score -= 20
        elif wake_percent > 5:
            disruption_score -= 10

    if awakenings_count is not None:
        if awakenings_count > 10:
            disruption_score -= 30
            recommendations.append("Frequent awakenings. Check room temperature, noise, and light levels.")
        elif awakenings_count > 5:
            disruption_score -= 15
        elif awakenings_count > 3:
            disruption_score -= 5

    total_score += max(0, disruption_score) * 0.3
    weights_used += 0.3

    # Normalize if not all components available
    # Note: total_score is already weighted (components * weights), so we just normalize
    if weights_used > 0:
        final_score = total_score / weights_used
    else:
        final_score = 0.0

    final_score = max(0, min(100, final_score))

    # Quality rating
    if final_score >= 90:
        quality_rating = 'excellent'
    elif final_score >= 75:
        quality_rating = 'good'
    elif final_score >= 60:
        quality_rating = 'fair'
    else:
        quality_rating = 'poor'

    if not recommendations:
        recommendations.append("Sleep quality is excellent. Maintain current sleep habits.")

    return {
        'score': round(final_score, 1),
        'duration_score': round(duration_score, 1),
        'stage_score': round(stage_score, 1) if stage_score is not None else None,
        'disruption_score': round(disruption_score, 1),
        'quality_rating': quality_rating,
        'recommendations': recommendations,
        'metrics': {
            'total_minutes': total_sleep_minutes,
            'deep_percent': round((deep_sleep_minutes / total_sleep_minutes) * 100, 1) if deep_sleep_minutes else None,
            'rem_percent': round((rem_sleep_minutes / total_sleep_minutes) * 100, 1) if rem_sleep_minutes else None,
            'awakenings': awakenings_count
        }
    }


def get_sleep_average(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 7,
    min_nights: int = 4
) -> Dict[str, any]:
    """
    Calculate average sleep metrics over specified period.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for calculation (default: today)
        days: Number of days to average (default: 7)
        min_nights: Minimum nights of data required (default: 4)

    Returns:
        Dictionary containing:
        - avg_duration_hours: Average total sleep time
        - avg_deep_minutes: Average deep sleep
        - avg_rem_minutes: Average REM sleep
        - avg_quality_score: Average quality score
        - sleep_consistency: Consistency score (0-100, based on std dev)
        - nights_analyzed: Number of nights with data

    Example:
        >>> avg = get_sleep_average(db, "user123", days=7)
        >>> print(f"Average sleep: {avg['avg_duration_hours']:.1f} hours")
        >>> print(f"Consistency: {avg['sleep_consistency']}/100")

    Notes:
        - High consistency (>80) indicates regular sleep schedule
        - Low consistency (<60) may impact recovery and HRV
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Query daily metrics with sleep data
    metrics = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date,
            DailyMetrics.total_sleep_minutes.isnot(None)
        )
    ).all()

    if len(metrics) < min_nights:
        return {
            'avg_duration_hours': None,
            'avg_deep_minutes': None,
            'avg_rem_minutes': None,
            'avg_quality_score': None,
            'sleep_consistency': None,
            'nights_analyzed': len(metrics),
            'status': 'insufficient_data'
        }

    # Extract sleep durations
    durations = [m.total_sleep_minutes for m in metrics]
    deep_sleep = [m.deep_sleep_minutes for m in metrics if m.deep_sleep_minutes is not None]
    rem_sleep = [m.rem_sleep_minutes for m in metrics if m.rem_sleep_minutes is not None]
    quality_scores = []

    # Calculate quality scores for each night
    for m in metrics:
        score_result = calculate_sleep_quality_score(
            total_sleep_minutes=m.total_sleep_minutes,
            deep_sleep_minutes=m.deep_sleep_minutes,
            light_sleep_minutes=m.light_sleep_minutes,
            rem_sleep_minutes=m.rem_sleep_minutes,
            awake_minutes=m.awake_minutes
        )
        quality_scores.append(score_result['score'])

    # Calculate averages
    avg_duration = float(np.mean(durations)) / 60  # Convert to hours
    avg_deep = float(np.mean(deep_sleep)) if deep_sleep else None
    avg_rem = float(np.mean(rem_sleep)) if rem_sleep else None
    avg_quality = float(np.mean(quality_scores)) if quality_scores else None

    # Calculate consistency (based on std dev of duration)
    std_dev = standard_deviation(durations)
    # Lower std dev = higher consistency
    # Std dev of 30 min or less = 100% consistency, 120+ min = 0% consistency
    consistency = max(0, min(100, 100 - (std_dev - 30) / 90 * 100))

    return {
        'avg_duration_hours': round(avg_duration, 1),
        'avg_deep_minutes': round(avg_deep, 1) if avg_deep else None,
        'avg_rem_minutes': round(avg_rem, 1) if avg_rem else None,
        'avg_quality_score': round(avg_quality, 1) if avg_quality else None,
        'sleep_consistency': round(consistency, 1),
        'nights_analyzed': len(metrics),
        'status': 'sufficient_data'
    }


def detect_sleep_debt(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 7,
    target_sleep_hours: float = 8.0
) -> Dict[str, any]:
    """
    Detect accumulated sleep debt over a period.

    Sleep debt occurs when actual sleep is consistently less than needed sleep.
    Chronic sleep debt impairs recovery, performance, and health.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for analysis (default: today)
        days: Number of days to analyze (default: 7)
        target_sleep_hours: Individual's required sleep (default: 8.0 hours)

    Returns:
        Dictionary containing:
        - total_debt_hours: Total accumulated sleep debt
        - avg_debt_per_night: Average debt per night
        - nights_short: Number of nights below target
        - worst_night_deficit: Largest single night deficit
        - severity: 'none', 'mild', 'moderate', or 'severe'
        - recovery_nights_needed: Estimated nights to recover
        - recommendation: Sleep debt recovery strategy

    Formula:
        Sleep Debt = Σ(target_hours - actual_hours) for each night

    Example:
        >>> debt = detect_sleep_debt(db, "user123", days=7)
        >>> if debt['severity'] in ['moderate', 'severe']:
        >>>     print(f"Sleep debt: {debt['total_debt_hours']:.1f} hours")
        >>>     print(f"Recovery needed: {debt['recovery_nights_needed']} nights")

    Interpretation:
        - <2 hours debt: Minimal, easily recovered
        - 2-5 hours debt: Moderate, needs attention
        - 5-10 hours debt: Significant, affecting performance
        - >10 hours debt: Severe, major recovery priority

    Notes:
        - Sleep debt accumulates over days/weeks
        - Cannot be "repaid" all at once
        - Requires consistent good sleep to eliminate
        - Affects HRV, cognitive function, and training adaptation
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)
    target_sleep_minutes = target_sleep_hours * 60

    # Query daily metrics
    metrics = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date,
            DailyMetrics.total_sleep_minutes.isnot(None)
        )
    ).order_by(DailyMetrics.date).all()

    if not metrics:
        return {
            'total_debt_hours': 0.0,
            'severity': 'no_data',
            'recommendation': 'No sleep data available'
        }

    # Calculate daily deficits
    deficits = []
    for m in metrics:
        deficit_minutes = max(0, target_sleep_minutes - m.total_sleep_minutes)
        deficits.append(deficit_minutes)

    total_debt_minutes = sum(deficits)
    total_debt_hours = total_debt_minutes / 60
    nights_short = sum(1 for d in deficits if d > 0)
    avg_debt_per_night = total_debt_minutes / len(metrics) / 60
    worst_night_deficit = max(deficits) / 60 if deficits else 0.0

    # Determine severity
    if total_debt_hours < 2:
        severity = 'none'
        recovery_nights = 0
        recommendation = 'Minimal sleep debt. Maintain current sleep habits.'
    elif total_debt_hours < 5:
        severity = 'mild'
        recovery_nights = 2
        recommendation = 'Mild sleep debt. Try to get 30-60 min extra sleep for 2-3 nights.'
    elif total_debt_hours < 10:
        severity = 'moderate'
        recovery_nights = 4
        recommendation = 'Moderate sleep debt. Prioritize 8-9 hours of sleep for at least 4 nights.'
    else:
        severity = 'severe'
        recovery_nights = 7
        recommendation = 'Severe sleep debt. Major recovery priority. Aim for 9+ hours for a full week.'

    return {
        'total_debt_hours': round(total_debt_hours, 1),
        'avg_debt_per_night': round(avg_debt_per_night, 1),
        'nights_short': nights_short,
        'nights_analyzed': len(metrics),
        'worst_night_deficit': round(worst_night_deficit, 1),
        'severity': severity,
        'recovery_nights_needed': recovery_nights,
        'recommendation': recommendation
    }


def get_sleep_status(
    db: Session,
    user_id: str,
    current_date: Optional[date] = None
) -> Dict[str, any]:
    """
    Get comprehensive sleep status and readiness impact.

    Combines sleep quality, averages, and debt into single assessment.

    Args:
        db: Database session
        user_id: User identifier
        current_date: Date to assess (default: today)

    Returns:
        Dictionary containing:
        - last_night: Last night's sleep quality
        - weekly_average: 7-day sleep averages
        - sleep_debt: Current sleep debt status
        - readiness_impact: Impact on training readiness (0-100)
        - status: Overall sleep status
        - recommendation: Primary recommendation

    Example:
        >>> status = get_sleep_status(db, "user123")
        >>> print(f"Sleep Status: {status['status']}")
        >>> print(f"Readiness Impact: {status['readiness_impact']}/100")
        >>> print(f"Recommendation: {status['recommendation']}")

    Notes:
        - Sleep status strongly influences training readiness
        - Poor sleep should lower training intensity recommendations
        - Chronic poor sleep requires intervention
    """
    if current_date is None:
        current_date = date.today()

    # Get last night's sleep
    current_metric = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date == current_date
        )
    ).first()

    if not current_metric or current_metric.total_sleep_minutes is None:
        return {
            'status': 'no_data',
            'readiness_impact': 50,  # Neutral
            'recommendation': 'No sleep data available for assessment'
        }

    # Calculate last night's quality
    last_night = calculate_sleep_quality_score(
        total_sleep_minutes=current_metric.total_sleep_minutes,
        deep_sleep_minutes=current_metric.deep_sleep_minutes,
        light_sleep_minutes=current_metric.light_sleep_minutes,
        rem_sleep_minutes=current_metric.rem_sleep_minutes,
        awake_minutes=current_metric.awake_minutes
    )

    # Get weekly averages
    weekly_avg = get_sleep_average(db, user_id, current_date, days=7)

    # Check for sleep debt
    sleep_debt = detect_sleep_debt(db, user_id, current_date, days=7)

    # Calculate readiness impact (0-100)
    # Based on: last night (50%), weekly average (30%), sleep debt (20%)
    readiness_impact = 0.0

    readiness_impact += (last_night['score'] / 100) * 50

    if weekly_avg['avg_quality_score']:
        readiness_impact += (weekly_avg['avg_quality_score'] / 100) * 30
    else:
        readiness_impact += 15  # Neutral if no data

    debt_impact = 20
    if sleep_debt['severity'] == 'severe':
        debt_impact = 0
    elif sleep_debt['severity'] == 'moderate':
        debt_impact = 10
    elif sleep_debt['severity'] == 'mild':
        debt_impact = 15
    readiness_impact += debt_impact

    # Determine overall status
    if last_night['quality_rating'] == 'excellent' and sleep_debt['severity'] == 'none':
        status = 'optimal'
        recommendation = 'Sleep is excellent. No limitations on training intensity.'
    elif last_night['quality_rating'] in ['good', 'excellent'] and sleep_debt['severity'] in ['none', 'mild']:
        status = 'good'
        recommendation = 'Sleep is good. Ready for quality training.'
    elif sleep_debt['severity'] in ['moderate', 'severe']:
        status = 'impaired'
        recommendation = f"Sleep debt detected: {sleep_debt['recommendation']}"
    elif last_night['quality_rating'] == 'poor':
        status = 'impaired'
        recommendation = 'Poor sleep last night. Consider easy training or rest.'
    else:
        status = 'fair'
        recommendation = 'Sleep is adequate but could be improved.'

    return {
        'last_night': last_night,
        'weekly_average': weekly_avg,
        'sleep_debt': sleep_debt,
        'readiness_impact': round(readiness_impact, 1),
        'status': status,
        'recommendation': recommendation
    }


def get_sleep_score(sleep_status: Dict[str, any]) -> int:
    """
    Convert sleep status to 0-100 readiness score.

    Args:
        sleep_status: Output from get_sleep_status()

    Returns:
        Score from 0-100 (100 = optimal sleep for training)

    Example:
        >>> status = get_sleep_status(db, "user123")
        >>> score = get_sleep_score(status)
        >>> print(f"Sleep Readiness Score: {score}/100")
    """
    return int(sleep_status.get('readiness_impact', 50))
