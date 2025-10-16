"""
Heart Rate Variability (HRV) analysis utilities.

This module provides comprehensive HRV analysis including:
- Baseline calculations (7-day and 30-day rolling averages)
- Trend detection (improving, declining, stable)
- Overtraining detection (significant HRV drops)
- Recovery status assessment

HRV is a key indicator of autonomic nervous system function and recovery status.
Lower HRV or declining trends indicate insufficient recovery or overtraining.

Key Concepts:
- Baseline: Rolling average HRV over 7 or 30 days
- Drop: Current HRV significantly below baseline (>10-15%)
- Trend: Direction of HRV change over time (slope of regression)
"""

from datetime import date, timedelta
from typing import Optional, Dict, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np
from numpy.typing import NDArray

from app.models.database_models import DailyMetrics, HRVReading
from app.utils.statistics import moving_average, linear_regression, standard_deviation


def calculate_hrv_baseline(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 7,
    hrv_metric: str = 'rmssd',
    min_readings: int = 5
) -> Optional[float]:
    """
    Calculate HRV baseline as rolling average over specified days.

    The baseline represents the athlete's "normal" HRV and is used to detect
    significant deviations that may indicate poor recovery or overtraining.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for baseline calculation (default: today)
        days: Number of days for rolling average (7 for short-term, 30 for long-term)
        hrv_metric: HRV metric to use ('rmssd' or 'sdnn')
        min_readings: Minimum number of readings required for valid baseline

    Returns:
        Baseline HRV value (float), or None if insufficient data

    Example:
        >>> baseline_7d = calculate_hrv_baseline(db, "user123", days=7)
        >>> baseline_30d = calculate_hrv_baseline(db, "user123", days=30)

    Notes:
        - RMSSD is preferred for daily HRV monitoring (reflects parasympathetic activity)
        - 7-day baseline is more responsive to recent changes
        - 30-day baseline provides stable long-term reference
        - Requires at least min_readings valid readings for reliable baseline
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Query daily metrics with HRV data
    metrics = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date
        )
    ).order_by(DailyMetrics.date).all()

    # Extract HRV values
    if hrv_metric == 'rmssd':
        hrv_values = [m.hrv_rmssd for m in metrics if m.hrv_rmssd is not None]
    elif hrv_metric == 'sdnn':
        hrv_values = [m.hrv_sdnn for m in metrics if m.hrv_sdnn is not None]
    else:
        raise ValueError(f"Invalid hrv_metric: {hrv_metric}. Use 'rmssd' or 'sdnn'")

    # Check if we have enough data
    if len(hrv_values) < min_readings:
        return None

    # Calculate baseline as mean of available readings
    baseline = float(np.mean(hrv_values))
    return baseline


def get_hrv_trend(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 30,
    hrv_metric: str = 'rmssd',
    min_readings: int = 7
) -> Dict[str, any]:
    """
    Analyze HRV trend over specified period.

    Uses linear regression to determine if HRV is improving, declining, or stable.
    The slope indicates the rate of change per day.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for trend analysis (default: today)
        days: Number of days to analyze (default: 30)
        hrv_metric: HRV metric to use ('rmssd' or 'sdnn')
        min_readings: Minimum readings required for trend analysis

    Returns:
        Dictionary containing:
        - trend: 'improving', 'declining', or 'stable'
        - slope: Rate of change per day (ms/day)
        - r_squared: Quality of fit (0-1)
        - start_value: HRV at start of period
        - end_value: HRV at end of period
        - percent_change: Total percentage change
        - data_points: Number of readings used

    Example:
        >>> trend = get_hrv_trend(db, "user123", days=30)
        >>> if trend['trend'] == 'declining':
        >>>     print(f"HRV declining at {trend['slope']:.2f} ms/day")

    Notes:
        - Improving trend (positive slope) indicates good adaptation
        - Declining trend may indicate overtraining or poor recovery
        - R² > 0.5 indicates strong trend; < 0.3 suggests noise
        - Consider absolute HRV level along with trend direction
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Query daily metrics
    metrics = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date
        )
    ).order_by(DailyMetrics.date).all()

    # Extract HRV values and dates
    hrv_data = []
    for m in metrics:
        hrv_value = m.hrv_rmssd if hrv_metric == 'rmssd' else m.hrv_sdnn
        if hrv_value is not None:
            days_from_start = (m.date - start_date).days
            hrv_data.append((days_from_start, hrv_value))

    if len(hrv_data) < min_readings:
        return {
            'trend': 'unknown',
            'slope': None,
            'r_squared': None,
            'start_value': None,
            'end_value': None,
            'percent_change': None,
            'data_points': len(hrv_data)
        }

    # Perform linear regression
    x_values = [d[0] for d in hrv_data]
    y_values = [d[1] for d in hrv_data]

    slope, intercept, r_squared = linear_regression(x_values, y_values)

    # Determine trend direction
    # Threshold: slope > 0.1 ms/day is improving, < -0.1 is declining
    if slope > 0.1:
        trend = 'improving'
    elif slope < -0.1:
        trend = 'declining'
    else:
        trend = 'stable'

    # Calculate start and end values
    start_value = float(y_values[0])
    end_value = float(y_values[-1])
    percent_change = ((end_value - start_value) / start_value) * 100 if start_value > 0 else 0.0

    return {
        'trend': trend,
        'slope': float(slope),
        'r_squared': float(r_squared),
        'start_value': start_value,
        'end_value': end_value,
        'percent_change': percent_change,
        'data_points': len(hrv_data)
    }


