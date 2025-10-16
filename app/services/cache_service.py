"""
Cache Service - Two-tier caching for AI responses.

Implements:
1. In-memory LRU cache (fast, limited size)
2. Database-backed cache (persistent, larger capacity)

Cache Strategy:
- Cache key: SHA256 hash of ReadinessContext (excluding timestamp)
- TTL: 24 hours (AI responses stay relevant for a day)
- Eviction: LRU for in-memory, TTL-based for database
- Size: 100 entries in-memory by default

Cache Hit Scenarios:
- Same user, same metrics, same day → cache hit
- Different metrics, same day → cache miss (correct)
- Same metrics, different day → cache miss (correct)

Performance Goals:
- Memory cache: <1ms lookup
- Database cache: <10ms lookup
- Cache hit rate target: >50%
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import OrderedDict
from sqlalchemy.orm import Session

from app.models.ai_schemas import (
    ReadinessContext,
    ReadinessAnalysis,
    TrainingRecommendation,
    RecoveryRecommendation,
    CompleteRecommendation
)

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.

    Uses OrderedDict to maintain insertion/access order.
    When capacity is reached, oldest item is evicted.
    """

    def __init__(self, capacity: int = 100):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items to store
        """
        self.cache: OrderedDict = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        if key not in self.cache:
            self.misses += 1
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        """
        Put item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item and mark as recently used
            self.cache.move_to_end(key)

        self.cache[key] = value

        # Evict oldest item if over capacity
        if len(self.cache) > self.capacity:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"LRU cache evicted key: {oldest_key[:16]}...")

    def clear(self) -> None:
        """Clear all items from cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            'size': len(self.cache),
            'capacity': self.capacity,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2)
        }


class CacheService:
    """
    Two-tier caching service for AI responses.

    Architecture:
    1. Check in-memory cache first (fast)
    2. If miss, check database cache
    3. If found in database, populate memory cache
    4. If miss everywhere, return None (caller fetches from AI)

    Cache Invalidation:
    - TTL-based (24 hours)
    - Can manually invalidate by user_id or cache key
    """

    def __init__(
        self,
        db_session: Session,
        in_memory_size: int = 100,
        ttl_hours: int = 24
    ):
        """
        Initialize cache service.

        Args:
            db_session: Database session for persistent cache
            in_memory_size: Size of in-memory LRU cache
            ttl_hours: Time-to-live for cache entries (hours)
        """
        self.db = db_session
        self.memory_cache = LRUCache(capacity=in_memory_size)
        self.ttl_hours = ttl_hours

        logger.info(f"CacheService initialized (memory_size={in_memory_size}, ttl={ttl_hours}h)")

    def _generate_cache_key(self, context: ReadinessContext, cache_type: str) -> str:
        """
        Generate cache key from context.

        Strategy:
        - Hash the context data (excluding timestamp/date)
        - Include the date separately
        - Include cache type (readiness, training, recovery, complete)

        This ensures:
        - Same context on same day = same key
        - Same context on different day = different key
        - Different analysis types = different keys

        Args:
            context: Readiness context
            cache_type: Type of cached data (readiness, training, recovery, complete)

        Returns:
            SHA256 hash as cache key
        """
        # Convert context to dict, excluding analysis_date
        context_dict = context.model_dump(mode='json', exclude={'analysis_date'})

        # Build cache key structure
        cache_key_data = {
            'user_id': context.user_id,
            'date': str(context.analysis_date),
            'type': cache_type,
            'data': context_dict
        }

        # Generate hash
        content = json.dumps(cache_key_data, sort_keys=True)
        cache_key = hashlib.sha256(content.encode()).hexdigest()

        logger.debug(f"Generated cache key: {cache_key[:16]}... for {context.user_id} on {context.analysis_date}")

        return cache_key

    def get_readiness_analysis(
        self,
        context: ReadinessContext
    ) -> Optional[ReadinessAnalysis]:
        """
        Get cached readiness analysis.

        Args:
            context: Readiness context

        Returns:
            Cached analysis if found and valid, None otherwise
        """
        cache_key = self._generate_cache_key(context, 'readiness')

        # Try memory cache first
        cached = self.memory_cache.get(cache_key)
        if cached:
            logger.info(f"Cache HIT (memory) for readiness analysis: {context.user_id}")
            return self._deserialize_readiness(cached)

        # Try database cache
        cached = self._get_from_db(cache_key)
        if cached:
            logger.info(f"Cache HIT (database) for readiness analysis: {context.user_id}")
            # Populate memory cache
            self.memory_cache.put(cache_key, cached)
            return self._deserialize_readiness(cached)

        logger.debug(f"Cache MISS for readiness analysis: {context.user_id}")
        return None

    def cache_readiness_analysis(
        self,
        context: ReadinessContext,
        analysis: ReadinessAnalysis
    ) -> None:
        """
        Cache readiness analysis.

        Args:
            context: Readiness context
            analysis: Analysis to cache
        """
        cache_key = self._generate_cache_key(context, 'readiness')
        cached_data = self._serialize_readiness(analysis)

        # Store in both caches
        self.memory_cache.put(cache_key, cached_data)
        self._store_in_db(cache_key, cached_data, context.user_id, 'readiness')

        logger.info(f"Cached readiness analysis for {context.user_id}")

    def get_complete_recommendation(
        self,
        context: ReadinessContext
    ) -> Optional[CompleteRecommendation]:
        """
        Get cached complete recommendation.

        Args:
            context: Readiness context

        Returns:
            Cached recommendation if found and valid, None otherwise
        """
        cache_key = self._generate_cache_key(context, 'complete')

        # Try memory cache first
        cached = self.memory_cache.get(cache_key)
        if cached:
            logger.info(f"Cache HIT (memory) for complete recommendation: {context.user_id}")
            return self._deserialize_complete(cached)

        # Try database cache
        cached = self._get_from_db(cache_key)
        if cached:
            logger.info(f"Cache HIT (database) for complete recommendation: {context.user_id}")
            # Populate memory cache
            self.memory_cache.put(cache_key, cached)
            return self._deserialize_complete(cached)

        logger.debug(f"Cache MISS for complete recommendation: {context.user_id}")
        return None

    def cache_complete_recommendation(
        self,
        context: ReadinessContext,
        recommendation: CompleteRecommendation
    ) -> None:
        """
        Cache complete recommendation.

        Args:
            context: Readiness context
            recommendation: Recommendation to cache
        """
        cache_key = self._generate_cache_key(context, 'complete')
        cached_data = self._serialize_complete(recommendation)

        # Store in both caches
        self.memory_cache.put(cache_key, cached_data)
        self._store_in_db(cache_key, cached_data, context.user_id, 'complete')

        logger.info(f"Cached complete recommendation for {context.user_id}")

    def invalidate_user_cache(self, user_id: str) -> int:
        """
        Invalidate all cache entries for a user.

        Useful when user data changes significantly (e.g., manual data correction).

        Args:
            user_id: User identifier

        Returns:
            Number of entries invalidated
        """
        # Database invalidation
        from app.models.database_models import AIResponseCache

        count = self.db.query(AIResponseCache).filter(
            AIResponseCache.user_id == user_id
        ).delete()

        self.db.commit()

        # Memory cache - we can't selectively delete by user_id, so clear all
        # (This is a trade-off for simplicity; could be optimized)
        self.memory_cache.clear()

        logger.info(f"Invalidated {count} cache entries for user {user_id}")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from database cache.

        Should be run periodically (e.g., daily cron job).

        Returns:
            Number of entries removed
        """
        from app.models.database_models import AIResponseCache

        cutoff = datetime.now() - timedelta(hours=self.ttl_hours)

        count = self.db.query(AIResponseCache).filter(
            AIResponseCache.cached_at < cutoff
        ).delete()

        self.db.commit()

        logger.info(f"Cleaned up {count} expired cache entries")
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        from app.models.database_models import AIResponseCache

        # Memory cache stats
        memory_stats = self.memory_cache.get_stats()

        # Database cache stats
        db_total = self.db.query(AIResponseCache).count()

        cutoff = datetime.now() - timedelta(hours=self.ttl_hours)
        db_valid = self.db.query(AIResponseCache).filter(
            AIResponseCache.cached_at >= cutoff
        ).count()

        return {
            'memory': memory_stats,
            'database': {
                'total_entries': db_total,
                'valid_entries': db_valid,
                'expired_entries': db_total - db_valid
            },
            'ttl_hours': self.ttl_hours
        }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_from_db(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get entry from database cache if valid."""
        from app.models.database_models import AIResponseCache

        entry = self.db.query(AIResponseCache).filter(
            AIResponseCache.cache_key == cache_key
        ).first()

        if not entry:
            return None

        # Check if expired
        cutoff = datetime.now() - timedelta(hours=self.ttl_hours)
        if entry.cached_at < cutoff:
            logger.debug(f"Database cache entry expired: {cache_key[:16]}...")
            return None

        return entry.response_data

    def _store_in_db(
        self,
        cache_key: str,
        data: Dict[str, Any],
        user_id: str,
        cache_type: str
    ) -> None:
        """Store entry in database cache."""
        from app.models.database_models import AIResponseCache

        # Check if entry exists
        entry = self.db.query(AIResponseCache).filter(
            AIResponseCache.cache_key == cache_key
        ).first()

        if entry:
            # Update existing
            entry.response_data = data
            entry.cached_at = datetime.now()
        else:
            # Create new
            entry = AIResponseCache(
                cache_key=cache_key,
                user_id=user_id,
                cache_type=cache_type,
                response_data=data,
                cached_at=datetime.now()
            )
            self.db.add(entry)

        self.db.commit()

    def _serialize_readiness(self, analysis: ReadinessAnalysis) -> Dict[str, Any]:
        """Serialize readiness analysis for caching."""
        return analysis.model_dump(mode='json')

    def _deserialize_readiness(self, data: Dict[str, Any]) -> ReadinessAnalysis:
        """Deserialize readiness analysis from cache."""
        return ReadinessAnalysis(**data)

    def _serialize_complete(self, recommendation: CompleteRecommendation) -> Dict[str, Any]:
        """Serialize complete recommendation for caching."""
        return recommendation.model_dump(mode='json')

    def _deserialize_complete(self, data: Dict[str, Any]) -> CompleteRecommendation:
        """Deserialize complete recommendation from cache."""
        return CompleteRecommendation(**data)
