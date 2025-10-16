"""
Claude AI service for generating training insights and recommendations.

Provides:
- Readiness analysis
- Training recommendations
- Recovery guidance
- Workout planning

Includes:
- Rate limiting (token bucket algorithm)
- Retry logic with exponential backoff
- Response validation
- Error handling
- Cost tracking
"""

import os
import time
import logging
from datetime import datetime
from typing import Optional
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.models.ai_schemas import (
    ReadinessContext,
    ReadinessAnalysis,
    ReadinessLevel,
    TrainingRecommendation,
    TrainingIntensity,
    WorkoutType,
    RecoveryRecommendation,
    WorkoutRecommendation,
    CompleteRecommendation,
    AIServiceError
)

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Token bucket algorithm for rate limiting.

    Refills tokens at a constant rate and allows bursts up to capacity.
    """

    def __init__(self, requests_per_minute: int = 50):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.capacity = requests_per_minute
        self.tokens = float(requests_per_minute)
        self.last_refill = time.time()
        self.refill_rate = requests_per_minute / 60.0  # Tokens per second

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens. Returns False if rate limited.

        Args:
            tokens: Number of tokens to acquire (default 1)

        Returns:
            True if tokens acquired, False if rate limited
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate seconds until requested tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds to wait
        """
        self._refill()

        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class ClaudeServiceError(Exception):
    """Base exception for Claude service errors."""
    pass


class ClaudeRateLimitError(ClaudeServiceError):
    """Rate limit exceeded."""
    pass


class ClaudeAPIError(ClaudeServiceError):
    """API communication error."""
    pass


class ClaudeValidationError(ClaudeServiceError):
    """Response validation error."""
    pass


