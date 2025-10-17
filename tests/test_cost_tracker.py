"""
Tests for Cost Tracker service.

This module tests the CostTracker service which handles:
- Token usage tracking
- Cost calculation based on Claude pricing
- Per-user cost aggregation
- Monthly budget tracking
- Cost alerts and warnings
- Historical cost analysis
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.cost_tracker import (
    CostTracker,
    APICallCost,
    PRICING,
    get_cost_tracker
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    return session


@pytest.fixture
def cost_tracker(mock_db_session):
    """Create a CostTracker instance with mock database."""
    return CostTracker(
        db_session=mock_db_session,
        monthly_budget_per_user=15.00
    )


class TestCostCalculation:
    """Test cost calculation logic."""

    def test_calculate_call_cost_input_only(self, cost_tracker):
        """Test cost calculation for input tokens only."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=1_000_000,
            output_tokens=0
        )

        assert result['input_cost'] == 3.00  # $3 per million input tokens
        assert result['output_cost'] == 0.00
        assert result['cache_write_cost'] == 0.00
        assert result['cache_read_cost'] == 0.00
        assert result['total_cost'] == 3.00

    def test_calculate_call_cost_output_only(self, cost_tracker):
        """Test cost calculation for output tokens only."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=0,
            output_tokens=1_000_000
        )

        assert result['output_cost'] == 15.00  # $15 per million output tokens
        assert result['total_cost'] == 15.00

    def test_calculate_call_cost_with_cache_writes(self, cost_tracker):
        """Test cost calculation including cache writes."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=0,
            output_tokens=0,
            cache_write_tokens=1_000_000
        )

        assert result['cache_write_cost'] == 3.75  # $3.75 per million cache write tokens
        assert result['total_cost'] == 3.75

    def test_calculate_call_cost_with_cache_reads(self, cost_tracker):
        """Test cost calculation including cache reads."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=1_000_000
        )

        assert result['cache_read_cost'] == 0.30  # $0.30 per million cache read tokens
        assert result['total_cost'] == 0.30

    def test_calculate_call_cost_combined(self, cost_tracker):
        """Test cost calculation with all token types."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=500_000,
            output_tokens=100_000,
            cache_write_tokens=200_000,
            cache_read_tokens=1_000_000
        )

        expected_input = 0.5 * 3.00  # 1.50
        expected_output = 0.1 * 15.00  # 1.50
        expected_cache_write = 0.2 * 3.75  # 0.75
        expected_cache_read = 1.0 * 0.30  # 0.30
        expected_total = expected_input + expected_output + expected_cache_write + expected_cache_read

        assert result['input_cost'] == pytest.approx(1.50)
        assert result['output_cost'] == pytest.approx(1.50)
        assert result['cache_write_cost'] == pytest.approx(0.75)
        assert result['cache_read_cost'] == pytest.approx(0.30)
        assert result['total_cost'] == pytest.approx(expected_total)

    def test_calculate_call_cost_small_values(self, cost_tracker):
        """Test cost calculation with small token counts."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=1000,  # 0.001 million tokens
            output_tokens=500
        )

        expected_input = 0.001 * 3.00  # 0.003
        expected_output = 0.0005 * 15.00  # 0.0075
        expected_total = expected_input + expected_output

        assert result['total_cost'] == pytest.approx(expected_total, abs=1e-6)

    def test_calculate_call_cost_rounding(self, cost_tracker):
        """Test that costs are rounded to 6 decimal places."""
        result = cost_tracker.calculate_call_cost(
            input_tokens=1,
            output_tokens=1
        )

        # Very small values should still be rounded properly
        assert isinstance(result['total_cost'], float)
        assert len(str(result['total_cost']).split('.')[-1]) <= 6


class TestAPICallRecording:
    """Test recording of API calls."""

    @patch('app.services.cost_tracker.uuid.uuid4')
    def test_record_api_call_creates_cost_record(self, mock_uuid, cost_tracker, mock_db_session):
        """Test that recording an API call creates a database record."""
        mock_uuid.return_value = "test-call-id"

        result = cost_tracker.record_api_call(
            user_id="user-123",
            model="claude-3-5-sonnet-20241022",
            input_tokens=10000,
            output_tokens=5000
        )

        # Should have called db.add() and db.commit()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Should return APICallCost object
        assert isinstance(result, APICallCost)
        assert result.user_id == "user-123"
        assert result.model == "claude-3-5-sonnet-20241022"
        assert result.input_tokens == 10000
        assert result.output_tokens == 5000

    def test_record_api_call_includes_metadata(self, cost_tracker, mock_db_session):
        """Test that metadata is stored with the API call."""
        metadata = {
            "operation": "readiness_analysis",
            "endpoint": "/api/v1/analyze"
        }

        cost_tracker.record_api_call(
            user_id="user-123",
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000,
            output_tokens=500,
            metadata=metadata
        )

        # Check that metadata was passed to CostTracking model
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.call_metadata == metadata

    def test_record_api_call_calculates_costs(self, cost_tracker, mock_db_session):
        """Test that API call recording calculates costs correctly."""
        result = cost_tracker.record_api_call(
            user_id="user-123",
            model="claude-3-5-sonnet-20241022",
            input_tokens=1_000_000,
            output_tokens=500_000
        )

        assert result.input_cost == 3.00
        assert result.output_cost == 7.50
        assert result.total_cost == 10.50


class TestUserCostQueries:
    """Test querying user costs."""

    def test_get_user_cost_today(self, cost_tracker, mock_db_session):
        """Test getting user's cost for today."""
        # Mock database results
        mock_record = MagicMock()
        mock_record.total_cost = 2.50
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_record]

        result = cost_tracker.get_user_cost_today("user-123")

        assert result == 2.50

    def test_get_user_cost_today_multiple_calls(self, cost_tracker, mock_db_session):
        """Test aggregating multiple calls for today."""
        mock_records = [
            MagicMock(total_cost=1.25),
            MagicMock(total_cost=0.75),
            MagicMock(total_cost=0.50)
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        result = cost_tracker.get_user_cost_today("user-123")

        assert result == 2.50

    def test_get_user_cost_today_no_calls(self, cost_tracker, mock_db_session):
        """Test getting cost when user has no calls today."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        result = cost_tracker.get_user_cost_today("user-123")

        assert result == 0.0

    def test_get_user_cost_month_current(self, cost_tracker, mock_db_session):
        """Test getting user's cost for current month."""
        mock_records = [MagicMock(total_cost=5.00)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        result = cost_tracker.get_user_cost_month("user-123")

        assert result == 5.00

    def test_get_user_cost_month_specific(self, cost_tracker, mock_db_session):
        """Test getting user's cost for specific month."""
        mock_records = [MagicMock(total_cost=3.50)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        result = cost_tracker.get_user_cost_month("user-123", year=2024, month=9)

        assert result == 3.50


class TestBudgetTracking:
    """Test budget tracking and alerts."""

    def test_get_user_remaining_budget(self, cost_tracker, mock_db_session):
        """Test calculating remaining budget."""
        mock_records = [MagicMock(total_cost=7.50)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        result = cost_tracker.get_user_remaining_budget("user-123")

        assert result['monthly_budget'] == 15.00
        assert result['spent_this_month'] == 7.50
        assert result['remaining'] == 7.50
        assert result['percent_used'] == 50.0
        assert result['over_budget'] is False

    def test_get_user_remaining_budget_over_budget(self, cost_tracker, mock_db_session):
        """Test budget info when user is over budget."""
        mock_records = [MagicMock(total_cost=20.00)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        result = cost_tracker.get_user_remaining_budget("user-123")

        assert result['over_budget'] is True
        assert result['remaining'] < 0

    def test_check_budget_alert_no_alert(self, cost_tracker, mock_db_session):
        """Test budget alert when usage is low."""
        mock_records = [MagicMock(total_cost=5.00)]  # 33% usage
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        alert = cost_tracker.check_budget_alert("user-123")

        assert alert is None

    def test_check_budget_alert_75_percent(self, cost_tracker, mock_db_session):
        """Test budget alert at 75% usage."""
        mock_records = [MagicMock(total_cost=11.25)]  # 75% usage
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        alert = cost_tracker.check_budget_alert("user-123")

        assert alert is not None
        assert "NOTICE" in alert
        assert "75" in alert

    def test_check_budget_alert_90_percent(self, cost_tracker, mock_db_session):
        """Test budget alert at 90% usage."""
        mock_records = [MagicMock(total_cost=13.50)]  # 90% usage
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        alert = cost_tracker.check_budget_alert("user-123")

        assert alert is not None
        assert "WARNING" in alert
        assert "90" in alert

    def test_check_budget_alert_over_budget(self, cost_tracker, mock_db_session):
        """Test budget alert when over budget."""
        mock_records = [MagicMock(total_cost=20.00)]  # Over budget
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

        alert = cost_tracker.check_budget_alert("user-123")

        assert alert is not None
        assert "OVER BUDGET" in alert


class TestCostHistory:
    """Test cost history and statistics."""

    def test_get_call_history(self, cost_tracker, mock_db_session):
        """Test retrieving call history."""
        mock_record = MagicMock()
        mock_record.call_id = "call-123"
        mock_record.call_date = date.today()
        mock_record.model = "claude-3-5-sonnet-20241022"
        mock_record.input_tokens = 1000
        mock_record.output_tokens = 500
        mock_record.total_cost = 0.025
        mock_record.created_at = datetime.now()

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_record]

        history = cost_tracker.get_call_history("user-123", days=7)

        assert len(history) == 1
        assert history[0]['call_id'] == "call-123"
        assert history[0]['total_tokens'] == 1500

    def test_get_cost_statistics(self, cost_tracker, mock_db_session):
        """Test getting comprehensive cost statistics."""
        # Mock today's cost
        with patch.object(cost_tracker, 'get_user_cost_today', return_value=2.50):
            # Mock month's cost
            with patch.object(cost_tracker, 'get_user_cost_month', return_value=10.00):
                # Mock this month's calls
                mock_records = [
                    MagicMock(input_tokens=1000, output_tokens=500),
                    MagicMock(input_tokens=2000, output_tokens=1000)
                ]
                mock_db_session.query.return_value.filter.return_value.all.return_value = mock_records

                stats = cost_tracker.get_cost_statistics("user-123")

                assert stats['user_id'] == "user-123"
                assert stats['today_cost'] == 2.50
                assert stats['month_cost'] == 10.00
                assert stats['total_calls_this_month'] == 2
                assert stats['total_tokens_this_month'] == 4500

    def test_get_daily_costs(self, cost_tracker, mock_db_session):
        """Test getting daily cost breakdown."""
        # Mock database aggregation results
        mock_result = MagicMock()
        mock_result.call_date = date.today()
        mock_result.total_cost = 5.00
        mock_result.call_count = 10
        mock_result.total_tokens = 50000

        mock_db_session.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_result]

        daily_costs = cost_tracker.get_daily_costs("user-123", days=30)

        assert len(daily_costs) == 1
        assert daily_costs[0]['total_cost'] == 5.00
        assert daily_costs[0]['call_count'] == 10


class TestCostTrackerFactory:
    """Test the factory function."""

    def test_get_cost_tracker_returns_instance(self, mock_db_session):
        """Test that factory function returns CostTracker instance."""
        tracker = get_cost_tracker(mock_db_session)

        assert isinstance(tracker, CostTracker)
        assert tracker.db == mock_db_session


class TestPricingConstants:
    """Test pricing configuration."""

    def test_pricing_constants_defined(self):
        """Test that all pricing constants are defined."""
        assert 'input_per_mtok' in PRICING
        assert 'output_per_mtok' in PRICING
        assert 'cache_write_per_mtok' in PRICING
        assert 'cache_read_per_mtok' in PRICING

    def test_pricing_values_reasonable(self):
        """Test that pricing values are in reasonable ranges."""
        assert PRICING['input_per_mtok'] > 0
        assert PRICING['output_per_mtok'] > PRICING['input_per_mtok']  # Output should be more expensive
        assert PRICING['cache_write_per_mtok'] > PRICING['cache_read_per_mtok']  # Writes more expensive than reads


# ============================================================================
# Integration Tests
# ============================================================================

class TestCostTrackerIntegration:
    """Integration tests with real database."""

    @pytest.mark.integration
    def test_full_workflow_with_database(self, db_session):
        """Test complete workflow with real database."""
        # TODO: Implement with real database session
        pass

    @pytest.mark.integration
    def test_concurrent_cost_tracking(self, db_session):
        """Test that concurrent cost tracking works correctly."""
        # TODO: Implement concurrency test
        pass


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_calculate_cost_zero_tokens(self, cost_tracker):
        """Test cost calculation with zero tokens."""
        result = cost_tracker.calculate_call_cost(0, 0, 0, 0)

        assert result['total_cost'] == 0.0

    def test_calculate_cost_negative_tokens_not_allowed(self, cost_tracker):
        """Test that negative tokens are handled."""
        # Should either raise error or treat as zero
        # Implementation depends on business rules
        pass

    def test_budget_with_zero_monthly_budget(self, mock_db_session):
        """Test budget tracking with zero budget."""
        tracker = CostTracker(mock_db_session, monthly_budget_per_user=0.0)
        # Should handle division by zero
        pass

    def test_cost_aggregation_across_month_boundary(self, cost_tracker, mock_db_session):
        """Test that costs are properly separated by month."""
        # TODO: Implement test for month boundaries
        pass


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.performance
    def test_cost_calculation_performance(self, cost_tracker):
        """Test that cost calculations are fast."""
        import time

        start = time.time()
        for _ in range(10000):
            cost_tracker.calculate_call_cost(1000, 500, 200, 1000)
        elapsed = time.time() - start

        # Should be very fast - less than 1 second for 10k calculations
        assert elapsed < 1.0

    @pytest.mark.performance
    def test_bulk_query_performance(self, cost_tracker, mock_db_session):
        """Test performance of querying large datasets."""
        # TODO: Implement with large mock datasets
        pass


"""
TODO: Additional test cases to implement:

1. Multi-user scenarios:
   - test_cost_isolation_between_users()
   - test_aggregate_costs_across_users()

2. Date range queries:
   - test_cost_by_week()
   - test_cost_by_quarter()
   - test_cost_year_to_date()

3. Advanced statistics:
   - test_cost_trends_over_time()
   - test_peak_usage_detection()
   - test_cost_forecasting()

4. Alert customization:
   - test_custom_alert_thresholds()
   - test_multiple_alert_levels()

5. Data export:
   - test_export_cost_report_csv()
   - test_export_cost_report_json()
"""
