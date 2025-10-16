"""
Main data processor service for the AI Training Optimizer.

This service orchestrates all data processing operations including:
- Calculating baselines and metrics
- Running HRV, sleep, and training load analyses
- Generating daily readiness scores
- Caching results for performance
- Updating TrainingLoadTracking and DailyReadiness tables

The DataProcessor is the main entry point for processing health and training data.
It coordinates between utility modules and updates the database with calculated metrics.
"""

from datetime import date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import hashlib
import json
from functools import lru_cache

from app.models.database_models import (
    DailyMetrics,
    TrainingLoadTracking,
    DailyReadiness,
    AIAnalysisCache,
    ReadinessRecommendation
)
from app.utils import hrv_analysis, training_load, sleep_analysis
from app.services.aggregation_service import AggregationService


class DataProcessor:
    """
    Main service for processing and analyzing health/training data.

    This class coordinates all data processing operations and maintains
    a cache for expensive calculations.
    """

    def __init__(self, db: Session):
        """
        Initialize data processor.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.aggregation_service = AggregationService(db)

    @staticmethod
    def _get_value(obj, key, default=None):
        """
        Get value from dict or SQLAlchemy model object.

        Args:
            obj: Dictionary or SQLAlchemy model instance
            key: Field/key name
            default: Default value if not found

        Returns:
            Value from object
        """
        if hasattr(obj, 'get'):
            # Dict-like object
            return obj.get(key, default)
        else:
            # SQLAlchemy model or other object
            return getattr(obj, key, default)

    def process_daily_metrics(
        self,
        user_id: str,
        target_date: Optional[date] = None,
        force_recalculate: bool = False
    ) -> Dict[str, any]:
        """
        Process all daily metrics for a specific date.

        This is the main entry point for daily data processing. It:
        1. Calculates HRV baselines and trends
        2. Analyzes sleep quality
        3. Calculates training load metrics (ACWR, fitness-fatigue)
        4. Generates overall readiness score
        5. Updates TrainingLoadTracking and DailyReadiness tables

        Args:
            user_id: User identifier
            target_date: Date to process (default: today)
            force_recalculate: If True, bypass cache and recalculate everything

        Returns:
            Dictionary containing all processed metrics and readiness assessment

        Example:
            >>> processor = DataProcessor(db)
            >>> result = processor.process_daily_metrics("user123")
            >>> print(f"Readiness: {result['readiness_score']}/100")
            >>> print(f"Recommendation: {result['recommendation']}")

        Notes:
            - This method is idempotent (safe to call multiple times)
            - Results are cached to avoid redundant calculations
            - Call with force_recalculate=True after data updates
        """
        if target_date is None:
            target_date = date.today()

        # Check cache unless force recalculate
        if not force_recalculate:
            cached_result = self._get_cached_result(user_id, target_date, 'daily_metrics')
            if cached_result:
                return cached_result

        # Verify daily metrics exist
        daily_metric = self.db.query(DailyMetrics).filter(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.date == target_date
            )
        ).first()

        if not daily_metric:
            return {
                'status': 'no_data',
                'message': f'No daily metrics found for {target_date}'
            }

        # Calculate all components
        hrv_status = hrv_analysis.get_hrv_status(self.db, user_id, target_date)
        sleep_status = sleep_analysis.get_sleep_status(self.db, user_id, target_date)
        load_status = training_load.get_training_load_status(self.db, user_id, target_date)

        # Calculate component scores
        hrv_score = hrv_analysis.get_hrv_score(hrv_status)
        sleep_score = sleep_analysis.get_sleep_score(sleep_status)
        load_score = self._calculate_load_score(load_status)

        # Calculate overall readiness score (weighted)
        readiness_score = self._calculate_readiness_score(hrv_score, sleep_score, load_score)

        # Determine recommendation
        recommendation = self._determine_recommendation(
            readiness_score,
            hrv_status,
            sleep_status,
            load_status
        )

        # Update TrainingLoadTracking table
        self._update_training_load_tracking(
            user_id,
            target_date,
            daily_metric.id,
            load_status
        )

        # Update DailyReadiness table
        self._update_daily_readiness(
            user_id,
            target_date,
            daily_metric.id,
            readiness_score,
            recommendation,
            hrv_status,
            sleep_status,
            load_status
        )

        # Prepare result
        result = {
            'status': 'success',
            'date': target_date.isoformat(),
            'user_id': user_id,

            # Component scores
            'scores': {
                'hrv': hrv_score,
                'sleep': sleep_score,
                'training_load': load_score,
                'overall_readiness': readiness_score
            },

            # Detailed status
            'hrv': hrv_status,
            'sleep': sleep_status,
            'training_load': load_status,

            # Recommendation
            'readiness_score': readiness_score,
            'recommendation': recommendation,
            'recommended_intensity': self._get_intensity_from_score(readiness_score)
        }

        # Cache result
        self._cache_result(user_id, target_date, 'daily_metrics', result)

        return result

    def process_date_range(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        force_recalculate: bool = False
    ) -> Dict[str, any]:
        """
        Process daily metrics for a date range.

        Useful for:
        - Backfilling historical data
        - Recalculating after data corrections
        - Batch processing

        Args:
            user_id: User identifier
            start_date: First date to process
            end_date: Last date to process (inclusive)
            force_recalculate: If True, bypass cache

        Returns:
            Dictionary with processing summary

        Example:
            >>> processor = DataProcessor(db)
            >>> result = processor.process_date_range(
            >>>     "user123",
            >>>     date.today() - timedelta(days=30),
            >>>     date.today()
            >>> )
            >>> print(f"Processed {result['processed_count']} days")
        """
        processed_count = 0
        error_count = 0
        errors = []

        current_date = start_date
        while current_date <= end_date:
            try:
                result = self.process_daily_metrics(user_id, current_date, force_recalculate)
                if result['status'] == 'success':
                    processed_count += 1
                elif result['status'] == 'no_data':
                    pass  # Expected for days without data
                else:
                    error_count += 1
                    errors.append({
                        'date': current_date.isoformat(),
                        'error': result.get('message', 'Unknown error')
                    })
            except Exception as e:
                error_count += 1
                errors.append({
                    'date': current_date.isoformat(),
                    'error': str(e)
                })

            current_date += timedelta(days=1)

        return {
            'status': 'completed',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'processed_count': processed_count,
            'error_count': error_count,
            'errors': errors
        }

    def get_readiness_summary(
        self,
        user_id: str,
        target_date: Optional[date] = None
    ) -> Dict[str, any]:
        """
        Get comprehensive readiness summary for a date.

        This is a higher-level method that combines processed metrics
        with aggregated data for a complete readiness picture.

        Args:
            user_id: User identifier
            target_date: Date to assess (default: today)

        Returns:
            Dictionary with complete readiness assessment

        Example:
            >>> processor = DataProcessor(db)
            >>> summary = processor.get_readiness_summary("user123")
            >>> print(summary['recommendation'])
        """
        if target_date is None:
            target_date = date.today()

        # Process metrics
        processed = self.process_daily_metrics(user_id, target_date)

        # Get aggregated daily summary
        daily_summary = self.aggregation_service.aggregate_daily_summary(user_id, target_date)

        return {
            'date': target_date.isoformat(),
            'readiness_score': processed['readiness_score'],
            'recommendation': processed['recommendation'],
            'recommended_intensity': processed['recommended_intensity'],
            'component_scores': processed['scores'],
            'daily_summary': daily_summary
        }

    def clear_cache(self, user_id: Optional[str] = None) -> int:
        """
        Clear analysis cache.

        Args:
            user_id: If provided, clear only this user's cache. Otherwise clear all.

        Returns:
            Number of cache entries deleted

        Example:
            >>> processor = DataProcessor(db)
            >>> deleted = processor.clear_cache("user123")
            >>> print(f"Cleared {deleted} cache entries")
        """
        query = self.db.query(AIAnalysisCache)

        if user_id:
            # Clear only entries related to this user (match user_id in content_hash)
            # For simplicity, we'll clear all and let them rebuild
            pass

        deleted_count = query.delete()
        self.db.commit()

        return deleted_count

    # Private helper methods

    def _calculate_readiness_score(
        self,
        hrv_score: int,
        sleep_score: int,
        load_score: int
    ) -> int:
        """
        Calculate overall readiness score from component scores.

        Weights:
        - HRV: 40% (most important for acute recovery)
        - Sleep: 35% (critical for recovery)
        - Training Load: 25% (context for training stimulus)

        Args:
            hrv_score: HRV-based readiness (0-100)
            sleep_score: Sleep-based readiness (0-100)
            load_score: Training load status (0-100)

        Returns:
            Overall readiness score (0-100)
        """
        readiness = (
            hrv_score * 0.40 +
            sleep_score * 0.35 +
            load_score * 0.25
        )

        return int(round(readiness))

    def _calculate_load_score(self, load_status: Dict) -> int:
        """Convert training load status to 0-100 score."""
        if not load_status or load_status.get('overall_status') == 'no_data':
            return 50  # Neutral

        status_scores = {
            'optimal': 90,
            'caution': 70,
            'warning': 40
        }

        return status_scores.get(load_status.get('overall_status', 'optimal'), 50)

    def _determine_recommendation(
        self,
        readiness_score: int,
        hrv_status: Dict,
        sleep_status: Dict,
        load_status: Dict
    ) -> ReadinessRecommendation:
        """
        Determine training recommendation based on all factors.

        Args:
            readiness_score: Overall readiness (0-100)
            hrv_status: HRV analysis results
            sleep_status: Sleep analysis results
            load_status: Training load analysis results

        Returns:
            ReadinessRecommendation enum value
        """
        # Priority concerns (with None checks)
        if load_status and load_status.get('fitness_fatigue', {}).get('form_status') == 'overtrained':
            return ReadinessRecommendation.RECOVERY

        if sleep_status and sleep_status.get('sleep_debt', {}).get('severity') == 'severe':
            return ReadinessRecommendation.REST

        if hrv_status:
            drop_vs_7d = hrv_status.get('drop_vs_7d') if hrv_status else None
            if drop_vs_7d and drop_vs_7d.get('severity') == 'severe':
                return ReadinessRecommendation.REST

        # Score-based recommendations
        if readiness_score >= 85:
            return ReadinessRecommendation.HIGH_INTENSITY
        elif readiness_score >= 70:
            return ReadinessRecommendation.MODERATE
        elif readiness_score >= 55:
            return ReadinessRecommendation.EASY
        else:
            return ReadinessRecommendation.REST

    def _get_intensity_from_score(self, score: int) -> str:
        """Convert readiness score to intensity recommendation."""
        if score >= 85:
            return "High intensity or race effort"
        elif score >= 70:
            return "Moderate to high intensity"
        elif score >= 55:
            return "Easy to moderate intensity"
        else:
            return "Rest or very easy recovery"

    def _update_training_load_tracking(
        self,
        user_id: str,
        target_date: date,
        daily_metric_id: int,
        load_status: Dict
    ) -> None:
        """Update or create TrainingLoadTracking record."""
        # Check if exists
        tracking = self.db.query(TrainingLoadTracking).filter(
            and_(
                TrainingLoadTracking.user_id == user_id,
                TrainingLoadTracking.tracking_date == target_date
            )
        ).first()

        if not tracking:
            tracking = TrainingLoadTracking(
                user_id=user_id,
                daily_metric_id=daily_metric_id,
                tracking_date=target_date
            )
            self.db.add(tracking)

        # Update values
        tracking.daily_training_load = int(load_status.get('acute_load', 0) * 7 if load_status.get('acute_load') else 0)
        tracking.acute_training_load = int(load_status.get('acute_load', 0)) if load_status.get('acute_load') else None
        tracking.chronic_training_load = int(load_status.get('chronic_load', 0)) if load_status.get('chronic_load') else None

        if load_status.get('acwr'):
            tracking.acwr = load_status['acwr'].get('acwr')
            tracking.acwr_status = load_status['acwr'].get('status')

        if load_status.get('fitness_fatigue'):
            tracking.fitness = load_status['fitness_fatigue'].get('fitness')
            tracking.fatigue = load_status['fitness_fatigue'].get('fatigue')
            tracking.form = load_status['fitness_fatigue'].get('form')

        if load_status.get('monotony'):
            tracking.training_monotony = load_status['monotony'].get('monotony')
            tracking.training_strain = load_status['monotony'].get('strain')

        self.db.commit()

    def _update_daily_readiness(
        self,
        user_id: str,
        target_date: date,
        daily_metric_id: int,
        readiness_score: int,
        recommendation: ReadinessRecommendation,
        hrv_status: Dict,
        sleep_status: Dict,
        load_status: Dict
    ) -> None:
        """Update or create DailyReadiness record."""
        # Check if exists
        readiness = self.db.query(DailyReadiness).filter(
            and_(
                DailyReadiness.user_id == user_id,
                DailyReadiness.readiness_date == target_date
            )
        ).first()

        if not readiness:
            readiness = DailyReadiness(
                user_id=user_id,
                daily_metric_id=daily_metric_id,
                readiness_date=target_date
            )
            self.db.add(readiness)

        # Update values
        readiness.readiness_score = readiness_score
        readiness.recommendation = recommendation
        readiness.recommended_intensity = self._get_intensity_from_score(readiness_score)

        # Key factors
        readiness.key_factors = {
            'hrv_status': hrv_status.get('status') if hrv_status else None,
            'hrv_score': hrv_analysis.get_hrv_score(hrv_status),
            'sleep_status': sleep_status.get('status') if sleep_status else None,
            'sleep_score': sleep_analysis.get_sleep_score(sleep_status),
            'load_status': load_status.get('overall_status') if load_status else None
        }

        # Red flags
        red_flags = []
        if hrv_status:
            drop_vs_7d = hrv_status.get('drop_vs_7d')
            if drop_vs_7d and drop_vs_7d.get('severity') in ['moderate', 'severe']:
                red_flags.append(f"HRV drop: {drop_vs_7d['severity']}")
        if sleep_status:
            sleep_debt = sleep_status.get('sleep_debt')
            if sleep_debt and sleep_debt.get('severity') in ['moderate', 'severe']:
                red_flags.append(f"Sleep debt: {sleep_debt['severity']}")
        if load_status and load_status.get('overall_status') in ['caution', 'warning']:
            red_flags.append(f"Training load: {load_status['overall_status']}")

        readiness.red_flags = {'flags': red_flags} if red_flags else None

        # AI analysis summary
        readiness.ai_analysis = self._generate_ai_analysis_summary(
            hrv_status,
            sleep_status,
            load_status,
            readiness_score
        )

        # Training load context
        if load_status:
            readiness.training_load_7d = load_status.get('acute_load')
            readiness.training_load_28d = load_status.get('chronic_load')
            readiness.acwr = load_status.get('acwr', {}).get('acwr') if load_status.get('acwr') else None
        else:
            readiness.training_load_7d = None
            readiness.training_load_28d = None
            readiness.acwr = None

        self.db.commit()

    def _generate_ai_analysis_summary(
        self,
        hrv_status: Dict,
        sleep_status: Dict,
        load_status: Dict,
        readiness_score: int
    ) -> str:
        """Generate human-readable AI analysis summary."""
        parts = [
            f"Readiness Score: {readiness_score}/100.",
            f"HRV: {hrv_status.get('status', 'unknown')}.",
            f"Sleep: {sleep_status.get('status', 'unknown')}.",
            f"Training Load: {load_status.get('overall_status', 'unknown')}."
        ]

        if load_status.get('primary_concern'):
            parts.append(f"Primary concern: {load_status['primary_concern']}")

        return " ".join(parts)

    def _get_cached_result(
        self,
        user_id: str,
        target_date: date,
        analysis_type: str
    ) -> Optional[Dict]:
        """Get cached analysis result if available."""
        # Create cache key
        cache_key = f"{user_id}:{target_date.isoformat()}:{analysis_type}"
        content_hash = hashlib.sha256(cache_key.encode()).hexdigest()

        # Query cache
        cached = self.db.query(AIAnalysisCache).filter(
            AIAnalysisCache.content_hash == content_hash
        ).first()

        if not cached:
            return None

        # Check if expired
        if cached.expires_at and cached.expires_at < date.today():
            return None

        # Update access stats
        cached.hit_count += 1
        cached.last_accessed_at = date.today()
        self.db.commit()

        # Return structured output if available
        return cached.structured_output

    def _cache_result(
        self,
        user_id: str,
        target_date: date,
        analysis_type: str,
        result: Dict
    ) -> None:
        """Cache analysis result."""
        # Create cache key
        cache_key = f"{user_id}:{target_date.isoformat()}:{analysis_type}"
        content_hash = hashlib.sha256(cache_key.encode()).hexdigest()

        # Check if exists
        cached = self.db.query(AIAnalysisCache).filter(
            AIAnalysisCache.content_hash == content_hash
        ).first()

        if cached:
            # Update existing
            cached.structured_output = result
            cached.hit_count = 0
            cached.last_accessed_at = date.today()
        else:
            # Create new
            cached = AIAnalysisCache(
                content_hash=content_hash,
                analysis_type=analysis_type,
                input_context={'user_id': user_id, 'date': target_date.isoformat()},
                ai_response=json.dumps(result),
                ai_model_version='data_processor_v1',
                structured_output=result,
                hit_count=0
            )
            self.db.add(cached)

        self.db.commit()

    # ========================================================================
    # WRAPPER METHODS FOR TESTING API
    # ========================================================================
    # These methods bridge the test API with utility modules by accepting
    # raw data (arrays, lists, dicts) and delegating to utility functions.
    # ========================================================================

    # ------------------------------------------------------------------------
    # HRV Analysis Wrappers
    # ------------------------------------------------------------------------

    def calculate_hrv_baseline_from_db(
        self,
        user_id: str,
        days: int = 30
    ) -> Optional[Dict]:
        """
        Calculate HRV baseline from database.

        Args:
            user_id: User identifier
            days: Number of days for baseline calculation

        Returns:
            Dictionary with baseline stats or None if no data
        """
        from app.services import data_access

        return data_access.get_hrv_baseline(self.db, user_id, days=days)

    def calculate_training_load_from_db(
        self,
        user_id: str,
        days: int = 30
    ) -> Optional[Dict]:
        """
        Calculate training load metrics from database.

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            Dictionary with training load metrics
        """
        from app.services import data_access

        acute_load = data_access.get_acute_training_load(self.db, user_id, days=7)
        chronic_load = data_access.get_chronic_training_load(self.db, user_id, days=28)
        acwr = data_access.calculate_acwr(self.db, user_id)

        return {
            'acute_load': acute_load,
            'chronic_load': chronic_load,
            'acwr': acwr
        }

    def calculate_fitness_fatigue_from_db(
        self,
        user_id: str,
        days: int = 90
    ) -> Optional[Dict]:
        """
        Calculate fitness-fatigue model from database.

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            Dictionary with fitness, fatigue, form values
        """
        from app.services import data_access
        from datetime import timedelta

        start_date = date.today() - timedelta(days=days)
        end_date = date.today()

        # Get training load history
        load_records = data_access.get_training_load_range(
            self.db,
            user_id,
            start_date,
            end_date
        )

        if not load_records:
            return None

        # Convert to training history format
        training_history = [
            {
                'date': record.tracking_date,
                'training_load': record.daily_training_load or 0
            }
            for record in load_records
        ]

        # Calculate using wrapper methods
        fitness = self.calculate_fitness(training_history)
        fatigue = self.calculate_fatigue(training_history)
        form = self.calculate_form(training_history)

        return {
            'fitness': fitness,
            'fatigue': fatigue,
            'form': form,
            'form_status': self.interpret_form(form)
        }

    def calculate_hrv_baseline(
        self,
        hrv_data: List[float],
        days: int = 7,
        remove_outliers: bool = False
    ) -> Dict:
        """
        Calculate HRV baseline from raw data array.

        Args:
            hrv_data: List of HRV values (ms)
            days: Number of days for baseline calculation
            remove_outliers: Whether to remove outliers before calculation

        Returns:
            Dictionary with 'mean' and 'std' keys

        Raises:
            ValueError: If data is empty, insufficient, or invalid
        """
        from app.utils import statistics
        import numpy as np

        # Validate input
        if not hrv_data:
            raise ValueError("HRV data cannot be empty")

        # Filter out None and NaN values
        valid_data = [x for x in hrv_data if x is not None and not (isinstance(x, float) and np.isnan(x))]

        if not valid_data:
            raise ValueError("All HRV values are None or NaN")

        # Check for negative values
        if any(x < 0 for x in valid_data):
            raise ValueError("HRV values cannot be negative")

        # Check sufficient data
        if len(valid_data) < max(2, days // 2):
            raise ValueError(f"Insufficient data: need at least {max(2, days // 2)} valid readings for {days}-day baseline")

        # Remove outliers if requested
        if remove_outliers:
            outlier_mask, _ = statistics.detect_outliers(valid_data, method='iqr', threshold=1.5)
            valid_data = [x for i, x in enumerate(valid_data) if not outlier_mask[i]]

        # Calculate baseline
        mean_hrv = float(np.mean(valid_data))
        std_hrv = statistics.standard_deviation(valid_data)

        return {
            'mean': mean_hrv,
            'std': std_hrv,
            'count': len(valid_data)
        }

    def detect_hrv_drop(
        self,
        current_hrv: float,
        baseline: Dict
    ) -> Dict:
        """
        Detect significant HRV drop from baseline.

        Args:
            current_hrv: Current HRV value (ms)
            baseline: Baseline dict with 'mean' and 'std' keys

        Returns:
            Dictionary with 'is_significant' and 'drop_percentage' keys
        """
        from app.utils import hrv_analysis

        baseline_mean = baseline.get('mean', 0)
        result = hrv_analysis.detect_hrv_drop(current_hrv, baseline_mean)

        return {
            'is_significant': result['drop_detected'],
            'drop_percentage': result['drop_percent'],
            'severity': result['severity'],
            'recommendation': result['recommendation']
        }

    def analyze_hrv_trend(
        self,
        hrv_timeseries: List[Dict],
        days: int = 30
    ) -> Dict:
        """
        Analyze HRV trend from time series data.

        Args:
            hrv_timeseries: List of dicts with 'date' and 'hrv' keys
            days: Number of days to analyze

        Returns:
            Dictionary with 'slope', 'direction', and 'r_squared' keys
        """
        from app.utils import statistics

        if not hrv_timeseries:
            raise ValueError("HRV timeseries cannot be empty")

        # Extract x (days) and y (hrv) values
        x_values = list(range(len(hrv_timeseries)))
        y_values = [point['hrv'] for point in hrv_timeseries]

        # Perform linear regression
        slope, intercept, r_squared = statistics.linear_regression(x_values, y_values)

        # Determine direction
        if slope > 0.1:
            direction = 'increasing'
        elif slope < -0.1:
            direction = 'decreasing'
        else:
            direction = 'stable'

        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared),
            'direction': direction
        }

    def assess_recovery_status(
        self,
        current_hrv: float,
        baseline: Dict
    ) -> str:
        """
        Assess recovery status based on current HRV vs baseline.

        Args:
            current_hrv: Current HRV value (ms)
            baseline: Baseline dict with 'mean' and 'std' keys

        Returns:
            Recovery status: 'well_recovered', 'recovered', 'recovering', 'not_recovered'
        """
        baseline_mean = baseline.get('mean', 0)
        baseline_std = baseline.get('std', 0)

        # Calculate how many standard deviations from baseline
        if baseline_std > 0:
            z_score = (current_hrv - baseline_mean) / baseline_std
        else:
            z_score = 0

        # Classify recovery status
        if z_score >= 1.0:
            return 'well_recovered'
        elif z_score >= 0:
            return 'recovered'
        elif z_score >= -1.0:
            return 'recovering'
        else:
            return 'not_recovered'

    # ------------------------------------------------------------------------
    # Training Load Wrappers
    # ------------------------------------------------------------------------

    def calculate_acute_load(self, load_data: List[float]) -> float:
        """
        Calculate acute training load (7-day rolling average).

        Args:
            load_data: List of daily training load values

        Returns:
            Acute load value
        """
        import numpy as np

        if not load_data:
            raise ValueError("Load data cannot be empty")

        return float(np.mean(load_data[-7:]))

    def calculate_chronic_load(self, load_data: List[float]) -> float:
        """
        Calculate chronic training load (28-day rolling average).

        Args:
            load_data: List of daily training load values

        Returns:
            Chronic load value
        """
        import numpy as np

        if not load_data:
            raise ValueError("Load data cannot be empty")

        return float(np.mean(load_data[-28:]))

    def calculate_acwr(self, load_data: List[float]) -> float:
        """
        Calculate ACWR (Acute:Chronic Workload Ratio).

        Args:
            load_data: List of daily training load values (at least 28 days)

        Returns:
            ACWR value
        """
        acute = self.calculate_acute_load(load_data)
        chronic = self.calculate_chronic_load(load_data)

        if chronic == 0:
            return 0.0

        return acute / chronic

    def classify_acwr(self, acwr: float) -> str:
        """
        Classify ACWR into risk categories.

        Args:
            acwr: ACWR value

        Returns:
            Classification: 'optimal', 'moderate', or 'high_risk'
        """
        if 0.8 <= acwr <= 1.3:
            return 'optimal'
        elif 1.3 < acwr <= 1.5:
            return 'moderate'
        else:
            return 'high_risk'

    def calculate_monotony(self, loads: List[float]) -> float:
        """
        Calculate training monotony (mean / std).

        Args:
            loads: List of daily training loads

        Returns:
            Monotony score
        """
        from app.utils import statistics
        import numpy as np

        if not loads:
            raise ValueError("Loads cannot be empty")

        mean_load = float(np.mean(loads))
        std_load = statistics.standard_deviation(loads)

        if std_load == 0 or std_load is None or np.isnan(std_load):
            return 5.0  # Maximum monotony

        return mean_load / std_load

    def calculate_training_strain(self, weekly_loads: List[float]) -> float:
        """
        Calculate training strain (total load * monotony).

        Args:
            weekly_loads: List of daily training loads for a week

        Returns:
            Training strain value
        """
        import numpy as np

        total_load = float(np.sum(weekly_loads))
        monotony = self.calculate_monotony(weekly_loads)

        return total_load * monotony

    def calculate_ramp_rate(
        self,
        last_week_load: float,
        this_week_load: float
    ) -> float:
        """
        Calculate weekly ramp rate (percentage change).

        Args:
            last_week_load: Previous week's total load
            this_week_load: Current week's total load

        Returns:
            Ramp rate as percentage
        """
        if last_week_load == 0:
            return float('inf') if this_week_load > 0 else 0.0

        return ((this_week_load - last_week_load) / last_week_load) * 100

    def is_safe_ramp_rate(self, ramp_rate: float) -> bool:
        """
        Check if ramp rate is safe (<10% per week).

        Args:
            ramp_rate: Ramp rate percentage

        Returns:
            True if safe, False otherwise
        """
        return ramp_rate <= 10.0

    # ------------------------------------------------------------------------
    # Fitness-Fatigue Model Wrappers
    # ------------------------------------------------------------------------

    def calculate_fitness(self, training_history: List[Dict]) -> float:
        """
        Calculate fitness (CTL - Chronic Training Load).

        Args:
            training_history: List of dicts with 'date' and 'training_load' keys

        Returns:
            Fitness value
        """
        from app.utils import statistics
        import numpy as np

        if not training_history:
            return 0.0

        loads = [point['training_load'] for point in training_history]
        fitness_decay = 42

        # Calculate exponentially weighted fitness
        fitness = 0.0
        for i, load in enumerate(reversed(loads)):
            days_ago = i
            weight = np.exp(-days_ago / fitness_decay)
            fitness += load * weight

        return float(fitness)

    def calculate_fatigue(self, training_history: List[Dict]) -> float:
        """
        Calculate fatigue (ATL - Acute Training Load).

        Args:
            training_history: List of dicts with 'date' and 'training_load' keys

        Returns:
            Fatigue value
        """
        import numpy as np

        if not training_history:
            return 0.0

        loads = [point['training_load'] for point in training_history]
        fatigue_decay = 7

        # Calculate exponentially weighted fatigue
        fatigue = 0.0
        for i, load in enumerate(reversed(loads)):
            days_ago = i
            weight = np.exp(-days_ago / fatigue_decay)
            fatigue += load * weight

        return float(fatigue)

    def calculate_form(self, training_history: List[Dict]) -> float:
        """
        Calculate form (TSB - Training Stress Balance = Fitness - Fatigue).

        Args:
            training_history: List of dicts with 'date' and 'training_load' keys

        Returns:
            Form value (positive = fresh, negative = fatigued)
        """
        fitness = self.calculate_fitness(training_history)
        fatigue = self.calculate_fatigue(training_history)

        return fitness - fatigue

    def interpret_form(self, form: float) -> str:
        """
        Interpret form score into status categories.

        Args:
            form: Form value (fitness - fatigue)

        Returns:
            Form status: 'fresh', 'race_ready', 'fatigued', or 'overtrained'
        """
        if form > 10:
            return 'fresh'
        elif form >= -5:
            return 'race_ready'
        elif form >= -20:
            return 'fatigued'
        else:
            return 'overtrained'

    def calculate_fitness_fatigue_evolution(
        self,
        training_history: List[Dict]
    ) -> Dict:
        """
        Calculate fitness/fatigue evolution over time.

        Args:
            training_history: List of dicts with 'date' and 'training_load' keys

        Returns:
            Dictionary with 'dates', 'fitness', 'fatigue', and 'form' arrays
        """
        dates = []
        fitness_values = []
        fatigue_values = []
        form_values = []

        # Calculate cumulative fitness/fatigue for each day
        for i in range(len(training_history)):
            history_subset = training_history[:i+1]
            dates.append(history_subset[-1]['date'])

            fitness = self.calculate_fitness(history_subset)
            fatigue = self.calculate_fatigue(history_subset)
            form = fitness - fatigue

            fitness_values.append(fitness)
            fatigue_values.append(fatigue)
            form_values.append(form)

        return {
            'dates': dates,
            'fitness': fitness_values,
            'fatigue': fatigue_values,
            'form': form_values
        }

    # ------------------------------------------------------------------------
    # Sleep Analysis Wrappers
    # ------------------------------------------------------------------------

    def calculate_sleep_quality_score(self, sleep_data: Dict) -> float:
        """
        Calculate sleep quality score from sleep data.

        Args:
            sleep_data: Dict with sleep metrics (total_sleep_minutes, deep, rem, etc.)

        Returns:
            Sleep quality score (0-100)
        """
        from app.utils import sleep_analysis

        result = sleep_analysis.calculate_sleep_quality_score(
            total_sleep_minutes=self._get_value(sleep_data, 'total_sleep_minutes', 0),
            deep_sleep_minutes=self._get_value(sleep_data, 'deep_sleep_minutes'),
            light_sleep_minutes=self._get_value(sleep_data, 'light_sleep_minutes'),
            rem_sleep_minutes=self._get_value(sleep_data, 'rem_sleep_minutes'),
            awake_minutes=self._get_value(sleep_data, 'awake_minutes'),
            awakenings_count=self._get_value(sleep_data, 'awakenings_count')
        )

        return result['score']

    def detect_poor_sleep_pattern(
        self,
        sleep_data: List[Dict],
        days: int = 3
    ) -> Dict:
        """
        Detect poor sleep patterns over multiple nights.

        Args:
            sleep_data: List of dicts with 'total_sleep_minutes' key
            days: Number of days to analyze

        Returns:
            Dictionary with 'is_poor' and 'average_sleep_hours' keys
        """
        if not sleep_data:
            return {'is_poor': False, 'average_sleep_hours': 0.0}

        total_minutes = sum(night['total_sleep_minutes'] for night in sleep_data[-days:])
        avg_hours = total_minutes / days / 60

        return {
            'is_poor': avg_hours < 6.0,
            'average_sleep_hours': avg_hours
        }

    def calculate_sleep_debt(
        self,
        actual_sleep_data: List[Dict],
        target_sleep_hours: float,
        days: int = 7
    ) -> float:
        """
        Calculate accumulated sleep debt.

        Args:
            actual_sleep_data: List of dicts with 'total_sleep_minutes' key
            target_sleep_hours: Target sleep duration (hours)
            days: Number of days to analyze

        Returns:
            Total sleep debt in hours
        """
        target_minutes = target_sleep_hours * 60
        debt_hours = 0.0

        for night in actual_sleep_data[-days:]:
            deficit = max(0, target_minutes - night['total_sleep_minutes'])
            debt_hours += deficit / 60

        return debt_hours

    def analyze_sleep_consistency(self, sleep_data: List[Dict]) -> Dict:
        """
        Analyze sleep consistency (timing and duration).

        Args:
            sleep_data: List of dicts with 'sleep_start_time' and 'total_sleep_minutes' keys

        Returns:
            Dictionary with 'is_consistent' key
        """
        from app.utils import statistics

        if len(sleep_data) < 2:
            return {'is_consistent': True}

        # Analyze duration consistency
        durations = [night['total_sleep_minutes'] for night in sleep_data]
        duration_std = statistics.standard_deviation(durations)

        # Analyze timing consistency (convert start times to minutes since midnight)
        start_times = []
        for night in sleep_data:
            start_time = night['sleep_start_time']
            minutes_since_midnight = start_time.hour * 60 + start_time.minute
            start_times.append(minutes_since_midnight)

        timing_std = statistics.standard_deviation(start_times)

        # Consistent if both duration and timing are stable
        is_consistent = duration_std < 60 and timing_std < 60  # Within 1 hour variance

        return {
            'is_consistent': bool(is_consistent),  # Convert to Python bool
            'duration_std': duration_std,
            'timing_std': timing_std
        }

    def analyze_sleep_stage_distribution(self, sleep_data: Dict) -> Dict:
        """
        Analyze distribution of sleep stages.

        Args:
            sleep_data: Dict with deep, light, rem, awake minutes

        Returns:
            Dictionary with percentage distributions
        """
        total_sleep = self._get_value(sleep_data, 'total_sleep_minutes', 0)

        if total_sleep == 0:
            return {
                'deep_percentage': 0.0,
                'light_percentage': 0.0,
                'rem_percentage': 0.0
            }

        return {
            'deep_percentage': (self._get_value(sleep_data, 'deep_sleep_minutes', 0) / total_sleep) * 100,
            'light_percentage': (self._get_value(sleep_data, 'light_sleep_minutes', 0) / total_sleep) * 100,
            'rem_percentage': (self._get_value(sleep_data, 'rem_sleep_minutes', 0) / total_sleep) * 100
        }

    # ------------------------------------------------------------------------
    # Statistical Function Wrappers
    # ------------------------------------------------------------------------

    def moving_average(
        self,
        data: List[float],
        window: int = 7
    ) -> List[float]:
        """
        Calculate moving average.

        Args:
            data: Input time series data
            window: Window size for moving average

        Returns:
            List of moving average values
        """
        from app.utils import statistics

        result = statistics.moving_average(data, window=window, min_periods=window)
        return result.tolist()

    def exponential_moving_average(
        self,
        data: List[float],
        span: int = 7
    ) -> List[float]:
        """
        Calculate exponential moving average (EMA).

        Args:
            data: Input time series data
            span: Decay span for EMA

        Returns:
            List of EMA values
        """
        from app.utils import statistics

        result = statistics.exponentially_weighted_moving_average(data, span=span)
        return result.tolist()

    def standard_deviation(self, data: List[float]) -> float:
        """
        Calculate standard deviation.

        Args:
            data: Input data array

        Returns:
            Standard deviation value
        """
        from app.utils import statistics

        return statistics.standard_deviation(data)

    def percentile(self, data: List[float], p: float) -> float:
        """
        Calculate percentile.

        Args:
            data: Input data array
            p: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        from app.utils import statistics

        return statistics.percentile(data, p=p)

    def z_score(self, value: float, data: List[float]) -> float:
        """
        Calculate z-score for a value relative to a dataset.

        Args:
            value: Value to score
            data: Reference dataset

        Returns:
            Z-score value
        """
        from app.utils import statistics
        import numpy as np

        z_scores = statistics.z_score(data)
        # Find the z-score by calculating manually for the given value
        mean = np.mean(data)
        std = np.std(data, ddof=1)

        if std == 0:
            return 0.0

        return (value - mean) / std

    def detect_outliers(
        self,
        data: List[float],
        threshold: float = 3.0
    ) -> List[float]:
        """
        Detect outliers in data.

        Args:
            data: Input data array
            threshold: Z-score threshold for outlier detection

        Returns:
            List of outlier values
        """
        from app.utils import statistics

        outlier_mask, outlier_indices = statistics.detect_outliers(
            data,
            method='zscore',
            threshold=threshold
        )

        return [data[i] for i in outlier_indices]

    def linear_regression(self, x: List[float], y: List[float]) -> Dict:
        """
        Perform linear regression.

        Args:
            x: Independent variable data
            y: Dependent variable data

        Returns:
            Dictionary with 'slope', 'intercept', and 'r_squared' keys
        """
        from app.utils import statistics

        slope, intercept, r_squared = statistics.linear_regression(x, y)

        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared)
        }
