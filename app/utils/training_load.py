"""
Training load calculations and monitoring.

This module implements advanced training load metrics for monitoring training stress,
adaptation, and injury/overtraining risk:

1. Acute:Chronic Workload Ratio (ACWR)
   - Acute load: 7-day rolling average
   - Chronic load: 28-day rolling average
   - ACWR = Acute / Chronic
   - Optimal range: 0.8-1.3

2. Fitness-Fatigue Model (Banister model)
   - Fitness: Long-term training adaptation (42-day decay)
   - Fatigue: Short-term fatigue (7-day decay)
   - Form = Fitness - Fatigue

3. Training Monotony and Strain
   - Monotony = Mean load / Std dev of load
   - Strain = Total load * Monotony

Key References:
- Gabbett, T. J. (2016). ACWR for injury prediction
- Banister, E. W. (1991). Fitness-fatigue model
- Foster, C. (1998). Training monotony and strain
"""

from datetime import date, timedelta
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import numpy as np
from numpy.typing import NDArray

from app.models.database_models import Activity, DailyMetrics, TrainingLoadTracking
from app.utils.statistics import (
    moving_average,
    exponentially_weighted_moving_average,
    standard_deviation,
    rolling_standard_deviation
)


def calculate_acute_load(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 7,
    method: str = 'rolling_average'
) -> Optional[float]:
    """
    Calculate acute training load (7-day rolling average).

    Acute load represents recent training stress and short-term fatigue accumulation.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for calculation (default: today)
        days: Number of days for acute window (default: 7)
        method: Calculation method ('rolling_average' or 'ewma')

    Returns:
        Acute training load value, or None if insufficient data

    Formula:
        - Rolling Average: ATL = mean(load[t-6:t])
        - EWMA: ATL = exponentially weighted moving average (more weight to recent days)

    Example:
        >>> acute = calculate_acute_load(db, "user123")
        >>> print(f"7-day acute load: {acute}")

    Notes:
        - Uses training_load from Activity table (Garmin's training load score)
        - If no activities on a day, load = 0 for that day
        - EWMA is more responsive to recent changes
        - Minimum 5 days of data recommended for meaningful result
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Get all dates in range
    date_range = [start_date + timedelta(days=x) for x in range(days)]

    # Query activities and aggregate by date
    activities = db.query(
        Activity.activity_date,
        func.sum(Activity.training_load).label('daily_load')
    ).filter(
        and_(
            Activity.user_id == user_id,
            Activity.activity_date >= start_date,
            Activity.activity_date <= end_date,
            Activity.training_load.isnot(None)
        )
    ).group_by(Activity.activity_date).all()

    # Create dictionary of date -> load
    load_by_date = {a.activity_date: float(a.daily_load) for a in activities}

    # Fill in missing dates with 0 load
    daily_loads = [load_by_date.get(d, 0.0) for d in date_range]

    # Need at least some data
    if sum(1 for load in daily_loads if load > 0) < 3:
        return None

    if method == 'rolling_average':
        acute_load = float(np.mean(daily_loads))
    elif method == 'ewma':
        ewma_values = exponentially_weighted_moving_average(daily_loads, span=days)
        acute_load = float(ewma_values[-1])
    else:
        raise ValueError(f"Unknown method: {method}")

    return acute_load


def calculate_chronic_load(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 28,
    method: str = 'rolling_average'
) -> Optional[float]:
    """
    Calculate chronic training load (28-day rolling average).

    Chronic load represents long-term training adaptation and fitness level.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for calculation (default: today)
        days: Number of days for chronic window (default: 28)
        method: Calculation method ('rolling_average' or 'ewma')

    Returns:
        Chronic training load value, or None if insufficient data

    Formula:
        - Rolling Average: CTL = mean(load[t-27:t])
        - EWMA: CTL = exponentially weighted moving average

    Example:
        >>> chronic = calculate_chronic_load(db, "user123")
        >>> print(f"28-day chronic load: {chronic}")

    Notes:
        - Represents fitness and training history
        - More stable than acute load (less day-to-day variation)
        - Minimum 14 days of data recommended
        - Higher chronic load = better fitness/conditioning
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Get all dates in range
    date_range = [start_date + timedelta(days=x) for x in range(days)]

    # Query activities and aggregate by date
    activities = db.query(
        Activity.activity_date,
        func.sum(Activity.training_load).label('daily_load')
    ).filter(
        and_(
            Activity.user_id == user_id,
            Activity.activity_date >= start_date,
            Activity.activity_date <= end_date,
            Activity.training_load.isnot(None)
        )
    ).group_by(Activity.activity_date).all()

    # Create dictionary of date -> load
    load_by_date = {a.activity_date: float(a.daily_load) for a in activities}

    # Fill in missing dates with 0 load
    daily_loads = [load_by_date.get(d, 0.0) for d in date_range]

    # Need at least some data (at least half the period)
    if sum(1 for load in daily_loads if load > 0) < days // 2:
        return None

    if method == 'rolling_average':
        chronic_load = float(np.mean(daily_loads))
    elif method == 'ewma':
        ewma_values = exponentially_weighted_moving_average(daily_loads, span=days)
        chronic_load = float(ewma_values[-1])
    else:
        raise ValueError(f"Unknown method: {method}")

    return chronic_load


