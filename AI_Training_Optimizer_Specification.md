# AI-Powered Training Optimization System
## Project Specification

---

## 🎯 Project Overview

Build an intelligent fitness training optimization system that:
- **Automatically fetches** Garmin health and training data
- **Analyzes patterns** using Claude AI to understand your body's signals
- **Generates daily workout recommendations** based on recovery status
- **Creates adaptive training plans** aligned with your goals
- **Prevents overtraining and injury** through smart load management
- **Provides actionable insights** through AI-powered analysis

### ⚠️ Critical Considerations Before Starting

**1. Unofficial Garmin Integration**
This system uses the `garminconnect` Python library, which is unofficial and reverse-engineers Garmin's web API. This means:
- ❌ Not endorsed by Garmin
- ❌ May violate Garmin's Terms of Service
- ⚠️ Could break if Garmin updates their system
- ✅ Works reliably for personal use (as of Oct 2025)
- ✅ Actively maintained by community

**Alternative**: Use Apple HealthKit if you're willing to build iOS-only.

**2. Claude API Costs**
Estimated monthly costs for AI analysis:
- Daily readiness analysis: ~$0.10-0.20/day
- Weekly insights: ~$0.50/week
- Training plan generation: ~$1-2/plan
- Chat queries: ~$0.05-0.15/query
- **Total estimate: $5-15/month** for regular use

Uses Claude Sonnet 4.5 (most intelligent model). Can reduce costs by:
- Using prompt caching (automatically enabled)
- Reducing analysis frequency
- Limiting data context window

**3. Time Commitment**
- Initial setup: 4-8 hours
- Full implementation: 20-40 hours over 5 weeks
- Daily usage: 5 minutes (automated after setup)

**4. Technical Prerequisites**
- Python programming knowledge (intermediate level)
- Basic understanding of APIs and databases
- Familiarity with FastAPI or Flask
- Understanding of heart rate training zones and HRV
- Comfortable with command line

---

## 🏗️ Tech Stack

- **Python 3.10+**
- **FastAPI** - Web API and dashboard
- **garminconnect** - Garmin data fetching (unofficial but functional)
- **SQLite** - Data storage (upgradeable to PostgreSQL)
- **Anthropic Python SDK** - Claude AI integration (claude-sonnet-4-5-20250929)
- **Plotly/Dash** - Interactive visualizations
- **APScheduler** - Automated daily syncing
- **Pandas** - Data processing and analysis
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation

---

## 📁 Project Structure

```
training-optimizer/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Configuration management
│   ├── database.py                 # Database models and session
│   │
│   ├── services/
│   │   ├── garmin_service.py       # Garmin data fetching
│   │   ├── ai_analyzer.py          # Claude AI analysis engine
│   │   ├── training_planner.py     # Workout plan generation
│   │   ├── data_processor.py       # Data aggregation and prep
│   │   └── notification_service.py # Email/push notifications
│   │
│   ├── models/
│   │   ├── database_models.py      # SQLAlchemy models
│   │   ├── schemas.py              # Pydantic models
│   │   └── workout_library.py      # Structured workout definitions
│   │
│   ├── routers/
│   │   ├── health.py               # Health data endpoints
│   │   ├── analysis.py             # AI analysis endpoints
│   │   ├── training.py             # Training plan endpoints
│   │   └── chat.py                 # AI chat interface
│   │
│   ├── templates/                  # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── insights.html
│   │   ├── training_plan.html
│   │   └── chat.html
│   │
│   └── static/                     # CSS, JS, images
│       ├── css/
│       ├── js/
│       └── images/
│
├── scripts/
│   ├── sync_data.py               # Manual data sync
│   ├── initial_setup.py           # First-time setup wizard
│   └── backfill_data.py           # Import historical data
│
├── tests/
│   ├── test_garmin_service.py
│   ├── test_ai_analyzer.py
│   └── test_training_planner.py
│
├── notebooks/
│   └── exploratory_analysis.ipynb # Jupyter notebook for data exploration
│
├── data/                          # Local data storage
│   └── training_data.db          # SQLite database
│
├── logs/                          # Application logs
│
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore
├── README.md                      # Setup and usage instructions
└── docker-compose.yml            # Optional containerization
```

---

## 📊 Database Schema

### Core Tables

#### `daily_metrics`
```sql
- id: INTEGER PRIMARY KEY
- date: DATE UNIQUE
- steps: INTEGER
- distance_meters: FLOAT
- calories: INTEGER
- active_minutes: INTEGER
- resting_heart_rate: INTEGER
- max_heart_rate: INTEGER
- avg_heart_rate: INTEGER
- hrv_sdnn: FLOAT
- stress_score: INTEGER
- body_battery: INTEGER
- sleep_score: INTEGER
- vo2_max: FLOAT
- weight_kg: FLOAT
- body_fat_percent: FLOAT
- hydration_ml: INTEGER
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### `sleep_sessions`
```sql
- id: INTEGER PRIMARY KEY
- date: DATE
- start_time: TIMESTAMP
- end_time: TIMESTAMP
- duration_minutes: INTEGER
- deep_sleep_minutes: INTEGER
- light_sleep_minutes: INTEGER
- rem_sleep_minutes: INTEGER
- awake_minutes: INTEGER
- sleep_score: INTEGER
- restlessness: FLOAT
- created_at: TIMESTAMP
```

#### `activities`
```sql
- id: INTEGER PRIMARY KEY
- garmin_activity_id: VARCHAR UNIQUE
- date: DATE
- start_time: TIMESTAMP
- activity_type: VARCHAR (running, cycling, swimming, etc.)
- duration_minutes: INTEGER
- distance_meters: FLOAT
- avg_heart_rate: INTEGER
- max_heart_rate: INTEGER
- avg_pace_per_km: INTEGER (seconds)
- calories: INTEGER
- elevation_gain_meters: FLOAT
- training_effect_aerobic: FLOAT
- training_effect_anaerobic: FLOAT
- training_load: INTEGER
- recovery_time_hours: INTEGER
- avg_power: INTEGER (for cycling)
- notes: TEXT
- created_at: TIMESTAMP
```

#### `heart_rate_samples`
```sql
- id: INTEGER PRIMARY KEY
- activity_id: INTEGER (FK to activities)
- timestamp: TIMESTAMP
- heart_rate: INTEGER
- (For detailed intra-workout HR analysis)
```

#### `hrv_readings`
```sql
- id: INTEGER PRIMARY KEY
- date: DATE
- timestamp: TIMESTAMP
- hrv_sdnn: FLOAT
- hrv_rmssd: FLOAT
- measurement_type: VARCHAR (morning, all_day, sleep)
```

#### `training_plans`
```sql
- id: INTEGER PRIMARY KEY
- name: VARCHAR
- goal: VARCHAR (marathon, 5k_pr, general_fitness, etc.)
- start_date: DATE
- target_date: DATE
- is_active: BOOLEAN
- created_by_ai: BOOLEAN
- notes: TEXT
- created_at: TIMESTAMP
```

#### `planned_workouts`
```sql
- id: INTEGER PRIMARY KEY
- plan_id: INTEGER (FK to training_plans)
- date: DATE
- workout_type: VARCHAR (easy_run, intervals, tempo, long_run, rest, etc.)
- description: TEXT
- target_duration_minutes: INTEGER
- target_distance_meters: FLOAT
- target_heart_rate_zone: VARCHAR
- intensity_level: INTEGER (1-10)
- was_completed: BOOLEAN
- actual_activity_id: INTEGER (FK to activities)
- ai_reasoning: TEXT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### `daily_readiness`
```sql
- id: INTEGER PRIMARY KEY
- date: DATE UNIQUE
- readiness_score: INTEGER (0-100)
- recommendation: VARCHAR (high_intensity, moderate, easy, rest)
- key_factors: JSON
- red_flags: JSON
- recovery_tips: JSON
- suggested_workout_id: INTEGER (FK to planned_workouts)
- ai_analysis: TEXT
- created_at: TIMESTAMP
```

