"""
Performance tests for database queries and operations.

Tests ensure:
- Query performance <100ms
- Bulk insert performance <5s for 90 days
- Data processing <1s for 90 days
- Memory usage within acceptable limits
"""

import pytest
import time
from datetime import date, timedelta
from memory_profiler import memory_usage
import psutil


@pytest.mark.performance
@pytest.mark.slow
class TestQueryPerformance:
    """Test database query performance."""

    def test_single_day_query_under_100ms(self, db_session, populated_user_data):
        """Test single day query completes in <100ms."""
        from app.services import data_access
        user_id = populated_user_data['user_id']

        start = time.perf_counter()
        metrics = data_access.get_daily_metrics(db_session, user_id, date.today())
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100, f"Query took {elapsed:.2f}ms (should be <100ms)"
        assert metrics is not None

    def test_date_range_query_7_days_under_150ms(self, db_session, populated_user_data):
        """Test 7-day range query completes in <150ms."""
        from app.services import data_access
        user_id = populated_user_data['user_id']

        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        start = time.perf_counter()
        metrics_list = data_access.get_metrics_range(db_session, user_id, start_date, end_date)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 150, f"Range query took {elapsed:.2f}ms (should be <150ms)"
        assert len(metrics_list) > 0

    def test_date_range_query_30_days_under_300ms(self, db_session, populated_user_data):
        """Test 30-day range query completes in <300ms."""
        from app.services import data_access
        user_id = populated_user_data['user_id']

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        start = time.perf_counter()
        metrics_list = data_access.get_metrics_range(db_session, user_id, start_date, end_date)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 300, f"Range query took {elapsed:.2f}ms (should be <300ms)"

    def test_activity_query_by_user_under_200ms(self, db_session, populated_user_data):
        """Test activity query completes in <200ms."""
        from app.services import data_access
        user_id = populated_user_data['user_id']

        start = time.perf_counter()
        activities = data_access.get_recent_activities(db_session, user_id, limit=30)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 200, f"Activity query took {elapsed:.2f}ms (should be <200ms)"


@pytest.mark.performance
@pytest.mark.slow
class TestBulkOperationPerformance:
    """Test bulk operation performance."""

    def test_bulk_insert_90_days_under_5_seconds(self, db_session, sample_user):
        """Test bulk inserting 90 days of data completes in <5s."""
        from app.services import data_access

        # Prepare 90 days of data
        metrics_list = [
            {
                'user_id': sample_user.user_id,
                'date': date.today() - timedelta(days=i),
                'steps': 10000 + i * 100,
                'calories': 2000 + i * 50,
                'hrv_sdnn': 65.0 + (i % 10)
            }
            for i in range(90)
        ]

        start = time.perf_counter()
        result = data_access.bulk_insert_daily_metrics(db_session, metrics_list)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Bulk insert took {elapsed:.2f}s (should be <5s)"
        assert result == 90

    def test_bulk_update_performance(self, db_session, populated_user_data):
        """Test bulk update performance."""
        from app.services import data_access
        user_id = populated_user_data['user_id']

        # Get all metrics
        metrics_list = data_access.get_metrics_range(
            db_session,
            user_id,
            date.today() - timedelta(days=89),
            date.today()
        )

        # Prepare updates
        updates = [
            {'id': m.id, 'steps': m.steps + 1000}
            for m in metrics_list
        ]

        start = time.perf_counter()
        data_access.bulk_update_daily_metrics(db_session, updates)
        elapsed = time.perf_counter() - start

        assert elapsed < 3.0, f"Bulk update took {elapsed:.2f}s (should be <3s)"


