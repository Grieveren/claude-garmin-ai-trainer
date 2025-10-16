"""
User profile models for athlete data and training configuration.

Includes heart rate zones, training goals, and athlete metrics.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class Gender(str, Enum):
    """Athlete gender for physiological calculations"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class TrainingGoalType(str, Enum):
    """Types of training goals"""
    RACE = "race"
    FITNESS = "fitness"
    WEIGHT_LOSS = "weight_loss"
    ENDURANCE = "endurance"
    SPEED = "speed"
    STRENGTH = "strength"
    RECOVERY = "recovery"
    MAINTENANCE = "maintenance"


class HeartRateZones(BaseModel):
    """
    Heart rate training zones based on maximum heart rate.

    Zones follow the 5-zone model commonly used in endurance training:
    - Zone 1 (Recovery): 50-60% max HR - Active recovery, warm-up
    - Zone 2 (Easy): 60-70% max HR - Base aerobic training
    - Zone 3 (Moderate): 70-80% max HR - Aerobic endurance
    - Zone 4 (Threshold): 80-90% max HR - Lactate threshold training
    - Zone 5 (Max): 90-100% max HR - VO2 max, high intensity
    """

    max_heart_rate: int = Field(..., ge=100, le=220, description="Maximum heart rate")
    resting_heart_rate: int = Field(..., ge=30, le=100, description="Resting heart rate")

    # Zone boundaries (calculated)
    zone1_min: int = Field(default=0, description="Zone 1 minimum HR")
    zone1_max: int = Field(default=0, description="Zone 1 maximum HR")
    zone2_min: int = Field(default=0, description="Zone 2 minimum HR")
    zone2_max: int = Field(default=0, description="Zone 2 maximum HR")
    zone3_min: int = Field(default=0, description="Zone 3 minimum HR")
    zone3_max: int = Field(default=0, description="Zone 3 maximum HR")
    zone4_min: int = Field(default=0, description="Zone 4 minimum HR")
    zone4_max: int = Field(default=0, description="Zone 4 maximum HR")
    zone5_min: int = Field(default=0, description="Zone 5 minimum HR")
    zone5_max: int = Field(default=0, description="Zone 5 maximum HR")

    def __init__(self, **data):
        """Initialize and calculate zones"""
        super().__init__(**data)
        self._calculate_zones()

    def _calculate_zones(self) -> None:
        """Calculate heart rate zones based on max HR"""
        max_hr = self.max_heart_rate

        # Zone 1: 50-60% (Recovery)
        self.zone1_min = round(max_hr * 0.50)
        self.zone1_max = round(max_hr * 0.60)

        # Zone 2: 60-70% (Easy aerobic)
        self.zone2_min = self.zone1_max + 1
        self.zone2_max = round(max_hr * 0.70)

        # Zone 3: 70-80% (Moderate aerobic)
        self.zone3_min = self.zone2_max + 1
        self.zone3_max = round(max_hr * 0.80)

        # Zone 4: 80-90% (Threshold)
        self.zone4_min = self.zone3_max + 1
        self.zone4_max = round(max_hr * 0.90)

        # Zone 5: 90-100% (VO2 max)
        self.zone5_min = self.zone4_max + 1
        self.zone5_max = max_hr

    @property
    def hr_reserve(self) -> int:
        """Heart rate reserve (Karvonen method)"""
        return self.max_heart_rate - self.resting_heart_rate

    def get_zone(self, heart_rate: int) -> int:
        """
        Determine which zone a heart rate falls into.

        Args:
            heart_rate: Heart rate in bpm

        Returns:
            int: Zone number (1-5), or 0 if below zone 1
        """
        if heart_rate < self.zone1_min:
            return 0
        elif heart_rate <= self.zone1_max:
            return 1
        elif heart_rate <= self.zone2_max:
            return 2
        elif heart_rate <= self.zone3_max:
            return 3
        elif heart_rate <= self.zone4_max:
            return 4
        else:
            return 5

    def get_zone_range(self, zone: int) -> tuple[int, int]:
        """
        Get the heart rate range for a specific zone.

        Args:
            zone: Zone number (1-5)

        Returns:
            tuple: (min_hr, max_hr) for the zone

        Raises:
            ValueError: If zone is not 1-5
        """
        if zone == 1:
            return (self.zone1_min, self.zone1_max)
        elif zone == 2:
            return (self.zone2_min, self.zone2_max)
        elif zone == 3:
            return (self.zone3_min, self.zone3_max)
        elif zone == 4:
            return (self.zone4_min, self.zone4_max)
        elif zone == 5:
            return (self.zone5_min, self.zone5_max)
        else:
            raise ValueError(f"Invalid zone {zone}. Must be 1-5.")

    def get_zone_name(self, zone: int) -> str:
        """
        Get the descriptive name for a zone.

        Args:
            zone: Zone number (1-5)

        Returns:
            str: Zone name
        """
        zone_names = {
            0: "Below Zone 1",
            1: "Zone 1 - Recovery",
            2: "Zone 2 - Easy Aerobic",
            3: "Zone 3 - Moderate Aerobic",
            4: "Zone 4 - Threshold",
            5: "Zone 5 - VO2 Max",
        }
        return zone_names.get(zone, "Unknown")

    def get_zone_description(self, zone: int) -> str:
        """
        Get a detailed description for a zone.

        Args:
            zone: Zone number (1-5)

        Returns:
            str: Zone description
        """
        descriptions = {
            1: "Active recovery, warm-up, cool-down. Very comfortable pace.",
            2: "Base aerobic training. Comfortable, conversational pace. Build endurance.",
            3: "Aerobic endurance. Moderate effort, can still talk in short sentences.",
            4: "Lactate threshold training. Hard effort, minimal talking. Improves speed.",
            5: "VO2 max intervals. Maximum effort, very hard breathing. Boosts performance.",
        }
        return descriptions.get(zone, "")

    def to_dict(self) -> dict:
        """Convert zones to dictionary with all zone information"""
        return {
            "max_heart_rate": self.max_heart_rate,
            "resting_heart_rate": self.resting_heart_rate,
            "hr_reserve": self.hr_reserve,
            "zones": [
                {
                    "zone": 1,
                    "name": "Recovery",
                    "min_hr": self.zone1_min,
                    "max_hr": self.zone1_max,
                    "percentage": "50-60%",
                    "description": self.get_zone_description(1),
                },
                {
                    "zone": 2,
                    "name": "Easy Aerobic",
                    "min_hr": self.zone2_min,
                    "max_hr": self.zone2_max,
                    "percentage": "60-70%",
                    "description": self.get_zone_description(2),
                },
                {
                    "zone": 3,
                    "name": "Moderate Aerobic",
                    "min_hr": self.zone3_min,
                    "max_hr": self.zone3_max,
                    "percentage": "70-80%",
                    "description": self.get_zone_description(3),
                },
                {
                    "zone": 4,
                    "name": "Threshold",
                    "min_hr": self.zone4_min,
                    "max_hr": self.zone4_max,
                    "percentage": "80-90%",
                    "description": self.get_zone_description(4),
                },
                {
                    "zone": 5,
                    "name": "VO2 Max",
                    "min_hr": self.zone5_min,
                    "max_hr": self.zone5_max,
                    "percentage": "90-100%",
                    "description": self.get_zone_description(5),
                },
            ],
        }