#### `ai_analysis_cache`
```sql
- id: INTEGER PRIMARY KEY
- analysis_type: VARCHAR (daily_readiness, weekly_insights, performance_trends)
- date: DATE
- input_data_hash: VARCHAR
- result: JSON
- expires_at: TIMESTAMP
- created_at: TIMESTAMP
```

#### `training_load_tracking`
```sql
- id: INTEGER PRIMARY KEY
- date: DATE
- acute_load: FLOAT (7-day average)
- chronic_load: FLOAT (28-day average)
- acwr: FLOAT (acute:chronic ratio)
- fatigue: INTEGER
- fitness: INTEGER
- form: INTEGER
```

#### `user_profile`
```sql
- id: INTEGER PRIMARY KEY
- age: INTEGER
- gender: VARCHAR
- max_heart_rate: INTEGER
- resting_heart_rate: INTEGER
- lactate_threshold_hr: INTEGER
- vo2_max: FLOAT
- training_goal: VARCHAR
- target_race_date: DATE
- weekly_training_hours: FLOAT
- injury_history: JSON
- preferences: JSON
- updated_at: TIMESTAMP
```

---

## 🤖 AI Analysis Engine - CORE FEATURE

### AIAnalyzer Class (`services/ai_analyzer.py`)

This is the intelligence center of the system. It uses Claude AI to analyze your data and provide recommendations.

#### Key Methods:

#### 1. **Daily Readiness Analysis** (MOST IMPORTANT)

```python
async def analyze_daily_readiness(self, date: str) -> DailyReadinessResponse:
    """
    Analyzes whether you should train hard, easy, or rest today.
    
    This runs every morning automatically and is the core feature.
    
    Inputs analyzed:
    - Last night's sleep (duration, quality, sleep stages)
    - This morning's HRV (compared to 7-day and 30-day baseline)
    - Resting heart rate (compared to baseline)
    - Yesterday's training load
    - Last 7 days cumulative training stress
    - Current acute:chronic workload ratio
    - Body battery / stress levels
    - Previous day's recovery status
    
    Output:
    {
        "date": "2025-10-16",
        "readiness_score": 82,  # 0-100
        "recommendation": "moderate",  # high_intensity | moderate | easy | rest
        "confidence": "high",  # high | medium | low
        "key_factors": [
            "Sleep quality excellent (8.2 hours, 85% score)",
            "HRV normal at 62ms (your 7-day avg: 58ms)",
            "Resting HR at baseline: 48 bpm",
            "Training load stable, no spikes"
        ],
        "red_flags": [
            "Slight elevation in morning HR (+3 bpm from baseline)",
            "Only 2 hours deep sleep vs your usual 2.5 hours"
        ],
        "suggested_workout": {
            "type": "tempo_run",
            "description": "45-minute tempo run with 10min warm-up, 25min at threshold pace (zone 4), 10min cool-down",
            "target_duration_minutes": 45,
            "target_hr_zone": "4",
            "hr_range": "165-175 bpm",
            "intensity": 7,
            "rationale": "Your recovery metrics are good. Body is ready for moderate-high intensity. Threshold work will improve lactate clearance without excessive stress."
        },
        "alternative_workouts": [
            {
                "type": "easy_run",
                "description": "If you feel tired during warm-up, switch to 45min easy run",
                "target_hr_zone": "2"
            }
        ],
        "recovery_tips": [
            "Focus on hydration today - you tend to perform better when well-hydrated",
            "Consider foam rolling before workout - helps with your typical calf tightness",
            "Protein within 30min post-workout for optimal recovery"
        ],
        "warnings": [],
        "next_rest_day": "2025-10-18",
        "ai_reasoning": "Full detailed explanation of the analysis and recommendation..."
    }
    ```

**AI Prompt Structure:**
```python
prompt = f"""
You are an expert running coach and sports scientist analyzing an athlete's readiness to train.

ATHLETE PROFILE:
{user_profile}

TODAY'S PHYSIOLOGICAL DATA:
- Date: {date}
- Sleep last night: {sleep_data}
- HRV this morning: {hrv_data} (7-day baseline: {hrv_baseline}, 30-day: {hrv_30day})
- Resting HR: {rhr_data} (baseline: {rhr_baseline})
- Body Battery: {body_battery}
- Stress level: {stress_level}

RECENT TRAINING HISTORY (Last 7 days):
{recent_activities}

TRAINING LOAD METRICS:
- Acute training load (7-day): {acute_load}
- Chronic training load (28-day): {chronic_load}
- Acute:Chronic Ratio: {acwr} (optimal: 0.8-1.3, injury risk if >1.5)
- Current fitness: {fitness}
- Current fatigue: {fatigue}
- Form (fitness - fatigue): {form}

TRAINING GOAL:
{training_goal}

NEXT KEY WORKOUT IN PLAN:
{next_planned_workout}

TASK:
Analyze the athlete's readiness to train TODAY and provide:
1. Readiness score (0-100)
2. Training recommendation (high_intensity, moderate, easy, or rest)
3. Specific workout suggestion aligned with their goal
4. Key factors influencing the decision
5. Any red flags or concerns
6. Recovery optimization tips

Return response in this EXACT JSON format:
{json_schema}

IMPORTANT CONSIDERATIONS:
- HRV drop >10% from baseline = possible illness/overtraining, recommend easy or rest
- Resting HR elevated >5 bpm = stress/fatigue, scale back intensity
- Sleep <6 hours or sleep score <60 = inadequate recovery
- ACWR >1.5 = injury risk, recommend easy week
- Back-to-back high intensity days = risky, alternate with easy days
- After long runs (>90 min), need 24-48 hours easy
- Trust the data but also acknowledge subjective feel matters

Be specific with workout details (pace, HR zones, duration, structure).
"""
```

