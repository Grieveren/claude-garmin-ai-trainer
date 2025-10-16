"""
Mock Claude AI service for testing.

Provides realistic AI responses without making actual API calls.
Responses are deterministic and based on input context patterns.
"""

from datetime import datetime, date
from typing import Optional
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


class MockClaudeService:
    """
    Mock implementation of ClaudeService for testing.

    Provides deterministic responses based on input patterns:
    - HRV >= 90% baseline → OPTIMAL/GOOD readiness
    - HRV 80-90% baseline → MODERATE readiness
    - HRV < 80% baseline → LOW/POOR readiness
    - ACWR > 1.5 → Suggests rest/recovery
    - Sleep < 6 hours → Reduces readiness
    """

    def __init__(self, api_key: str = "mock_key", rate_limit: int = 50):
        """Initialize mock service."""
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.call_count = 0
        self.failure_mode = False
        self.model_version = "claude-3-5-sonnet-20241022"

    def set_failure_mode(self, enabled: bool):
        """Enable/disable failure mode for testing error handling."""
        self.failure_mode = enabled

    def analyze_readiness(
        self,
        context: ReadinessContext
    ) -> ReadinessAnalysis:
        """
        Analyze readiness and provide recommendations.

        Returns deterministic responses based on context metrics.
        """
        self.call_count += 1

        if self.failure_mode:
            raise Exception("Mock API failure")

        # Calculate readiness score based on context
        readiness_score = self._calculate_mock_readiness_score(context)
        readiness_level = self._determine_readiness_level(readiness_score)

        # Generate component scores
        hrv_score = self._calculate_hrv_score(context)
        sleep_score = self._calculate_sleep_score(context)
        load_score = self._calculate_load_score(context)

        # Generate insights
        key_factors = self._generate_key_factors(context)
        positive_indicators = self._generate_positive_indicators(context)
        concerns = self._generate_concerns(context)

        # Generate summary
        summary = self._generate_summary(context, readiness_level)

        return ReadinessAnalysis(
            user_id=context.user_id,
            analysis_date=context.analysis_date,
            readiness_score=readiness_score,
            readiness_level=readiness_level,
            hrv_score=hrv_score,
            sleep_score=sleep_score,
            load_score=load_score,
            key_factors=key_factors,
            positive_indicators=positive_indicators,
            concerns=concerns,
            summary=summary,
            confidence=0.85,
            model_version=self.model_version,
            timestamp=datetime.now()
        )

    def recommend_training(
        self,
        context: ReadinessContext,
        readiness: ReadinessAnalysis
    ) -> TrainingRecommendation:
        """Generate training recommendations based on readiness."""
        self.call_count += 1

        if self.failure_mode:
            raise Exception("Mock API failure")

        # Determine intensity based on readiness
        intensity = self._determine_training_intensity(readiness.readiness_level, context)

        # Determine duration
        duration = self._determine_duration(intensity, context)

        # Determine workout types
        workout_types = self._determine_workout_types(intensity, readiness.readiness_level)

        # Generate guidance
        training_focus = self._generate_training_focus(intensity, context)
        key_considerations = self._generate_training_considerations(intensity, context)
        avoid_list = self._generate_avoid_list(intensity, context)
        rationale = self._generate_training_rationale(intensity, readiness, context)

        return TrainingRecommendation(
            user_id=context.user_id,
            recommendation_date=context.analysis_date,
            recommended_intensity=intensity,
            recommended_duration_minutes=duration,
            workout_types=workout_types,
            training_focus=training_focus,
            key_considerations=key_considerations,
            avoid_list=avoid_list,
            rationale=rationale,
            confidence=0.82,
            model_version=self.model_version,
            timestamp=datetime.now()
        )

    def recommend_recovery(
        self,
        context: ReadinessContext,
        readiness: ReadinessAnalysis
    ) -> RecoveryRecommendation:
        """Generate recovery recommendations."""
        self.call_count += 1

        if self.failure_mode:
            raise Exception("Mock API failure")

        # Determine recovery priority
        recovery_priority = self._determine_recovery_priority(readiness.readiness_level, context)

        # Sleep target
        sleep_target = 8.0 if recovery_priority in ["high", "moderate"] else 7.5

        # Rest days needed
        rest_days = self._determine_rest_days_needed(context, readiness.readiness_level)

        # Recovery strategies
        recovery_strategies = self._generate_recovery_strategies(recovery_priority, context)

        # Nutrition focus
        nutrition_focus = self._generate_nutrition_focus(recovery_priority)

        # Warning signs
        warning_signs = self._generate_warning_signs(context, readiness.readiness_level)

        # Guidance
        guidance = self._generate_recovery_guidance(recovery_priority, rest_days, context)

        return RecoveryRecommendation(
            user_id=context.user_id,
            recommendation_date=context.analysis_date,
            recovery_priority=recovery_priority,
            sleep_target_hours=sleep_target,
            rest_days_needed=rest_days,
            recovery_strategies=recovery_strategies,
            nutrition_focus=nutrition_focus,
            warning_signs=warning_signs,
            guidance=guidance,
            confidence=0.80,
            model_version=self.model_version,
            timestamp=datetime.now()
        )

    def recommend_workout(
        self,
        context: ReadinessContext,
        training_rec: TrainingRecommendation
    ) -> Optional[WorkoutRecommendation]:
        """Generate specific workout recommendation."""
        self.call_count += 1

        if self.failure_mode:
            raise Exception("Mock API failure")

        # Don't generate workout for rest days
        if training_rec.recommended_intensity == TrainingIntensity.REST:
            return None

        # Determine workout type
        workout_type = training_rec.workout_types[0] if training_rec.workout_types else WorkoutType.ENDURANCE

        # Calculate durations
        total_duration = training_rec.recommended_duration_minutes or 45
        warmup = max(10, int(total_duration * 0.2))
        cooldown = max(5, int(total_duration * 0.1))
        main = total_duration - warmup - cooldown

        # Generate workout details
        target_hr_zone = self._generate_hr_zone(training_rec.recommended_intensity)
        target_pace = self._generate_pace_description(training_rec.recommended_intensity)
        perceived_effort = self._generate_perceived_effort(training_rec.recommended_intensity)

        workout_description = self._generate_workout_description(
            workout_type,
            training_rec.recommended_intensity,
            total_duration
        )

        key_points = self._generate_workout_key_points(
            workout_type,
            training_rec.recommended_intensity
        )

        success_metrics = self._generate_success_metrics(
            training_rec.recommended_intensity,
            workout_type
        )

        return WorkoutRecommendation(
            user_id=context.user_id,
            workout_date=context.analysis_date,
            workout_type=workout_type,
            total_duration_minutes=total_duration,
            warmup_duration=warmup,
            main_duration=main,
            cooldown_duration=cooldown,
            target_heart_rate_zone=target_hr_zone,
            target_pace=target_pace,
            perceived_effort=perceived_effort,
            workout_description=workout_description,
            key_points=key_points,
            success_metrics=success_metrics,
            confidence=0.85,
            model_version=self.model_version,
            timestamp=datetime.now()
        )

    def get_complete_recommendation(
        self,
        context: ReadinessContext
    ) -> CompleteRecommendation:
        """Generate complete set of recommendations."""
        readiness = self.analyze_readiness(context)
        training = self.recommend_training(context, readiness)
        recovery = self.recommend_recovery(context, readiness)
        workout = self.recommend_workout(context, training)

        daily_summary = self._generate_daily_summary(
            readiness,
            training,
            recovery
        )

        return CompleteRecommendation(
            readiness=readiness,
            training=training,
            recovery=recovery,
            workout=workout,
            daily_summary=daily_summary
        )

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _calculate_mock_readiness_score(self, context: ReadinessContext) -> float:
        """Calculate mock readiness score based on context."""
        # Start with base score - use 60 if we have recent activities (suggests active training)
        # Use 70 if no activity data (suggests recovery/rest period)
        if context.recent_activities and len(context.recent_activities) > 0:
            score = 60.0  # Lower base for active athletes
        else:
            score = 70.0  # Normal base for those with less data

        # HRV contribution (strongest signal)
        if context.hrv_percent_of_baseline is not None:
            if context.hrv_percent_of_baseline >= 95:
                score += 15
            elif context.hrv_percent_of_baseline >= 85:
                score += 10
            elif context.hrv_percent_of_baseline >= 75:
                score += 5
            elif context.hrv_percent_of_baseline < 80:
                # Very low HRV is a major red flag
                score -= 20
            else:
                score -= 10
        # If no HRV baseline but we have current HRV, use absolute value
        elif context.hrv_current is not None:
            if context.hrv_current < 45:  # Very low absolute HRV
                score -= 25
            elif context.hrv_current < 55:  # Low absolute HRV
                score -= 15

        # Sleep contribution
        if context.sleep_last_night is not None:
            if context.sleep_last_night >= 480:  # 8+ hours
                score += 10
            elif context.sleep_last_night >= 420:  # 7-8 hours
                score += 5
            elif context.sleep_last_night < 360:  # < 6 hours
                score -= 15
            elif context.sleep_last_night < 400:  # 6-7 hours
                score -= 8

        # Training load contribution
        if context.acwr is not None:
            if 0.8 <= context.acwr <= 1.3:
                score += 5
            elif context.acwr > 1.5:
                score -= 20  # Increased penalty for high ACWR
            elif context.acwr < 0.7:
                score -= 5

        # Consecutive hard days
        if context.consecutive_hard_days and context.consecutive_hard_days > 3:
            score -= context.consecutive_hard_days * 3

        # Days since last rest (high value means need rest soon)
        if context.days_since_last_rest is not None:
            if context.days_since_last_rest >= 7:
                score -= 15  # 7+ days without rest
            elif context.days_since_last_rest >= 5:
                score -= 8  # 5-6 days without rest

        # Check recent activities for high volume
        if context.recent_activities:
            # Count days with significant training (>60 min or >10km)
            hard_days = 0
            for activity in context.recent_activities:
                duration = activity.get('duration_minutes', 0) or 0
                # distance can be in meters or km depending on source
                distance = activity.get('distance', 0) or activity.get('distance_meters', 0) or 0

                # Convert distance to meters if it's in km (< 1000 means it's in km)
                if distance > 0 and distance < 1000:
                    distance = distance * 1000

                if duration >= 60 or distance >= 10000:
                    hard_days += 1

            # If 4+ hard days in recent activities, penalize
            if hard_days >= 4:
                score -= (hard_days - 3) * 5  # -5 points per day over 3

            # Extra penalty for 7 consecutive hard days (no rest)
            if hard_days >= 7:
                score -= 10  # Additional penalty for no rest

        # Resting heart rate (if elevated significantly)
        if context.resting_heart_rate and context.rhr_baseline_7d:
            hr_diff = context.resting_heart_rate - context.rhr_baseline_7d
            if hr_diff > 5:
                score -= hr_diff * 2  # -2 points per bpm over baseline

        return max(0.0, min(100.0, score))

    def _determine_readiness_level(self, score: float) -> ReadinessLevel:
        """Determine readiness level from score."""
        if score >= 85:
            return ReadinessLevel.OPTIMAL
        elif score >= 70:
            return ReadinessLevel.GOOD
        elif score >= 55:
            return ReadinessLevel.MODERATE
        elif score >= 40:
            return ReadinessLevel.LOW
        else:
            return ReadinessLevel.POOR

    def _calculate_hrv_score(self, context: ReadinessContext) -> Optional[float]:
        """Calculate HRV component score."""
        if context.hrv_percent_of_baseline is None:
            return None

        if context.hrv_percent_of_baseline >= 95:
            return 90.0
        elif context.hrv_percent_of_baseline >= 85:
            return 75.0
        elif context.hrv_percent_of_baseline >= 75:
            return 60.0
        else:
            return 40.0

    def _calculate_sleep_score(self, context: ReadinessContext) -> Optional[float]:
        """Calculate sleep component score."""
        if context.sleep_last_night is None:
            return None

        hours = context.sleep_last_night / 60
        if hours >= 8:
            return 90.0
        elif hours >= 7:
            return 75.0
        elif hours >= 6:
            return 60.0
        else:
            return 40.0

    def _calculate_load_score(self, context: ReadinessContext) -> Optional[float]:
        """Calculate training load component score."""
        if context.acwr is None:
            return None

        if 0.8 <= context.acwr <= 1.3:
            return 85.0
        elif context.acwr > 1.5:
            return 40.0
        else:
            return 65.0

    def _generate_key_factors(self, context: ReadinessContext) -> list[str]:
        """Generate key factors affecting readiness."""
        factors = []

        if context.hrv_percent_of_baseline is not None:
            if context.hrv_percent_of_baseline < 90:
                factors.append(f"HRV at {context.hrv_percent_of_baseline:.1f}% of baseline")
            else:
                factors.append("HRV within optimal range")

        if context.sleep_last_night is not None:
            hours = context.sleep_last_night / 60
            if hours < 7:
                factors.append(f"Limited sleep ({hours:.1f} hours)")
            else:
                factors.append(f"Good sleep duration ({hours:.1f} hours)")

        if context.acwr is not None:
            if context.acwr > 1.3:
                factors.append(f"Elevated ACWR ({context.acwr:.2f})")
            else:
                factors.append("Training load in optimal range")

        return factors

    def _generate_positive_indicators(self, context: ReadinessContext) -> list[str]:
        """Generate positive indicators."""
        indicators = []

        if context.hrv_percent_of_baseline and context.hrv_percent_of_baseline >= 95:
            indicators.append("Strong HRV recovery")

        if context.sleep_last_night and context.sleep_last_night >= 480:
            indicators.append("Excellent sleep duration")

        if context.acwr and 0.8 <= context.acwr <= 1.3:
            indicators.append("Optimal acute:chronic workload ratio")

        if context.consecutive_hard_days and context.consecutive_hard_days <= 2:
            indicators.append("Adequate recovery between hard sessions")

        return indicators

    def _generate_concerns(self, context: ReadinessContext) -> list[str]:
        """Generate areas of concern."""
        concerns = []

        # Check HRV - both baseline percent and absolute value
        if context.hrv_percent_of_baseline and context.hrv_percent_of_baseline < 80:
            concerns.append("HRV significantly below baseline")
        elif context.hrv_current and context.hrv_current < 50:
            concerns.append("Very low HRV indicating poor recovery")

        # Check sleep
        if context.sleep_last_night and context.sleep_last_night < 360:
            concerns.append("Insufficient sleep for recovery")
        elif context.sleep_last_night and context.sleep_last_night < 400:
            concerns.append("Sub-optimal sleep duration")

        # Check training load
        if context.acwr and context.acwr > 1.5:
            concerns.append("High training load relative to fitness")

        # Check consecutive hard days
        if context.consecutive_hard_days and context.consecutive_hard_days > 3:
            concerns.append("Extended period without adequate recovery")

        # Check resting heart rate elevation
        if context.resting_heart_rate and context.rhr_baseline_7d:
            hr_diff = context.resting_heart_rate - context.rhr_baseline_7d
            if hr_diff > 5:
                concerns.append(f"Elevated resting heart rate (+{hr_diff:.0f} bpm)")

        return concerns

    def _generate_summary(self, context: ReadinessContext, level: ReadinessLevel) -> str:
        """Generate human-readable summary."""
        summaries = {
            ReadinessLevel.OPTIMAL: "You're in excellent shape for training today. All key metrics indicate strong readiness.",
            ReadinessLevel.GOOD: "You're in good shape for training today. Most metrics are positive with minor areas to monitor.",
            ReadinessLevel.MODERATE: "You're moderately ready for training. Consider lighter intensity or shorter duration.",
            ReadinessLevel.LOW: "Your readiness is low today. Focus on recovery activities or take a rest day.",
            ReadinessLevel.POOR: "Your body needs rest. Take a rest day or limit activity to very light movement."
        }
        return summaries[level]

    def _determine_training_intensity(
        self,
        readiness_level: ReadinessLevel,
        context: ReadinessContext
    ) -> TrainingIntensity:
        """Determine appropriate training intensity."""
        if readiness_level == ReadinessLevel.OPTIMAL:
            return TrainingIntensity.HIGH
        elif readiness_level == ReadinessLevel.GOOD:
            return TrainingIntensity.MODERATE
        elif readiness_level == ReadinessLevel.MODERATE:
            return TrainingIntensity.LOW
        else:
            return TrainingIntensity.REST

    def _determine_duration(
        self,
        intensity: TrainingIntensity,
        context: ReadinessContext
    ) -> Optional[int]:
        """Determine training duration."""
        durations = {
            TrainingIntensity.HIGH: 60,
            TrainingIntensity.MODERATE: 45,
            TrainingIntensity.LOW: 30,
            TrainingIntensity.REST: None
        }
        return durations.get(intensity)

    def _determine_workout_types(
        self,
        intensity: TrainingIntensity,
        readiness_level: ReadinessLevel
    ) -> list[WorkoutType]:
        """Determine appropriate workout types."""
        if intensity == TrainingIntensity.HIGH:
            return [WorkoutType.INTERVAL, WorkoutType.TEMPO]
        elif intensity == TrainingIntensity.MODERATE:
            return [WorkoutType.ENDURANCE, WorkoutType.TEMPO]
        elif intensity == TrainingIntensity.LOW:
            return [WorkoutType.RECOVERY]
        else:
            return [WorkoutType.REST]

    def _generate_training_focus(self, intensity: TrainingIntensity, context: ReadinessContext) -> str:
        """Generate training focus description."""
        focuses = {
            TrainingIntensity.HIGH: "High-intensity work with full recovery between intervals",
            TrainingIntensity.MODERATE: "Aerobic base building and endurance development",
            TrainingIntensity.LOW: "Active recovery and movement quality",
            TrainingIntensity.REST: "Complete rest and recovery"
        }
        return focuses.get(intensity, "General fitness maintenance")

    def _generate_training_considerations(
        self,
        intensity: TrainingIntensity,
        context: ReadinessContext
    ) -> list[str]:
        """Generate training considerations."""
        if intensity == TrainingIntensity.HIGH:
            return [
                "Ensure proper warmup",
                "Monitor fatigue during workout",
                "Be prepared to adjust if feeling off"
            ]
        elif intensity == TrainingIntensity.MODERATE:
            return [
                "Maintain comfortable pace",
                "Focus on form and technique",
                "Stay in aerobic zones"
            ]
        else:
            return [
                "Keep intensity very light",
                "Focus on movement and circulation",
                "Prioritize how you feel"
            ]

    def _generate_avoid_list(
        self,
        intensity: TrainingIntensity,
        context: ReadinessContext
    ) -> list[str]:
        """Generate list of things to avoid."""
        if intensity == TrainingIntensity.REST:
            return ["All structured training", "High intensity activity"]
        elif intensity == TrainingIntensity.LOW:
            return ["High intensity intervals", "Long duration sessions", "Heavy strength work"]
        elif intensity == TrainingIntensity.MODERATE:
            return ["Maximum efforts", "Very long duration"]
        else:
            return ["Overextending beyond planned work"]

    def _generate_training_rationale(
        self,
        intensity: TrainingIntensity,
        readiness: ReadinessAnalysis,
        context: ReadinessContext
    ) -> str:
        """Generate training rationale."""
        return f"Based on your {readiness.readiness_level.value} readiness level and current metrics, {intensity.value} intensity training is recommended to optimize adaptation while managing fatigue."

    def _determine_recovery_priority(
        self,
        readiness_level: ReadinessLevel,
        context: ReadinessContext
    ) -> str:
        """Determine recovery priority."""
        if readiness_level in [ReadinessLevel.POOR, ReadinessLevel.LOW]:
            return "high"
        elif readiness_level == ReadinessLevel.MODERATE:
            return "moderate"
        else:
            return "low"

    def _determine_rest_days_needed(
        self,
        context: ReadinessContext,
        readiness_level: ReadinessLevel
    ) -> Optional[int]:
        """Determine number of rest days needed."""
        if readiness_level == ReadinessLevel.POOR:
            return 2
        elif readiness_level == ReadinessLevel.LOW:
            return 1
        elif context.consecutive_hard_days and context.consecutive_hard_days > 4:
            return 1
        else:
            return 0

    def _generate_recovery_strategies(self, priority: str, context: ReadinessContext) -> list[str]:
        """Generate recovery strategies."""
        if priority == "high":
            return [
                "Complete rest or very light activity only",
                "Focus on sleep quality and duration",
                "Consider massage or bodywork",
                "Hydration and nutrition focus"
            ]
        elif priority == "moderate":
            return [
                "Active recovery activities (walking, easy cycling)",
                "Stretching and mobility work",
                "Adequate sleep (7-8 hours)",
                "Proper nutrition timing"
            ]
        else:
            return [
                "Regular stretching routine",
                "Maintain sleep consistency",
                "Stay hydrated"
            ]

    def _generate_nutrition_focus(self, priority: str) -> list[str]:
        """Generate nutrition focus areas."""
        if priority == "high":
            return [
                "Adequate protein for repair (1.6-2.2g/kg)",
                "Anti-inflammatory foods",
                "Hydration with electrolytes",
                "Sufficient carbohydrates"
            ]
        else:
            return [
                "Balanced macronutrients",
                "Adequate protein intake",
                "Proper hydration"
            ]

    def _generate_warning_signs(
        self,
        context: ReadinessContext,
        readiness_level: ReadinessLevel
    ) -> list[str]:
        """Generate warning signs to watch for."""
        signs = [
            "Persistent fatigue that doesn't improve with rest",
            "Elevated resting heart rate (>5 bpm above baseline)",
            "Mood changes or irritability",
            "Decreased motivation for training"
        ]

        if readiness_level in [ReadinessLevel.LOW, ReadinessLevel.POOR]:
            signs.extend([
                "Ongoing sleep disturbances",
                "Loss of appetite",
                "Increased illness susceptibility"
            ])

        return signs

    def _generate_recovery_guidance(
        self,
        priority: str,
        rest_days: Optional[int],
        context: ReadinessContext
    ) -> str:
        """Generate recovery guidance."""
        if priority == "high":
            return f"Your body needs significant recovery. Take {rest_days or 2} full rest days and focus on sleep and nutrition."
        elif priority == "moderate":
            return f"Moderate recovery focus is needed. Consider a rest day within the next {rest_days or 2} days."
        else:
            return "Continue with normal recovery practices between training sessions."

    def _generate_hr_zone(self, intensity: TrainingIntensity) -> str:
        """Generate heart rate zone description."""
        zones = {
            TrainingIntensity.HIGH: "Zone 4-5 (80-95% max HR)",
            TrainingIntensity.MODERATE: "Zone 2-3 (65-80% max HR)",
            TrainingIntensity.LOW: "Zone 1-2 (50-70% max HR)",
            TrainingIntensity.REST: "N/A"
        }
        return zones.get(intensity, "Zone 2")

    def _generate_pace_description(self, intensity: TrainingIntensity) -> str:
        """Generate pace description."""
        paces = {
            TrainingIntensity.HIGH: "Hard effort, challenging pace",
            TrainingIntensity.MODERATE: "Comfortable, conversational pace",
            TrainingIntensity.LOW: "Easy, recovery pace",
            TrainingIntensity.REST: "N/A"
        }
        return paces.get(intensity, "Easy pace")

    def _generate_perceived_effort(self, intensity: TrainingIntensity) -> str:
        """Generate perceived effort description."""
        efforts = {
            TrainingIntensity.HIGH: "8-9 out of 10",
            TrainingIntensity.MODERATE: "5-6 out of 10",
            TrainingIntensity.LOW: "3-4 out of 10",
            TrainingIntensity.REST: "1 out of 10"
        }
        return efforts.get(intensity, "5 out of 10")

    def _generate_workout_description(
        self,
        workout_type: WorkoutType,
        intensity: TrainingIntensity,
        duration: int
    ) -> str:
        """Generate workout description."""
        descriptions = {
            WorkoutType.ENDURANCE: f"Steady endurance session at {intensity.value} intensity for {duration} minutes",
            WorkoutType.TEMPO: f"Tempo run with sustained moderate-hard effort for {duration} minutes",
            WorkoutType.INTERVAL: f"Interval session with high-intensity work and recovery periods over {duration} minutes",
            WorkoutType.RECOVERY: f"Easy recovery session for {duration} minutes focusing on movement quality",
            WorkoutType.STRENGTH: f"Strength training session for {duration} minutes"
        }
        return descriptions.get(workout_type, f"Training session for {duration} minutes")

    def _generate_workout_key_points(
        self,
        workout_type: WorkoutType,
        intensity: TrainingIntensity
    ) -> list[str]:
        """Generate workout key execution points."""
        if workout_type == WorkoutType.INTERVAL:
            return [
                "Proper warmup is critical",
                "Focus on quality over quantity",
                "Take full recovery between intervals",
                "Cut session short if form deteriorates"
            ]
        elif workout_type == WorkoutType.ENDURANCE:
            return [
                "Start conservatively",
                "Maintain steady effort throughout",
                "Focus on breathing rhythm",
                "Stay in target heart rate zone"
            ]
        else:
            return [
                "Keep effort very light",
                "Focus on form and technique",
                "Enjoy the movement",
                "Listen to your body"
            ]

    def _generate_success_metrics(
        self,
        intensity: TrainingIntensity,
        workout_type: WorkoutType
    ) -> list[str]:
        """Generate success metrics for workout."""
        if intensity == TrainingIntensity.HIGH:
            return [
                "Completed all planned intervals",
                "Maintained target intensities",
                "Felt challenged but controlled",
                "Good recovery after session"
            ]
        elif intensity == TrainingIntensity.MODERATE:
            return [
                "Maintained comfortable pace throughout",
                "Stayed in target heart rate zone",
                "Could hold conversation",
                "Felt energized after"
            ]
        else:
            return [
                "Kept effort very light",
                "No signs of strain or fatigue",
                "Felt refreshed after",
                "Maintained good form"
            ]

    def _generate_daily_summary(
        self,
        readiness: ReadinessAnalysis,
        training: TrainingRecommendation,
        recovery: RecoveryRecommendation
    ) -> str:
        """Generate overall daily summary."""
        return f"{readiness.summary} Recommended intensity: {training.recommended_intensity.value}. {recovery.guidance}"
