"""
Unit tests for CacheService.

Tests using in-memory database to verify:
- Two-tier caching (memory + database)
- Cache key generation
- TTL expiration
- Cache hit/miss scenarios
- User-based invalidation
- Cache statistics
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

from app.services.cache_service import CacheService, LRUCache
from app.models.ai_schemas import (
    ReadinessContext,
    ReadinessAnalysis,
    ReadinessLevel,
    CompleteRecommendation,
    TrainingRecommendation,
    RecoveryRecommendation,
    TrainingIntensity,
    WorkoutType
)
from app.models.database_models import AIResponseCache


class TestLRUCache:
    """Test LRU cache implementation."""

    def test_lru_cache_basic_operations(self):
        """Test basic get/put operations."""
        cache = LRUCache(capacity=3)

        # Put items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # Get items
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Non-existent key
        assert cache.get("key4") is None

    def test_lru_cache_eviction(self):
        """Test LRU eviction when capacity is exceeded."""
        cache = LRUCache(capacity=2)

        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Access key1 (makes it recently used)
        cache.get("key1")

        # Add key3 - should evict key2 (least recently used)
        cache.put("key3", "value3")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # New item

    def test_lru_cache_update_existing(self):
        """Test updating an existing key doesn't increase size."""
        cache = LRUCache(capacity=2)

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Update key1
        cache.put("key1", "updated_value1")

        # Should still have both keys
        assert cache.get("key1") == "updated_value1"
        assert cache.get("key2") == "value2"
        assert len(cache.cache) == 2

    def test_lru_cache_statistics(self):
        """Test cache hit/miss statistics."""
        cache = LRUCache(capacity=3)

        cache.put("key1", "value1")

        # Hit
        cache.get("key1")
        # Miss
        cache.get("key2")
        # Hit
        cache.get("key1")

        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 66.67  # 2/3 * 100

    def test_lru_cache_clear(self):
        """Test clearing cache."""
        cache = LRUCache(capacity=2)

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        cache.clear()

        assert len(cache.cache) == 0
        # Note: clear() resets stats, but get() after clear increments misses
        result = cache.get("key1")
        assert result is None
        assert cache.hits == 0
        assert cache.misses == 1  # This get() counted as a miss