#### 2. **Weekly Training Pattern Analysis**

```python
async def analyze_weekly_patterns(self, start_date: str, end_date: str) -> WeeklyInsights:
    """
    Analyzes a week (or multiple weeks) of training for patterns and balance.
    
    Identifies:
    - Training load distribution (are you doing too much intensity?)
    - Recovery adequacy (are rest days actually restful?)
    - Workout variety (too much running? need cross-training?)
    - Sleep and HRV trends
    - Overtraining risk
    
    Output includes:
    - Training load score
    - Intensity distribution (easy/moderate/hard ratio)
    - Overtraining risk score
    - Recommendations for next week
    - Specific adjustments needed
    """
```

#### 3. **Performance Trend Analysis**

```python
async def analyze_performance_trends(self, metric: str, period_days: int = 90) -> TrendAnalysis:
    """
    Analyzes long-term trends in key performance indicators.
    
    Metrics analyzed:
    - VO2 Max progression
    - Running pace at same HR (efficiency)
    - HR at same pace (fitness indicator)
    - HRV baseline trend
    - Resting HR trend
    - Body composition changes
    
    Identifies:
    - Improvements or plateaus
    - Potential causes
    - Breakthrough moments
    - Recommendations to break through plateaus
    """
```

#### 4. **Training Plan Generation** (NEW FEATURE)

```python
async def generate_training_plan(
    self, 
    goal: str,
    target_date: str,
    current_fitness_level: dict,
    constraints: dict
) -> TrainingPlan:
    """
    Generates a complete periodized training plan to achieve a goal.
    
    Example goals:
    - "Run a sub-3:30 marathon on December 1, 2025"
    - "Improve 5K time from 22:00 to 20:30"
    - "Build base fitness for 6 months"
    - "Recover from injury and return to running"
    
    Inputs:
    - Goal description
    - Target race date
    - Current fitness metrics (recent pace, VO2 max, training volume)
    - Constraints (available training days, injury history, time budget)
    
    Generates:
    - Week-by-week training plan
    - Daily workout prescriptions
    - Periodization phases (base, build, peak, taper)
    - Progression logic
    - Recovery weeks
    - Cross-training integration
    
    Plan adapts dynamically based on:
    - How your body responds to training
    - Illness or injury
    - Life events (travel, stress)
    - Progress toward goal
    """
```

#### 5. **Workout Library Integration**

Create a structured workout database with progressive overload:

```python
WORKOUT_LIBRARY = {
    "easy_runs": [
        {
            "name": "Recovery Run",
            "description": "30-45 min easy pace, HR Zone 2",
            "target_duration": 40,
            "target_hr_zone": "2",
            "intensity": 3,
            "when_to_use": "Day after hard workout or long run"
        },
        {
            "name": "Easy Endurance",
            "description": "60-75 min easy conversational pace",
            "target_duration": 70,
            "target_hr_zone": "2",
            "intensity": 4,
            "when_to_use": "Building aerobic base"
        }
    ],
    "tempo_runs": [
        {
            "name": "Threshold Intervals",
            "description": "3x10min at threshold pace, 2min rest",
            "workout_structure": [
                {"segment": "warm_up", "duration": 15, "intensity": "easy"},
                {"segment": "interval", "duration": 10, "intensity": "threshold", "repeats": 3, "rest": 2},
                {"segment": "cool_down", "duration": 10, "intensity": "easy"}
            ],
            "target_duration": 55,
            "target_hr_zone": "4",
            "intensity": 8,
            "when_to_use": "Midweek quality session"
        },
        {
            "name": "Continuous Tempo",
            "description": "20-30min continuous at threshold",
            "target_duration": 45,
            "target_hr_zone": "4",
            "intensity": 7,
            "when_to_use": "Race-specific endurance"
        }
    ],
    "interval_sessions": [
        {
            "name": "VO2 Max Intervals",
            "description": "6x800m at 5K pace, 400m jog recovery",
            "target_duration": 50,
            "target_hr_zone": "5",
            "intensity": 9,
            "when_to_use": "Improving aerobic capacity"
        },
        {
            "name": "Short Speed",
            "description": "10x400m at 3K pace, 90sec rest",
            "target_duration": 45,
            "target_hr_zone": "5",
            "intensity": 9,
            "when_to_use": "Building speed and power"
        }
    ],
    "long_runs": [
        {
            "name": "Conversational Long Run",
            "description": "90-180min at easy pace with HR in Zone 2",
            "target_duration": 120,
            "target_hr_zone": "2",
            "intensity": 5,
            "progression_notes": "Add 10-15min each week"
        },
        {
            "name": "Progressive Long Run",
            "description": "Start easy, finish last 20min at marathon pace",
            "target_duration": 120,
            "intensity": 6,
            "when_to_use": "Marathon preparation"
        }
    ]
}
```

AI selects from this library and customizes based on your fitness level and goals.

#### 6. **Real-Time Plan Adaptation**

```python
async def adapt_training_plan(
    self, 
    current_plan_id: int,
    today_date: str,
    readiness_score: int
) -> AdaptedPlan:
    """
    Modifies upcoming workouts based on today's readiness.
    
    Example scenarios:
    
    Scenario 1: HRV crash
    - Planned: Hard interval session
    - Readiness: 45/100 (HRV down 20%, poor sleep)
    - Adaptation: Change to easy run, push intervals to tomorrow or next week
    
    Scenario 2: Feeling great after planned easy day
    - Planned: Easy run
    - Readiness: 95/100 (all metrics excellent)
    - Adaptation: Keep easy run (recovery is important), move next hard session up
    
    Scenario 3: Illness detected
    - Planned: Long run
    - Readiness: 30/100 (HRV very low, elevated RHR)
    - Adaptation: Rest, cancel next 2-3 days, focus on recovery
    
    The AI adjusts the entire week/plan to maintain progression while respecting recovery.
    """
```

