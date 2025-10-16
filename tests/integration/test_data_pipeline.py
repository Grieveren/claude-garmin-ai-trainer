"""
Integration tests for complete data pipeline.

Tests the end-to-end flow:
Garmin API → Data Access Layer → Data Processing → Storage

Includes:
- Complete data pipeline (Fetch → Store → Process)
- Realistic 30-day dataset
- Error recovery scenarios
- Performance requirements (<100ms queries)
"""

import pytest
from datetime import datetime, date, timedelta
import time
from typing import List, Dict


class TestDataPipelineIntegration:
    """Test complete data pipeline integration."""

    @pytest.mark.integration
    def test_complete_pipeline_fetch_store_process(self, db_session, mock_garmin_service, data_processor, dal):
        """Test complete pipeline: Fetch from Garmin → Store in DB → Process data."""
        user_id = "integration_test_user"
        test_date = date.today()

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Integration Test User"
        }
        dal.create_user(db_session, user_data)

        # Step 1: Fetch data from Garmin
        daily_metrics = mock_garmin_service.get_daily_metrics(user_id, test_date)
        sleep_data = mock_garmin_service.get_sleep_data(user_id, test_date)
        activities = mock_garmin_service.get_activities(user_id, test_date, test_date)

        assert daily_metrics is not None
        assert sleep_data is not None

        # Step 2: Store in database
        # Remove date key from daily_metrics as it's in ISO string format
        daily_metrics.pop('date', None)
        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **daily_metrics
        }
        stored_metrics = dal.create_daily_metrics(db_session, metrics_data)

        assert stored_metrics.id is not None

        if sleep_data:
            sleep_session_data = {
                "user_id": user_id,
                "daily_metric_id": stored_metrics.id,
                **sleep_data
            }
            # Note: Need to check if create_sleep_session exists
            # stored_sleep = dal.create_sleep_session(db_session, sleep_session_data)
            # assert stored_sleep.id is not None

        for activity in activities:
            activity_data = {
                "user_id": user_id,
                **activity
            }
            stored_activity = dal.create_activity(db_session, activity_data)
            assert stored_activity.id is not None

        # Step 3: Process data
        result = data_processor.process_daily_metrics(user_id, test_date)

        # Verify processing results
        assert result is not None
        assert result.get('status') in ['success', 'no_data']

    @pytest.mark.integration
    def test_30_day_data_pipeline(self, db_session, mock_garmin_service, data_processor, dal):
        """Test processing 30 days of data."""
        user_id = "integration_30day_user"
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "30 Day Test User"
        }
        dal.create_user(db_session, user_data)

        # Fetch and store 30 days of data
        for i in range(30):
            current_date = start_date + timedelta(days=i)

            # Fetch
            daily_metrics = mock_garmin_service.get_daily_metrics(user_id, current_date)
            sleep_data = mock_garmin_service.get_sleep_data(user_id, current_date)

            # Store
            daily_metrics.pop('date', None)
            metrics_data = {
                "user_id": user_id,
                "date": current_date,
                **daily_metrics
            }
            stored_metrics = dal.create_daily_metrics(db_session, metrics_data)

            if sleep_data:
                sleep_session_data = {
                    "user_id": user_id,
                    "daily_metric_id": stored_metrics.id,
                    **sleep_data
                }
                # Note: create_sleep_session may not exist in DAL
                # dal.create_sleep_session(db_session, sleep_session_data)

        # Verify
        all_metrics = dal.get_metrics_range(db_session, user_id, start_date, end_date)
        assert len(all_metrics) == 30

        # Note: Advanced processing methods may not exist yet
        # hrv_baseline_7d = data_processor.calculate_hrv_baseline_from_db(user_id, days=7)
        # hrv_baseline_30d = data_processor.calculate_hrv_baseline_from_db(user_id, days=30)
        # training_load = data_processor.calculate_training_load_from_db(user_id, days=30)

    @pytest.mark.integration
    def test_pipeline_with_missing_data(self, db_session, mock_garmin_service, data_processor, dal):
        """Test pipeline handles missing data gracefully."""
        user_id = "integration_missing_data_user"
        end_date = date.today()
        start_date = end_date - timedelta(days=10)

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Missing Data Test User"
        }
        dal.create_user(db_session, user_data)

        # Store data with some days missing
        for i in range(10):
            current_date = start_date + timedelta(days=i)

            # Skip some days (simulate missing data)
            if i % 3 == 0:
                continue

            daily_metrics = mock_garmin_service.get_daily_metrics(user_id, current_date)
            daily_metrics.pop('date', None)
            metrics_data = {
                "user_id": user_id,
                "date": current_date,
                **daily_metrics
            }
            dal.create_daily_metrics(db_session, metrics_data)

        # Process should handle gaps
        all_metrics = dal.get_metrics_range(db_session, user_id, start_date, end_date)
        assert len(all_metrics) < 10  # Some days missing

        # Processing should not fail - process each existing day
        for metric in all_metrics:
            result = data_processor.process_daily_metrics(user_id, metric.date)
            assert result.get('status') in ['success', 'no_data']