def detect_hrv_drop(
    current_hrv: float,
    baseline_hrv: float,
    threshold_percent: float = 10.0
) -> Dict[str, any]:
    """
    Detect significant HRV drop indicating poor recovery or overtraining.

    A drop of >10-15% below baseline is considered significant and may indicate:
    - Incomplete recovery from previous training
    - Accumulated fatigue
    - Illness or infection
    - Psychological stress
    - Overtraining syndrome

    Args:
        current_hrv: Current HRV value (ms)
        baseline_hrv: Baseline HRV value (ms)
        threshold_percent: Threshold for significant drop (default: 10%)

    Returns:
        Dictionary containing:
        - drop_detected: Boolean indicating significant drop
        - drop_percent: Percentage drop from baseline
        - severity: 'none', 'mild', 'moderate', or 'severe'
        - recommendation: Action recommendation

    Example:
        >>> result = detect_hrv_drop(current_hrv=40, baseline_hrv=50)
        >>> if result['drop_detected']:
        >>>     print(f"HRV drop: {result['drop_percent']:.1f}% - {result['severity']}")

    Interpretation:
        - 0-5% drop: Normal daily variation
        - 5-10% drop: Mild, monitor closely
        - 10-20% drop: Moderate, reduce training intensity
        - >20% drop: Severe, consider rest day

    Notes:
        - HRV naturally varies day-to-day (~5%)
        - Morning alcohol, poor sleep, or stress can cause acute drops
        - Persistent drops over multiple days are more concerning
    """
    if baseline_hrv <= 0:
        return {
            'drop_detected': False,
            'drop_percent': 0.0,
            'severity': 'unknown',
            'recommendation': 'Invalid baseline HRV'
        }

    # Calculate percentage drop (negative = drop, positive = increase)
    drop_percent = ((baseline_hrv - current_hrv) / baseline_hrv) * 100

    # Determine severity
    if drop_percent < 5:
        severity = 'none'
        recommendation = 'Normal HRV variation. Proceed with planned training.'
        drop_detected = False
    elif drop_percent < 10:
        severity = 'mild'
        recommendation = 'Mild HRV drop. Monitor closely. Consider easy training.'
        drop_detected = False
    elif drop_percent < 20:
        severity = 'moderate'
        recommendation = 'Moderate HRV drop. Reduce training intensity or volume. Prioritize recovery.'
        drop_detected = True
    else:
        severity = 'severe'
        recommendation = 'Severe HRV drop. Consider rest day or very easy recovery activity.'
        drop_detected = True

    return {
        'drop_detected': drop_detected,
        'drop_percent': float(drop_percent),
        'severity': severity,
        'recommendation': recommendation
    }


