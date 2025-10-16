"""
Prompt Manager - Version control and management for AI prompts.

This service provides:
- Versioned prompt templates
- A/B testing capability
- Prompt history tracking
- Rollback functionality
- Performance metrics per prompt version

Follows semantic versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes in prompt structure
- MINOR: New features or significant improvements
- PATCH: Bug fixes or minor tweaks
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of prompts in the system."""
    READINESS_ANALYSIS = "readiness_analysis"
    TRAINING_RECOMMENDATION = "training_recommendation"
    RECOVERY_RECOMMENDATION = "recovery_recommendation"
    WORKOUT_GENERATION = "workout_generation"
    COMPLETE_RECOMMENDATION = "complete_recommendation"


class PromptVersion:
    """
    Represents a versioned prompt template.

    Attributes:
        version: Semantic version string (e.g., "1.2.3")
        prompt_type: Type of prompt
        template: Prompt template string
        created_at: When this version was created
        metadata: Additional metadata (author, changelog, etc.)
    """

    def __init__(
        self,
        version: str,
        prompt_type: PromptType,
        template: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize prompt version.

        Args:
            version: Semantic version string
            prompt_type: Type of prompt
            template: Prompt template string
            metadata: Optional metadata
        """
        self.version = version
        self.prompt_type = prompt_type
        self.template = template
        self.created_at = datetime.now()
        self.metadata = metadata or {}

        # Performance tracking
        self.usage_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.avg_confidence = 0.0

    def __repr__(self) -> str:
        return f"<PromptVersion({self.prompt_type.value} v{self.version})>"


class PromptManager:
    """
    Manages versioned prompts for AI analysis.

    Provides:
    - Prompt version management
    - Active version selection
    - A/B testing support
    - Performance tracking
    - Rollback capability
    """

    def __init__(self):
        """Initialize prompt manager with default prompts."""
        self.prompts: Dict[PromptType, Dict[str, PromptVersion]] = {
            prompt_type: {} for prompt_type in PromptType
        }

        self.active_versions: Dict[PromptType, str] = {}

        # Initialize default prompts
        self._initialize_default_prompts()

        logger.info("PromptManager initialized with default prompts")

    def _initialize_default_prompts(self):
        """Initialize default prompt versions."""

        # Readiness Analysis Prompt v1.0.0
        readiness_prompt_v1 = """You are an expert sports scientist and coach analyzing an athlete's training readiness.

**Context:**
- User ID: {user_id}
- Date: {analysis_date}
- HRV (current): {hrv_current} ms
- HRV (7-day baseline): {hrv_baseline_7d} ms
- HRV % of baseline: {hrv_percent_of_baseline}%
- Sleep last night: {sleep_last_night} minutes
- Training load (7-day): {training_load_7d}
- Training load (28-day): {training_load_28d}
- ACWR: {acwr}
- Consecutive hard days: {consecutive_hard_days}
- Days since last rest: {days_since_last_rest}

**Your Task:**
Analyze the athlete's readiness for training today and provide:

1. **Readiness Score** (0-100): Overall training readiness
2. **Readiness Level**: OPTIMAL, GOOD, MODERATE, LOW, or POOR
3. **Component Scores**:
   - HRV Score (0-100)
   - Sleep Score (0-100)
   - Load Score (0-100)
4. **Key Factors**: List 3-5 factors influencing readiness
5. **Positive Indicators**: What's going well
6. **Concerns**: What needs attention
7. **Summary**: 2-3 sentence plain English explanation
8. **Confidence**: Your confidence in this analysis (0-1)

**Guidelines:**
- HRV <75% of baseline = concern
- HRV >105% of baseline = excellent recovery
- ACWR 0.8-1.3 = optimal, >1.5 = high injury risk
- >3 consecutive hard days = fatigue concern
- <6 hours sleep = significant concern
- Use evidence-based reasoning

Provide your analysis in a structured, objective manner."""

        self.register_prompt(
            prompt_type=PromptType.READINESS_ANALYSIS,
            version="1.0.0",
            template=readiness_prompt_v1,
            metadata={
                "author": "system",
                "changelog": "Initial readiness analysis prompt",
                "created": "2025-10-16"
            }
        )

        # Training Recommendation Prompt v1.0.0
        training_prompt_v1 = """You are an expert coach providing training recommendations based on readiness analysis.

**Readiness Summary:**
- Readiness Score: {readiness_score}
- Readiness Level: {readiness_level}
- Key Factors: {key_factors}
- Concerns: {concerns}

**Context:**
- Recent Activities: {recent_activities}
- Training Load Trend: {training_load_trend}
- ACWR: {acwr}

**Your Task:**
Recommend today's training and provide:

1. **Recommended Intensity**: HIGH, MODERATE, LOW, or REST
2. **Recommended Duration**: Minutes (if applicable)
3. **Workout Types**: List appropriate workout types
4. **Training Focus**: Primary focus for today's training
5. **Key Considerations**: 3-5 important factors to consider
6. **Avoid List**: What to avoid today
7. **Rationale**: Clear explanation of your recommendation

**Guidelines:**
- OPTIMAL readiness (85-100): High intensity OK
- GOOD readiness (70-84): Moderate to high intensity
- MODERATE readiness (55-69): Low to moderate intensity
- LOW readiness (40-54): Recovery or rest
- POOR readiness (<40): Rest day
- Never recommend high intensity with >3 consecutive hard days
- Never recommend high intensity with ACWR >1.5
- Consider accumulated fatigue and recent training

Provide actionable, safe training guidance."""

        self.register_prompt(
            prompt_type=PromptType.TRAINING_RECOMMENDATION,
            version="1.0.0",
            template=training_prompt_v1,
            metadata={
                "author": "system",
                "changelog": "Initial training recommendation prompt",
                "created": "2025-10-16"
            }
        )

        # Recovery Recommendation Prompt v1.0.0
        recovery_prompt_v1 = """You are a sports medicine expert providing recovery guidance.

**Readiness Analysis:**
- Readiness Score: {readiness_score}
- Readiness Level: {readiness_level}
- HRV Status: {hrv_status}
- Sleep Quality: {sleep_quality}
- Training Load Status: {training_load_status}

**Your Task:**
Provide recovery recommendations including:

1. **Recovery Priority**: HIGH, MODERATE, or LOW
2. **Sleep Target**: Recommended sleep duration (hours)
3. **Rest Days Needed**: Number of rest days recommended
4. **Recovery Strategies**: 5-7 specific recovery activities
5. **Nutrition Focus**: Key nutritional recommendations
6. **Warning Signs**: What symptoms to watch for
7. **Guidance**: Clear recovery guidance explanation

**Guidelines:**
- HRV <75% baseline = high recovery priority
- >5 consecutive training days = rest day needed
- ACWR >1.5 = high recovery priority
- Sleep <6 hours = immediate concern
- Fatigue accumulation requires proactive recovery

Focus on evidence-based recovery strategies."""

        self.register_prompt(
            prompt_type=PromptType.RECOVERY_RECOMMENDATION,
            version="1.0.0",
            template=recovery_prompt_v1,
            metadata={
                "author": "system",
                "changelog": "Initial recovery recommendation prompt",
                "created": "2025-10-16"
            }
        )

        # Set active versions
        for prompt_type in PromptType:
            if prompt_type in [
                PromptType.READINESS_ANALYSIS,
                PromptType.TRAINING_RECOMMENDATION,
                PromptType.RECOVERY_RECOMMENDATION
            ]:
                self.active_versions[prompt_type] = "1.0.0"

    def register_prompt(
        self,
        prompt_type: PromptType,
        version: str,
        template: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptVersion:
        """
        Register a new prompt version.

        Args:
            prompt_type: Type of prompt
            version: Semantic version string
            template: Prompt template
            metadata: Optional metadata

        Returns:
            Registered PromptVersion

        Raises:
            ValueError: If version already exists
        """
        if version in self.prompts[prompt_type]:
            raise ValueError(
                f"Prompt version {version} already exists for {prompt_type.value}"
            )

        prompt_version = PromptVersion(
            version=version,
            prompt_type=prompt_type,
            template=template,
            metadata=metadata
        )

        self.prompts[prompt_type][version] = prompt_version

        logger.info(f"Registered prompt {prompt_type.value} v{version}")

        return prompt_version

    def get_prompt(
        self,
        prompt_type: PromptType,
        version: Optional[str] = None
    ) -> PromptVersion:
        """
        Get a prompt by type and version.

        Args:
            prompt_type: Type of prompt to retrieve
            version: Specific version (defaults to active version)

        Returns:
            PromptVersion

        Raises:
            KeyError: If prompt not found
        """
        if version is None:
            version = self.active_versions.get(prompt_type)
            if version is None:
                raise KeyError(f"No active version set for {prompt_type.value}")

        if version not in self.prompts[prompt_type]:
            raise KeyError(
                f"Prompt version {version} not found for {prompt_type.value}"
            )

        return self.prompts[prompt_type][version]

    def get_active_prompt(self, prompt_type: PromptType) -> PromptVersion:
        """
        Get the currently active prompt version.

        Args:
            prompt_type: Type of prompt

        Returns:
            Active PromptVersion

        Raises:
            KeyError: If no active version set
        """
        return self.get_prompt(prompt_type, version=None)

    def set_active_version(self, prompt_type: PromptType, version: str) -> None:
        """
        Set the active version for a prompt type.

        Args:
            prompt_type: Type of prompt
            version: Version to activate

        Raises:
            KeyError: If version doesn't exist
        """
        if version not in self.prompts[prompt_type]:
            raise KeyError(
                f"Cannot activate non-existent version {version} "
                f"for {prompt_type.value}"
            )

        old_version = self.active_versions.get(prompt_type)
        self.active_versions[prompt_type] = version

        logger.info(
            f"Activated {prompt_type.value} v{version} "
            f"(was: {old_version})"
        )

    def render_prompt(
        self,
        prompt_type: PromptType,
        context: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """
        Render a prompt with context data.

        Args:
            prompt_type: Type of prompt
            context: Context data to fill template
            version: Specific version (defaults to active)

        Returns:
            Rendered prompt string
        """
        prompt_version = self.get_prompt(prompt_type, version)

        # Track usage
        prompt_version.usage_count += 1

        # Render template with context
        try:
            rendered = prompt_version.template.format(**context)
            return rendered
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            raise ValueError(f"Missing template variable: {e}")

    def record_success(
        self,
        prompt_type: PromptType,
        version: str,
        confidence: float
    ) -> None:
        """
        Record successful prompt usage.

        Args:
            prompt_type: Type of prompt
            version: Version used
            confidence: AI confidence score (0-1)
        """
        prompt_version = self.get_prompt(prompt_type, version)

        prompt_version.success_count += 1

        # Update average confidence
        total = prompt_version.success_count + prompt_version.failure_count
        current_sum = prompt_version.avg_confidence * (total - 1)
        prompt_version.avg_confidence = (current_sum + confidence) / total

    def record_failure(self, prompt_type: PromptType, version: str) -> None:
        """
        Record failed prompt usage.

        Args:
            prompt_type: Type of prompt
            version: Version used
        """
        prompt_version = self.get_prompt(prompt_type, version)
        prompt_version.failure_count += 1

    def get_prompt_stats(
        self,
        prompt_type: PromptType,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a prompt version.

        Args:
            prompt_type: Type of prompt
            version: Version (defaults to active)

        Returns:
            Dictionary with statistics
        """
        prompt_version = self.get_prompt(prompt_type, version)

        total_usage = prompt_version.success_count + prompt_version.failure_count
        success_rate = (
            (prompt_version.success_count / total_usage * 100)
            if total_usage > 0 else 0.0
        )

        return {
            'version': prompt_version.version,
            'prompt_type': prompt_version.prompt_type.value,
            'usage_count': prompt_version.usage_count,
            'success_count': prompt_version.success_count,
            'failure_count': prompt_version.failure_count,
            'success_rate': round(success_rate, 2),
            'avg_confidence': round(prompt_version.avg_confidence, 3),
            'created_at': prompt_version.created_at.isoformat(),
            'metadata': prompt_version.metadata
        }

    def list_versions(self, prompt_type: PromptType) -> List[str]:
        """
        List all available versions for a prompt type.

        Args:
            prompt_type: Type of prompt

        Returns:
            List of version strings
        """
        return sorted(self.prompts[prompt_type].keys())

    def get_all_active_versions(self) -> Dict[str, str]:
        """
        Get all currently active prompt versions.

        Returns:
            Dictionary mapping prompt type to active version
        """
        return {
            prompt_type.value: version
            for prompt_type, version in self.active_versions.items()
        }


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """
    Get or create the global prompt manager instance.

    Returns:
        PromptManager singleton
    """
    global _prompt_manager

    if _prompt_manager is None:
        _prompt_manager = PromptManager()

    return _prompt_manager
