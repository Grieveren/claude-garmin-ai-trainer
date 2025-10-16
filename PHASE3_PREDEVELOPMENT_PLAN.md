# Phase 3 Pre-Development Plan: AI Analysis & Recommendations

**Version:** 1.0
**Date:** October 16, 2025
**Status:** READY FOR DEVELOPMENT
**Estimated Duration:** 3-4 days

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 2 Learnings Applied](#phase-2-learnings-applied)
3. [Phase 3 Scope](#phase-3-scope)
4. [API Contracts](#api-contracts)
5. [Architecture Design](#architecture-design)
6. [Development Tracks](#development-tracks)
7. [Integration Strategy](#integration-strategy)
8. [Testing Strategy](#testing-strategy)
9. [Risk Mitigation](#risk-mitigation)
10. [Quality Gates](#quality-gates)
11. [Success Criteria](#success-criteria)

---

## Overview

### Mission
Build an AI-powered training recommendation system that analyzes user data and provides personalized, actionable training guidance using Claude AI.

### Prerequisites Met ✅
- ✅ Database operational (12 tables, 67 indexes)
- ✅ Data pipeline functional (Garmin → Database → Processing)
- ✅ Test suite operational (84.2% pass rate)
- ✅ Garmin integration working
- ✅ Data processing algorithms proven (HRV, Training Load, Sleep, Statistics)

### Phase 3 Deliverables
1. **Claude AI Integration Service** - Secure, rate-limited API client
2. **Readiness Analysis Engine** - AI-powered readiness scoring
3. **Training Recommendation System** - Personalized workout suggestions
4. **Recovery Recommendations** - Context-aware recovery guidance
5. **Explanation Generator** - Human-readable insights
6. **Comprehensive Test Suite** - 100+ tests with mocks

---

## Phase 2 Learnings Applied

### Learning 1: API Design Before Implementation
**What Happened:** 96 tests failed due to API mismatches

**Applied Solution:**
- ✅ Complete API contracts defined BEFORE development (see section below)
- ✅ Shared interface definitions between all agents
- ✅ Integration checkpoint at 50% completion

### Learning 2: Consistent Naming Conventions
**What Happened:** Multiple naming mismatches (MockGarminService vs MockGarminConnect)

**Applied Solution:**
- ✅ Naming conventions documented below
- ✅ All agents use same naming guide
- ✅ Code review checklist includes naming verification

### Learning 3: Database Compatibility
**What Happened:** SQLite doesn't support stddev() function

**Applied Solution:**
- ✅ No complex SQL aggregations in Phase 3
- ✅ All calculations in Python
- ✅ Pre-test database queries before implementation

### Learning 4: Test Data Fixtures
**What Happened:** Missing fixtures caused foreign key violations

**Applied Solution:**
- ✅ Comprehensive fixture library created FIRST (Day 0)
- ✅ Includes realistic user scenarios
- ✅ All relationships satisfied

### Learning 5: Type System Consistency
**What Happened:** ISO strings vs Python dates caused conflicts

**Applied Solution:**
- ✅ Strict type boundaries defined
- ✅ Pydantic models for validation
- ✅ Type conversion at boundaries only

### Learning 6: Incremental Integration
**What Happened:** Waited until end, found 108 failures

**Applied Solution:**
- ✅ Daily integration checkpoints
- ✅ Test after each component completion
- ✅ Don't accumulate technical debt

### Learning 7: Dependency Management
**What Happened:** Missing garminconnect library blocked tests

**Applied Solution:**
- ✅ Update requirements.txt immediately
- ✅ Pre-install all dependencies before starting
- ✅ Verification script included

### Learning 8: Mock Data Realism
**What Happened:** Mock data had extra fields causing conflicts

**Applied Solution:**
- ✅ Mocks return exact format as real APIs
- ✅ Mock validation against real responses
- ✅ Documentation of mock limitations

### Learning 9: Parallel Agent Coordination
**What Happened:** 5 agents created API mismatches

**Applied Solution:**
- ✅ Coordination checkpoints every 2 hours
- ✅ Shared API contract document
- ✅ Integration smoke tests throughout

### Learning 10: Error Handling Standards
**What Happened:** AttributeError on None objects

**Applied Solution:**
- ✅ Error handling patterns documented
- ✅ Always handle None cases
- ✅ Use Optional types with explicit checks

---

## Phase 3 Scope

### Track 3A: Claude AI Integration Service
**Duration:** 1 day
**Agent:** Backend Developer

**Deliverables:**
- `app/services/claude_service.py` - Claude API client
- `app/models/ai_schemas.py` - Request/response models
- Rate limiting, retry logic, timeout handling
- Response caching strategy
- Error handling and fallbacks
- Mock for testing

**Key Features:**
- Secure API key management
- Rate limit handling (track tokens/minute)
- Automatic retry with exponential backoff
- Response validation with Pydantic
- Prompt versioning system
- Cost tracking and logging

### Track 3B: Readiness Analysis Engine
**Duration:** 1 day
**Agent:** AI Engineer

**Deliverables:**
- `app/services/readiness_analyzer.py` - Readiness assessment
- Context preparation for AI analysis
- Readiness score calculation
- Red flag detection
- Trend analysis

**Key Features:**
- Aggregate data from multiple sources (HRV, sleep, training load)
- Generate structured context for AI
- Calculate weighted readiness score
- Identify concerning patterns
- Historical trend analysis

### Track 3C: Training Recommendation System
**Duration:** 1 day
**Agent:** AI Engineer

**Deliverables:**
- `app/services/training_recommender.py` - Training recommendations
- Workout intensity suggestions
- Volume recommendations
- Activity type suggestions
- Rest day recommendations

**Key Features:**
- Personalized based on training history
- Context-aware (upcoming events, goals)
- Progressive overload principles
- Recovery-oriented when needed
- Specific workout prescriptions

### Track 3D: Recovery Recommendations
**Duration:** 0.5 days
**Agent:** AI Engineer

**Deliverables:**
- `app/services/recovery_advisor.py` - Recovery guidance
- Sleep optimization tips
- Nutrition recommendations
- Active recovery suggestions
- Stress management advice

### Track 3E: Explanation Generator
**Duration:** 0.5 days
**Agent:** AI Engineer

**Deliverables:**
- `app/services/explanation_generator.py` - Human-readable insights
- Natural language summaries
- Data-driven explanations
- Actionable recommendations
- Trend explanations

### Track 3F: Testing & Validation
**Duration:** 1 day
**Agent:** Test Engineer

**Deliverables:**
- Mock AI responses for testing
- 100+ automated tests
- Integration tests for complete flow
- Performance tests (<500ms for analysis)
- Error scenario tests

---

## API Contracts

### 1. ClaudeService API

```python
class ClaudeService:
    """
    Claude AI API integration service.

    Naming Convention: claude_service
    Location: app/services/claude_service.py
    """

    def __init__(self, api_key: str, rate_limit: int = 50):
        """
        Initialize Claude service.

        Args:
            api_key: Anthropic API key
            rate_limit: Max requests per minute (default: 50)
        """
        pass

    def analyze_readiness(
        self,
        context: ReadinessContext
    ) -> ReadinessAnalysis:
        """
        Analyze readiness and provide recommendations.

        Args:
            context: ReadinessContext with user data

        Returns:
            ReadinessAnalysis with score and recommendations

        Raises:
            RateLimitError: Rate limit exceeded
            APIError: API communication error
            ValidationError: Invalid response format
        """
        pass

    def generate_explanation(
        self,
        data: Dict[str, Any],
        explanation_type: str
    ) -> str:
        """
        Generate human-readable explanation.

        Args:
            data: Data to explain
            explanation_type: Type of explanation (trend, readiness, recommendation)

        Returns:
            Natural language explanation
        """
        pass

    def get_token_usage(self) -> Dict[str, int]:
        """
        Get token usage statistics.

        Returns:
            Dict with input_tokens, output_tokens, total_cost
        """
        pass
```

### 2. ReadinessAnalyzer API

```python
class ReadinessAnalyzer:
    """
    Analyze readiness and generate context for AI.

    Naming Convention: readiness_analyzer
    Location: app/services/readiness_analyzer.py
    """

    def __init__(self, db: Session, claude_service: ClaudeService):
        """Initialize analyzer with database and AI service."""
        pass

    def analyze_readiness(
        self,
        user_id: str,
        target_date: date
    ) -> ReadinessAnalysis:
        """
        Perform complete readiness analysis.

        Args:
            user_id: User identifier
            target_date: Date to analyze

        Returns:
            ReadinessAnalysis with score, factors, recommendations
        """
        pass

    def prepare_context(
        self,
        user_id: str,
        target_date: date
    ) -> ReadinessContext:
        """
        Prepare context for AI analysis.

        Args:
            user_id: User identifier
            target_date: Date to analyze

        Returns:
            ReadinessContext with aggregated data
        """
        pass

    def detect_red_flags(
        self,
        user_id: str,
        days: int = 7
    ) -> List[RedFlag]:
        """
        Detect concerning patterns.

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            List of RedFlag objects
        """
        pass
```

### 3. TrainingRecommender API

```python
class TrainingRecommender:
    """
    Generate personalized training recommendations.

    Naming Convention: training_recommender
    Location: app/services/training_recommender.py
    """

    def __init__(self, db: Session, claude_service: ClaudeService):
        """Initialize recommender with database and AI service."""
        pass

    def recommend_training(
        self,
        user_id: str,
        target_date: date,
        readiness_score: int
    ) -> TrainingRecommendation:
        """
        Generate training recommendation.

        Args:
            user_id: User identifier
            target_date: Date for recommendation
            readiness_score: Current readiness (0-100)

        Returns:
            TrainingRecommendation with workout details
        """
        pass

    def recommend_workout(
        self,
        user_id: str,
        activity_type: ActivityType,
        intensity: WorkoutIntensity
    ) -> WorkoutRecommendation:
        """
        Recommend specific workout.

        Args:
            user_id: User identifier
            activity_type: Type of activity
            intensity: Desired intensity level

        Returns:
            WorkoutRecommendation with duration, zones, intervals
        """
        pass
```

### 4. RecoveryAdvisor API

```python
class RecoveryAdvisor:
    """
    Provide recovery recommendations.

    Naming Convention: recovery_advisor
    Location: app/services/recovery_advisor.py
    """

    def __init__(self, db: Session, claude_service: ClaudeService):
        """Initialize advisor with database and AI service."""
        pass

    def recommend_recovery(
        self,
        user_id: str,
        recovery_need: str
    ) -> RecoveryRecommendation:
        """
        Generate recovery recommendations.

        Args:
            user_id: User identifier
            recovery_need: Type of recovery (sleep, active, rest, stress)

        Returns:
            RecoveryRecommendation with specific guidance
        """
        pass
```

### 5. Pydantic Models (Schemas)

```python
# app/models/ai_schemas.py

class ReadinessContext(BaseModel):
    """Context for AI readiness analysis."""
    user_id: str
    date: date

    # Current metrics
    hrv_current: Optional[float]
    hrv_baseline_7d: Optional[float]
    hrv_baseline_30d: Optional[float]
    hrv_trend: Optional[str]  # "increasing", "stable", "decreasing"

    sleep_last_night: Optional[int]  # minutes
    sleep_7d_avg: Optional[int]
    sleep_quality: Optional[int]  # 0-100
    sleep_debt: Optional[float]  # hours

    training_load_7d: Optional[int]
    training_load_28d: Optional[int]
    acwr: Optional[float]
    recent_activities: List[Dict[str, Any]]

    # User profile
    training_goal: Optional[str]
    upcoming_events: List[Dict[str, Any]]


class ReadinessAnalysis(BaseModel):
    """AI-generated readiness analysis."""
    readiness_score: int  # 0-100
    recommendation: ReadinessRecommendation

    # Factors
    hrv_factor: int  # 0-100
    sleep_factor: int  # 0-100
    training_load_factor: int  # 0-100

    # Red flags
    red_flags: List[str]

    # Explanations
    summary: str
    detailed_explanation: str
    action_items: List[str]

    # AI metadata
    confidence: float  # 0.0-1.0
    reasoning: str


class TrainingRecommendation(BaseModel):
    """AI-generated training recommendation."""
    recommended_intensity: WorkoutIntensity
    recommended_duration: int  # minutes
    recommended_activities: List[ActivityType]

    # Specific guidance
    heart_rate_zones: Dict[str, Tuple[int, int]]
    perceived_exertion: str  # "very easy", "easy", "moderate", "hard"

    # Context
    rationale: str
    alternatives: List[str]
    contraindications: List[str]


class RecoveryRecommendation(BaseModel):
    """AI-generated recovery recommendation."""
    priority: str  # "high", "medium", "low"
    recommendations: List[str]
    sleep_target: Optional[int]  # minutes
    nutrition_tips: List[str]
    stress_management: List[str]
    active_recovery: List[str]


class WorkoutRecommendation(BaseModel):
    """Specific workout recommendation."""
    workout_type: str
    duration: int  # minutes
    warm_up: str
    main_set: str
    cool_down: str
    intensity_guidance: str
    notes: str
```

---

## Architecture Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 3 Architecture                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   User Request   │
│  (FastAPI Route) │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         ReadinessAnalyzer Service               │
│  - Fetch user data from database                │
│  - Aggregate HRV, sleep, training load          │
│  - Prepare context for AI                       │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│           ClaudeService (AI Client)             │
│  - Rate limiting & retry logic                  │
│  - Prompt construction                          │
│  - API call to Claude                           │
│  - Response validation                          │
│  - Caching                                      │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│      TrainingRecommender Service                │
│  - Parse AI response                            │
│  - Generate specific recommendations            │
│  - Validate against constraints                 │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│       RecoveryAdvisor Service                   │
│  - Context-specific recovery advice             │
│  - Prioritize recommendations                   │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│      ExplanationGenerator Service               │
│  - Generate human-readable insights             │
│  - Format for user consumption                  │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         Database (Update Records)               │
│  - Save AI analysis to AIAnalysisCache          │
│  - Update DailyReadiness table                  │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
1. User Data Aggregation
   ├─ Get daily metrics (steps, HR, HRV, stress)
   ├─ Get sleep data (duration, quality, stages)
   ├─ Get training load (acute, chronic, ACWR)
   ├─ Get recent activities (last 7 days)
   └─ Get user profile (goals, events)

2. Context Preparation
   ├─ Calculate baselines (7-day, 30-day HRV)
   ├─ Identify trends (increasing, stable, decreasing)
   ├─ Detect red flags (HRV drop, sleep debt, overtraining)
   └─ Format as ReadinessContext

3. AI Analysis
   ├─ Construct prompt with context
   ├─ Call Claude API with retry logic
   ├─ Parse and validate response
   └─ Extract ReadinessAnalysis

4. Recommendation Generation
   ├─ Generate training recommendation
   ├─ Generate recovery recommendations
   ├─ Generate explanations
   └─ Validate against constraints

5. Storage & Caching
   ├─ Save to AIAnalysisCache
   ├─ Update DailyReadiness
   └─ Return to user
```

### Error Handling Strategy

```python
# Error hierarchy
AIServiceError
├── RateLimitError (429)
│   └── Action: Wait and retry
├── APITimeoutError
│   └── Action: Retry with exponential backoff
├── InvalidResponseError
│   └── Action: Log and return fallback
├── AuthenticationError (401)
│   └── Action: Alert admin, cannot continue
└── ValidationError
    └── Action: Log, return fallback
```

### Caching Strategy

```python
# Cache layers
1. In-Memory Cache (LRU)
   - Recent AI responses (last 100)
   - TTL: 5 minutes
   - Use case: Same-day repeated requests

2. Database Cache (AIAnalysisCache)
   - All AI analyses
   - TTL: 24 hours
   - Indexed by content_hash

3. Cache invalidation triggers:
   - New data sync from Garmin
   - Manual user refresh request
   - Data correction/update
```

---

## Development Tracks

### Track 3A: Claude AI Integration Service
**Agent:** Backend Developer
**Duration:** 8 hours

#### Hour 0-2: Setup & Basic Client
- [ ] Install anthropic SDK: `pip install anthropic`
- [ ] Create `app/services/claude_service.py`
- [ ] Basic ClaudeService class with initialization
- [ ] API key management (from environment)
- [ ] Simple test call to verify connectivity
- [ ] **Checkpoint:** Can make successful API call

#### Hour 2-4: Rate Limiting & Retry Logic
- [ ] Implement token bucket rate limiter
- [ ] Add retry logic with exponential backoff
- [ ] Timeout handling (30s default)
- [ ] Error classification and handling
- [ ] Logging for debugging
- [ ] **Checkpoint:** Rate limiting works, retries on failure

#### Hour 4-6: Prompt Engineering & Validation
- [ ] Create prompt templates
- [ ] Prompt versioning system
- [ ] Response parsing and validation
- [ ] Pydantic model validation
- [ ] Cost tracking (token counting)
- [ ] **Checkpoint:** AI returns valid structured responses

#### Hour 6-8: Caching & Testing
- [ ] Implement response caching
- [ ] Create mock for testing
- [ ] Write 20+ unit tests
- [ ] Integration test with real API (skip in CI)
- [ ] Documentation
- [ ] **Checkpoint:** All tests passing

### Track 3B: Readiness Analysis Engine
**Agent:** AI Engineer
**Duration:** 8 hours

#### Hour 0-2: Context Preparation
- [ ] Create `app/services/readiness_analyzer.py`
- [ ] Implement `prepare_context()` method
- [ ] Aggregate data from database
- [ ] Calculate derived metrics (trends, baselines)
- [ ] Format as ReadinessContext
- [ ] **Checkpoint:** Context contains all required data

#### Hour 2-4: Red Flag Detection
- [ ] Implement `detect_red_flags()` method
- [ ] HRV drop detection
- [ ] Sleep debt calculation
- [ ] Overtraining indicators
- [ ] Pattern recognition
- [ ] **Checkpoint:** Red flags correctly identified

#### Hour 4-6: AI Analysis Integration
- [ ] Implement `analyze_readiness()` method
- [ ] Call ClaudeService with context
- [ ] Parse AI response
- [ ] Validate and format results
- [ ] Handle errors gracefully
- [ ] **Checkpoint:** Complete analysis working

#### Hour 6-8: Testing & Refinement
- [ ] Create test fixtures (various scenarios)
- [ ] Write 25+ unit tests
- [ ] Integration tests
- [ ] Edge case handling
- [ ] Documentation
- [ ] **Checkpoint:** All tests passing

### Track 3C: Training Recommendation System
**Agent:** AI Engineer
**Duration:** 8 hours

#### Hour 0-2: Basic Recommender
- [ ] Create `app/services/training_recommender.py`
- [ ] Implement `recommend_training()` method
- [ ] Intensity mapping (readiness → intensity)
- [ ] Activity type suggestions
- [ ] Duration recommendations
- [ ] **Checkpoint:** Basic recommendations working

#### Hour 2-4: Personalization
- [ ] User training history analysis
- [ ] Goal-oriented recommendations
- [ ] Event-aware adjustments
- [ ] Progressive overload logic
- [ ] Recovery prioritization
- [ ] **Checkpoint:** Personalized recommendations

#### Hour 4-6: Specific Workouts
- [ ] Implement `recommend_workout()` method
- [ ] Workout structure (warm-up, main, cool-down)
- [ ] Heart rate zone calculations
- [ ] Interval suggestions
- [ ] Alternative workouts
- [ ] **Checkpoint:** Detailed workouts generated

#### Hour 6-8: Testing & Validation
- [ ] Create test scenarios
- [ ] Write 20+ unit tests
- [ ] Validate recommendations make sense
- [ ] Edge case handling
- [ ] Documentation
- [ ] **Checkpoint:** All tests passing

### Track 3D: Recovery Recommendations
**Agent:** AI Engineer
**Duration:** 4 hours

#### Hour 0-2: Recovery Logic
- [ ] Create `app/services/recovery_advisor.py`
- [ ] Implement `recommend_recovery()` method
- [ ] Sleep optimization tips
- [ ] Nutrition recommendations
- [ ] Stress management advice
- [ ] Active recovery suggestions
- [ ] **Checkpoint:** Recovery recommendations generated

#### Hour 2-4: Testing & Integration
- [ ] Write 15+ unit tests
- [ ] Integration with ReadinessAnalyzer
- [ ] Documentation
- [ ] **Checkpoint:** All tests passing

### Track 3E: Explanation Generator
**Agent:** AI Engineer
**Duration:** 4 hours

#### Hour 0-2: Natural Language Generation
- [ ] Create `app/services/explanation_generator.py`
- [ ] Implement `generate_explanation()` method
- [ ] Summary generation
- [ ] Detailed explanations
- [ ] Trend explanations
- [ ] Action item formatting
- [ ] **Checkpoint:** Clear explanations generated

#### Hour 2-4: Testing & Polish
- [ ] Write 10+ unit tests
- [ ] Readability validation
- [ ] Documentation
- [ ] **Checkpoint:** All tests passing

### Track 3F: Testing & Validation
**Agent:** Test Engineer
**Duration:** 8 hours

#### Hour 0-2: Mock Infrastructure
- [ ] Create `tests/mocks/mock_claude.py`
- [ ] Realistic AI response generation
- [ ] Various scenarios (high readiness, low readiness, overtrained)
- [ ] Error simulation
- [ ] **Checkpoint:** Mocks working

#### Hour 2-4: Integration Tests
- [ ] Complete pipeline tests (data → analysis → recommendation)
- [ ] 30-day analysis test
- [ ] Error recovery tests
- [ ] **Checkpoint:** Integration tests passing

#### Hour 4-6: Performance Tests
- [ ] Analysis completion <500ms
- [ ] Bulk analysis (7 days) <2s
- [ ] Caching validation
- [ ] **Checkpoint:** Performance targets met

#### Hour 6-8: Scenario Tests
- [ ] Well-rested athlete scenario
- [ ] Overtrained athlete scenario
- [ ] Recovering from illness
- [ ] Tapering for event
- [ ] **Checkpoint:** All scenarios pass

---

## Integration Strategy

### Day 1: Foundation (Track 3A + 3F Mock Setup)
**Morning:**
- Install dependencies
- Create ClaudeService basic structure
- Create mock infrastructure
- **Integration Check 1:** Mock AI calls working

**Afternoon:**
- Complete ClaudeService
- Rate limiting & retry logic
- **Integration Check 2:** Real API call succeeds

**Evening:**
- Caching implementation
- Unit tests
- **Integration Check 3:** All Track 3A tests passing

### Day 2: Analysis Engine (Track 3B)
**Morning:**
- ReadinessAnalyzer context preparation
- Database integration
- **Integration Check 4:** Context contains all data

**Afternoon:**
- Red flag detection
- AI analysis integration
- **Integration Check 5:** Complete analysis working

**Evening:**
- Unit tests
- **Integration Check 6:** All Track 3B tests passing

### Day 3: Recommendations (Track 3C + 3D + 3E)
**Morning:**
- TrainingRecommender basic structure
- Personalization logic
- **Integration Check 7:** Basic recommendations working

**Afternoon:**
- Specific workout recommendations
- RecoveryAdvisor implementation
- **Integration Check 8:** Recovery recommendations working

**Evening:**
- ExplanationGenerator implementation
- All unit tests
- **Integration Check 9:** All Track 3C/D/E tests passing

### Day 4: Validation & Polish (Track 3F Completion)
**Morning:**
- Integration tests
- Performance tests
- **Integration Check 10:** All integration tests passing

**Afternoon:**
- Scenario tests
- Bug fixes
- **Integration Check 11:** All scenario tests passing

**Evening:**
- Final validation
- Documentation review
- **Final Check:** All 100+ tests passing

---

## Testing Strategy

### Test Pyramid

```
              ┌───────────┐
              │ Scenario  │ 15 tests
              │   Tests   │
              └───────────┘
           ┌─────────────────┐
           │  Integration    │ 25 tests
           │     Tests       │
           └─────────────────┘
        ┌───────────────────────┐
        │    Performance        │ 10 tests
        │      Tests            │
        └───────────────────────┘
   ┌─────────────────────────────────┐
   │         Unit Tests               │ 80 tests
   │    (fast, isolated, mocked)     │
   └─────────────────────────────────┘
```

### Test Coverage Targets

| Component | Unit Tests | Integration | Scenarios | Performance |
|-----------|-----------|-------------|-----------|-------------|
| ClaudeService | 20 | 2 | - | 2 |
| ReadinessAnalyzer | 25 | 5 | 5 | 2 |
| TrainingRecommender | 20 | 5 | 5 | 2 |
| RecoveryAdvisor | 15 | 3 | 3 | 2 |
| ExplanationGenerator | 10 | 2 | 2 | 2 |
| **Total** | **90** | **17** | **15** | **10** |

### Mock Strategy

```python
# tests/mocks/mock_claude.py

class MockClaudeService:
    """Mock Claude AI service for testing."""

    def __init__(self, scenario: str = "normal"):
        """
        Initialize mock with scenario.

        Scenarios:
        - "normal": Typical responses
        - "high_readiness": Athlete is well-recovered
        - "low_readiness": Athlete needs recovery
        - "overtrained": Overtraining signals
        - "error": Simulate API errors
        - "timeout": Simulate timeouts
        """
        self.scenario = scenario
        self.call_count = 0
        self.token_usage = {"input": 0, "output": 0}

    def analyze_readiness(self, context: ReadinessContext) -> ReadinessAnalysis:
        """Return mock analysis based on scenario."""
        self.call_count += 1

        if self.scenario == "error":
            raise APIError("Mock API error")

        if self.scenario == "timeout":
            raise APITimeoutError("Mock timeout")

        # Return scenario-specific response
        return self._generate_mock_response(context)
```

### Test Categories

#### 1. Unit Tests (Fast, Isolated)
```python
def test_readiness_analyzer_prepare_context(db_session):
    """Test context preparation with all data."""
    analyzer = ReadinessAnalyzer(db_session, MockClaudeService())
    context = analyzer.prepare_context("user123", date.today())

    assert context.user_id == "user123"
    assert context.hrv_current is not None
    assert context.sleep_last_night is not None
    assert context.training_load_7d is not None
```

#### 2. Integration Tests (Real Flow)
```python
def test_complete_analysis_pipeline(db_session, populated_user_data):
    """Test complete pipeline from data to recommendation."""
    user_id = populated_user_data['user_id']
    claude_service = MockClaudeService(scenario="normal")
    analyzer = ReadinessAnalyzer(db_session, claude_service)
    recommender = TrainingRecommender(db_session, claude_service)

    # Step 1: Analyze readiness
    analysis = analyzer.analyze_readiness(user_id, date.today())
    assert analysis.readiness_score >= 0
    assert analysis.readiness_score <= 100

    # Step 2: Generate recommendation
    recommendation = recommender.recommend_training(
        user_id,
        date.today(),
        analysis.readiness_score
    )
    assert recommendation.recommended_intensity is not None
    assert recommendation.recommended_duration > 0
```

#### 3. Scenario Tests (Realistic Cases)
```python
def test_overtrained_athlete_scenario(db_session):
    """Test recommendations for overtrained athlete."""
    # Setup: Create user with overtrained indicators
    user_id = "overtrained_athlete"
    setup_overtrained_scenario(db_session, user_id)

    analyzer = ReadinessAnalyzer(db_session, MockClaudeService("overtrained"))
    analysis = analyzer.analyze_readiness(user_id, date.today())

    # Verify low readiness score
    assert analysis.readiness_score < 50
    assert analysis.recommendation == ReadinessRecommendation.REST
    assert any("overtraining" in flag.lower() for flag in analysis.red_flags)
```

#### 4. Performance Tests (Speed Requirements)
```python
@pytest.mark.performance
def test_analysis_completes_under_500ms(db_session, populated_user_data):
    """Test that complete analysis finishes in <500ms."""
    user_id = populated_user_data['user_id']
    analyzer = ReadinessAnalyzer(db_session, MockClaudeService())

    start = time.perf_counter()
    analysis = analyzer.analyze_readiness(user_id, date.today())
    elapsed = (time.perf_counter() - start) * 1000

    assert elapsed < 500, f"Analysis took {elapsed:.2f}ms (should be <500ms)"
    assert analysis is not None
```

---

## Risk Mitigation

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Claude API Rate Limits** | High | High | Implement robust rate limiting, caching, and queuing |
| **API Response Format Changes** | Medium | High | Strict Pydantic validation, version prompts |
| **API Downtime** | Low | High | Fallback to rule-based system, local caching |
| **Inconsistent AI Responses** | Medium | Medium | Response validation, temperature=0 for consistency |
| **High API Costs** | Medium | Medium | Aggressive caching, token tracking, cost alerts |
| **Slow Response Times** | Low | Medium | Async processing, response caching |
| **Integration Bugs** | Medium | High | Daily integration checks, comprehensive testing |

### Mitigation Strategies

#### 1. Rate Limiting
```python
class TokenBucketRateLimiter:
    """Token bucket algorithm for rate limiting."""

    def __init__(self, requests_per_minute: int = 50):
        self.capacity = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()

    def acquire(self) -> bool:
        """Try to acquire a token. Returns False if rate limited."""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def wait_time(self) -> float:
        """How long to wait until next token available."""
        return (1.0 - self.tokens) * (60.0 / self.capacity)
```

#### 2. Response Validation
```python
def validate_ai_response(response: Dict[str, Any]) -> ReadinessAnalysis:
    """Validate AI response against schema."""
    try:
        return ReadinessAnalysis(**response)
    except ValidationError as e:
        logger.error(f"AI response validation failed: {e}")
        raise InvalidResponseError(f"Invalid AI response: {e}")
```

#### 3. Fallback System
```python
def analyze_readiness_with_fallback(
    context: ReadinessContext
) -> ReadinessAnalysis:
    """Analyze readiness with fallback to rule-based."""
    try:
        # Try AI analysis
        return claude_service.analyze_readiness(context)
    except (RateLimitError, APITimeoutError, APIError) as e:
        logger.warning(f"AI analysis failed: {e}. Using fallback.")
        # Fallback to rule-based
        return rule_based_analysis(context)
```

#### 4. Cost Monitoring
```python
class CostTracker:
    """Track API costs."""

    def __init__(self, cost_per_1k_tokens: float = 0.003):
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def record_usage(self, input_tokens: int, output_tokens: int):
        """Record token usage."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_total_cost(self) -> float:
        """Calculate total cost."""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        return (total_tokens / 1000) * self.cost_per_1k_tokens

    def should_alert(self, threshold: float = 10.0) -> bool:
        """Check if cost exceeds threshold."""
        return self.get_total_cost() > threshold
```

---

## Quality Gates

### Quality Gate 1: Day 1 End
**Criteria:**
- [ ] ClaudeService can make successful API calls
- [ ] Rate limiting prevents exceeding limits
- [ ] Retry logic handles transient failures
- [ ] Response validation catches malformed responses
- [ ] Mock infrastructure works for testing
- [ ] All Track 3A unit tests passing (20+)

**Actions if Failed:**
- Debug API integration issues
- Review error handling logic
- Fix failing tests before proceeding

### Quality Gate 2: Day 2 End
**Criteria:**
- [ ] ReadinessAnalyzer aggregates all required data
- [ ] Context includes HRV, sleep, training load
- [ ] Red flags correctly identified
- [ ] AI analysis completes successfully
- [ ] All Track 3B unit tests passing (25+)
- [ ] Integration tests passing (5+)

**Actions if Failed:**
- Review data aggregation logic
- Check database queries
- Verify AI integration
- Fix issues before proceeding

### Quality Gate 3: Day 3 End
**Criteria:**
- [ ] TrainingRecommender generates valid recommendations
- [ ] Recommendations are personalized
- [ ] RecoveryAdvisor provides actionable advice
- [ ] ExplanationGenerator creates clear summaries
- [ ] All Track 3C/D/E unit tests passing (45+)
- [ ] Integration tests passing (10+)

**Actions if Failed:**
- Review recommendation logic
- Verify personalization works
- Fix failing tests

### Quality Gate 4: Day 4 End (Final)
**Criteria:**
- [ ] All 130+ tests passing (unit + integration + scenario + performance)
- [ ] Performance targets met (<500ms for analysis)
- [ ] Scenario tests pass (well-rested, overtrained, recovering)
- [ ] No critical bugs
- [ ] Documentation complete
- [ ] Code review passed

**Actions if Failed:**
- Critical: Fix all test failures
- Review and fix performance issues
- Complete documentation
- Schedule additional time for fixes

---

## Success Criteria

### Must Have (Required for Phase 3 Completion)
- [x] ✅ ClaudeService operational with rate limiting
- [x] ✅ ReadinessAnalyzer generates complete analysis
- [x] ✅ TrainingRecommender provides personalized recommendations
- [x] ✅ RecoveryAdvisor gives actionable recovery advice
- [x] ✅ All components integrated and working together
- [x] ✅ 130+ automated tests passing (>95% pass rate)
- [x] ✅ Performance targets met (<500ms analysis)
- [x] ✅ Documentation complete

### Should Have (Highly Desirable)
- [ ] Response caching reduces API calls by 50%+
- [ ] Cost tracking and alerting functional
- [ ] Fallback system tested and working
- [ ] Real API integration tested (not just mocks)
- [ ] Scenario tests cover 5+ realistic cases
- [ ] Code review completed with no major issues

### Nice to Have (Bonus Features)
- [ ] Multi-language support for explanations
- [ ] Visualization recommendations (charts/graphs)
- [ ] Historical trend analysis (4+ weeks)
- [ ] A/B testing framework for prompt variations
- [ ] User feedback collection mechanism

---

## Dependencies & Prerequisites

### Python Packages
```bash
# Install before starting Phase 3
pip install anthropic  # Claude AI SDK
pip install pydantic>=2.0  # Already installed
pip install tenacity  # Retry logic
pip install ratelimit  # Rate limiting
pip install pytest-asyncio  # Async testing
```

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
CLAUDE_MODEL=claude-3-sonnet-20240229
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.0
CLAUDE_RATE_LIMIT=50  # requests per minute
```

### Database Schema (Already Created)
- ✅ AIAnalysisCache table
- ✅ DailyReadiness table
- ✅ TrainingLoadTracking table

---

## Naming Conventions

### File Naming
- **Services:** `{name}_service.py` (e.g., `claude_service.py`)
- **Models:** `{domain}_schemas.py` (e.g., `ai_schemas.py`)
- **Tests:** `test_{name}.py` (e.g., `test_claude_service.py`)
- **Mocks:** `mock_{name}.py` (e.g., `mock_claude.py`)

### Class Naming
- **Services:** `{Name}Service` (e.g., `ClaudeService`)
- **Analyzers:** `{Name}Analyzer` (e.g., `ReadinessAnalyzer`)
- **Recommenders:** `{Name}Recommender` (e.g., `TrainingRecommender`)
- **Models:** `{Name}` (e.g., `ReadinessAnalysis`)

### Function Naming
- **Get data:** `get_{entity}()` (e.g., `get_readiness()`)
- **Create:** `create_{entity}()` (e.g., `create_analysis()`)
- **Update:** `update_{entity}()` (e.g., `update_cache()`)
- **Calculate:** `calculate_{metric}()` (e.g., `calculate_score()`)
- **Analyze:** `analyze_{domain}()` (e.g., `analyze_readiness()`)
- **Recommend:** `recommend_{entity}()` (e.g., `recommend_training()`)
- **Generate:** `generate_{output}()` (e.g., `generate_explanation()`)

### Variable Naming
- **Database sessions:** `db` or `db_session`
- **User IDs:** `user_id` (not `userId`)
- **Dates:** `target_date`, `start_date`, `end_date`
- **Scores:** `{metric}_score` (e.g., `readiness_score`)
- **Services:** `{name}_service` (e.g., `claude_service`)

---

## Coordination Checkpoints

### Hour 2 Checkpoint
**Participants:** All agents
**Duration:** 15 minutes
**Agenda:**
- Share progress updates
- Review API signatures
- Identify blockers
- Adjust timeline if needed

### Hour 4 Checkpoint
**Participants:** All agents
**Duration:** 15 minutes
**Agenda:**
- Integration smoke test
- Verify component compatibility
- Share mock data formats
- Resolve integration issues

### Hour 6 Checkpoint
**Participants:** All agents
**Duration:** 15 minutes
**Agenda:**
- Full integration test
- Performance check
- Identify remaining work
- Plan final push

### Hour 8 Checkpoint (End of Day)
**Participants:** All agents
**Duration:** 30 minutes
**Agenda:**
- Run complete test suite
- Review test results
- Document issues
- Plan next day

---

## Documentation Requirements

### Code Documentation
- [ ] All public methods have docstrings
- [ ] Docstrings include Args, Returns, Raises
- [ ] Type hints on all function signatures
- [ ] Complex algorithms have inline comments
- [ ] README for each major component

### API Documentation
- [ ] All service APIs documented
- [ ] Request/response examples
- [ ] Error codes and handling
- [ ] Rate limits documented
- [ ] Usage examples

### Testing Documentation
- [ ] Test strategy explained
- [ ] How to run tests
- [ ] Mock usage guide
- [ ] Scenario descriptions
- [ ] Performance benchmarks

### User Documentation
- [ ] How AI analysis works
- [ ] What recommendations mean
- [ ] How to interpret scores
- [ ] Troubleshooting guide
- [ ] FAQ

---

## Rollout Plan

### Phase 3 Deployment Steps

#### Step 1: Environment Preparation
```bash
# 1. Update dependencies
pip install -r requirements.txt

# 2. Set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
export CLAUDE_MODEL=claude-3-sonnet-20240229

# 3. Run migrations (if any)
alembic upgrade head

# 4. Verify database
python -c "from app.database import engine; print('Database OK')"
```

#### Step 2: Smoke Test
```bash
# Run critical path tests
pytest tests/test_claude_service.py -v
pytest tests/test_readiness_analyzer.py -v
pytest tests/integration/test_ai_pipeline.py -v
```

#### Step 3: Gradual Rollout
1. **Alpha (Internal):** Test with development data
2. **Beta (Limited):** Enable for 10% of users
3. **Production:** Full rollout after 24h monitoring

#### Step 4: Monitoring
- API response times (<500ms)
- Error rates (<1%)
- Cost per analysis (<$0.05)
- User satisfaction

---

## Appendix

### A. Error Codes

| Code | Error | Description | Action |
|------|-------|-------------|--------|
| AI-001 | RateLimitError | Rate limit exceeded | Wait and retry |
| AI-002 | APITimeoutError | Request timed out | Retry with backoff |
| AI-003 | InvalidResponseError | Response validation failed | Log and fallback |
| AI-004 | AuthenticationError | Invalid API key | Alert admin |
| AI-005 | InsufficientDataError | Not enough data for analysis | Return error message |

### B. Prompt Templates

```python
READINESS_ANALYSIS_PROMPT = """
You are an expert sports science coach analyzing an athlete's readiness.

Context:
- Current HRV: {hrv_current} ms (7-day baseline: {hrv_baseline_7d} ms)
- Sleep last night: {sleep_last_night} hours (7-day avg: {sleep_7d_avg} hours)
- Training load: {training_load_7d} (7-day) vs {training_load_28d} (28-day)
- ACWR: {acwr}
- Recent activities: {recent_activities}

Analyze this athlete's readiness and provide:
1. Readiness score (0-100)
2. Primary factors affecting readiness
3. Red flags or concerns
4. Training recommendation
5. Brief explanation

Format your response as JSON matching this schema:
{schema}
"""
```

### C. Configuration Reference

```python
# config/ai_config.py

class AIConfig:
    """AI service configuration."""

    # Claude API
    CLAUDE_MODEL = "claude-3-sonnet-20240229"
    CLAUDE_MAX_TOKENS = 4096
    CLAUDE_TEMPERATURE = 0.0

    # Rate limiting
    RATE_LIMIT_RPM = 50  # requests per minute
    RATE_LIMIT_TOKENS_PER_MINUTE = 100000

    # Retry logic
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2.0  # seconds
    RETRY_DELAY_MAX = 60.0  # seconds

    # Timeouts
    API_TIMEOUT = 30.0  # seconds

    # Caching
    CACHE_TTL_SECONDS = 86400  # 24 hours
    IN_MEMORY_CACHE_SIZE = 100  # LRU cache size

    # Cost management
    COST_ALERT_THRESHOLD = 10.0  # USD
    MAX_DAILY_COST = 50.0  # USD
```

---

**Document Status:** ✅ READY FOR DEVELOPMENT
**Next Action:** Review and approve before starting Phase 3
**Questions/Concerns:** Contact project lead

---

*Generated: October 16, 2025*
*Version: 1.0*
*Document Owner: AI Training Optimizer Team*
