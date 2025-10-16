# Data Processing & Analytics Formulas

## Overview

This document provides detailed documentation of all formulas and algorithms implemented in the AI Training Optimizer data processing system.

## Table of Contents

1. [Statistical Functions](#statistical-functions)
2. [HRV Analysis](#hrv-analysis)
3. [Training Load Metrics](#training-load-metrics)
4. [Fitness-Fatigue Model](#fitness-fatigue-model)
5. [Sleep Analysis](#sleep-analysis)
6. [Readiness Scoring](#readiness-scoring)

---

## Statistical Functions

### Moving Average (Rolling Mean)

**Purpose**: Smooth time-series data and calculate trends.

**Formula**:
```
MA(t, w) = (1/w) * Σ(x[t-w+1:t])
```

Where:
- `t` = current time point
- `w` = window size (e.g., 7 days)
- `x` = data array

**Implementation**: `app/utils/statistics.py::moving_average()`

**Usage**:
- Acute load: 7-day moving average
- Chronic load: 28-day moving average
- HRV baseline: 7-day or 30-day moving average

---

### Exponentially Weighted Moving Average (EWMA)

**Purpose**: More responsive moving average that weights recent data more heavily.

**Formula**:
```
EWMA[0] = x[0]
EWMA[t] = α * x[t] + (1 - α) * EWMA[t-1]

where α = 2 / (span + 1)
```

**Implementation**: `app/utils/statistics.py::exponentially_weighted_moving_average()`

**Usage**:
- Alternative to simple moving average for load calculations
- More responsive to recent changes

---

### Standard Deviation

**Formula**:
```
σ = sqrt((1/(n-1)) * Σ(xi - μ)²)
```

Where:
- `σ` = standard deviation
- `n` = number of observations
- `xi` = individual values
- `μ` = mean

**Implementation**: `app/utils/statistics.py::standard_deviation()`

---

### Linear Regression

**Purpose**: Detect trends in time-series data (e.g., HRV trending up/down).

**Formulas**:
```
slope (m) = (n*Σ(xy) - Σx*Σy) / (n*Σ(x²) - (Σx)²)
intercept (b) = (Σy - m*Σx) / n
R² = 1 - (SS_res / SS_tot)

where:
SS_res = Σ(yi - ŷi)²  (residual sum of squares)
SS_tot = Σ(yi - ȳ)²   (total sum of squares)
```

**Implementation**: `app/utils/statistics.py::linear_regression()`

---

## HRV Analysis

### HRV Baseline

**Purpose**: Establish athlete's normal HRV range for comparison.

**Formula**:
```
Baseline = mean(HRV[t-n:t])
```

**Typical Periods**:
- Short-term: 7 days (more responsive)
- Long-term: 30 days (stable reference)

**Implementation**: `app/utils/hrv_analysis.py::calculate_hrv_baseline()`

**Minimum Data**: Requires at least 5 valid readings for reliable baseline.

---

### HRV Drop Detection

**Purpose**: Detect significant drops indicating poor recovery or overtraining.

**Formula**:
```
Drop % = ((Baseline - Current) / Baseline) * 100
```

**Thresholds**:
- 0-5%: Normal daily variation
- 5-10%: Mild drop (monitor)
- 10-20%: Moderate drop (reduce intensity) ⚠️
- >20%: Severe drop (rest recommended) 🔴

**Implementation**: `app/utils/hrv_analysis.py::detect_hrv_drop()`

---

### HRV Trend Analysis

**Purpose**: Determine if HRV is improving, stable, or declining over time.

**Method**: Linear regression on HRV time series.

**Interpretation**:
- Slope > 0.1 ms/day: **Improving** (good adaptation)
- Slope -0.1 to 0.1 ms/day: **Stable**
- Slope < -0.1 ms/day: **Declining** (overtraining risk)

**Implementation**: `app/utils/hrv_analysis.py::get_hrv_trend()`

---

### Coefficient of Variation (CV)

**Purpose**: Measure HRV consistency/stability.

**Formula**:
```
CV = (σ / μ) * 100
```

**Interpretation**:
- CV < 15%: Stable, consistent recovery
- CV 15-20%: Moderate variability
- CV > 20%: High variability (inconsistent recovery)

**Implementation**: `app/utils/statistics.py::coefficient_of_variation()`

---

## Training Load Metrics

### Acute Training Load (ATL)

**Purpose**: Measure recent training stress (fatigue).

**Formula**:
```
ATL = mean(Training_Load[t-6:t])  // 7-day rolling average
```

**Implementation**: `app/utils/training_load.py::calculate_acute_load()`

---

### Chronic Training Load (CTL)

**Purpose**: Measure long-term fitness/conditioning.

**Formula**:
```
CTL = mean(Training_Load[t-27:t])  // 28-day rolling average
```

**Implementation**: `app/utils/training_load.py::calculate_chronic_load()`

---

### Acute:Chronic Workload Ratio (ACWR)

**Purpose**: Monitor injury risk from rapid load changes.

**Formula**:
```
ACWR = ATL / CTL
```

**Interpretation**:
| ACWR Range | Status | Injury Risk | Action |
|------------|--------|-------------|--------|
| < 0.8 | Low | Low but detraining | Consider gradual increase |
| 0.8 - 1.3 | **Optimal** | Low | "Sweet spot" for adaptation |
| 1.3 - 1.5 | Moderate Risk | Moderate | Monitor fatigue closely |
| > 1.5 | High Risk | High | Reduce volume/intensity |

**Implementation**: `app/utils/training_load.py::calculate_acwr()`

**Research**: Gabbett, T. J. (2016). BJSM, 50(5), 273-280.

---

### Training Monotony

**Purpose**: Detect lack of training variation (injury/illness risk).

**Formula**:
```
Monotony = mean(daily_loads) / std(daily_loads)
```

**Interpretation**:
- < 1.5: Good variation
- 1.5 - 2.0: Moderate monotony
- > 2.0: High monotony (risk factor)

**Implementation**: `app/utils/training_load.py::calculate_training_monotony()`

---

### Training Strain

**Purpose**: Combined metric of load and monotony.

**Formula**:
```
Strain = Σ(weekly_loads) * Monotony
```

**High-Risk Threshold**: Strain > 7000 with high monotony

**Implementation**: `app/utils/training_load.py::calculate_training_monotony()`

**Research**: Foster, C. (1998). MSSE.

---

## Fitness-Fatigue Model

### Banister Model Overview

The fitness-fatigue model separates training adaptations into:
1. **Fitness**: Long-term positive adaptations
2. **Fatigue**: Short-term negative effects
3. **Form**: Current readiness (Fitness - Fatigue)

---

### Fitness Calculation

**Purpose**: Model long-term training adaptations.

**Formula**:
```
Fitness(t) = Σ(load[i] * e^(-(t-i)/τ_fitness))

where:
τ_fitness = 42 days (fitness time constant)
```

**Interpretation**:
- Higher fitness = better conditioning
- Builds slowly, decays slowly
- Represents chronic adaptations

**Implementation**: `app/utils/training_load.py::calculate_fitness_fatigue()`

---

### Fatigue Calculation

**Purpose**: Model short-term fatigue accumulation.

**Formula**:
```
Fatigue(t) = Σ(load[i] * e^(-(t-i)/τ_fatigue))

where:
τ_fatigue = 7 days (fatigue time constant)
```

**Interpretation**:
- Higher fatigue = more tired
- Accumulates quickly, dissipates quickly
- Represents acute training stress

---

### Form (Training Stress Balance)

**Formula**:
```
Form(t) = Fitness(t) - Fatigue(t)
```

**Interpretation**:

| Form Range | Status | Interpretation |
|------------|--------|----------------|
| > +20 | Fresh | Over-rested, may have lost sharpness |
| 0 to +20 | **Optimal** | Ready for quality training/competition |
| -20 to 0 | Fatigued | Accumulated fatigue, recovery needed |
| < -20 | Overtrained | High fatigue, rest priority |

**Implementation**: `app/utils/training_load.py::calculate_fitness_fatigue()`

**Research**: Banister, E. W. (1991). JAP, 69(3), 1171-1177.

---

### Taper Strategy

**Optimal Taper**:
- Reduce volume 40-60%
- Maintain some intensity
- Allow form to become positive
- Peak form typically at +5 to +15

---

## Sleep Analysis

### Sleep Quality Score

**Purpose**: Quantify overall sleep quality (0-100 scale).

**Components**:

1. **Duration Score (40% weight)**:
```
if sleep_duration < 70% of target:
    score = (duration / (0.7 * target)) * 60
elif sleep_duration < 90% of target:
    score = 60 + scaled_value
elif sleep_duration <= 110% of target:
    score = 90 + scaled_value
else:
    score = 95
```

2. **Sleep Stages Score (30% weight)**:
```
Optimal ranges:
- Deep sleep: 15-25% of total
- REM sleep: 20-25% of total

Deductions for deviations from optimal ranges
```

3. **Disruption Score (30% weight)**:
```
Factors:
- Wake time percentage
- Number of awakenings
- Sleep continuity
```

**Final Score**:
```
Quality_Score = (Duration * 0.4) + (Stages * 0.3) + (Disruption * 0.3)
```

**Implementation**: `app/utils/sleep_analysis.py::calculate_sleep_quality_score()`

---

### Sleep Debt

**Purpose**: Track accumulated sleep deficit.

**Formula**:
```
Sleep_Debt = Σ(max(0, target_sleep - actual_sleep))
```

**Interpretation**:

| Total Debt | Severity | Recovery Needed |
|------------|----------|-----------------|
| < 2 hours | Minimal | 1-2 nights |
| 2-5 hours | Moderate | 3-4 nights |
| 5-10 hours | Significant | 5-7 nights |
| > 10 hours | Severe | 7+ nights |

**Implementation**: `app/utils/sleep_analysis.py::detect_sleep_debt()`

---

## Readiness Scoring

### Overall Readiness Score

**Purpose**: Combine all factors into single readiness metric.

**Formula**:
```
Readiness = (HRV_Score * 0.40) + (Sleep_Score * 0.35) + (Load_Score * 0.25)
```

**Weights Rationale**:
- **HRV (40%)**: Most direct indicator of acute recovery
- **Sleep (35%)**: Critical for recovery and performance
- **Training Load (25%)**: Context for training stimulus

**Implementation**: `app/services/data_processor.py::_calculate_readiness_score()`

---

### Component Scoring

#### HRV Score (0-100)

Based on:
- Current HRV vs baseline
- Trend direction (improving/declining)
- Coefficient of variation
- Drop severity

```
Base scores:
- Optimal: 95
- Good: 80
- Caution: 65
- Warning: 40

Adjustments:
+5 if improving trend
-10 if declining trend
-5 if high CV (>20%)
```

---

#### Sleep Score (0-100)

Based on sleep quality assessment (see Sleep Quality Score above).

---

#### Training Load Score (0-100)

```
Status scores:
- Optimal: 90
- Caution: 70
- Warning: 40
- No data: 50 (neutral)
```

---

### Readiness Interpretation

| Score Range | Status | Training Recommendation |
|-------------|--------|------------------------|
| 85-100 | Excellent | High-intensity training or competition |
| 70-84 | Good | Quality training sessions |
| 55-69 | Fair | Easy to moderate training |
| 0-54 | Poor | Rest or very easy recovery |

**Implementation**: `app/services/data_processor.py::process_daily_metrics()`

---

## Data Caching

### Cache Strategy

**Purpose**: Avoid redundant calculations of expensive metrics.

**Cache Key**:
```
SHA-256(user_id + date + analysis_type)
```

**Cache Invalidation**:
- Automatic expiration (configurable)
- Manual clear on data updates
- Force recalculate flag available

**Implementation**: `app/services/data_processor.py::_cache_result()`

---

## References

### Scientific Research

1. **ACWR**: Gabbett, T. J. (2016). "The training-injury prevention paradox: should athletes be training smarter and harder?" *British Journal of Sports Medicine*, 50(5), 273-280.

2. **Fitness-Fatigue Model**: Banister, E. W., Calvert, T. W., Savage, M. V., & Bach, T. (1975). "A systems model of training for athletic performance." *Australian Journal of Sports Medicine*, 7(3), 57-61.

3. **Training Monotony**: Foster, C. (1998). "Monitoring training in athletes with reference to overtraining syndrome." *Medicine & Science in Sports & Exercise*, 30(7), 1164-1168.

4. **HRV and Recovery**: Plews, D. J., et al. (2013). "Training adaptation and heart rate variability in elite endurance athletes: opening the door to effective monitoring." *Sports Medicine*, 43(9), 773-781.

5. **Sleep and Performance**: Fullagar, H. H., et al. (2015). "Sleep and athletic performance: the effects of sleep loss on exercise performance, and physiological and cognitive responses to exercise." *Sports Medicine*, 45(2), 161-186.

---

## File Structure

```
app/
├── utils/
│   ├── statistics.py          # Core statistical functions
│   ├── hrv_analysis.py        # HRV calculations and analysis
│   ├── training_load.py       # Training load metrics (ACWR, FF model)
│   └── sleep_analysis.py      # Sleep quality scoring
│
├── services/
│   ├── data_processor.py      # Main orchestrator
│   └── aggregation_service.py # Daily/weekly/monthly summaries
│
└── models/
    └── database_models.py     # TrainingLoadTracking, DailyReadiness models
```

---

## Testing

Comprehensive test coverage in `tests/test_data_processor.py`:
- Unit tests for all formulas
- Integration tests for data processing pipeline
- Edge case handling (NaN, missing data, outliers)
- Target coverage: >90%

---

## Future Enhancements

1. **Machine Learning Integration**: Use ML to personalize thresholds and weights
2. **Multi-Sport Support**: Sport-specific load calculations
3. **Altitude Adjustment**: HRV adjustments for altitude training
4. **Injury Prediction**: ML model for injury risk prediction
5. **Workout Recommendations**: AI-generated daily workout prescriptions

---

*Last Updated: 2025-10-16*
*Version: 1.0*