---

## 📅 Daily Workflow - User Experience

### Morning Routine (Automated)

**8:00 AM - System runs automatically:**

1. **Data Sync** (5 minutes)
   - Fetch yesterday's complete data from Garmin
   - Fetch last night's sleep
   - Fetch this morning's HRV and resting HR
   - Store in database

2. **AI Analysis** (2 minutes)
   - Analyze readiness
   - Generate daily recommendation
   - Check training plan adherence
   - Adapt plan if needed

3. **Notification Sent** (instant)
   - Email or push notification with:
     - Readiness score
     - Today's recommended workout
     - Key insights
     - Link to full dashboard

### User Opens Dashboard

**Landing Page - Today's Training:**

```
┌─────────────────────────────────────────────────────────┐
│  TRAINING OPTIMIZER                       Oct 16, 2025  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🟢 READY TO TRAIN                                       │
│  Readiness Score: 82/100                                │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  TODAY'S RECOMMENDED WORKOUT                    │    │
│  │                                                  │    │
│  │  🏃 Tempo Run - 45 minutes                       │    │
│  │                                                  │    │
│  │  Structure:                                      │    │
│  │  • 10min warm-up (easy)                         │    │
│  │  • 25min at threshold pace                      │    │
│  │    Target: 4:45-5:00/km, HR 165-175            │    │
│  │  • 10min cool-down (easy)                       │    │
│  │                                                  │    │
│  │  Why this workout?                              │    │
│  │  Your recovery metrics are excellent. Body is   │    │
│  │  ready for quality work. Threshold training     │    │
│  │  will improve lactate clearance and race pace   │    │
│  │  endurance for your marathon goal.              │    │
│  │                                                  │    │
│  │  [VIEW DETAILED PLAN] [LOG WORKOUT]             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  KEY FACTORS ✓                                          │
│  • Sleep: 8.2 hours (85% quality) - Excellent          │
│  • HRV: 62ms (vs 7-day avg 58ms) - Normal              │
│  • Resting HR: 48 bpm (baseline) - Good                │
│  • Training load: Stable, no spikes                     │
│                                                          │
│  RECOVERY TIPS 💡                                       │
│  • Hydrate well (aim for 500ml before workout)         │
│  • You perform better in afternoon - consider 4PM      │
│  • Post-workout protein within 30 minutes              │
│                                                          │
│  WHAT IF I FEEL TIRED?                                  │
│  Switch to: 45min easy run at Zone 2 (135-145 bpm)    │
│                                                          │
└─────────────────────────────────────────────────────────┘

THIS WEEK'S PLAN                        Week 8 of 16
Mon    Rest Day                         ✓ Completed
Tue    Easy Run 60min                   ✓ Completed  
Wed    Tempo Run 45min                  ← Today
Thu    Easy Run 45min                   Upcoming
Fri    Intervals 8x800m                 Upcoming
Sat    Easy Run 50min                   Upcoming  
Sun    Long Run 22km                    Upcoming

RECENT PROGRESS
[Chart showing: Weekly volume, HRV trend, Fitness/Fatigue/Form]
```

### Interaction with AI

**AI Chat Interface:**
```
You: Why did you recommend tempo instead of intervals today?

AI: Great question! Here's my reasoning:

1. Training Pattern: You did a hard interval session on Friday (5 
   days ago), which was excellent quality. Your body has recovered 
   well from that.

2. Progressive Overload: Your plan calls for increasing your 
   threshold pace endurance. Last week you did 20min at threshold, 
   today's 25min builds on that.

3. Friday's Big Session: You have a VO2 max interval session 
   planned for Friday (8x800m). I'm spacing out your high-intensity 
   work to optimize both quality and recovery.

4. Sunday's Long Run: With a 22km long run on Sunday, today's 
   tempo run provides quality without excessive fatigue that would 
   compromise your long run.

The rhythm is: Easy (Mon), Easy (Tue), Tempo (Wed), Easy (Thu), 
Intervals (Fri), Easy (Sat), Long (Sun). This gives you 2 quality 
sessions with adequate recovery between them.

Want me to explain the Friday interval session structure?
```

```
You: My legs feel a bit heavy today. Should I still do the tempo?

AI: Good that you're listening to your body! Let me check your data:

Your HRV (62ms) and resting HR (48) both look normal, which is 
positive. However, "heavy legs" can be an early warning sign.

RECOMMENDATION: Start with a 10-minute easy warm-up and assess.

If after 10 minutes:
- Legs feel loose → Proceed with tempo as planned
- Still feel heavy → Switch to 45min easy run, Zone 2

I've prepared an alternative easy workout for you just in case. 
There's no shame in taking it easy - better to have a great 
interval session Friday than force a mediocre tempo today.

Should I adjust Friday's workout if you do the easy run today?
```

---

## 🎯 Training Plan Generation - Advanced Feature

### Goal Input Form

User specifies:
```python
{
    "goal_type": "marathon",
    "target_time": "3:30:00",
    "race_date": "2025-12-01",
    "current_fitness": {
        "recent_long_run": 16.0,  # km
        "weekly_volume": 45.0,     # km/week
        "recent_10k_time": "45:00",
        "vo2_max": 48.5
    },
    "available_days": [1, 2, 3, 4, 5, 6],  # Mon-Sat
    "time_constraints": {
        "weekday_max_minutes": 60,
        "weekend_max_minutes": 180
    },
    "injury_history": ["IT band syndrome 2024"],
    "preferences": {
        "preferred_workout_time": "afternoon",
        "cross_training": ["cycling", "swimming"]
    }
}
```

### AI Generates Complete Plan

```python
async def generate_marathon_plan(goal_data: dict) -> TrainingPlan:
    """
    Creates a 16-week periodized marathon training plan.
    
    Phases:
    1. Base Building (weeks 1-5)
       - Build aerobic capacity
       - Increase weekly volume gradually
       - Focus: Easy miles, long run progression
    
    2. Build Phase (weeks 6-11)
       - Introduce quality workouts
       - Tempo runs, threshold intervals
       - Speed work for efficiency
    
    3. Peak Phase (weeks 12-14)
       - Highest volume
       - Race-specific workouts
       - Marathon pace practice
    
    4. Taper (weeks 15-16)
       - Reduce volume, maintain intensity
       - Fresh legs for race day
    
    Each week includes:
    - 1 long run (progressively longer)
    - 1-2 quality sessions (tempo/intervals)
    - 3-4 easy runs
    - 1 rest day
    - Optional cross-training
    """
```