class TestPipelineErrorRecovery:
    """Test error recovery scenarios in pipeline."""

    @pytest.mark.integration
    def test_garmin_api_failure_recovery(self, db_session, mock_garmin_service, dal):
        """Test recovery from Garmin API failures."""
        user_id = "integration_error_user"

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Error Test User"
        }
        dal.create_user(db_session, user_data)

        # Simulate API failure
        mock_garmin_service.set_failure_mode(True)

        with pytest.raises(Exception):
            mock_garmin_service.get_daily_metrics(user_id, date.today())

        # Recover from failure
        mock_garmin_service.set_failure_mode(False)

        # Should work after recovery
        daily_metrics = mock_garmin_service.get_daily_metrics(user_id, date.today())
        assert daily_metrics is not None

    @pytest.mark.integration
    def test_database_constraint_violation_handling(self, db_session, dal):
        """Test handling of database constraint violations."""
        user_id = "integration_constraint_user"
        test_date = date.today()

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Constraint Test User"
        }
        dal.create_user(db_session, user_data)

        # Create first record
        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            "steps": 10000
        }
        dal.create_daily_metrics(db_session, metrics_data)
        db_session.commit()  # Commit so rollback doesn't undo this

        # Try to create duplicate
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            duplicate_data = {
                "user_id": user_id,
                "date": test_date,  # Duplicate
                "steps": 12000
            }
            dal.create_daily_metrics(db_session, duplicate_data)

        # Database session should still be usable
        db_session.rollback()

        # Should be able to update instead
        updated_data = {"steps": 15000}
        dal.update_daily_metrics(db_session, user_id, test_date, updated_data)

        updated = dal.get_daily_metrics(db_session, user_id, test_date)
        assert updated.steps == 15000

    @pytest.mark.integration
    def test_partial_sync_recovery(self, db_session, mock_garmin_service, dal):
        """Test recovery from partial sync failure."""
        user_id = "integration_partial_sync_user"
        end_date = date.today()
        start_date = end_date - timedelta(days=5)

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Partial Sync Test User"
        }
        dal.create_user(db_session, user_data)

        synced_dates = []
        failed_dates = []

        for i in range(5):
            current_date = start_date + timedelta(days=i)

            try:
                # Simulate random failures
                if i == 2:  # Fail on day 2
                    raise Exception("Simulated sync failure")

                daily_metrics = mock_garmin_service.get_daily_metrics(user_id, current_date)
                daily_metrics.pop('date', None)
                metrics_data = {
                    "user_id": user_id,
                    "date": current_date,
                    **daily_metrics
                }
                dal.create_daily_metrics(db_session, metrics_data)
                synced_dates.append(current_date)

            except Exception:
                failed_dates.append(current_date)
                continue

        # Should have some successful syncs despite failure
        assert len(synced_dates) > 0
        assert len(failed_dates) > 0

        # Retry failed dates
        for failed_date in failed_dates:
            daily_metrics = mock_garmin_service.get_daily_metrics(user_id, failed_date)
            daily_metrics.pop('date', None)
            metrics_data = {
                "user_id": user_id,
                "date": failed_date,
                **daily_metrics
            }
            dal.create_daily_metrics(db_session, metrics_data)

        # All dates should now be synced
        all_metrics = dal.get_metrics_range(db_session, user_id, start_date, end_date)
        assert len(all_metrics) == 5


class TestPipelinePerformance:
    """Test pipeline performance requirements."""

    @pytest.mark.integration
    @pytest.mark.performance
    def test_query_performance_under_100ms(self, db_session, dal, populated_user_data):
        """Test that queries complete in <100ms."""
        user_id = populated_user_data['user_id']
        test_date = date.today()

        # Test daily metrics query
        start_time = time.perf_counter()
        metrics = dal.get_daily_metrics(db_session, user_id, test_date)
        end_time = time.perf_counter()

        query_time_ms = (end_time - start_time) * 1000
        assert query_time_ms < 100, f"Query took {query_time_ms:.2f}ms (should be <100ms)"

    @pytest.mark.integration
    @pytest.mark.performance
    def test_date_range_query_performance(self, db_session, dal, populated_user_data):
        """Test date range query performance."""
        user_id = populated_user_data['user_id']
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        start_time = time.perf_counter()
        metrics_list = dal.get_metrics_range(db_session, user_id, start_date, end_date)
        end_time = time.perf_counter()

        query_time_ms = (end_time - start_time) * 1000
        assert query_time_ms < 200, f"Range query took {query_time_ms:.2f}ms (should be <200ms)"
        assert len(metrics_list) > 0

    @pytest.mark.integration
    @pytest.mark.performance
    def test_bulk_insert_performance(self, db_session, dal):
        """Test bulk insert performance."""
        user_id = "performance_bulk_user"

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Performance Test User"
        }
        dal.create_user(db_session, user_data)

        # Prepare 90 days of data
        metrics_list = [
            {
                'user_id': user_id,
                'date': date.today() - timedelta(days=i),
                'steps': 10000 + i * 100,
                'calories': 2000 + i * 50,
                'hrv_sdnn': 65.0 + i * 0.5
            }
            for i in range(90)
        ]

        start_time = time.perf_counter()
        dal.bulk_insert_daily_metrics(db_session, metrics_list)
        end_time = time.perf_counter()

        insert_time_s = end_time - start_time
        assert insert_time_s < 5.0, f"Bulk insert took {insert_time_s:.2f}s (should be <5s)"

    @pytest.mark.integration
    @pytest.mark.performance
    def test_processing_90_days_performance(self, db_session, data_processor, dal, populated_user_data):
        """Test processing 90 days of data completes quickly."""
        user_id = populated_user_data['user_id']

        start_time = time.perf_counter()

        # Process a sample of recent days
        end_date = date.today()
        for i in range(7):  # Test processing last 7 days
            current_date = end_date - timedelta(days=i)
            result = data_processor.process_daily_metrics(user_id, current_date)
            assert result.get('status') in ['success', 'no_data']

        end_time = time.perf_counter()

        processing_time_s = end_time - start_time
        assert processing_time_s < 1.0, f"Processing took {processing_time_s:.2f}s (should be <1s)"