def calculate_hrv_coefficient_of_variation(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 7,
    hrv_metric: str = 'rmssd'
) -> Optional[float]:
    """
    Calculate coefficient of variation (CV) for HRV.

    CV = (standard deviation / mean) * 100

    High CV indicates unstable or variable HRV, which may suggest:
    - Inconsistent recovery patterns
    - High training stress
    - Need for better recovery strategies

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for calculation (default: today)
        days: Number of days to analyze (default: 7)
        hrv_metric: HRV metric to use ('rmssd' or 'sdnn')

    Returns:
        Coefficient of variation as percentage, or None if insufficient data

    Example:
        >>> cv = calculate_hrv_coefficient_of_variation(db, "user123", days=7)
        >>> if cv and cv > 20:
        >>>     print("High HRV variability detected")

    Notes:
        - Lower CV (< 15%) = stable, consistent recovery
        - Higher CV (> 20%) = variable, inconsistent recovery
        - Very high CV may indicate measurement inconsistencies
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Query daily metrics
    metrics = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date
        )
    ).all()

    # Extract HRV values
    if hrv_metric == 'rmssd':
        hrv_values = [m.hrv_rmssd for m in metrics if m.hrv_rmssd is not None]
    else:
        hrv_values = [m.hrv_sdnn for m in metrics if m.hrv_sdnn is not None]

    if len(hrv_values) < 3:
        return None

    mean_hrv = float(np.mean(hrv_values))
    std_hrv = standard_deviation(hrv_values)

    if mean_hrv == 0:
        return None

    cv = (std_hrv / mean_hrv) * 100
    return float(cv)


def get_hrv_status(
    db: Session,
    user_id: str,
    current_date: Optional[date] = None,
    hrv_metric: str = 'rmssd'
) -> Dict[str, any]:
    """
    Get comprehensive HRV status including baseline, trend, and drop detection.

    This is the main function to assess current HRV status for training readiness.

    Args:
        db: Database session
        user_id: User identifier
        current_date: Date to assess (default: today)
        hrv_metric: HRV metric to use ('rmssd' or 'sdnn')

    Returns:
        Dictionary containing:
        - current_hrv: Today's HRV value
        - baseline_7d: 7-day baseline
        - baseline_30d: 30-day baseline
        - trend_30d: 30-day trend analysis
        - drop_vs_7d: Drop detection vs 7-day baseline
        - drop_vs_30d: Drop detection vs 30-day baseline
        - cv_7d: 7-day coefficient of variation
        - status: Overall status ('optimal', 'good', 'caution', 'warning')
        - recommendation: Training recommendation

    Example:
        >>> status = get_hrv_status(db, "user123")
        >>> print(f"Status: {status['status']}")
        >>> print(f"Recommendation: {status['recommendation']}")

    Notes:
        - Combines multiple HRV metrics for comprehensive assessment
        - Prioritizes 7-day baseline for acute recovery status
        - Uses 30-day baseline for longer-term trends
    """
    if current_date is None:
        current_date = date.today()

    # Get current HRV
    current_metric = db.query(DailyMetrics).filter(
        and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.date == current_date
        )
    ).first()

    if not current_metric:
        return {'status': 'no_data', 'recommendation': 'No HRV data available for today'}

    current_hrv = current_metric.hrv_rmssd if hrv_metric == 'rmssd' else current_metric.hrv_sdnn

    if current_hrv is None:
        return {'status': 'no_data', 'recommendation': 'No HRV reading for today'}

    # Calculate baselines
    baseline_7d = calculate_hrv_baseline(db, user_id, current_date, days=7, hrv_metric=hrv_metric)
    baseline_30d = calculate_hrv_baseline(db, user_id, current_date, days=30, hrv_metric=hrv_metric)

    # Get trend
    trend_30d = get_hrv_trend(db, user_id, current_date, days=30, hrv_metric=hrv_metric)

    # Detect drops
    drop_vs_7d = detect_hrv_drop(current_hrv, baseline_7d) if baseline_7d else None
    drop_vs_30d = detect_hrv_drop(current_hrv, baseline_30d) if baseline_30d else None

    # Calculate CV
    cv_7d = calculate_hrv_coefficient_of_variation(db, user_id, current_date, days=7, hrv_metric=hrv_metric)

    # Determine overall status
    status = 'optimal'
    recommendation = 'HRV is optimal. Ready for high-intensity training.'

    if drop_vs_7d and drop_vs_7d['severity'] == 'severe':
        status = 'warning'
        recommendation = drop_vs_7d['recommendation']
    elif drop_vs_7d and drop_vs_7d['severity'] == 'moderate':
        status = 'caution'
        recommendation = drop_vs_7d['recommendation']
    elif trend_30d['trend'] == 'declining' and trend_30d['r_squared'] > 0.5:
        status = 'caution'
        recommendation = 'HRV is declining over time. Monitor recovery and consider reducing training load.'
    elif drop_vs_7d and drop_vs_7d['severity'] == 'mild':
        status = 'good'
        recommendation = 'HRV slightly below baseline. Proceed with caution.'

    return {
        'current_hrv': float(current_hrv),
        'baseline_7d': float(baseline_7d) if baseline_7d else None,
        'baseline_30d': float(baseline_30d) if baseline_30d else None,
        'trend_30d': trend_30d,
        'drop_vs_7d': drop_vs_7d,
        'drop_vs_30d': drop_vs_30d,
        'cv_7d': float(cv_7d) if cv_7d else None,
        'status': status,
        'recommendation': recommendation
    }


def get_hrv_score(hrv_status: Dict[str, any]) -> int:
    """
    Convert HRV status to 0-100 readiness score.

    Args:
        hrv_status: Output from get_hrv_status()

    Returns:
        Score from 0-100 (100 = optimal readiness)

    Example:
        >>> status = get_hrv_status(db, "user123")
        >>> score = get_hrv_score(status)
        >>> print(f"HRV Readiness Score: {score}/100")

    Scoring:
        - 90-100: Optimal (no drop, improving or stable trend)
        - 75-89: Good (mild drop or stable)
        - 50-74: Caution (moderate drop)
        - 0-49: Warning (severe drop or declining trend)
    """
    if hrv_status['status'] == 'no_data':
        return 50  # Neutral score when no data

    status_scores = {
        'optimal': 95,
        'good': 80,
        'caution': 65,
        'warning': 40
    }

    base_score = status_scores.get(hrv_status['status'], 50)

    # Adjust based on trend
    if hrv_status['trend_30d']['trend'] == 'improving':
        base_score = min(100, base_score + 5)
    elif hrv_status['trend_30d']['trend'] == 'declining':
        base_score = max(0, base_score - 10)

    # Adjust based on CV (variability)
    cv = hrv_status.get('cv_7d')
    if cv:
        if cv > 20:
            base_score = max(0, base_score - 5)

    return int(base_score)