**Example Generated Plan - Week 8:**

```
WEEK 8 - BUILD PHASE
Goal: Increase threshold endurance
Weekly Volume Target: 65km
Key Session: Marathon pace segments in long run

Monday: Rest or yoga
  Why: Recovery from weekend long run

Tuesday: Easy Run - 10km
  Pace: 5:45-6:00/km
  HR: Zone 2 (135-145 bpm)
  Notes: Conversational pace, focus on form

Wednesday: Tempo Run - 11km
  Structure: 2km easy, 7km at threshold (4:50-5:00/km), 2km easy
  HR: Zone 4 (165-175 bpm) during tempo
  Purpose: Improve lactate threshold for marathon pace sustainability

Thursday: Easy Run - 8km
  Pace: 5:45-6:00/km
  HR: Zone 2
  Optional: Add 4x100m strides at end

Friday: Rest or cross-train
  Options: 30min easy bike, swimming, or complete rest
  Why: Prepare for quality weekend

Saturday: Easy Run - 10km
  Pace: 5:45-6:00/km
  Keep it truly easy before long run

Sunday: Long Run - 24km
  Structure: 
    - 14km easy (5:45-6:00/km)
    - 8km at marathon pace (5:00-5:10/km)
    - 2km easy cool-down
  Purpose: Marathon-specific endurance, practice race pace
  Nutrition: Take 2-3 gels, practice race-day fueling
  
WEEK TOTAL: 63km
```

### Dynamic Plan Adaptation

**Scenario: Wednesday's tempo didn't go well**

```python
# Wednesday evening analysis
ai_analysis = {
    "workout_quality": "poor",
    "signs": [
        "Heart rate elevated for given pace (10 bpm higher than expected)",
        "Couldn't maintain threshold pace",
        "Reported feeling fatigued"
    ],
    "possible_causes": [
        "Insufficient recovery from previous week",
        "Accumulated fatigue",
        "Possible early illness"
    ]
}

# AI adjusts remaining week
adapted_plan = {
    "thursday": "Change from easy 8km to REST - body needs recovery",
    "friday": "Keep as rest day",
    "saturday": "Change from 10km to easy 6km",
    "sunday": "Modify long run: 20km all at easy pace, skip marathon pace segments",
    "rationale": "Your body is showing fatigue signs. Better to have a slightly reduced week than risk injury or illness. Next week we'll reassess and potentially make up the quality work."
}
```

---

## 🔔 Notification System

### Daily Morning Alert (Email/SMS/Push)

```
Subject: Today's Training - Tempo Run 🏃

Good morning!

Readiness Score: 82/100 ✓

Today's Workout: Tempo Run (45 min)
• 10min warm-up
• 25min at threshold pace (4:45-5:00/km)
• 10min cool-down

Why: Your recovery is excellent. Time for quality work!

Key Metrics:
✓ Sleep: 8.2 hours (85% quality)
✓ HRV: 62ms (normal)
✓ Resting HR: 48 bpm

View full details: [Link to dashboard]

Remember: If you feel tired during warm-up, switch to easy run.

Good luck! 💪
```

### Alert Triggers

**Overtraining Warning:**
```
⚠️ OVERTRAINING RISK DETECTED

Your HRV has dropped 18% over the last 3 days and resting HR is 
elevated 6 bpm.

RECOMMENDED ACTION:
- Take the next 2 days completely off
- Focus on sleep (aim for 8+ hours)
- Hydrate well
- Light walking or yoga only

This is not weakness - this is smart training. Your body needs 
recovery now to prevent injury or illness.

I've adjusted your plan - no hard workouts until your metrics 
normalize.
```

**Illness Detection:**
```
🚨 POSSIBLE ILLNESS ALERT

Unusual pattern detected:
- HRV: 42ms (normally 58-65ms)
- Resting HR: 56 bpm (normally 48 bpm)
- Poor sleep quality

Your body is fighting something. 

ACTION: Skip today's workout. Rest completely.

If you have other symptoms (sore throat, fatigue, fever), consider 
seeing a doctor.

I'll monitor your metrics and let you know when it's safe to return 
to training.
```

---

## 📈 Advanced Analytics Features

### 1. Performance Predictions

```python
async def predict_race_time(
    distance: str,  # "5k", "10k", "half_marathon", "marathon"
    current_fitness: dict
) -> RacePrediction:
    """
    Predicts race performance based on current fitness.
    
    Uses:
    - Recent workout paces
    - VO2 max estimate
    - Training volume
    - Race-specific training completed
    
    Example output:
    {
        "predicted_time": "3:28:45",
        "confidence": "medium",
        "confidence_factors": {
            "positive": [
                "Long run pace consistent with goal",
                "Threshold pace on target",
                "Training volume adequate"
            ],
            "concerns": [
                "Limited marathon pace practice",
                "Need more 30k+ long runs"
            ]
        },
        "improvement_needed": "Need to run 2:45-3:00 more in marathon pace zone",
        "probability_ranges": {
            "conservative": "3:32:00",
            "expected": "3:28:45",
            "optimistic": "3:25:30"
        }
    }
    ```

### 2. Training Load Management

**Acute:Chronic Workload Ratio (ACWR)**

```python
def calculate_training_load_metrics(date: str) -> dict:
    """
    Tracks training load to prevent injury.
    
    Metrics:
    - Acute Load: 7-day rolling average (recent stress)
    - Chronic Load: 28-day rolling average (fitness base)
    - ACWR: Acute / Chronic (optimal: 0.8-1.3)
    
    Interpretation:
    - ACWR < 0.8: Detraining risk
    - ACWR 0.8-1.3: Optimal (sweet spot)
    - ACWR 1.3-1.5: Caution
    - ACWR > 1.5: High injury risk
    
    Returns daily values + trend + recommendations
    """
```