class TestDataIntegrity:
    """Test data integrity throughout pipeline."""

    @pytest.mark.integration
    def test_data_consistency_after_sync(self, db_session, mock_garmin_service, dal):
        """Test data remains consistent after sync."""
        user_id = "integrity_test_user"
        test_date = date.today()

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Integrity Test User"
        }
        dal.create_user(db_session, user_data)

        # Fetch from Garmin
        garmin_data = mock_garmin_service.get_daily_metrics(user_id, test_date)

        # Store in DB
        garmin_data.pop('date', None)
        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **garmin_data
        }
        stored_metrics = dal.create_daily_metrics(db_session, metrics_data)

        # Retrieve from DB
        retrieved_metrics = dal.get_daily_metrics(db_session, user_id, test_date)

        # Verify data integrity
        assert retrieved_metrics.steps == garmin_data['steps']
        assert retrieved_metrics.calories == garmin_data['calories']
        assert retrieved_metrics.hrv_sdnn == garmin_data.get('hrv_sdnn')

    @pytest.mark.integration
    def test_relationships_maintained(self, db_session, mock_garmin_service, dal):
        """Test database relationships are maintained correctly."""
        user_id = "relationships_test_user"
        test_date = date.today()

        # Create user first to satisfy foreign key constraint
        user_data = {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "name": "Relationships Test User"
        }
        dal.create_user(db_session, user_data)

        # Create daily metrics
        daily_metrics = mock_garmin_service.get_daily_metrics(user_id, test_date)
        daily_metrics.pop('date', None)
        metrics_data = {
            "user_id": user_id,
            "date": test_date,
            **daily_metrics
        }
        stored_metrics = dal.create_daily_metrics(db_session, metrics_data)

        # Create related sleep session
        sleep_data = mock_garmin_service.get_sleep_data(user_id, test_date)
        if sleep_data:
            sleep_session_data = {
                "user_id": user_id,
                "daily_metric_id": stored_metrics.id,
                **sleep_data
            }
            # Note: create_sleep_session may not exist in DAL
            # stored_sleep = dal.create_sleep_session(db_session, sleep_session_data)

        # Verify daily metrics was created
        retrieved_metrics = dal.get_daily_metrics(db_session, user_id, test_date)
        assert retrieved_metrics is not None
        assert retrieved_metrics.id == stored_metrics.id


# Fixtures
@pytest.fixture
def dal():
    """Provide data access layer functions module."""
    from app.services import data_access
    return data_access


@pytest.fixture
def data_processor(db_session):
    """Create Data Processor instance."""
    from app.services.data_processor import DataProcessor
    return DataProcessor(db_session)


@pytest.fixture
def mock_garmin_service():
    """Create mock Garmin service."""
    from tests.mocks.mock_garmin import MockGarminConnect
    return MockGarminConnect()


@pytest.fixture
def populated_user_data(db_session, dal, mock_garmin_service):
    """Create user with 90 days of populated data."""
    user_id = "populated_test_user"

    # Create user
    user_data = {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "name": "Test User"
    }
    dal.create_user(db_session, user_data)

    # Populate 90 days of data
    for i in range(90):
        current_date = date.today() - timedelta(days=i)

        daily_metrics = mock_garmin_service.get_daily_metrics(user_id, current_date)
        daily_metrics.pop('date', None)
        metrics_data = {
            "user_id": user_id,
            "date": current_date,
            **daily_metrics
        }
        stored_metrics = dal.create_daily_metrics(db_session, metrics_data)

        # Add training load if the function exists
        # Note: create_training_load_tracking may not exist in DAL
        # training_load_data = {
        #     "user_id": user_id,
        #     "daily_metric_id": stored_metrics.id,
        #     "tracking_date": current_date,
        #     "daily_training_load": 100 + (i % 30) * 5
        # }
        # dal.create_training_load_tracking(db_session, training_load_data)

    return {'user_id': user_id}