class TrainingGoal(BaseModel):
    """Training goal definition"""

    goal_type: TrainingGoalType = Field(..., description="Type of training goal")
    description: str = Field(..., min_length=1, max_length=200, description="Goal description")
    target_date: Optional[date] = Field(default=None, description="Target completion date")
    priority: int = Field(default=1, ge=1, le=5, description="Goal priority (1=highest, 5=lowest)")

    # Race-specific fields
    race_name: Optional[str] = Field(default=None, description="Race name (for race goals)")
    race_distance: Optional[float] = Field(default=None, ge=0, description="Race distance in km")
    target_time: Optional[str] = Field(default=None, description="Target finish time (HH:MM:SS)")

    # Progress tracking
    is_active: bool = Field(default=True, description="Is goal currently active")
    completed: bool = Field(default=False, description="Has goal been completed")
    completed_date: Optional[date] = Field(default=None, description="Date goal was completed")

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: Optional[date]) -> Optional[date]:
        """Ensure target date is not in the past"""
        if v and v < date.today():
            raise ValueError("Target date cannot be in the past")
        return v

    @model_validator(mode='after')
    def validate_completed_date(self) -> 'TrainingGoal':
        """Ensure completed date makes sense"""
        if self.completed_date and not self.completed:
            raise ValueError("Cannot have completed_date without completed=True")
        return self


class AthleteMetrics(BaseModel):
    """Current athlete performance metrics"""

    # Timestamp
    recorded_at: datetime = Field(default_factory=datetime.utcnow, description="When metrics were recorded")

    # Cardiovascular metrics
    resting_hr: Optional[int] = Field(default=None, ge=30, le=100, description="Current resting HR")
    max_hr: Optional[int] = Field(default=None, ge=100, le=220, description="Current max HR")
    vo2_max: Optional[float] = Field(default=None, ge=20, le=100, description="VO2 max estimate")

    # Body metrics
    weight: Optional[float] = Field(default=None, ge=30, le=300, description="Current weight (kg)")
    body_fat_percentage: Optional[float] = Field(default=None, ge=3, le=50, description="Body fat %")

    # Performance metrics
    ftp: Optional[int] = Field(default=None, ge=50, le=500, description="Functional Threshold Power (watts)")
    lactate_threshold_hr: Optional[int] = Field(default=None, ge=100, le=220, description="Lactate threshold HR")

    # Recovery metrics
    hrv: Optional[float] = Field(default=None, ge=0, le=200, description="Heart rate variability (ms)")
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24, description="Average sleep hours")
    fatigue_level: Optional[int] = Field(default=None, ge=1, le=10, description="Self-reported fatigue (1-10)")
    stress_level: Optional[int] = Field(default=None, ge=1, le=10, description="Stress level (1-10)")

    # Training load
    weekly_volume: Optional[float] = Field(default=None, ge=0, description="Weekly training volume (hours)")
    weekly_tss: Optional[float] = Field(default=None, ge=0, description="Weekly Training Stress Score")