def calculate_acwr(
    acute_load: float,
    chronic_load: float
) -> Dict[str, any]:
    """
    Calculate Acute:Chronic Workload Ratio (ACWR).

    ACWR is a key metric for monitoring injury and overtraining risk. Research shows:
    - ACWR 0.8-1.3: "Sweet spot" - optimal training stimulus
    - ACWR 1.3-1.5: Moderate risk - rapid load increase
    - ACWR > 1.5: High risk - excessive load spike
    - ACWR < 0.8: Low risk but detraining may occur

    Args:
        acute_load: 7-day acute load
        chronic_load: 28-day chronic load

    Returns:
        Dictionary containing:
        - acwr: Ratio value
        - status: 'optimal', 'moderate_risk', 'high_risk', or 'detraining'
        - injury_risk: Risk level description
        - recommendation: Training adjustment recommendation

    Formula:
        ACWR = Acute Load (7d) / Chronic Load (28d)

    Example:
        >>> acute = calculate_acute_load(db, "user123")
        >>> chronic = calculate_chronic_load(db, "user123")
        >>> acwr = calculate_acwr(acute, chronic)
        >>> print(f"ACWR: {acwr['acwr']:.2f} - Status: {acwr['status']}")

    References:
        Gabbett, T. J. (2016). "The training-injury prevention paradox"
        British Journal of Sports Medicine, 50(5), 273-280.
    """
    if chronic_load == 0:
        return {
            'acwr': None,
            'status': 'insufficient_data',
            'injury_risk': 'unknown',
            'recommendation': 'Need more training history to calculate ACWR'
        }

    acwr_value = acute_load / chronic_load

    # Determine status and risk
    if acwr_value < 0.5:
        status = 'very_low'
        injury_risk = 'low'
        recommendation = 'Very low training load. Risk of detraining. Consider increasing training volume.'
    elif acwr_value < 0.8:
        status = 'low'
        injury_risk = 'low'
        recommendation = 'Low training load. Safe but may lead to detraining. Consider gradual increase.'
    elif acwr_value <= 1.3:
        status = 'optimal'
        injury_risk = 'low'
        recommendation = 'Optimal training load. "Sweet spot" for adaptation with minimal injury risk.'
    elif acwr_value <= 1.5:
        status = 'moderate_risk'
        injury_risk = 'moderate'
        recommendation = 'Moderate risk. Recent training spike detected. Monitor for fatigue signs.'
    else:
        status = 'high_risk'
        injury_risk = 'high'
        recommendation = 'High injury risk. Significant training spike. Consider reducing volume or intensity.'

    return {
        'acwr': float(acwr_value),
        'status': status,
        'injury_risk': injury_risk,
        'recommendation': recommendation
    }


