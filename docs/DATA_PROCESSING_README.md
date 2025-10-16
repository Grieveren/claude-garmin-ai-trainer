# Data Processing & Analytics Module

## Overview

The Data Processing & Analytics module is the core calculation engine of the AI Training Optimizer. It processes raw health and activity data from Garmin devices to generate actionable training insights and readiness recommendations.

## Features

### ✅ Implemented (Phase 2 - Track 2C)

1. **Statistical Functions** (`app/utils/statistics.py`)
   - Moving averages (simple and exponential)
   - Standard deviation and variance
   - Percentile calculations
   - Outlier detection (IQR and Z-score methods)
   - Linear regression for trend analysis
   - Rolling statistics
   - Coefficient of variation
   - Rate of change calculations

2. **HRV Analysis** (`app/utils/hrv_analysis.py`)
   - 7-day and 30-day baseline calculations
   - HRV trend detection (improving/declining/stable)
   - Drop detection with severity levels
   - Recovery status assessment
   - Coefficient of variation for consistency
   - Comprehensive HRV status with recommendations

3. **Training Load Calculations** (`app/utils/training_load.py`)
   - Acute load (7-day rolling average)
   - Chronic load (28-day rolling average)
   - **ACWR** (Acute:Chronic Workload Ratio) with injury risk classification
   - **Fitness-Fatigue Model** (Banister model)
     - Fitness calculation (42-day decay)
     - Fatigue calculation (7-day decay)
     - Form/TSB calculation
   - Training monotony and strain
   - Weekly ramp rate
   - Recovery time estimation

4. **Sleep Analysis** (`app/utils/sleep_analysis.py`)
   - Sleep quality score (0-100) with weighted components:
     - Duration score (40%)
     - Sleep stages score (30%)
     - Disruption score (30%)
   - Sleep debt detection and tracking
   - 7-day sleep averages
   - Sleep consistency analysis
   - Recovery impact assessment

5. **Data Aggregation** (`app/services/aggregation_service.py`)
   - Daily summary (complete day overview)
   - Weekly summary (7-day aggregation)
   - Monthly summary (30-day trends)
   - Training volume by type
   - Performance highlights

6. **Main Data Processor** (`app/services/data_processor.py`)
   - Orchestrates all calculations
   - Calculates overall readiness score
   - Generates training recommendations
   - Updates TrainingLoadTracking table
   - Updates DailyReadiness table
   - Result caching for performance
   - Batch processing for date ranges

## Quick Start

### Basic Usage

```python
from app.services.data_processor import DataProcessor
from app.database import get_db_context

# Process today's data
with get_db_context() as db:
    processor = DataProcessor(db)

    # Get readiness summary
    summary = processor.get_readiness_summary("user123")

    print(f"Readiness Score: {summary['readiness_score']}/100")
    print(f"Recommendation: {summary['recommendation']}")
    print(f"Intensity: {summary['recommended_intensity']}")
```

### Calculate Specific Metrics

```python
from app.utils import hrv_analysis, training_load, sleep_analysis
from datetime import date

with get_db_context() as db:
    # HRV status
    hrv_status = hrv_analysis.get_hrv_status(db, "user123", date.today())
    print(f"HRV Status: {hrv_status['status']}")
    print(f"HRV: {hrv_status['current_hrv']} ms (Baseline: {hrv_status['baseline_7d']} ms)")

    # Training load
    load_status = training_load.get_training_load_status(db, "user123", date.today())
    print(f"ACWR: {load_status['acwr']['acwr']:.2f}")
    print(f"Form: {load_status['fitness_fatigue']['form']:.1f}")

    # Sleep
    sleep_status = sleep_analysis.get_sleep_status(db, "user123", date.today())
    print(f"Sleep Quality: {sleep_status['last_night']['score']}/100")
    print(f"Sleep Debt: {sleep_status['sleep_debt']['total_debt_hours']:.1f} hours")
```

### Batch Processing

```python
from datetime import date, timedelta

with get_db_context() as db:
    processor = DataProcessor(db)

    # Process last 30 days
    start = date.today() - timedelta(days=30)
    end = date.today()

    result = processor.process_date_range("user123", start, end)
    print(f"Processed {result['processed_count']} days")
```

## Architecture

### Data Flow

```
Raw Data (Garmin API)
    ↓
DailyMetrics, Activity, SleepSession
    ↓
Statistical Functions
    ↓
Analysis Utilities (HRV, Load, Sleep)
    ↓
Data Processor (Orchestration)
    ↓
TrainingLoadTracking, DailyReadiness
    ↓
API Response / Frontend
```

### Module Structure

```
app/
├── utils/                      # Calculation utilities
│   ├── statistics.py          # Core statistical functions
│   ├── hrv_analysis.py        # HRV calculations
│   ├── training_load.py       # Training load & ACWR
│   └── sleep_analysis.py      # Sleep analysis
│
├── services/                   # High-level services
│   ├── data_processor.py      # Main orchestrator
│   └── aggregation_service.py # Data aggregation
│
└── models/
    └── database_models.py     # Data models
```

## Key Metrics

### Readiness Score Components

The overall readiness score (0-100) is calculated as:

```
Readiness = (HRV_Score × 0.40) + (Sleep_Score × 0.35) + (Load_Score × 0.25)
```

**Weight Rationale:**
- **HRV (40%)**: Most direct indicator of acute recovery status
- **Sleep (35%)**: Critical foundation for recovery and performance
- **Training Load (25%)**: Context for training stimulus and adaptation

### Interpretation

| Score | Status | Training Recommendation |
|-------|--------|------------------------|
| 85-100 | Excellent | High-intensity training or competition |
| 70-84 | Good | Quality training sessions |
| 55-69 | Fair | Easy to moderate training |
| 0-54 | Poor | Rest or very easy recovery |

