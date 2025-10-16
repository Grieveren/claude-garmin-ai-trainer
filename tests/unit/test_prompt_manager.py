"""
Unit tests for PromptManager.

Tests prompt versioning, A/B testing capabilities, and performance tracking.
"""

import pytest
from datetime import datetime

from app.services.prompt_manager import (
    PromptManager,
    PromptType,
    PromptVersion,
    get_prompt_manager
)


class TestPromptVersion:
    """Test PromptVersion class."""

    def test_prompt_version_creation(self):
        """Test creating a prompt version."""
        version = PromptVersion(
            version="1.0.0",
            prompt_type=PromptType.READINESS_ANALYSIS,
            template="Test prompt with {variable}",
            metadata={"author": "test"}
        )

        assert version.version == "1.0.0"
        assert version.prompt_type == PromptType.READINESS_ANALYSIS
        assert version.template == "Test prompt with {variable}"
        assert version.metadata["author"] == "test"
        assert version.usage_count == 0
        assert version.success_count == 0
        assert version.failure_count == 0
        assert isinstance(version.created_at, datetime)

    def test_prompt_version_repr(self):
        """Test string representation."""
        version = PromptVersion(
            version="2.0.0",
            prompt_type=PromptType.TRAINING_RECOMMENDATION,
            template="Test"
        )

        assert "PromptVersion" in repr(version)
        assert "training_recommendation" in repr(version)
        assert "2.0.0" in repr(version)