def calculate_fitness_fatigue(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 42,
    fitness_decay: int = 42,
    fatigue_decay: int = 7
) -> Dict[str, any]:
    """
    Calculate fitness and fatigue using the Banister model.

    The fitness-fatigue model separates training adaptations into:
    1. Fitness: Long-term positive adaptations (slow to build, slow to decay)
    2. Fatigue: Short-term negative effects (quick to accumulate, quick to dissipate)
    3. Form: Readiness to perform (Fitness - Fatigue)

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for calculation (default: today)
        days: Number of historical days to include (default: 42)
        fitness_decay: Fitness decay constant in days (default: 42)
        fatigue_decay: Fatigue decay constant in days (default: 7)

    Returns:
        Dictionary containing:
        - fitness: Fitness level (higher = better conditioning)
        - fatigue: Fatigue level (higher = more tired)
        - form: Current form (fitness - fatigue)
        - form_status: 'fresh', 'optimal', 'fatigued', or 'overtrained'
        - recommendation: Training recommendation

    Formulas:
        Fitness(t) = Σ(load[i] * exp(-(t-i)/τ_fitness))
        Fatigue(t) = Σ(load[i] * exp(-(t-i)/τ_fatigue))
        Form(t) = Fitness(t) - Fatigue(t)

        where:
        - τ_fitness = 42 days (fitness time constant)
        - τ_fatigue = 7 days (fatigue time constant)
        - t = current day
        - i = historical day

    Example:
        >>> ff = calculate_fitness_fatigue(db, "user123")
        >>> print(f"Fitness: {ff['fitness']:.1f}, Fatigue: {ff['fatigue']:.1f}, Form: {ff['form']:.1f}")
        >>> print(f"Status: {ff['form_status']}")

    Interpretation:
        - Form > 0: Ready to perform (fitness > fatigue)
        - Form = 0: Balanced state
        - Form < 0: Fatigued state (fatigue > fitness)
        - Optimal performance: Form slightly positive after taper

    References:
        Banister, E. W. (1991). "Modeling human performance in running"
        Journal of Applied Physiology, 69(3), 1171-1177.
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    # Query all activities in the period
    activities = db.query(
        Activity.activity_date,
        func.sum(Activity.training_load).label('daily_load')
    ).filter(
        and_(
            Activity.user_id == user_id,
            Activity.activity_date >= start_date,
            Activity.activity_date <= end_date,
            Activity.training_load.isnot(None)
        )
    ).group_by(Activity.activity_date).all()

    if not activities:
        return {
            'fitness': 0.0,
            'fatigue': 0.0,
            'form': 0.0,
            'form_status': 'no_data',
            'recommendation': 'No training data available'
        }

    # Create dictionary of date -> load
    load_by_date = {a.activity_date: float(a.daily_load) for a in activities}

    # Calculate fitness and fatigue with exponential decay
    fitness = 0.0
    fatigue = 0.0

    for i in range(days):
        day = end_date - timedelta(days=i)
        load = load_by_date.get(day, 0.0)

        # Apply exponential decay: exp(-days_ago / time_constant)
        fitness_weight = np.exp(-i / fitness_decay)
        fatigue_weight = np.exp(-i / fatigue_decay)

        fitness += load * fitness_weight
        fatigue += load * fatigue_weight

    # Calculate form
    form = fitness - fatigue

    # Determine form status
    if form > 20:
        form_status = 'fresh'
        recommendation = 'Excellent form. Ready for high-intensity or race performance.'
    elif form > 0:
        form_status = 'optimal'
        recommendation = 'Good form. Ready for quality training or competition.'
    elif form > -20:
        form_status = 'fatigued'
        recommendation = 'Accumulated fatigue. Consider recovery or easy training.'
    else:
        form_status = 'overtrained'
        recommendation = 'High fatigue accumulation. Prioritize rest and recovery.'

    return {
        'fitness': float(fitness),
        'fatigue': float(fatigue),
        'form': float(form),
        'form_status': form_status,
        'recommendation': recommendation
    }


def calculate_training_monotony(
    db: Session,
    user_id: str,
    end_date: Optional[date] = None,
    days: int = 7
) -> Dict[str, any]:
    """
    Calculate training monotony and strain.

    Training monotony measures day-to-day variation in training load. Low variation
    (high monotony) increases injury and illness risk even with appropriate volume.

    Args:
        db: Database session
        user_id: User identifier
        end_date: End date for calculation (default: today)
        days: Number of days to analyze (default: 7)

    Returns:
        Dictionary containing:
        - monotony: Monotony score (higher = less variation)
        - strain: Training strain (load * monotony)
        - status: 'varied', 'moderate', or 'monotonous'
        - recommendation: Training variation recommendation

    Formulas:
        Monotony = Mean daily load / Standard deviation of daily load
        Strain = Sum of weekly load * Monotony

    Example:
        >>> monotony = calculate_training_monotony(db, "user123", days=7)
        >>> if monotony['status'] == 'monotonous':
        >>>     print(f"Warning: {monotony['recommendation']}")

    Interpretation:
        - Monotony < 1.5: Good variation in training
        - Monotony 1.5-2.0: Moderate monotony
        - Monotony > 2.0: High monotony (injury/illness risk)

    Notes:
        - Vary training intensity and type to reduce monotony
        - Include easy days between hard sessions
        - High strain (>7000) with high monotony is particularly risky

    References:
        Foster, C. (1998). "Monitoring training in athletes with reference to
        overtraining syndrome" Medicine & Science in Sports & Exercise.
    """
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)
    date_range = [start_date + timedelta(days=x) for x in range(days)]

    # Query activities
    activities = db.query(
        Activity.activity_date,
        func.sum(Activity.training_load).label('daily_load')
    ).filter(
        and_(
            Activity.user_id == user_id,
            Activity.activity_date >= start_date,
            Activity.activity_date <= end_date,
            Activity.training_load.isnot(None)
        )
    ).group_by(Activity.activity_date).all()

    load_by_date = {a.activity_date: float(a.daily_load) for a in activities}
    daily_loads = [load_by_date.get(d, 0.0) for d in date_range]

    # Calculate mean and std
    mean_load = float(np.mean(daily_loads))
    std_load = standard_deviation(daily_loads)

    if std_load == 0 or std_load is None or np.isnan(std_load):
        # All days same load = maximum monotony
        monotony = 5.0
        status = 'monotonous'
    else:
        monotony = mean_load / std_load

        if monotony < 1.5:
            status = 'varied'
        elif monotony < 2.0:
            status = 'moderate'
        else:
            status = 'monotonous'

    # Calculate strain
    total_load = float(np.sum(daily_loads))
    strain = total_load * monotony

    # Recommendations
    if status == 'varied':
        recommendation = 'Good training variation. Continue varying intensity and type.'
    elif status == 'moderate':
        recommendation = 'Moderate monotony. Consider adding more variety in training intensity.'
    else:
        recommendation = 'High monotony detected. Add variety: easy days, different activities, or rest days.'

    return {
        'monotony': float(monotony),
        'strain': float(strain),
        'mean_load': mean_load,
        'std_load': std_load,
        'total_load': total_load,
        'status': status,
        'recommendation': recommendation
    }


def estimate_recovery_time(
    workout_load: int,
    current_fatigue: float,
    fitness_level: float,
    baseline_recovery_rate: float = 24.0
) -> Dict[str, any]:
    """
    Estimate recovery time needed after a workout.

    Args:
        workout_load: Training load of the workout
        current_fatigue: Current fatigue level (from fitness-fatigue model)
        fitness_level: Current fitness level
        baseline_recovery_rate: Hours needed to recover from load of 100 (default: 24)

    Returns:
        Dictionary containing:
        - recovery_hours: Estimated hours needed for recovery
        - recovery_complete_at: When recovery should be complete
        - intensity_recommendation: Recommended intensity for next workout

    Formula:
        Recovery hours = (workout_load / 100) * baseline_rate * (1 + fatigue/fitness)

    Example:
        >>> recovery = estimate_recovery_time(
        >>>     workout_load=200,
        >>>     current_fatigue=50,
        >>>     fitness_level=100
        >>> )
        >>> print(f"Recovery needed: {recovery['recovery_hours']:.1f} hours")

    Notes:
        - Higher fitness = faster recovery
        - Higher pre-existing fatigue = slower recovery
        - Assumes baseline: 24 hours for load of 100 in well-rested athlete
    """
    if fitness_level == 0:
        fitness_level = 1  # Prevent division by zero

    # Base recovery time
    base_recovery = (workout_load / 100.0) * baseline_recovery_rate

    # Adjust for fitness and fatigue
    fatigue_factor = 1 + (current_fatigue / fitness_level)
    recovery_hours = base_recovery * fatigue_factor

    # Cap at reasonable maximum
    recovery_hours = min(recovery_hours, 96.0)  # Max 4 days

    # Determine intensity recommendation for next workout
    if recovery_hours < 12:
        intensity = 'moderate_to_high'
        recommendation = 'Short recovery needed. Can train moderate-high intensity after 12+ hours.'
    elif recovery_hours < 24:
        intensity = 'easy_to_moderate'
        recommendation = 'Standard recovery. Easy-moderate training after 24 hours.'
    elif recovery_hours < 48:
        intensity = 'easy'
        recommendation = 'Extended recovery needed. Only easy training for 1-2 days.'
    else:
        intensity = 'rest'
        recommendation = 'Significant recovery needed. Rest or very easy activity for 2+ days.'

    return {
        'recovery_hours': float(recovery_hours),
        'intensity_recommendation': intensity,
        'recommendation': recommendation
    }


def get_training_load_status(
    db: Session,
    user_id: str,
    current_date: Optional[date] = None
) -> Dict[str, any]:
    """
    Get comprehensive training load status.

    Combines ACWR, fitness-fatigue, and monotony into single assessment.

    Args:
        db: Database session
        user_id: User identifier
        current_date: Date to assess (default: today)

    Returns:
        Dictionary containing all training load metrics and overall status

    Example:
        >>> status = get_training_load_status(db, "user123")
        >>> print(f"Overall Status: {status['overall_status']}")
        >>> print(f"Primary Concern: {status['primary_concern']}")
    """
    if current_date is None:
        current_date = date.today()

    # Calculate all metrics
    acute = calculate_acute_load(db, user_id, current_date)
    chronic = calculate_chronic_load(db, user_id, current_date)
    acwr_result = calculate_acwr(acute, chronic) if acute and chronic else None
    ff = calculate_fitness_fatigue(db, user_id, current_date)
    monotony = calculate_training_monotony(db, user_id, current_date)

    # Determine overall status
    concerns = []

    if acwr_result and acwr_result['status'] in ['moderate_risk', 'high_risk']:
        concerns.append(f"ACWR {acwr_result['status']}: {acwr_result['recommendation']}")

    if ff['form_status'] in ['overtrained', 'fatigued']:
        concerns.append(f"Form {ff['form_status']}: {ff['recommendation']}")

    if monotony['status'] == 'monotonous':
        concerns.append(f"High monotony: {monotony['recommendation']}")

    if not concerns:
        overall_status = 'optimal'
        primary_concern = 'Training load well-managed. Continue current approach.'
    elif len(concerns) == 1:
        overall_status = 'caution'
        primary_concern = concerns[0]
    else:
        overall_status = 'warning'
        primary_concern = 'Multiple concerns detected. Prioritize recovery.'

    return {
        'acute_load': acute,
        'chronic_load': chronic,
        'acwr': acwr_result,
        'fitness_fatigue': ff,
        'monotony': monotony,
        'overall_status': overall_status,
        'primary_concern': primary_concern,
        'all_concerns': concerns
    }