## Formulas Documentation

All formulas are comprehensively documented in [`DATA_PROCESSING_FORMULAS.md`](./DATA_PROCESSING_FORMULAS.md) including:

- Mathematical formulas with explanations
- Implementation details
- Scientific references
- Interpretation guidelines

### Key Formulas Summary

**ACWR (Injury Risk)**:
```
ACWR = Acute Load (7d) / Chronic Load (28d)
Optimal range: 0.8 - 1.3
```

**Fitness-Fatigue Model**:
```
Fitness(t) = Σ(load[i] × e^(-(t-i)/42))
Fatigue(t) = Σ(load[i] × e^(-(t-i)/7))
Form(t) = Fitness(t) - Fatigue(t)
```

**Sleep Quality Score**:
```
Score = (Duration × 0.4) + (Stages × 0.3) + (Disruption × 0.3)
Range: 0-100
```

## Testing

Comprehensive test suite in `tests/test_data_processor.py`:

```bash
# Run all data processing tests
pytest tests/test_data_processor.py -v

# Run specific test class
pytest tests/test_data_processor.py::TestHRVAnalysis -v

# Run with coverage
pytest tests/test_data_processor.py --cov=app/utils --cov=app/services
```

**Test Coverage**: Target >90%

### Test Categories

1. **Unit Tests**: Individual function testing
2. **Integration Tests**: End-to-end data processing
3. **Edge Cases**: NaN values, missing data, outliers
4. **Performance Tests**: Large dataset handling

## Performance

### Caching Strategy

The data processor implements intelligent caching:
- Results cached by user_id + date + analysis_type
- SHA-256 hash for cache keys
- Automatic cache invalidation
- Force recalculate option available

### Optimization Techniques

1. **Pandas/NumPy**: Vectorized operations for speed
2. **Database Indexing**: Optimized queries (see database_models.py)
3. **Batch Processing**: Process multiple days efficiently
4. **Lazy Evaluation**: Calculate only what's needed

## API Integration

The data processor is used by:

1. **Daily Sync** (`app/services/garmin_service.py`):
   - Called after fetching new data from Garmin
   - Automatically processes and calculates metrics

2. **API Endpoints** (`app/routers/`):
   - `/api/readiness` - Get current readiness
   - `/api/metrics/daily` - Daily metrics summary
   - `/api/metrics/weekly` - Weekly aggregation
   - `/api/metrics/monthly` - Monthly trends

3. **AI Recommendations** (Phase 3):
   - Provides data for AI training recommendations
   - Feeds Claude AI with context

## Database Updates

The processor updates two key tables:

### TrainingLoadTracking
Stores calculated training load metrics:
- Acute and chronic loads
- ACWR value and status
- Fitness, fatigue, and form
- Training monotony and strain
- Overtraining/injury risk flags

### DailyReadiness
Stores readiness assessment:
- Overall readiness score
- Recommendation (enum)
- Key factors (JSON)
- Red flags (warnings)
- AI analysis summary
- Component scores

## Error Handling

The processor gracefully handles:
- Missing data (returns None or default values)
- NaN values (filtered out)
- Insufficient data (requires minimums)
- Outliers (detection and optional removal)
- Database errors (rollback transactions)

## Configuration

Key parameters (can be customized per user):

```python
# HRV
HRV_BASELINE_DAYS_SHORT = 7
HRV_BASELINE_DAYS_LONG = 30
HRV_DROP_THRESHOLD = 10.0  # percent

# Training Load
ACUTE_LOAD_DAYS = 7
CHRONIC_LOAD_DAYS = 28
ACWR_OPTIMAL_MIN = 0.8
ACWR_OPTIMAL_MAX = 1.3

# Fitness-Fatigue
FITNESS_DECAY_DAYS = 42
FATIGUE_DECAY_DAYS = 7

# Sleep
TARGET_SLEEP_HOURS = 8.0
MIN_SLEEP_QUALITY_SCORE = 60
```

## Future Enhancements

### Phase 3 Additions
- AI-generated workout recommendations
- Personalized threshold learning (ML)
- Multi-sport optimization
- Race prediction

### Advanced Features
- Altitude training adjustments
- Heat/cold adaptation tracking
- Menstrual cycle impact (for female athletes)
- Injury risk ML model
- Performance prediction

## Dependencies

```
numpy>=2.1.3
pandas>=2.2.3
scipy>=1.11.0  (for advanced statistical functions)
sqlalchemy>=2.0.36
```

## References

### Scientific Research

1. **Gabbett, T. J. (2016)**. "The training-injury prevention paradox." *BJSM*, 50(5), 273-280.
2. **Banister, E. W. (1991)**. "Modeling human performance in running." *JAP*, 69(3), 1171-1177.
3. **Foster, C. (1998)**. "Monitoring training in athletes." *MSSE*, 30(7), 1164-1168.
4. **Plews, D. J. et al. (2013)**. "Heart rate variability in elite endurance athletes." *Sports Medicine*, 43(9), 773-781.
5. **Fullagar, H. H. et al. (2015)**. "Sleep and athletic performance." *Sports Medicine*, 45(2), 161-186.

## Contributing

When adding new calculations:

1. Add function to appropriate utility module
2. Include comprehensive docstring with formula
3. Add unit tests
4. Update formula documentation
5. Add integration test in data processor

## Support

For questions or issues:
- Review formula documentation: `DATA_PROCESSING_FORMULAS.md`
- Check test examples: `tests/test_data_processor.py`
- See main README: `README.md`

---

**Status**: ✅ Complete (Phase 2 - Track 2C)
**Last Updated**: 2025-10-16
**Version**: 1.0
