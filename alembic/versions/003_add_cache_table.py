"""Add AI response cache table for Phase 3

Revision ID: 003_add_cache_table
Revises: 002_add_indexes
Create Date: 2025-10-16

This migration adds the ai_response_cache table to support Phase 3
caching functionality. This table stores structured Pydantic responses
(ReadinessAnalysis, CompleteRecommendation) to reduce API costs and
improve response times.

Key Features:
- SHA-256 cache keys based on ReadinessContext
- 24-hour TTL for cache entries
- User-based cache invalidation support
- Separate from ai_analysis_cache (which stores raw text responses)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003_add_cache_table'
down_revision = '002_add_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add AI response cache table."""

    # Create ai_response_cache table
    op.create_table(
        'ai_response_cache',

        # Primary key
        sa.Column('id', sa.Integer(), nullable=False),

        # Cache key (SHA256 hash of context)
        sa.Column(
            'cache_key',
            sa.String(length=64),
            nullable=False,
            comment='SHA-256 hash of ReadinessContext + cache_type'
        ),

        # User and metadata
        sa.Column(
            'user_id',
            sa.String(length=100),
            nullable=False,
            comment='User who generated this cached response'
        ),

        sa.Column(
            'cache_type',
            sa.String(length=50),
            nullable=False,
            comment='readiness, training, recovery, complete'
        ),

        # Cached response (fully structured Pydantic model as JSON)
        sa.Column(
            'response_data',
            sa.JSON(),
            nullable=False,
            comment='Complete Pydantic model serialized to JSON'
        ),

        # Cache management
        sa.Column(
            'cached_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            comment='When this response was cached (for TTL)'
        ),

        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key', name='uq_cache_key')
    )

    # Create indexes for optimal query performance

    # Primary lookup index (cache key)
    op.create_index(
        'idx_response_cache_key',
        'ai_response_cache',
        ['cache_key'],
        unique=False
    )

    # User + cached_at index (for user-based queries and TTL cleanup)
    op.create_index(
        'idx_response_cache_user_date',
        'ai_response_cache',
        ['user_id', 'cached_at'],
        unique=False
    )

    # Cache type index (for stats and filtering)
    op.create_index(
        'idx_response_cache_type',
        'ai_response_cache',
        ['cache_type'],
        unique=False
    )

    # Composite index for cache stats queries
    op.create_index(
        'idx_response_cache_stats',
        'ai_response_cache',
        ['cache_type', 'cached_at', 'user_id'],
        unique=False
    )


def downgrade():
    """Remove AI response cache table."""

    # Drop indexes first
    op.drop_index('idx_response_cache_stats', 'ai_response_cache')
    op.drop_index('idx_response_cache_type', 'ai_response_cache')
    op.drop_index('idx_response_cache_user_date', 'ai_response_cache')
    op.drop_index('idx_response_cache_key', 'ai_response_cache')

    # Drop table
    op.drop_table('ai_response_cache')