**Visual Display:**
```
TRAINING LOAD ANALYSIS

[Chart showing 12-week trend]
Acute Load:    485 (↑ 12% from last week)
Chronic Load:  445 (↑ 3% from last week)
ACWR:          1.09 ✓ OPTIMAL

STATUS: GREEN - Training load is appropriate

You're in the sweet spot! Current load is challenging your fitness
without excessive injury risk.

NEXT WEEK PLAN:
Maintain current volume. Your body is adapting well.

WARNING THRESHOLD:
If ACWR exceeds 1.35, I'll recommend an easy week.
```

### 3. Sleep-Performance Correlation

```python
async def analyze_sleep_impact() -> SleepAnalysis:
    """
    Finds patterns between sleep and performance.
    
    Analyzes:
    - Optimal sleep duration for you
    - Sleep quality vs workout quality
    - Sleep stages and recovery
    - Best bedtime for you
    
    Example insights:
    - "Your best workouts occur after 7.5-8.5 hours sleep"
    - "Performance drops 12% when sleep < 6.5 hours"
    - "Deep sleep below 90min correlates with poor recovery"
    - "You need 8 hours sleep before long runs for best results"
    """
```

### 4. HR-Pace Efficiency

```python
async def analyze_cardiac_efficiency(activity_type: str = "running") -> EfficiencyAnalysis:
    """
    Tracks improvement in heart rate efficiency.
    
    Calculates:
    - Pace at given HR over time
    - HR at given pace over time
    - Aerobic decoupling
    
    Example:
    "3 months ago: 5:30/km at 150 bpm
     Today: 5:00/km at 150 bpm
     
     Improvement: 30 seconds/km at same effort!
     This indicates improved aerobic fitness."
    """
```

---

## 🔌 API Endpoints

### Core Endpoints

```python
# Health Data
GET  /api/health/summary?date={YYYY-MM-DD}
GET  /api/health/steps?start_date={}&end_date={}
GET  /api/health/heart-rate?date={}
GET  /api/health/hrv?start_date={}&end_date={}
GET  /api/health/sleep?date={}

# Activities
GET  /api/activities?start_date={}&end_date={}
GET  /api/activities/{activity_id}
GET  /api/activities/summary?period=week|month|year

# Training Plans
GET  /api/training/plans
POST /api/training/plans
GET  /api/training/plans/{plan_id}
PUT  /api/training/plans/{plan_id}
GET  /api/training/plans/{plan_id}/workouts
POST /api/training/plans/{plan_id}/workouts

# Daily Recommendations (CORE)
GET  /api/recommendations/today
GET  /api/recommendations/readiness?date={}
POST /api/recommendations/adapt-plan

# AI Analysis
GET  /api/analysis/weekly?start_date={}
GET  /api/analysis/performance-trends?metric={}
GET  /api/analysis/injury-risk
POST /api/analysis/custom-query
POST /api/chat

# Data Sync
POST /api/sync/manual
GET  /api/sync/status
GET  /api/sync/history

# Predictions
GET  /api/predictions/race-time?distance={}&date={}
GET  /api/predictions/vo2max-trend

# Export
GET  /api/export/json?start_date={}&end_date={}
GET  /api/export/csv?start_date={}&end_date={}
GET  /api/export/training-log?format=pdf
```

---

## 🚀 Implementation Instructions for Claude Code

### Phase 1: Foundation (Week 1)

**Step 1: Project Setup**
```bash
1. Create project structure as defined above
2. Set up virtual environment
3. Install dependencies:
   - fastapi
   - uvicorn
   - sqlalchemy
   - garminconnect
   - anthropic
   - pandas
   - plotly
   - apscheduler
   - python-dotenv
   - pydantic
   - aiofiles
4. Create .env.example file with required variables
```

**Step 2: Database Setup**
```bash
1. Implement database models (database_models.py)
2. Create database migration/initialization script
3. Add indexes for performance
4. Test database operations
```

**Step 3: Garmin Integration**
```bash
1. Implement GarminService class
2. Add authentication with token caching
3. Create methods for fetching:
   - Daily metrics
   - Sleep data
   - Activities
   - HRV readings
   - Heart rate samples
4. Implement error handling and retries
5. Test with your Garmin account
```

### Phase 2: AI Analysis Engine (Week 2)

**Step 4: Claude AI Integration**
```bash
1. Set up Anthropic client
2. Implement AIAnalyzer base class
3. Create data preparation methods
4. Build prompt templates for each analysis type
5. Implement response parsing and validation
6. Add caching for AI responses
```

**Step 5: Daily Readiness System (PRIORITY)**
```bash
1. Implement analyze_daily_readiness() method
2. Create comprehensive prompt with all data context
3. Parse AI response into structured format
4. Store results in daily_readiness table
5. Build readiness scoring logic
6. Test with historical data
```

**Step 6: Training Plan Generation**
```bash
1. Create workout library
2. Implement plan generation algorithm
3. Add periodization logic
4. Build plan adaptation system
5. Test with different goals (5K, 10K, marathon, etc.)
```

### Phase 3: Web Interface (Week 3)

**Step 7: API Routes**
```bash
1. Implement all health data endpoints
2. Add training plan endpoints
3. Create recommendation endpoints
4. Build AI chat endpoint with streaming
5. Add data export endpoints
6. Test all endpoints with Postman/curl
```

**Step 8: Web Dashboard**
```bash
1. Create base HTML template with navigation
2. Build today's training dashboard (priority)
3. Implement training plan view
4. Add analytics/insights pages
5. Create AI chat interface
6. Add interactive charts with Plotly
7. Make it responsive for mobile
```

### Phase 4: Automation & Notifications (Week 4)

**Step 9: Scheduled Tasks**
```bash
1. Set up APScheduler
2. Create daily sync job (runs at 8 AM)
3. Add automatic AI analysis after sync
4. Implement plan adaptation checks
5. Test scheduling with shorter intervals
```

**Step 10: Notification System**
```bash
1. Implement email notifications
2. Add SMS notifications (optional - Twilio)
3. Create notification templates
4. Add alert triggers (overtraining, illness)
5. Test notification delivery
```

### Phase 5: Advanced Features (Week 5+)

**Step 11: Analytics**
```bash
1. Implement training load tracking (ACWR)
2. Add performance trend analysis
3. Create race time predictions
4. Build sleep-performance correlation
5. Add HR-pace efficiency tracking
```

**Step 12: Polish & Optimization**
```bash
1. Add comprehensive logging
2. Implement error monitoring
3. Optimize database queries
4. Add data validation throughout
5. Write tests for critical functions
6. Create user documentation
7. Add data backup functionality
```