class TestPromptManager:
    """Test PromptManager functionality."""

    @pytest.fixture
    def prompt_manager(self):
        """Create fresh prompt manager for each test."""
        return PromptManager()

    def test_initialization_with_defaults(self, prompt_manager):
        """Test that manager initializes with default prompts."""
        # Should have default prompts registered
        assert len(prompt_manager.prompts[PromptType.READINESS_ANALYSIS]) > 0
        assert len(prompt_manager.prompts[PromptType.TRAINING_RECOMMENDATION]) > 0
        assert len(prompt_manager.prompts[PromptType.RECOVERY_RECOMMENDATION]) > 0

        # Should have active versions set
        assert PromptType.READINESS_ANALYSIS in prompt_manager.active_versions
        assert PromptType.TRAINING_RECOMMENDATION in prompt_manager.active_versions
        assert PromptType.RECOVERY_RECOMMENDATION in prompt_manager.active_versions

    def test_register_new_prompt(self, prompt_manager):
        """Test registering a new prompt version."""
        template = "New prompt template with {context}"

        prompt_version = prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="2.0.0",
            template=template,
            metadata={"author": "test_user", "changelog": "Added new feature"}
        )

        assert prompt_version.version == "2.0.0"
        assert prompt_version.template == template
        assert prompt_version.metadata["author"] == "test_user"

        # Should be retrievable
        retrieved = prompt_manager.get_prompt(
            PromptType.READINESS_ANALYSIS,
            version="2.0.0"
        )
        assert retrieved.version == "2.0.0"

    def test_register_duplicate_version_fails(self, prompt_manager):
        """Test that registering duplicate version raises error."""
        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="3.0.0",
            template="Test"
        )

        with pytest.raises(ValueError, match="already exists"):
            prompt_manager.register_prompt(
                prompt_type=PromptType.READINESS_ANALYSIS,
                version="3.0.0",  # Same version
                template="Different template"
            )

    def test_get_prompt_by_version(self, prompt_manager):
        """Test retrieving specific prompt version."""
        # Get default version
        prompt = prompt_manager.get_prompt(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        assert prompt.version == "1.0.0"
        assert prompt.prompt_type == PromptType.READINESS_ANALYSIS
        assert len(prompt.template) > 0

    def test_get_nonexistent_version_fails(self, prompt_manager):
        """Test that getting nonexistent version raises error."""
        with pytest.raises(KeyError):
            prompt_manager.get_prompt(
                PromptType.READINESS_ANALYSIS,
                version="99.99.99"
            )

    def test_get_active_prompt(self, prompt_manager):
        """Test retrieving active prompt version."""
        active_prompt = prompt_manager.get_active_prompt(
            PromptType.READINESS_ANALYSIS
        )

        assert active_prompt is not None
        assert active_prompt.version == "1.0.0"  # Default version

    def test_set_active_version(self, prompt_manager):
        """Test changing active version."""
        # Register new version
        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="2.0.0",
            template="Updated prompt"
        )

        # Change active version
        prompt_manager.set_active_version(
            PromptType.READINESS_ANALYSIS,
            "2.0.0"
        )

        # Active prompt should now be 2.0.0
        active_prompt = prompt_manager.get_active_prompt(
            PromptType.READINESS_ANALYSIS
        )
        assert active_prompt.version == "2.0.0"

    def test_set_nonexistent_version_fails(self, prompt_manager):
        """Test that setting nonexistent version fails."""
        with pytest.raises(KeyError):
            prompt_manager.set_active_version(
                PromptType.READINESS_ANALYSIS,
                "99.99.99"
            )

    def test_render_prompt_with_context(self, prompt_manager):
        """Test rendering prompt with context variables."""
        # Register simple template
        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="test.0.0",
            template="User {user_id} has HRV of {hrv_current} ms"
        )

        context = {
            "user_id": "test_user",
            "hrv_current": 65.0
        }

        rendered = prompt_manager.render_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            context=context,
            version="test.0.0"
        )

        assert "test_user" in rendered
        assert "65.0" in rendered
        assert "User test_user has HRV of 65.0 ms" == rendered

    def test_render_prompt_missing_variable_fails(self, prompt_manager):
        """Test that rendering with missing variable fails."""
        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="test.0.0",
            template="User {user_id} needs {required_variable}"
        )

        context = {
            "user_id": "test_user"
            # Missing required_variable
        }

        with pytest.raises(ValueError, match="Missing template variable"):
            prompt_manager.render_prompt(
                prompt_type=PromptType.READINESS_ANALYSIS,
                context=context,
                version="test.0.0"
            )

    def test_render_increments_usage_count(self, prompt_manager):
        """Test that rendering increments usage counter."""
        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="test.0.0",
            template="Test"
        )

        prompt_version = prompt_manager.get_prompt(
            PromptType.READINESS_ANALYSIS,
            version="test.0.0"
        )

        initial_count = prompt_version.usage_count

        prompt_manager.render_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            context={},
            version="test.0.0"
        )

        assert prompt_version.usage_count == initial_count + 1

    def test_record_success(self, prompt_manager):
        """Test recording successful prompt usage."""
        prompt_manager.record_success(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="1.0.0",
            confidence=0.85
        )

        prompt_version = prompt_manager.get_prompt(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        assert prompt_version.success_count == 1
        assert prompt_version.avg_confidence == 0.85

    def test_record_multiple_successes_updates_avg_confidence(self, prompt_manager):
        """Test that multiple successes update average confidence correctly."""
        prompt_manager.record_success(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0",
            confidence=0.8
        )

        prompt_manager.record_success(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0",
            confidence=0.9
        )

        prompt_version = prompt_manager.get_prompt(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        assert prompt_version.success_count == 2
        # Use approximate equality for floating point
        assert abs(prompt_version.avg_confidence - 0.85) < 0.0001  # (0.8 + 0.9) / 2

    def test_record_failure(self, prompt_manager):
        """Test recording failed prompt usage."""
        prompt_manager.record_failure(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        prompt_version = prompt_manager.get_prompt(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        assert prompt_version.failure_count == 1

    def test_get_prompt_stats(self, prompt_manager):
        """Test getting prompt statistics."""
        # Record some usage
        prompt_manager.record_success(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0",
            confidence=0.9
        )

        prompt_manager.record_failure(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        stats = prompt_manager.get_prompt_stats(
            PromptType.READINESS_ANALYSIS,
            version="1.0.0"
        )

        assert stats['version'] == "1.0.0"
        assert stats['prompt_type'] == "readiness_analysis"
        assert stats['success_count'] == 1
        assert stats['failure_count'] == 1
        assert stats['success_rate'] == 50.0  # 1/2 * 100
        assert 'avg_confidence' in stats
        assert 'created_at' in stats
        assert 'metadata' in stats

    def test_list_versions(self, prompt_manager):
        """Test listing all versions for a prompt type."""
        # Register additional versions
        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="2.0.0",
            template="Version 2"
        )

        prompt_manager.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="1.5.0",
            template="Version 1.5"
        )

        versions = prompt_manager.list_versions(PromptType.READINESS_ANALYSIS)

        assert "1.0.0" in versions  # Default version
        assert "1.5.0" in versions
        assert "2.0.0" in versions
        assert len(versions) >= 3

    def test_get_all_active_versions(self, prompt_manager):
        """Test getting all active versions."""
        active_versions = prompt_manager.get_all_active_versions()

        assert "readiness_analysis" in active_versions
        assert "training_recommendation" in active_versions
        assert "recovery_recommendation" in active_versions

        assert active_versions["readiness_analysis"] == "1.0.0"

    def test_default_prompts_have_content(self, prompt_manager):
        """Test that default prompts have meaningful content."""
        readiness_prompt = prompt_manager.get_active_prompt(
            PromptType.READINESS_ANALYSIS
        )

        # Should contain key instructions
        assert "readiness" in readiness_prompt.template.lower()
        assert "HRV" in readiness_prompt.template or "hrv" in readiness_prompt.template.lower()
        assert "sleep" in readiness_prompt.template.lower()

        training_prompt = prompt_manager.get_active_prompt(
            PromptType.TRAINING_RECOMMENDATION
        )

        assert "training" in training_prompt.template.lower()
        assert "intensity" in training_prompt.template.lower()

    def test_prompt_template_variables(self, prompt_manager):
        """Test that default prompts have expected template variables."""
        readiness_prompt = prompt_manager.get_active_prompt(
            PromptType.READINESS_ANALYSIS
        )

        # Should have key variables
        assert "{user_id}" in readiness_prompt.template
        assert "{hrv_current}" in readiness_prompt.template
        assert "{sleep_last_night}" in readiness_prompt.template


class TestPromptManagerSingleton:
    """Test global prompt manager singleton."""

    def test_get_prompt_manager_returns_singleton(self):
        """Test that get_prompt_manager returns same instance."""
        manager1 = get_prompt_manager()
        manager2 = get_prompt_manager()

        assert manager1 is manager2

    def test_singleton_has_default_prompts(self):
        """Test that singleton is properly initialized."""
        manager = get_prompt_manager()

        assert len(manager.prompts[PromptType.READINESS_ANALYSIS]) > 0
        assert len(manager.active_versions) > 0