class UserProfile(BaseModel):
    """
    Complete user profile including athlete data, goals, and training zones.
    """

    # Basic information
    user_id: Optional[str] = Field(default=None, description="Unique user identifier")
    athlete_name: str = Field(..., min_length=1, max_length=100, description="Athlete name")
    email: str = Field(..., description="Contact email")

    # Personal data
    age: int = Field(..., ge=10, le=100, description="Age in years")
    gender: Gender = Field(..., description="Gender")
    weight: Optional[float] = Field(default=None, ge=30, le=300, description="Weight (kg)")
    height: Optional[float] = Field(default=None, ge=100, le=250, description="Height (cm)")

    # Heart rate data
    max_heart_rate: int = Field(..., ge=100, le=220, description="Maximum heart rate")
    resting_heart_rate: int = Field(..., ge=30, le=100, description="Resting heart rate")
    lactate_threshold_hr: Optional[int] = Field(default=None, description="Lactate threshold HR")

    # Training zones (calculated)
    heart_rate_zones: Optional[HeartRateZones] = Field(default=None, description="HR training zones")

    # Training configuration
    weekly_training_days: int = Field(default=6, ge=1, le=7, description="Training days per week")
    weekly_training_hours: Optional[float] = Field(default=None, ge=1, le=40, description="Weekly hours")
    preferred_training_types: list[str] = Field(default=["running"], description="Preferred activities")

    # Goals
    primary_goal: TrainingGoal = Field(..., description="Primary training goal")
    secondary_goals: list[TrainingGoal] = Field(default=[], description="Additional goals")

    # Medical/injury history
    injury_history: Optional[str] = Field(default=None, max_length=500, description="Injury history")
    medical_notes: Optional[str] = Field(default=None, max_length=500, description="Medical notes")

    # Current metrics
    current_metrics: Optional[AthleteMetrics] = Field(default=None, description="Current performance metrics")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation date")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update date")

    def __init__(self, **data):
        """Initialize profile and calculate zones"""
        super().__init__(**data)
        if not self.heart_rate_zones:
            self.calculate_heart_rate_zones()

    @model_validator(mode='after')
    def validate_max_hr(self) -> 'UserProfile':
        """Validate max HR is reasonable"""
        if self.age and self.max_heart_rate:
            # Rough estimate: max HR should be near 220 - age
            estimated_max = 220 - self.age
            if abs(self.max_heart_rate - estimated_max) > 30:
                import warnings
                warnings.warn(
                    f"Max HR ({self.max_heart_rate}) differs significantly from age-based estimate ({estimated_max}). "
                    "Ensure this value is accurate.",
                    UserWarning
                )
        return self

    def calculate_heart_rate_zones(self) -> None:
        """Calculate and set heart rate training zones"""
        self.heart_rate_zones = HeartRateZones(
            max_heart_rate=self.max_heart_rate,
            resting_heart_rate=self.resting_heart_rate,
        )

    def get_zone_for_hr(self, heart_rate: int) -> int:
        """Get training zone for a given heart rate"""
        if not self.heart_rate_zones:
            self.calculate_heart_rate_zones()
        return self.heart_rate_zones.get_zone(heart_rate)

    @property
    def bmi(self) -> Optional[float]:
        """Calculate BMI if weight and height are available"""
        if self.weight and self.height:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return None

    @property
    def days_to_goal(self) -> Optional[int]:
        """Days remaining until primary goal target date"""
        if self.primary_goal.target_date:
            return (self.primary_goal.target_date - date.today()).days
        return None

    @property
    def estimated_max_hr(self) -> int:
        """Estimated max HR using age-based formula (220 - age)"""
        return 220 - self.age

    def update_metrics(self, metrics: AthleteMetrics) -> None:
        """Update current athlete metrics"""
        self.current_metrics = metrics
        self.updated_at = datetime.utcnow()

        # Update HR zones if HR values changed
        if metrics.max_hr and metrics.resting_hr:
            if (metrics.max_hr != self.max_heart_rate or
                metrics.resting_hr != self.resting_heart_rate):
                self.max_heart_rate = metrics.max_hr
                self.resting_heart_rate = metrics.resting_hr
                self.calculate_heart_rate_zones()

    def to_summary_dict(self) -> dict:
        """Create a summary dictionary for display"""
        return {
            "name": self.athlete_name,
            "age": self.age,
            "gender": self.gender if isinstance(self.gender, str) else self.gender.value,
            "primary_goal": self.primary_goal.description,
            "target_date": str(self.primary_goal.target_date) if self.primary_goal.target_date else None,
            "days_to_goal": self.days_to_goal,
            "weekly_training_days": self.weekly_training_days,
            "max_hr": self.max_heart_rate,
            "resting_hr": self.resting_heart_rate,
            "hr_reserve": self.heart_rate_zones.hr_reserve if self.heart_rate_zones else None,
            "bmi": self.bmi,
        }

    model_config = ConfigDict(use_enum_values=True)