@pytest.mark.performance
@pytest.mark.slow
class TestDataProcessingPerformance:
    """Test data processing performance."""

    def test_hrv_baseline_calculation_under_100ms(self, db_session, populated_user_data):
        """Test HRV baseline calculation completes in <100ms."""
        from app.services.data_processor import DataProcessor
        processor = DataProcessor(db_session)
        user_id = populated_user_data['user_id']

        start = time.perf_counter()
        baseline = processor.calculate_hrv_baseline_from_db(user_id, days=30)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100, f"HRV calculation took {elapsed:.2f}ms (should be <100ms)"
        assert baseline is not None

    def test_training_load_calculation_under_200ms(self, db_session, populated_user_data):
        """Test training load calculation completes in <200ms."""
        from app.services.data_processor import DataProcessor
        processor = DataProcessor(db_session)
        user_id = populated_user_data['user_id']

        start = time.perf_counter()
        load = processor.calculate_training_load_from_db(user_id, days=30)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 200, f"Training load calculation took {elapsed:.2f}ms (should be <200ms)"

    def test_complete_processing_90_days_under_1_second(self, db_session, populated_user_data):
        """Test processing 90 days of data completes in <1s."""
        from app.services.data_processor import DataProcessor
        processor = DataProcessor(db_session)
        user_id = populated_user_data['user_id']

        start = time.perf_counter()

        # Calculate multiple metrics
        hrv_7d = processor.calculate_hrv_baseline_from_db(user_id, days=7)
        hrv_30d = processor.calculate_hrv_baseline_from_db(user_id, days=30)
        training_load = processor.calculate_training_load_from_db(user_id, days=30)
        fitness_fatigue = processor.calculate_fitness_fatigue_from_db(user_id, days=90)

        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Complete processing took {elapsed:.2f}s (should be <1s)"


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage during operations."""

    def test_bulk_insert_memory_reasonable(self, db_session, sample_user):
        """Test bulk insert doesn't consume excessive memory."""
        from app.services import data_access

        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Insert 90 days
        metrics_list = [
            {
                'user_id': sample_user.user_id,
                'date': date.today() - timedelta(days=i),
                'steps': 10000 + i * 100
            }
            for i in range(90)
        ]

        data_access.bulk_insert_daily_metrics(db_session, metrics_list)

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before

        # Should not increase by more than 50MB
        assert mem_increase < 50, f"Memory increased by {mem_increase:.2f}MB (should be <50MB)"

    def test_processing_memory_efficient(self, db_session, populated_user_data):
        """Test data processing is memory efficient."""
        from app.services.data_processor import DataProcessor
        processor = DataProcessor(db_session)
        user_id = populated_user_data['user_id']

        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024

        # Process data
        for _ in range(10):
            processor.calculate_hrv_baseline_from_db(user_id, days=30)
            processor.calculate_training_load_from_db(user_id, days=30)

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # Should not leak memory
        assert mem_increase < 30, f"Memory increased by {mem_increase:.2f}MB (possible leak)"


@pytest.mark.performance
class TestConcurrentOperations:
    """Test concurrent operation performance."""

    def test_concurrent_queries_no_blocking(self, db_session, populated_user_data):
        """Test concurrent queries don't block each other."""
        from app.services import data_access
        import threading

        user_id = populated_user_data['user_id']

        results = []
        errors = []

        def query_worker():
            try:
                start = time.perf_counter()
                metrics = data_access.get_daily_metrics(db_session, user_id, date.today())
                elapsed = time.perf_counter() - start
                results.append(elapsed)
            except Exception as e:
                errors.append(str(e))

        # Run 10 concurrent queries
        threads = [threading.Thread(target=query_worker) for _ in range(10)]

        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        # Concurrent execution should be faster than sequential
        assert elapsed < sum(results), "Queries appear to be blocking"


# Fixtures
@pytest.fixture
def populated_user_data(db_session):
    """Create user with 90 days of data for performance testing."""
    from app.services import data_access
    from app.models.database_models import UserProfile

    # Create user
    user = UserProfile(
        user_id='perf_test_user',
        email='perf@test.com',
        name='Performance Test User'
    )
    db_session.add(user)
    db_session.commit()

    # Bulk insert 90 days
    metrics_list = []
    for i in range(90):
        metrics_list.append({
            'user_id': user.user_id,
            'date': date.today() - timedelta(days=i),
            'steps': 10000 + i * 100,
            'calories': 2000 + i * 50,
            'hrv_sdnn': 65.0 + (i % 10),
            'resting_heart_rate': 55 + (i % 5)
        })

    data_access.bulk_insert_daily_metrics(db_session, metrics_list)

    # Add training load data
    metrics = data_access.get_metrics_range(
        db_session,
        user.user_id,
        date.today() - timedelta(days=89),
        date.today()
    )

    for metrics_obj in metrics:
        data_access.create_training_load_tracking(
            db_session,
            {
                'user_id': user.user_id,
                'daily_metric_id': metrics_obj.id,
                'tracking_date': metrics_obj.date,
                'daily_training_load': 100 + (metrics_obj.date.day % 20)
            }
        )

    return {'user_id': user.user_id}