---

## ⚙️ Configuration (.env)

```bash
# Garmin Credentials
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_secure_password

# Claude AI API
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Database
DATABASE_URL=sqlite:///./data/training_data.db
# For PostgreSQL: postgresql://user:password@localhost/training_optimizer

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=your-secret-key-for-sessions
DEBUG=True

# Scheduling
SYNC_HOUR=8
SYNC_MINUTE=0
TIMEZONE=America/New_York  # Set to your local timezone

# Notifications
ENABLE_EMAIL_NOTIFICATIONS=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# Optional: SMS Notifications (Twilio)
ENABLE_SMS_NOTIFICATIONS=False
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_TO_NUMBER=

# User Profile
ATHLETE_NAME=Your Name
ATHLETE_AGE=30
ATHLETE_GENDER=M
ATHLETE_WEIGHT_KG=70.0
MAX_HEART_RATE=188
RESTING_HEART_RATE=48
LACTATE_THRESHOLD_HR=175

# Training Goal
TRAINING_GOAL=marathon
GOAL_DESCRIPTION=Sub-3:30 Marathon
TARGET_RACE_DATE=2025-12-01
WEEKLY_TRAINING_DAYS=6
MAX_WEEKLY_HOURS=10

# AI Settings
AI_MODEL=claude-sonnet-4-5-20250929  # Check docs.anthropic.com for latest model
AI_CACHE_HOURS=24
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.7

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/training_optimizer.log

# Data Backup (IMPORTANT)
ENABLE_AUTO_BACKUP=True
BACKUP_FREQUENCY=weekly  # daily, weekly, monthly
BACKUP_DIRECTORY=./backups
MAX_BACKUP_COUNT=10  # Keep last 10 backups
```

---

## 📝 Usage Examples

### First-Time Setup

```bash
# 1. Clone and setup
git clone <your-repo>
cd training-optimizer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your credentials

# 3. Initialize database
python scripts/initial_setup.py

# 4. Backfill historical data (optional)
python scripts/backfill_data.py --days 90

# 5. Run application
uvicorn app.main:app --reload

# 6. Open browser
# Navigate to http://localhost:8000
```

### Daily Usage

```bash
# Automatic (preferred):
# System runs at 8 AM daily, sends notification

# Manual:
# 1. Check dashboard at http://localhost:8000
# 2. View today's recommendation
# 3. Complete workout
# 4. Sync Garmin device
# 5. System analyzes tomorrow's workout overnight
```

### API Usage Examples

```bash
# Get today's readiness
curl http://localhost:8000/api/recommendations/today

# Chat with AI
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why am I not improving my 10K time?"}'

# Generate training plan
curl -X POST http://localhost:8000/api/training/plans \
  -H "Content-Type: application/json" \
  -d '{
    "goal_type": "marathon",
    "target_time": "3:30:00",
    "race_date": "2025-12-01"
  }'

# Export data
curl http://localhost:8000/api/export/csv?start_date=2025-01-01 \
  > training_data.csv
```

---

## 🎨 Dashboard Wireframes

### Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ TRAINING OPTIMIZER                    [Sync] [Settings] [Chat]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ TODAY'S TRAINING - October 16, 2025                         │ │
│ │                                                               │ │
│ │  🟢 READY TO TRAIN - Readiness: 82/100                       │ │
│ │                                                               │ │
│ │  Recommended Workout: Tempo Run (45 min)                     │ │
│ │  [View Details] [Start Workout] [Adjust Plan]               │ │
│ │                                                               │ │
│ │  Why today? Your recovery is excellent, time for quality...  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│ │ Sleep        │ HRV          │ Resting HR   │ Training Load│  │
│ │ 8.2 hrs ✓    │ 62ms ✓       │ 48 bpm ✓     │ 485 ✓        │  │
│ │ 85% quality  │ (avg: 58ms)  │ (baseline)   │ ACWR: 1.09   │  │
│ └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                   │
│ THIS WEEK'S PLAN                              Week 8 of 16      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Mon  Rest              ✓                                     │ │
│ │ Tue  Easy 60min        ✓                                     │ │
│ │ Wed  Tempo 45min       ← Today                               │ │
│ │ Thu  Easy 45min                                              │ │
│ │ Fri  Intervals 8x800m                                        │ │
│ │ Sat  Easy 50min                                              │ │
│ │ Sun  Long Run 22km                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ WEEKLY SUMMARY                                                   │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ [Volume Chart] [HR Zones] [Training Load Graph]          │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│ RECENT ACTIVITIES                                                │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Oct 15  Easy Run       10.5 km  5:52/km  HR 142  ✓       │   │
│ │ Oct 14  Rest Day                                          │   │
│ │ Oct 13  Long Run       20.0 km  5:45/km  HR 148  ✓       │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│ [View All Activities] [Analytics] [Training Plan] [AI Chat]     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# Test Garmin data fetching
def test_garmin_authentication()
def test_fetch_daily_metrics()
def test_fetch_sleep_data()
def test_fetch_activities()

# Test AI analysis
def test_readiness_calculation()
def test_prompt_generation()
def test_response_parsing()
def test_plan_adaptation()