class ClaudeService:
    """
    Claude AI service for training analysis and recommendations.

    Handles all interactions with Claude AI API including:
    - Request formatting
    - Rate limiting
    - Error handling
    - Response parsing
    - Cost tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: int = 50,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """
        Initialize Claude service.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            rate_limit: Requests per minute limit (default 50)
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided or set in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.rate_limiter = TokenBucketRateLimiter(requests_per_minute=rate_limit)
        self.model = model

        # Cost tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0

        logger.info(f"Initialized ClaudeService with model {self.model}")

    @retry(
        retry=retry_if_exception_type((APITimeoutError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _make_api_call(self, system: str, messages: list) -> dict:
        """
        Make API call with retry logic.

        Args:
            system: System prompt
            messages: Conversation messages

        Returns:
            API response

        Raises:
            ClaudeRateLimitError: Rate limit exceeded
            ClaudeAPIError: API error
        """
        # Check rate limit
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.time_until_available()
            raise ClaudeRateLimitError(
                f"Rate limit exceeded. Retry after {wait_time:.1f} seconds"
            )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=messages
            )

            # Track usage
            self.total_requests += 1
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Calculate cost (approximate - update with actual pricing)
            # Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
            input_cost = (response.usage.input_tokens / 1_000_000) * 3.0
            output_cost = (response.usage.output_tokens / 1_000_000) * 15.0
            self.total_cost += input_cost + output_cost

            logger.info(
                f"API call successful. Tokens: {response.usage.input_tokens + response.usage.output_tokens}, "
                f"Cost: ${input_cost + output_cost:.4f}"
            )

            return {
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except RateLimitError as e:
            logger.warning(f"Rate limit error: {e}")
            raise ClaudeRateLimitError(str(e))
        except APITimeoutError as e:
            logger.warning(f"API timeout: {e}")
            raise
        except APIError as e:
            logger.error(f"API error: {e}")
            raise ClaudeAPIError(str(e))

    def analyze_readiness(
        self,
        context: ReadinessContext
    ) -> ReadinessAnalysis:
        """
        Analyze readiness and provide assessment.

        Args:
            context: Readiness context with metrics

        Returns:
            ReadinessAnalysis with score, level, and insights

        Raises:
            ClaudeServiceError: On service errors
        """
        logger.info(f"Analyzing readiness for user {context.user_id} on {context.date}")

        system_prompt = self._build_readiness_system_prompt()
        user_message = self._build_readiness_user_message(context)

        try:
            response = self._make_api_call(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            # Parse and validate response
            analysis = self._parse_readiness_response(response["content"], context)

            logger.info(
                f"Readiness analysis complete: {analysis.readiness_level.value} "
                f"(score: {analysis.readiness_score:.1f})"
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze readiness: {e}")
            raise

    def recommend_training(
        self,
        context: ReadinessContext,
        readiness: ReadinessAnalysis
    ) -> TrainingRecommendation:
        """
        Generate training recommendations.

        Args:
            context: Readiness context
            readiness: Readiness analysis results

        Returns:
            TrainingRecommendation

        Raises:
            ClaudeServiceError: On service errors
        """
        logger.info(f"Generating training recommendation for {context.user_id}")

        system_prompt = self._build_training_system_prompt()
        user_message = self._build_training_user_message(context, readiness)

        try:
            response = self._make_api_call(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            recommendation = self._parse_training_response(response["content"], context)

            logger.info(
                f"Training recommendation: {recommendation.recommended_intensity.value} "
                f"for {recommendation.recommended_duration_minutes}min"
            )

            return recommendation

        except Exception as e:
            logger.error(f"Failed to generate training recommendation: {e}")
            raise

    def recommend_recovery(
        self,
        context: ReadinessContext,
        readiness: ReadinessAnalysis
    ) -> RecoveryRecommendation:
        """
        Generate recovery recommendations.

        Args:
            context: Readiness context
            readiness: Readiness analysis

        Returns:
            RecoveryRecommendation

        Raises:
            ClaudeServiceError: On service errors
        """
        logger.info(f"Generating recovery recommendation for {context.user_id}")

        system_prompt = self._build_recovery_system_prompt()
        user_message = self._build_recovery_user_message(context, readiness)

        try:
            response = self._make_api_call(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            recommendation = self._parse_recovery_response(response["content"], context)

            logger.info(
                f"Recovery recommendation: {recommendation.recovery_priority} priority"
            )

            return recommendation

        except Exception as e:
            logger.error(f"Failed to generate recovery recommendation: {e}")
            raise

    def get_complete_recommendation(
        self,
        context: ReadinessContext
    ) -> CompleteRecommendation:
        """
        Generate complete set of recommendations.

        Args:
            context: Readiness context

        Returns:
            CompleteRecommendation with all components

        Raises:
            ClaudeServiceError: On service errors
        """
        logger.info(f"Generating complete recommendation for {context.user_id}")

        # Generate each component
        readiness = self.analyze_readiness(context)
        training = self.recommend_training(context, readiness)
        recovery = self.recommend_recovery(context, readiness)

        # Generate workout if not rest day
        workout = None
        if training.recommended_intensity != TrainingIntensity.REST:
            workout = self._generate_workout(context, training)

        # Create daily summary
        daily_summary = f"{readiness.summary} {training.rationale} {recovery.guidance}"

        return CompleteRecommendation(
            readiness=readiness,
            training=training,
            recovery=recovery,
            workout=workout,
            daily_summary=daily_summary
        )

    def _generate_workout(
        self,
        context: ReadinessContext,
        training_rec: TrainingRecommendation
    ) -> WorkoutRecommendation:
        """Generate specific workout recommendation."""
        # Use mock implementation for now
        # TODO: Implement AI-powered workout generation
        from tests.mocks.mock_claude_service import MockClaudeService
        mock = MockClaudeService()
        return mock.recommend_workout(context, training_rec)

    # ========================================================================
    # PROMPT BUILDERS
    # ========================================================================

    def _build_readiness_system_prompt(self) -> str:
        """Build system prompt for readiness analysis."""
        return """You are an expert sports scientist and coach specializing in training readiness assessment.

Your role is to analyze physiological metrics and provide evidence-based readiness assessments.

Key principles:
- HRV (Heart Rate Variability) is a primary indicator of recovery status
- Sleep quality and duration significantly impact readiness
- Training load must be balanced with recovery capacity
- Individual variation is important - context matters

Provide assessments that are:
- Evidence-based and scientifically sound
- Practical and actionable
- Honest and realistic
- Focused on long-term athlete development"""

    def _build_readiness_user_message(self, context: ReadinessContext) -> str:
        """Build user message for readiness analysis."""
        message = f"""Analyze training readiness for date: {context.analysis_date}

Current Metrics:
"""
        if context.hrv_current:
            message += f"- HRV: {context.hrv_current:.1f} ms"
            if context.hrv_baseline_7d:
                pct = (context.hrv_current / context.hrv_baseline_7d) * 100
                message += f" ({pct:.1f}% of 7-day baseline: {context.hrv_baseline_7d:.1f} ms)\n"
            else:
                message += "\n"

        if context.sleep_last_night:
            hours = context.sleep_last_night / 60
            message += f"- Sleep: {hours:.1f} hours last night"
            if context.sleep_average_7d:
                avg_hours = context.sleep_average_7d / 60
                message += f" (7-day avg: {avg_hours:.1f} hours)\n"
            else:
                message += "\n"

        if context.training_load_7d:
            message += f"- Training Load (7d): {context.training_load_7d}\n"

        if context.acwr:
            message += f"- Acute:Chronic Workload Ratio: {context.acwr:.2f}\n"

        if context.resting_heart_rate:
            message += f"- Resting Heart Rate: {context.resting_heart_rate} bpm\n"

        if context.consecutive_hard_days:
            message += f"- Consecutive hard training days: {context.consecutive_hard_days}\n"

        message += """
Provide a readiness assessment in the following JSON format:
{
    "readiness_score": <0-100>,
    "readiness_level": "<optimal|good|moderate|low|poor>",
    "hrv_score": <0-100 or null>,
    "sleep_score": <0-100 or null>,
    "load_score": <0-100 or null>,
    "key_factors": ["factor1", "factor2", ...],
    "positive_indicators": ["indicator1", ...],
    "concerns": ["concern1", ...],
    "summary": "Plain English summary",
    "confidence": <0.0-1.0>
}"""

        return message

    def _build_training_system_prompt(self) -> str:
        """Build system prompt for training recommendations."""
        return """You are an expert endurance coach specializing in training periodization and adaptation.

Your role is to recommend appropriate training based on readiness and training load.

Key principles:
- Training should match current readiness and recovery status
- Progressive overload must be balanced with adequate recovery
- Quality training is more important than quantity
- Individual response to training varies

Provide recommendations that are:
- Specific and actionable
- Aligned with readiness status
- Safe and sustainable
- Focused on long-term development"""

    def _build_training_user_message(
        self,
        context: ReadinessContext,
        readiness: ReadinessAnalysis
    ) -> str:
        """Build user message for training recommendation."""
        message = f"""Based on the following readiness assessment, recommend training for {context.analysis_date}:

Readiness: {readiness.readiness_level.value} (score: {readiness.readiness_score:.1f})
Key factors: {', '.join(readiness.key_factors)}
"""

        if readiness.concerns:
            message += f"Concerns: {', '.join(readiness.concerns)}\n"

        message += """
Provide training recommendation in JSON format:
{
    "recommended_intensity": "<high|moderate|low|rest>",
    "recommended_duration_minutes": <integer or null>,
    "workout_types": ["type1", "type2"],
    "training_focus": "description",
    "key_considerations": ["consideration1", ...],
    "avoid_list": ["avoid1", ...],
    "rationale": "explanation",
    "confidence": <0.0-1.0>
}"""

        return message

    def _build_recovery_system_prompt(self) -> str:
        """Build system prompt for recovery recommendations."""
        return """You are an expert in recovery science and athlete monitoring.

Your role is to provide evidence-based recovery guidance to optimize adaptation.

Key principles:
- Recovery is where adaptation happens
- Sleep is the most important recovery modality
- Active recovery has value when appropriate
- Individual recovery needs vary

Provide recommendations that are:
- Evidence-based
- Practical and achievable
- Prioritized by importance
- Supportive of long-term health"""

    def _build_recovery_user_message(
        self,
        context: ReadinessContext,
        readiness: ReadinessAnalysis
    ) -> str:
        """Build user message for recovery recommendation."""
        message = f"""Based on readiness assessment, recommend recovery strategies:

Readiness: {readiness.readiness_level.value} (score: {readiness.readiness_score:.1f})
"""

        if readiness.concerns:
            message += f"Concerns: {', '.join(readiness.concerns)}\n"

        message += """
Provide recovery recommendation in JSON format:
{
    "recovery_priority": "<high|moderate|low>",
    "sleep_target_hours": <float or null>,
    "rest_days_needed": <integer or null>,
    "recovery_strategies": ["strategy1", ...],
    "nutrition_focus": ["focus1", ...],
    "warning_signs": ["sign1", ...],
    "guidance": "overall guidance",
    "confidence": <0.0-1.0>
}"""

        return message

    # ========================================================================
    # RESPONSE PARSERS
    # ========================================================================

    def _parse_readiness_response(
        self,
        response: str,
        context: ReadinessContext
    ) -> ReadinessAnalysis:
        """Parse readiness analysis response."""
        import json

        try:
            # Extract JSON from response
            # Claude may wrap JSON in markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            return ReadinessAnalysis(
                user_id=context.user_id,
                analysis_date=context.analysis_date,
                readiness_score=float(data["readiness_score"]),
                readiness_level=ReadinessLevel(data["readiness_level"]),
                hrv_score=data.get("hrv_score"),
                sleep_score=data.get("sleep_score"),
                load_score=data.get("load_score"),
                key_factors=data.get("key_factors", []),
                positive_indicators=data.get("positive_indicators", []),
                concerns=data.get("concerns", []),
                summary=data["summary"],
                confidence=float(data.get("confidence", 0.8)),
                model_version=self.model,
                timestamp=datetime.now()
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse readiness response: {e}")
            raise ClaudeValidationError(f"Invalid response format: {e}")

    def _parse_training_response(
        self,
        response: str,
        context: ReadinessContext
    ) -> TrainingRecommendation:
        """Parse training recommendation response."""
        import json

        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            workout_types = [WorkoutType(wt) for wt in data.get("workout_types", [])]

            return TrainingRecommendation(
                user_id=context.user_id,
                recommendation_date=context.analysis_date,
                recommended_intensity=TrainingIntensity(data["recommended_intensity"]),
                recommended_duration_minutes=data.get("recommended_duration_minutes"),
                workout_types=workout_types,
                training_focus=data["training_focus"],
                key_considerations=data.get("key_considerations", []),
                avoid_list=data.get("avoid_list", []),
                rationale=data["rationale"],
                confidence=float(data.get("confidence", 0.8)),
                model_version=self.model,
                timestamp=datetime.now()
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse training response: {e}")
            raise ClaudeValidationError(f"Invalid response format: {e}")

    def _parse_recovery_response(
        self,
        response: str,
        context: ReadinessContext
    ) -> RecoveryRecommendation:
        """Parse recovery recommendation response."""
        import json

        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            return RecoveryRecommendation(
                user_id=context.user_id,
                recommendation_date=context.analysis_date,
                recovery_priority=data["recovery_priority"],
                sleep_target_hours=data.get("sleep_target_hours"),
                rest_days_needed=data.get("rest_days_needed"),
                recovery_strategies=data.get("recovery_strategies", []),
                nutrition_focus=data.get("nutrition_focus", []),
                warning_signs=data.get("warning_signs", []),
                guidance=data["guidance"],
                confidence=float(data.get("confidence", 0.8)),
                model_version=self.model,
                timestamp=datetime.now()
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse recovery response: {e}")
            raise ClaudeValidationError(f"Invalid response format: {e}")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_usage_stats(self) -> dict:
        """Get API usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "average_tokens_per_request": (
                self.total_tokens / self.total_requests
                if self.total_requests > 0
                else 0
            )
        }

    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
