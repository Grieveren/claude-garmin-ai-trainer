"""
Cost Tracker - Monitor and track AI API costs.

This service provides:
- Token usage tracking per API call
- Cost calculation based on Claude pricing
- Per-user cost aggregation
- Monthly budget tracking
- Cost alerts and warnings
- Persistence for historical analysis

Pricing (as of 2025-10):
- Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
- Cache writes: $3.75/MTok
- Cache reads: $0.30/MTok
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Claude 3.5 Sonnet pricing (per million tokens)
PRICING = {
    'input_per_mtok': 3.00,  # $3 per million input tokens
    'output_per_mtok': 15.00,  # $15 per million output tokens
    'cache_write_per_mtok': 3.75,  # $3.75 per million cache write tokens
    'cache_read_per_mtok': 0.30,  # $0.30 per million cache read tokens
}


@dataclass
class APICallCost:
    """
    Represents the cost of a single API call.

    Attributes:
        call_id: Unique identifier for this call
        user_id: User who made the call
        model: Model used (e.g., "claude-3-5-sonnet-20241022")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cache_write_tokens: Tokens written to cache
        cache_read_tokens: Tokens read from cache
        input_cost: Cost of input tokens ($)
        output_cost: Cost of output tokens ($)
        cache_write_cost: Cost of cache writes ($)
        cache_read_cost: Cost of cache reads ($)
        total_cost: Total cost for this call ($)
        timestamp: When the call was made
    """
    call_id: str
    user_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    input_cost: float
    output_cost: float
    cache_write_cost: float
    cache_read_cost: float
    total_cost: float
    timestamp: datetime


class CostTracker:
    """
    Track and analyze AI API costs.

    Provides:
    - Per-call cost tracking
    - User-level cost aggregation
    - Budget monitoring
    - Cost alerts
    - Historical analysis
    """

    def __init__(
        self,
        db_session: Session,
        monthly_budget_per_user: Optional[float] = None
    ):
        """
        Initialize cost tracker.

        Args:
            db_session: Database session for persistence
            monthly_budget_per_user: Monthly budget limit per user (optional)
        """
        self.db = db_session
        self.monthly_budget_per_user = monthly_budget_per_user or 15.00  # $15/month default

        logger.info(
            f"CostTracker initialized (monthly budget per user: ${self.monthly_budget_per_user})"
        )

    def calculate_call_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0
    ) -> Dict[str, float]:
        """
        Calculate cost for an API call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_write_tokens: Number of cache write tokens
            cache_read_tokens: Number of cache read tokens

        Returns:
            Dictionary with cost breakdown
        """
        # Convert to millions of tokens
        input_mtok = input_tokens / 1_000_000
        output_mtok = output_tokens / 1_000_000
        cache_write_mtok = cache_write_tokens / 1_000_000
        cache_read_mtok = cache_read_tokens / 1_000_000

        # Calculate costs
        input_cost = input_mtok * PRICING['input_per_mtok']
        output_cost = output_mtok * PRICING['output_per_mtok']
        cache_write_cost = cache_write_mtok * PRICING['cache_write_per_mtok']
        cache_read_cost = cache_read_mtok * PRICING['cache_read_per_mtok']

        total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost

        return {
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'cache_write_cost': round(cache_write_cost, 6),
            'cache_read_cost': round(cache_read_cost, 6),
            'total_cost': round(total_cost, 6)
        }

    def record_api_call(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> APICallCost:
        """
        Record an API call and its cost.

        Args:
            user_id: User who made the call
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_write_tokens: Cache write tokens
            cache_read_tokens: Cache read tokens
            metadata: Optional metadata (operation type, etc.)

        Returns:
            APICallCost object
        """
        from app.models.database_models import CostTracking
        import uuid

        # Calculate costs
        costs = self.calculate_call_cost(
            input_tokens,
            output_tokens,
            cache_write_tokens,
            cache_read_tokens
        )

        call_id = str(uuid.uuid4())

        # Create API call cost object
        api_call_cost = APICallCost(
            call_id=call_id,
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_write_tokens=cache_write_tokens,
            cache_read_tokens=cache_read_tokens,
            input_cost=costs['input_cost'],
            output_cost=costs['output_cost'],
            cache_write_cost=costs['cache_write_cost'],
            cache_read_cost=costs['cache_read_cost'],
            total_cost=costs['total_cost'],
            timestamp=datetime.now()
        )

        # Persist to database
        cost_record = CostTracking(
            call_id=call_id,
            user_id=user_id,
            call_date=date.today(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_write_tokens=cache_write_tokens,
            cache_read_tokens=cache_read_tokens,
            input_cost=costs['input_cost'],
            output_cost=costs['output_cost'],
            cache_write_cost=costs['cache_write_cost'],
            cache_read_cost=costs['cache_read_cost'],
            total_cost=costs['total_cost'],
            call_metadata=metadata or {}
        )

        self.db.add(cost_record)
        self.db.commit()

        logger.info(
            f"Recorded API call for {user_id}: "
            f"{input_tokens + output_tokens} tokens, ${costs['total_cost']:.4f}"
        )

        return api_call_cost

    def get_user_cost_today(self, user_id: str) -> float:
        """
        Get total cost for a user today.

        Args:
            user_id: User identifier

        Returns:
            Total cost today in dollars
        """
        from app.models.database_models import CostTracking

        today = date.today()

        result = self.db.query(CostTracking).filter(
            CostTracking.user_id == user_id,
            CostTracking.call_date == today
        ).all()

        total = sum(record.total_cost for record in result)

        return round(total, 4)

    def get_user_cost_month(
        self,
        user_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> float:
        """
        Get total cost for a user in a specific month.

        Args:
            user_id: User identifier
            year: Year (defaults to current year)
            month: Month (defaults to current month)

        Returns:
            Total cost for the month in dollars
        """
        from app.models.database_models import CostTracking
        from sqlalchemy import extract

        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month

        result = self.db.query(CostTracking).filter(
            CostTracking.user_id == user_id,
            extract('year', CostTracking.call_date) == year,
            extract('month', CostTracking.call_date) == month
        ).all()

        total = sum(record.total_cost for record in result)

        return round(total, 4)

    def get_user_remaining_budget(self, user_id: str) -> Dict[str, Any]:
        """
        Get remaining budget for a user this month.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with budget information
        """
        month_cost = self.get_user_cost_month(user_id)
        remaining = self.monthly_budget_per_user - month_cost
        percent_used = (month_cost / self.monthly_budget_per_user) * 100

        return {
            'monthly_budget': self.monthly_budget_per_user,
            'spent_this_month': round(month_cost, 4),
            'remaining': round(remaining, 4),
            'percent_used': round(percent_used, 2),
            'over_budget': month_cost > self.monthly_budget_per_user
        }

    def check_budget_alert(self, user_id: str) -> Optional[str]:
        """
        Check if user should receive a budget alert.

        Args:
            user_id: User identifier

        Returns:
            Alert message if applicable, None otherwise
        """
        budget_info = self.get_user_remaining_budget(user_id)

        if budget_info['over_budget']:
            return (
                f"OVER BUDGET: User {user_id} has exceeded monthly budget "
                f"(${budget_info['spent_this_month']:.2f} / ${budget_info['monthly_budget']:.2f})"
            )

        if budget_info['percent_used'] >= 90:
            return (
                f"WARNING: User {user_id} has used {budget_info['percent_used']:.1f}% "
                f"of monthly budget"
            )

        if budget_info['percent_used'] >= 75:
            return (
                f"NOTICE: User {user_id} has used {budget_info['percent_used']:.1f}% "
                f"of monthly budget"
            )

        return None

    def get_call_history(
        self,
        user_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get API call history for a user.

        Args:
            user_id: User identifier
            days: Number of days to look back

        Returns:
            List of API call records
        """
        from app.models.database_models import CostTracking

        start_date = date.today() - timedelta(days=days)

        records = self.db.query(CostTracking).filter(
            CostTracking.user_id == user_id,
            CostTracking.call_date >= start_date
        ).order_by(CostTracking.created_at.desc()).all()

        return [
            {
                'call_id': r.call_id,
                'date': r.call_date.isoformat(),
                'model': r.model,
                'input_tokens': r.input_tokens,
                'output_tokens': r.output_tokens,
                'total_tokens': r.input_tokens + r.output_tokens,
                'total_cost': round(r.total_cost, 4),
                'timestamp': r.created_at.isoformat()
            }
            for r in records
        ]

    def get_cost_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive cost statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with cost statistics
        """
        today_cost = self.get_user_cost_today(user_id)
        month_cost = self.get_user_cost_month(user_id)
        budget_info = self.get_user_remaining_budget(user_id)

        # Get average cost per call
        from app.models.database_models import CostTracking

        this_month_calls = self.db.query(CostTracking).filter(
            CostTracking.user_id == user_id,
            CostTracking.call_date >= date.today().replace(day=1)
        ).all()

        total_calls = len(this_month_calls)
        avg_cost_per_call = (
            month_cost / total_calls if total_calls > 0 else 0.0
        )

        total_tokens = sum(
            r.input_tokens + r.output_tokens
            for r in this_month_calls
        )

        return {
            'user_id': user_id,
            'today_cost': round(today_cost, 4),
            'month_cost': round(month_cost, 4),
            'budget_info': budget_info,
            'total_calls_this_month': total_calls,
            'total_tokens_this_month': total_tokens,
            'avg_cost_per_call': round(avg_cost_per_call, 4),
            'avg_tokens_per_call': int(total_tokens / total_calls) if total_calls > 0 else 0
        }

    def get_daily_costs(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily cost breakdown for a user.

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            List of daily cost records
        """
        from app.models.database_models import CostTracking
        from sqlalchemy import func

        start_date = date.today() - timedelta(days=days)

        # Group by date and sum costs
        results = self.db.query(
            CostTracking.call_date,
            func.sum(CostTracking.total_cost).label('total_cost'),
            func.count(CostTracking.id).label('call_count'),
            func.sum(CostTracking.input_tokens + CostTracking.output_tokens).label('total_tokens')
        ).filter(
            CostTracking.user_id == user_id,
            CostTracking.call_date >= start_date
        ).group_by(
            CostTracking.call_date
        ).order_by(
            CostTracking.call_date
        ).all()

        return [
            {
                'date': r.call_date.isoformat(),
                'total_cost': round(r.total_cost, 4),
                'call_count': r.call_count,
                'total_tokens': int(r.total_tokens) if r.total_tokens else 0
            }
            for r in results
        ]


def get_cost_tracker(db_session: Session) -> CostTracker:
    """
    Factory function to create a cost tracker.

    Args:
        db_session: Database session

    Returns:
        CostTracker instance
    """
    return CostTracker(db_session)