# Test database operations
def test_store_daily_metrics()
def test_query_historical_data()
def test_data_validation()
```

### Integration Tests
```python
# Test complete workflows
def test_daily_sync_workflow()
def test_recommendation_generation()
def test_plan_creation_workflow()
def test_api_endpoints()
```

### Data Validation Tests
```python
# Test data quality
def test_hrv_range_validation()
def test_heart_rate_anomaly_detection()
def test_sleep_data_consistency()
```

---

## 📊 Success Metrics

### System Health
- Daily sync success rate: >95%
- AI analysis completion time: <2 minutes
- API response time: <500ms
- Database query performance: <100ms

### Training Optimization
- Recommendation acceptance rate (track if user follows recommendation)
- Injury/overtraining prevention (track HRV trends)
- Training plan adherence rate
- User satisfaction with AI recommendations

---

## 🔒 Security Considerations

1. **Credentials Storage**
   - Store Garmin password encrypted
   - Use environment variables, never hardcode
   - Implement secure token storage

2. **API Security**
   - Add authentication for API endpoints
   - Rate limiting to prevent abuse
   - Input validation and sanitization

3. **Data Privacy**
   - Health data is sensitive
   - No external sharing without consent
   - Secure database access
   - Regular backups

---

## 🚀 Deployment Options

### Option 1: Local Development
```bash
# Run on your computer
uvicorn app.main:app --reload
# Access at http://localhost:8000
```

### Option 2: Home Server (Raspberry Pi, NAS)
```bash
# Run 24/7 on home server
# Use Docker for easy deployment
docker-compose up -d
```

### Option 3: Cloud Deployment (Advanced)
```bash
# Deploy to cloud (AWS, GCP, Azure)
# Use managed database
# Set up HTTPS
# Configure domain name
```

---

## 📚 Dependencies (requirements.txt)

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
jinja2==3.1.3
python-multipart==0.0.6

# Garmin Integration
garminconnect==0.2.17

# AI Integration
anthropic==0.18.1

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9  # For PostgreSQL

# Data Processing
pandas==2.2.0
numpy==1.26.3

# Visualization
plotly==5.18.0
dash==2.14.2

# Scheduling
apscheduler==3.10.4

# Configuration
python-dotenv==1.0.1
pydantic==2.5.3
pydantic-settings==2.1.0

# Utilities
requests==2.31.0
aiofiles==23.2.1
python-dateutil==2.8.2
pytz==2024.1

# Notifications
emails==0.6
twilio==8.11.1  # Optional for SMS

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# Logging
loguru==0.7.2

# Security
cryptography==42.0.0
python-jose[cryptography]==3.3.0

# Development
black==24.1.1
flake8==7.0.0
mypy==1.8.0
```

---

## 🎯 Priority Implementation Order

### Week 1: Core Data Pipeline
1. ✅ Garmin data fetching
2. ✅ Database setup and models
3. ✅ Data storage and validation
4. ✅ Manual sync functionality

### Week 2: AI Intelligence (CRITICAL)
1. ✅ Claude AI integration
2. ✅ Daily readiness analysis
3. ✅ Recommendation generation
4. ✅ Basic training plan creation

### Week 3: User Interface
1. ✅ API endpoints
2. ✅ Web dashboard
3. ✅ Today's training view
4. ✅ Training plan display

### Week 4: Automation
1. ✅ Scheduled daily sync
2. ✅ Automatic AI analysis
3. ✅ Email notifications
4. ✅ Plan adaptation

### Week 5+: Enhancement
1. Advanced analytics
2. Predictive modeling
3. Mobile optimization
4. Additional integrations

---

## 💡 Future Enhancements

### Phase 2 Features
- Integration with other platforms (Strava, TrainingPeaks)
- Nutrition tracking and recommendations
- Weather data integration
- Race performance analysis
- Training partner features
- Social sharing capabilities

### Phase 3 Features
- Mobile app (React Native)
- Wearable app (Garmin Connect IQ)
- Voice assistant integration
- Video coaching library
- Community features
- Coach collaboration tools

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue: Garmin login fails**
```bash
Solution:
1. Check credentials in .env file
2. Verify Garmin account is active
3. Check for 2FA (not currently supported by library)
4. Review garminconnect library issues on GitHub
5. Check for library updates: pip install --upgrade garminconnect
6. Look for community forks if official library is broken
```

**Issue: garminconnect library breaks (Garmin changed their API)**
```bash
Solution:
1. Check GitHub issues: https://github.com/cyberjunky/python-garminconnect
2. Look for updated versions or community forks
3. Temporary workaround: Manual data export from Garmin Connect
   - Export FIT files manually
   - Import into system using scripts/import_fit_files.py
4. Long-term: Consider building Apple HealthKit version instead
```

**Issue: AI analysis too slow**
```bash
Solution:
1. Reduce data context window
2. Implement better caching
3. Use faster Claude model
4. Optimize data preparation
```

**Issue: Database growing too large**
```bash
Solution:
1. Implement data archiving
2. Remove old HR samples (keep daily averages)
3. Compress historical data
4. Move to PostgreSQL if needed
```

---

## 🎓 Learning Resources

### Understanding HRV
- Research papers on HRV and recovery
- HRV baseline calculation methods
- Training stress and HRV correlation

### Training Science
- Periodization principles
- Training load management
- Overtraining syndrome markers
- Recovery optimization

### AI Prompt Engineering
- Effective prompt structuring
- Data context preparation
- Response validation
- Token optimization

---

## 📄 License & Disclaimer

⚠️ **Important Disclaimers:**

1. **Unofficial API**: This system uses the unofficial `garminconnect` library which reverse-engineers Garmin's web interface. This may violate Garmin's Terms of Service.

2. **Health Advice**: AI recommendations are NOT medical advice. Always consult healthcare professionals for medical concerns.

3. **Accuracy**: Data and recommendations are based on algorithms and may not always be accurate. Use your judgment.

4. **Personal Use Only**: This is designed for personal use. Commercial use may require licensing.

---

## ✅ Final Checklist Before Starting

- [ ] Garmin account active and syncing properly
- [ ] Claude API key obtained (anthropic.com)
- [ ] Python 3.10+ installed
- [ ] Development environment ready
- [ ] .env file configured
- [ ] Understand HRV and training load basics
- [ ] Clear training goal defined
- [ ] Ready to commit to using system daily

---

## 🚀 LET'S BUILD IT!

This system will revolutionize your training by:
- ✅ Preventing overtraining and injury
- ✅ Optimizing every workout for your current state
- ✅ Providing personalized AI coaching 24/7
- ✅ Adapting in real-time to your body's signals
- ✅ Helping you achieve your fitness goals faster and safer

---

## 🎬 Quick Start for Claude Code

**Copy and paste this command to Claude Code:**

```
Build me this AI-powered training optimization system based on the specification below.

Start with Phase 1: Foundation
1. Create the complete project structure as defined
2. Set up the database with all tables and relationships
3. Implement GarminService for data fetching with proper authentication
4. Create a manual sync script I can test with my Garmin credentials
5. Add comprehensive error handling and logging

Use Python 3.10+, FastAPI, SQLAlchemy, and the garminconnect library.
Follow the exact structure and naming conventions in the spec.
Include detailed docstrings and comments.

After Phase 1 is complete, I'll test it and we'll move to Phase 2: AI Integration.

[Paste the entire specification here]
```

**Then paste this entire document below that command.**

---

Good luck with your training! 🏃‍♂️💪📊

---

## 📋 Document Revision History

- **Version 1.0** (October 2025) - Initial specification
- Comprehensive training optimization system design
- Daily AI-powered workout recommendations
- Adaptive training plans with real-time adjustments
- Complete implementation guide for Claude Code