class TestCacheService:
    """Test cache service functionality."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    @pytest.fixture
    def cache_service(self, db_session):
        """Create cache service for testing."""
        return CacheService(db_session, in_memory_size=10, ttl_hours=24)

    @pytest.fixture
    def sample_context(self):
        """Create sample readiness context."""
        return ReadinessContext(
            user_id="test_user",
            analysis_date=date.today(),
            hrv_current=65.0,
            hrv_baseline_7d=65.0,
            hrv_percent_of_baseline=100.0,
            sleep_last_night=480,
            training_load_7d=400,
            training_load_28d=1600,
            acwr=1.0
        )

    @pytest.fixture
    def sample_readiness_analysis(self):
        """Create sample readiness analysis."""
        return ReadinessAnalysis(
            user_id="test_user",
            analysis_date=date.today(),
            readiness_score=85.0,
            readiness_level=ReadinessLevel.GOOD,
            hrv_score=80.0,
            sleep_score=90.0,
            load_score=85.0,
            key_factors=["Good HRV", "Excellent sleep"],
            positive_indicators=["Consistent sleep pattern"],
            concerns=[],
            summary="Ready for moderate to high intensity training",
            confidence=0.9,
            model_version="claude-3-5-sonnet-20241022"
        )

    @pytest.fixture
    def sample_complete_recommendation(self, sample_readiness_analysis):
        """Create sample complete recommendation."""
        training = TrainingRecommendation(
            user_id="test_user",
            recommendation_date=date.today(),
            recommended_intensity=TrainingIntensity.MODERATE,
            recommended_duration_minutes=45,
            workout_types=[WorkoutType.ENDURANCE],
            training_focus="Aerobic base",
            key_considerations=["Stay in Zone 2"],
            avoid_list=["High intensity"],
            rationale="Good readiness supports moderate training",
            confidence=0.85,
            model_version="claude-3-5-sonnet-20241022"
        )

        recovery = RecoveryRecommendation(
            user_id="test_user",
            recommendation_date=date.today(),
            recovery_priority="low",
            sleep_target_hours=8.0,
            rest_days_needed=0,
            recovery_strategies=["Active recovery"],
            nutrition_focus=["Hydration"],
            warning_signs=["Persistent fatigue"],
            guidance="Recovery is on track",
            confidence=0.85,
            model_version="claude-3-5-sonnet-20241022"
        )

        return CompleteRecommendation(
            readiness=sample_readiness_analysis,
            training=training,
            recovery=recovery,
            workout=None,
            daily_summary="Good day for training"
        )

    def test_cache_key_generation_same_context(self, cache_service, sample_context):
        """Test that same context generates same cache key."""
        key1 = cache_service._generate_cache_key(sample_context, 'readiness')
        key2 = cache_service._generate_cache_key(sample_context, 'readiness')

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hash length

    def test_cache_key_generation_different_dates(self, cache_service, sample_context):
        """Test that different dates generate different cache keys."""
        context1 = sample_context.model_copy()
        context2 = sample_context.model_copy()
        context2.analysis_date = date.today() + timedelta(days=1)

        key1 = cache_service._generate_cache_key(context1, 'readiness')
        key2 = cache_service._generate_cache_key(context2, 'readiness')

        assert key1 != key2

    def test_cache_key_generation_different_data(self, cache_service, sample_context):
        """Test that different data generates different cache keys."""
        context1 = sample_context.model_copy()
        context2 = sample_context.model_copy()
        context2.hrv_current = 70.0  # Different HRV

        key1 = cache_service._generate_cache_key(context1, 'readiness')
        key2 = cache_service._generate_cache_key(context2, 'readiness')

        assert key1 != key2

    def test_cache_key_generation_different_types(self, cache_service, sample_context):
        """Test that different cache types generate different keys."""
        key1 = cache_service._generate_cache_key(sample_context, 'readiness')
        key2 = cache_service._generate_cache_key(sample_context, 'complete')

        assert key1 != key2

    def test_cache_miss_readiness(self, cache_service, sample_context):
        """Test cache miss for readiness analysis."""
        result = cache_service.get_readiness_analysis(sample_context)

        assert result is None

    def test_cache_hit_readiness_memory(
        self,
        cache_service,
        sample_context,
        sample_readiness_analysis
    ):
        """Test cache hit from memory cache."""
        # Cache the analysis
        cache_service.cache_readiness_analysis(sample_context, sample_readiness_analysis)

        # Should hit memory cache
        result = cache_service.get_readiness_analysis(sample_context)

        assert result is not None
        assert result.user_id == sample_readiness_analysis.user_id
        assert result.readiness_score == sample_readiness_analysis.readiness_score
        assert result.readiness_level == sample_readiness_analysis.readiness_level

    def test_cache_hit_readiness_database(
        self,
        cache_service,
        sample_context,
        sample_readiness_analysis
    ):
        """Test cache hit from database after memory cache miss."""
        # Cache the analysis
        cache_service.cache_readiness_analysis(sample_context, sample_readiness_analysis)

        # Clear memory cache
        cache_service.memory_cache.clear()

        # Should hit database cache and populate memory cache
        result = cache_service.get_readiness_analysis(sample_context)

        assert result is not None
        assert result.user_id == sample_readiness_analysis.user_id
        assert result.readiness_score == sample_readiness_analysis.readiness_score

    def test_cache_complete_recommendation(
        self,
        cache_service,
        sample_context,
        sample_complete_recommendation
    ):
        """Test caching complete recommendation."""
        # Cache
        cache_service.cache_complete_recommendation(
            sample_context,
            sample_complete_recommendation
        )

        # Retrieve
        result = cache_service.get_complete_recommendation(sample_context)

        assert result is not None
        assert result.readiness.user_id == sample_complete_recommendation.readiness.user_id
        assert result.training.recommended_intensity == \
            sample_complete_recommendation.training.recommended_intensity
        assert result.recovery.recovery_priority == \
            sample_complete_recommendation.recovery.recovery_priority

    def test_cache_invalidate_user(
        self,
        cache_service,
        sample_context,
        sample_readiness_analysis
    ):
        """Test invalidating all cache entries for a user."""
        # Cache multiple entries for same user
        context1 = sample_context.model_copy()
        context2 = sample_context.model_copy()
        context2.hrv_current = 70.0  # Different data

        cache_service.cache_readiness_analysis(context1, sample_readiness_analysis)
        cache_service.cache_readiness_analysis(context2, sample_readiness_analysis)

        # Invalidate user cache
        count = cache_service.invalidate_user_cache("test_user")

        assert count >= 2  # At least 2 entries deleted

        # Should be cache misses now
        assert cache_service.get_readiness_analysis(context1) is None
        assert cache_service.get_readiness_analysis(context2) is None

    def test_cache_expiration(
        self,
        cache_service,
        sample_context,
        sample_readiness_analysis
    ):
        """Test that expired cache entries are not returned."""
        # Cache with short TTL
        cache_service.ttl_hours = 1

        # Cache entry
        cache_service.cache_readiness_analysis(sample_context, sample_readiness_analysis)

        # Manually set cached_at to 2 hours ago
        cache_key = cache_service._generate_cache_key(sample_context, 'readiness')
        entry = cache_service.db.query(AIResponseCache).filter(
            AIResponseCache.cache_key == cache_key
        ).first()

        entry.cached_at = datetime.now() - timedelta(hours=2)
        cache_service.db.commit()

        # Clear memory cache
        cache_service.memory_cache.clear()

        # Should not return expired entry
        result = cache_service.get_readiness_analysis(sample_context)
        assert result is None

    def test_cleanup_expired(
        self,
        cache_service,
        sample_context,
        sample_readiness_analysis
    ):
        """Test cleanup of expired cache entries."""
        cache_service.ttl_hours = 1

        # Cache entry
        cache_service.cache_readiness_analysis(sample_context, sample_readiness_analysis)

        # Manually expire it
        cache_key = cache_service._generate_cache_key(sample_context, 'readiness')
        entry = cache_service.db.query(AIResponseCache).filter(
            AIResponseCache.cache_key == cache_key
        ).first()

        entry.cached_at = datetime.now() - timedelta(hours=2)
        cache_service.db.commit()

        # Clean up
        count = cache_service.cleanup_expired()

        assert count == 1

        # Should be gone
        entry_after = cache_service.db.query(AIResponseCache).filter(
            AIResponseCache.cache_key == cache_key
        ).first()

        assert entry_after is None

    def test_cache_statistics(
        self,
        cache_service,
        sample_context,
        sample_readiness_analysis
    ):
        """Test cache statistics reporting."""
        # Cache some entries
        cache_service.cache_readiness_analysis(sample_context, sample_readiness_analysis)

        # Get stats
        stats = cache_service.get_cache_stats()

        assert 'memory' in stats
        assert 'database' in stats
        assert 'ttl_hours' in stats

        assert stats['memory']['size'] >= 1
        assert stats['database']['total_entries'] >= 1
        assert stats['ttl_hours'] == 24

    def test_serialization_deserialization(
        self,
        cache_service,
        sample_readiness_analysis
    ):
        """Test that serialization/deserialization preserves data."""
        # Serialize
        serialized = cache_service._serialize_readiness(sample_readiness_analysis)

        # Deserialize
        deserialized = cache_service._deserialize_readiness(serialized)

        # Check equality
        assert deserialized.user_id == sample_readiness_analysis.user_id
        assert deserialized.readiness_score == sample_readiness_analysis.readiness_score
        assert deserialized.readiness_level == sample_readiness_analysis.readiness_level
        assert deserialized.summary == sample_readiness_analysis.summary

    def test_multiple_users_isolated_caches(
        self,
        cache_service,
        sample_readiness_analysis
    ):
        """Test that different users have isolated caches."""
        context1 = ReadinessContext(
            user_id="user1",
            analysis_date=date.today(),
            hrv_current=65.0
        )

        context2 = ReadinessContext(
            user_id="user2",
            analysis_date=date.today(),
            hrv_current=65.0  # Same metrics, different user
        )

        analysis1 = sample_readiness_analysis.model_copy()
        analysis1.user_id = "user1"

        analysis2 = sample_readiness_analysis.model_copy()
        analysis2.user_id = "user2"

        # Cache for both users
        cache_service.cache_readiness_analysis(context1, analysis1)
        cache_service.cache_readiness_analysis(context2, analysis2)

        # Invalidate user1
        cache_service.invalidate_user_cache("user1")

        # user1 should have cache miss
        assert cache_service.get_readiness_analysis(context1) is None

        # user2 should still have cache hit
        result = cache_service.get_readiness_analysis(context2)
        assert result is not None
        assert result.user_id == "user2"

    def test_cache_service_initialization(self, db_session):
        """Test cache service initialization options."""
        # Test with different TTL
        cache_service = CacheService(db_session, in_memory_size=50, ttl_hours=12)

        assert cache_service.memory_cache.capacity == 50
        assert cache_service.ttl_hours == 12

        # Test with default settings
        cache_service_default = CacheService(db_session)

        assert cache_service_default.memory_cache.capacity == 100
        assert cache_service_default.ttl_hours == 24
