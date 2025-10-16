# API Design Documentation

## API Design Principles

1. **RESTful Conventions**: Resources as nouns, HTTP methods for actions
2. **Consistent Response Format**: Standardized JSON structure
3. **Proper HTTP Status Codes**: Semantic status codes for all responses
4. **Pagination**: Cursor-based pagination for large datasets
5. **Filtering & Sorting**: Query parameters for data filtering
6. **Versioning**: URL-based versioning (`/api/v1/...`)
7. **Documentation**: Auto-generated OpenAPI/Swagger docs

## Base URL Structure

```
Production:  https://api.garmin-ai-trainer.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### JWT-Based Authentication

All API endpoints (except public endpoints) require JWT authentication:

```http
Authorization: Bearer <jwt_token>
```

### Authentication Flow

```
POST /api/v1/auth/register    - Register new user
POST /api/v1/auth/login       - Login and receive tokens
POST /api/v1/auth/refresh     - Refresh access token
POST /api/v1/auth/logout      - Logout (invalidate refresh token)
```

## Standard Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    // Response payload
  },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error context",
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "total": 150,
      "page": 1,
      "page_size": 20,
      "total_pages": 8,
      "has_next": true,
      "has_previous": false,
      "next_cursor": "eyJpZCI6MTIzfQ==",
      "previous_cursor": null
    }
  },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## HTTP Status Codes

- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST (resource created)
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (duplicate)
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **502 Bad Gateway**: External API error
- **503 Service Unavailable**: Service temporarily unavailable

---

# API Endpoints

## 1. Authentication & User Management

### POST /api/v1/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "garmin_email": "garmin@example.com",
  "garmin_password": "GarminPassword123!"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2025-10-15T10:30:00Z"
  },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### POST /api/v1/auth/login
Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### POST /api/v1/auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### POST /api/v1/auth/logout
Logout user and invalidate refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (204 No Content)**

### GET /api/v1/users/me
Get current user profile.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "garmin_connected": true,
    "timezone": "America/New_York",
    "created_at": "2025-10-15T10:30:00Z",
    "last_sync": "2025-10-15T08:00:00Z"
  }
}
```

### PATCH /api/v1/users/me
Update current user profile.

**Request Body:**
```json
{
  "full_name": "John M. Doe",
  "timezone": "America/Los_Angeles"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "user@example.com",
    "full_name": "John M. Doe",
    "timezone": "America/Los_Angeles",
    "updated_at": "2025-10-15T10:35:00Z"
  }
}
```

---

## 2. Health Metrics (`/api/v1/health/*`)

### GET /api/v1/health/metrics
Get health metrics for a date range.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `metrics` (optional): Comma-separated metrics (hr,sleep,stress,steps,hrv)

**Example:**
```
GET /api/v1/health/metrics?start_date=2025-10-01&end_date=2025-10-15&metrics=hr,sleep,stress
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "date": "2025-10-15",
        "resting_hr": 52,
        "max_hr": 178,
        "avg_hr": 68,
        "hrv": 65.2,
        "sleep_hours": 7.5,
        "deep_sleep_hours": 1.8,
        "rem_sleep_hours": 1.2,
        "stress_score": 28,
        "steps": 12458,
        "calories": 2456,
        "active_calories": 856
      }
      // ... more daily metrics
    ],
    "summary": {
      "avg_resting_hr": 54,
      "avg_sleep_hours": 7.2,
      "avg_stress_score": 32,
      "total_steps": 186870
    }
  }
}
```

### GET /api/v1/health/metrics/latest
Get most recent health metrics.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "date": "2025-10-15",
    "resting_hr": 52,
    "max_hr": 178,
    "hrv": 65.2,
    "sleep_hours": 7.5,
    "stress_score": 28,
    "steps": 12458,
    "synced_at": "2025-10-15T08:00:00Z"
  }
}
```

### GET /api/v1/health/sleep
Get detailed sleep data.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "sleep_records": [
      {
        "date": "2025-10-15",
        "sleep_start": "2025-10-14T23:15:00Z",
        "sleep_end": "2025-10-15T06:45:00Z",
        "total_sleep_hours": 7.5,
        "deep_sleep_hours": 1.8,
        "light_sleep_hours": 4.5,
        "rem_sleep_hours": 1.2,
        "awake_hours": 0.5,
        "sleep_score": 82,
        "sleep_quality": "good"
      }
      // ... more records
    ],
    "summary": {
      "avg_total_sleep": 7.2,
      "avg_deep_sleep": 1.6,
      "avg_sleep_score": 78
    }
  }
}
```

### GET /api/v1/health/stress
Get stress level data.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "stress_records": [
      {
        "date": "2025-10-15",
        "avg_stress_level": 28,
        "max_stress_level": 65,
        "rest_time_minutes": 420,
        "activity_time_minutes": 180,
        "stress_time_minutes": 120,
        "low_stress_time_minutes": 720
      }
      // ... more records
    ],
    "summary": {
      "avg_stress_level": 32,
      "avg_rest_time_minutes": 400
    }
  }
}
```

### GET /api/v1/health/body
Get body composition data.

**Query Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "body_records": [
      {
        "date": "2025-10-15",
        "weight_kg": 72.5,
        "bmi": 22.8,
        "body_fat_percent": 14.2,
        "muscle_mass_kg": 58.3,
        "bone_mass_kg": 3.2,
        "body_water_percent": 62.1
      }
      // ... more records
    ]
  }
}
```

---

## 3. Activities & Workouts (`/api/v1/activities/*`)

### GET /api/v1/activities
Get list of activities/workouts.

**Query Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `activity_type` (optional): Filter by type (running,cycling,swimming,strength)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Example:**
```
GET /api/v1/activities?start_date=2025-10-01&activity_type=running&page=1&page_size=20
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "activity_id": "act_xyz789",
        "activity_type": "running",
        "activity_name": "Morning Run",
        "start_time": "2025-10-15T06:30:00Z",
        "duration_seconds": 3600,
        "distance_meters": 10000,
        "avg_hr": 152,
        "max_hr": 178,
        "avg_pace_min_km": 6.0,
        "calories": 650,
        "elevation_gain_meters": 120,
        "avg_cadence": 168,
        "training_effect_aerobic": 3.8,
        "training_effect_anaerobic": 1.2,
        "tss": 82
      }
      // ... more activities
    ],
    "pagination": {
      "total": 150,
      "page": 1,
      "page_size": 20,
      "total_pages": 8,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

### GET /api/v1/activities/{activity_id}
Get detailed activity data.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "activity_id": "act_xyz789",
    "activity_type": "running",
    "activity_name": "Morning Run",
    "start_time": "2025-10-15T06:30:00Z",
    "end_time": "2025-10-15T07:30:00Z",
    "duration_seconds": 3600,
    "distance_meters": 10000,
    "avg_hr": 152,
    "max_hr": 178,
    "avg_pace_min_km": 6.0,
    "calories": 650,
    "elevation_gain_meters": 120,
    "elevation_loss_meters": 115,
    "avg_cadence": 168,
    "avg_stride_length_meters": 1.12,
    "training_effect_aerobic": 3.8,
    "training_effect_anaerobic": 1.2,
    "tss": 82,
    "normalized_power": null,
    "intensity_factor": null,
    "gps_track": [
      {
        "timestamp": "2025-10-15T06:30:00Z",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "altitude": 10.5,
        "hr": 145,
        "speed_mps": 2.8
      }
      // ... more GPS points
    ],
    "lap_data": [
      {
        "lap_number": 1,
        "duration_seconds": 360,
        "distance_meters": 1000,
        "avg_hr": 148,
        "max_hr": 158,
        "avg_pace_min_km": 6.0
      }
      // ... more laps
    ]
  }
}
```

### GET /api/v1/activities/summary
Get activity summary statistics.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `activity_type` (optional): Filter by type

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2025-10-01",
      "end_date": "2025-10-15"
    },
    "total_activities": 18,
    "total_duration_hours": 24.5,
    "total_distance_km": 182.3,
    "total_calories": 8456,
    "total_elevation_gain_meters": 2340,
    "avg_weekly_distance_km": 91.2,
    "avg_weekly_activities": 9,
    "by_activity_type": {
      "running": {
        "count": 12,
        "total_distance_km": 120.5,
        "avg_pace_min_km": 5.8
      },
      "cycling": {
        "count": 4,
        "total_distance_km": 48.2,
        "avg_speed_kmh": 28.5
      },
      "strength": {
        "count": 2,
        "total_duration_hours": 2.0
      }
    }
  }
}
```

### DELETE /api/v1/activities/{activity_id}
Delete an activity.

**Response (204 No Content)**

---

## 4. Training Plans (`/api/v1/training/*`)

### GET /api/v1/training/plans
Get all training plans for user.

**Query Parameters:**
- `status` (optional): Filter by status (active,completed,draft)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plans": [
      {
        "plan_id": "plan_abc123",
        "name": "Marathon Training - Fall 2025",
        "goal": "Complete marathon in under 4 hours",
        "start_date": "2025-08-01",
        "end_date": "2025-11-01",
        "status": "active",
        "progress_percent": 45,
        "total_weeks": 16,
        "current_week": 7,
        "created_at": "2025-07-15T10:00:00Z"
      }
      // ... more plans
    ]
  }
}
```

### GET /api/v1/training/plans/{plan_id}
Get detailed training plan.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan_abc123",
    "name": "Marathon Training - Fall 2025",
    "description": "16-week progressive marathon training plan",
    "goal": "Complete marathon in under 4 hours",
    "start_date": "2025-08-01",
    "end_date": "2025-11-01",
    "status": "active",
    "progress_percent": 45,
    "total_weeks": 16,
    "current_week": 7,
    "weeks": [
      {
        "week_number": 1,
        "start_date": "2025-08-01",
        "end_date": "2025-08-07",
        "weekly_distance_km": 40,
        "workouts": [
          {
            "day": "monday",
            "workout_type": "easy_run",
            "name": "Easy Run",
            "description": "Easy aerobic run at conversational pace",
            "target_distance_km": 8,
            "target_duration_minutes": 50,
            "target_pace_min_km": 6.15,
            "target_hr_zone": "zone_2",
            "completed": true,
            "actual_activity_id": "act_xyz789"
          }
          // ... more workouts for the week
        ]
      }
      // ... more weeks
    ],
    "created_at": "2025-07-15T10:00:00Z",
    "created_by": "ai_generated"
  }
}
```

### POST /api/v1/training/plans
Create a new training plan.

**Request Body:**
```json
{
  "name": "5K Training - Spring 2025",
  "goal": "Run 5K in under 25 minutes",
  "start_date": "2025-03-01",
  "plan_duration_weeks": 8,
  "current_fitness_level": "intermediate",
  "weekly_availability": {
    "monday": true,
    "tuesday": true,
    "wednesday": true,
    "thursday": false,
    "friday": true,
    "saturday": true,
    "sunday": false
  },
  "preferred_training_days": 5,
  "race_date": "2025-04-26"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan_def456",
    "name": "5K Training - Spring 2025",
    "start_date": "2025-03-01",
    "end_date": "2025-04-26",
    "status": "draft",
    "total_weeks": 8,
    "created_at": "2025-02-25T10:00:00Z"
  }
}
```

### PATCH /api/v1/training/plans/{plan_id}
Update training plan.

**Request Body:**
```json
{
  "name": "5K Training - Updated",
  "status": "active"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan_def456",
    "name": "5K Training - Updated",
    "status": "active",
    "updated_at": "2025-02-26T10:00:00Z"
  }
}
```

### DELETE /api/v1/training/plans/{plan_id}
Delete a training plan.

**Response (204 No Content)**

### PATCH /api/v1/training/plans/{plan_id}/workouts/{workout_id}
Mark workout as completed or update details.

**Request Body:**
```json
{
  "completed": true,
  "actual_activity_id": "act_xyz789",
  "notes": "Felt strong today, good pace"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "workout_id": "workout_abc123",
    "completed": true,
    "completed_at": "2025-10-15T07:30:00Z",
    "actual_activity_id": "act_xyz789"
  }
}
```

---

## 5. AI Recommendations (`/api/v1/recommendations/*`)

### GET /api/v1/recommendations
Get AI-generated recommendations.

**Query Parameters:**
- `type` (optional): Filter by type (training,recovery,nutrition,general)
- `start_date` (optional): Start date
- `end_date` (optional): End date
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "recommendation_id": "rec_abc123",
        "type": "training",
        "priority": "high",
        "title": "Increase Easy Run Volume",
        "summary": "Your training load has decreased 15% over the past 2 weeks",
        "detailed_recommendation": "Based on your recent activity patterns and recovery metrics, I recommend gradually increasing your easy run volume by 10% this week. Your HRV and resting heart rate indicate good recovery capacity.",
        "reasoning": [
          "Training load decreased from 450 to 380 TSS/week",
          "HRV is 8% above baseline (65 vs 60)",
          "Resting HR is stable at 52 bpm",
          "Sleep quality averaging 82/100"
        ],
        "action_items": [
          "Add 5km to your weekly easy run total",
          "Maintain current intensity distribution",
          "Monitor fatigue levels closely"
        ],
        "expected_impact": "Maintain aerobic fitness and prepare for upcoming race",
        "created_at": "2025-10-15T08:00:00Z",
        "valid_until": "2025-10-22T08:00:00Z",
        "status": "active"
      }
      // ... more recommendations
    ],
    "pagination": {
      "total": 12,
      "page": 1,
      "page_size": 10,
      "has_next": true
    }
  }
}
```

### GET /api/v1/recommendations/latest
Get most recent recommendations.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "recommendation_id": "rec_abc123",
        "type": "recovery",
        "priority": "high",
        "title": "Prioritize Recovery This Week",
        "summary": "Elevated stress levels and reduced HRV suggest need for recovery",
        "created_at": "2025-10-15T08:00:00Z"
      }
      // ... top 5 recommendations
    ]
  }
}
```

### GET /api/v1/recommendations/{recommendation_id}
Get detailed recommendation.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "recommendation_id": "rec_abc123",
    "type": "training",
    "priority": "high",
    "title": "Increase Easy Run Volume",
    "summary": "Your training load has decreased 15% over the past 2 weeks",
    "detailed_recommendation": "Based on your recent activity patterns...",
    "reasoning": [...],
    "action_items": [...],
    "expected_impact": "Maintain aerobic fitness",
    "data_sources": [
      "7 days of activity data",
      "14 days of HRV measurements",
      "30 days of sleep data"
    ],
    "confidence_score": 0.87,
    "created_at": "2025-10-15T08:00:00Z",
    "valid_until": "2025-10-22T08:00:00Z",
    "status": "active"
  }
}
```

### PATCH /api/v1/recommendations/{recommendation_id}
Update recommendation status (mark as read, dismissed, implemented).

**Request Body:**
```json
{
  "status": "implemented",
  "user_feedback": "Great advice, adjusted my training plan accordingly"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "recommendation_id": "rec_abc123",
    "status": "implemented",
    "updated_at": "2025-10-15T12:00:00Z"
  }
}
```

---

## 6. AI Analysis (`/api/v1/analysis/*`)

### POST /api/v1/analysis/generate
Request AI analysis generation.

**Request Body:**
```json
{
  "analysis_type": "comprehensive",
  "time_period": {
    "start_date": "2025-09-15",
    "end_date": "2025-10-15"
  },
  "focus_areas": ["training_load", "recovery", "performance_trends"],
  "include_recommendations": true
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_abc123",
    "status": "processing",
    "estimated_completion_seconds": 10,
    "message": "Analysis is being generated"
  }
}
```

### GET /api/v1/analysis/{analysis_id}
Get analysis results.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_abc123",
    "status": "completed",
    "analysis_type": "comprehensive",
    "time_period": {
      "start_date": "2025-09-15",
      "end_date": "2025-10-15"
    },
    "summary": {
      "overall_fitness_trend": "improving",
      "training_load_balance": "good",
      "recovery_status": "adequate",
      "key_insights_count": 8,
      "recommendations_count": 5
    },
    "insights": [
      {
        "category": "training_load",
        "title": "Training Load Well Balanced",
        "description": "Your CTL is increasing at an optimal 5 TSS/week rate",
        "severity": "info",
        "data_points": {
          "current_ctl": 85,
          "target_ctl": 95,
          "weeks_to_target": 2
        }
      }
      // ... more insights
    ],
    "performance_metrics": {
      "vo2max_estimate": 52.3,
      "vo2max_trend": "stable",
      "lactate_threshold_hr": 165,
      "aerobic_efficiency": "good",
      "training_stress_balance": 12
    },
    "recommendations": [
      // ... recommendations array
    ],
    "created_at": "2025-10-15T08:00:00Z",
    "completed_at": "2025-10-15T08:00:08Z"
  }
}
```

### GET /api/v1/analysis
Get list of past analyses.

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "analysis_id": "analysis_abc123",
        "analysis_type": "comprehensive",
        "status": "completed",
        "time_period": {
          "start_date": "2025-09-15",
          "end_date": "2025-10-15"
        },
        "created_at": "2025-10-15T08:00:00Z"
      }
      // ... more analyses
    ],
    "pagination": {...}
  }
}
```

---

## 7. Data Synchronization (`/api/v1/sync/*`)

### POST /api/v1/sync/garmin
Trigger Garmin data sync.

**Request Body:**
```json
{
  "sync_type": "full",
  "start_date": "2025-10-01",
  "end_date": "2025-10-15",
  "data_types": ["health", "activities", "sleep", "stress"]
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "sync_id": "sync_abc123",
    "status": "processing",
    "estimated_completion_seconds": 30,
    "message": "Garmin data sync initiated"
  }
}
```

### GET /api/v1/sync/{sync_id}
Get sync job status.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "sync_id": "sync_abc123",
    "status": "completed",
    "sync_type": "full",
    "time_period": {
      "start_date": "2025-10-01",
      "end_date": "2025-10-15"
    },
    "results": {
      "health_metrics": {
        "records_fetched": 15,
        "records_saved": 15,
        "errors": 0
      },
      "activities": {
        "records_fetched": 18,
        "records_saved": 18,
        "errors": 0
      },
      "sleep": {
        "records_fetched": 15,
        "records_saved": 15,
        "errors": 0
      }
    },
    "started_at": "2025-10-15T08:00:00Z",
    "completed_at": "2025-10-15T08:00:25Z",
    "duration_seconds": 25
  }
}
```

### GET /api/v1/sync/history
Get sync history.

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "sync_id": "sync_abc123",
        "status": "completed",
        "sync_type": "full",
        "started_at": "2025-10-15T08:00:00Z",
        "completed_at": "2025-10-15T08:00:25Z",
        "total_records": 48
      }
      // ... more sync jobs
    ],
    "pagination": {...}
  }
}
```

### GET /api/v1/sync/schedule
Get configured sync schedule.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "frequency": "daily",
    "time": "08:00",
    "timezone": "America/New_York",
    "next_scheduled_run": "2025-10-16T08:00:00Z",
    "last_successful_run": "2025-10-15T08:00:00Z"
  }
}
```

### PATCH /api/v1/sync/schedule
Update sync schedule.

**Request Body:**
```json
{
  "enabled": true,
  "frequency": "daily",
  "time": "07:00",
  "timezone": "America/Los_Angeles"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "frequency": "daily",
    "time": "07:00",
    "timezone": "America/Los_Angeles",
    "next_scheduled_run": "2025-10-16T07:00:00Z"
  }
}
```

---

## 8. Data Export (`/api/v1/export/*`)

### POST /api/v1/export/activities
Export activities data.

**Request Body:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-10-15",
  "format": "csv",
  "include_gps_data": false
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "export_id": "export_abc123",
    "status": "processing",
    "estimated_completion_seconds": 15
  }
}
```

### GET /api/v1/export/{export_id}
Get export status and download link.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "export_id": "export_abc123",
    "status": "completed",
    "format": "csv",
    "file_size_bytes": 1048576,
    "record_count": 245,
    "download_url": "/api/v1/export/export_abc123/download",
    "expires_at": "2025-10-22T08:00:00Z",
    "created_at": "2025-10-15T08:00:00Z",
    "completed_at": "2025-10-15T08:00:12Z"
  }
}
```

### GET /api/v1/export/{export_id}/download
Download exported file.

**Response (200 OK):**
- Content-Type: application/octet-stream or text/csv
- Content-Disposition: attachment; filename="activities_export.csv"
- Binary file data

### POST /api/v1/export/health
Export health metrics data.

**Request Body:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-10-15",
  "format": "json",
  "metrics": ["hr", "sleep", "stress", "hrv"]
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "export_id": "export_def456",
    "status": "processing"
  }
}
```

---

## 9. System & Health Checks

### GET /api/v1/health
Basic health check.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T10:30:00Z",
  "version": "1.0.0"
}
```

### GET /api/v1/health/detailed
Detailed health check with component status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "garmin_api": {
      "status": "healthy",
      "response_time_ms": 245
    },
    "claude_api": {
      "status": "healthy",
      "response_time_ms": 180
    },
    "cache": {
      "status": "healthy",
      "hit_rate_percent": 78.5
    }
  }
}
```

---

## Rate Limiting

### Rate Limit Headers

All API responses include rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697368800
```

### Rate Limits by Endpoint Category

- **Authentication**: 10 requests/minute per IP
- **Data Fetch**: 60 requests/minute per user
- **AI Analysis**: 5 requests/hour per user
- **Data Sync**: 10 requests/hour per user
- **General**: 100 requests/minute per user

### Rate Limit Exceeded Response (429)

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": "You have exceeded the rate limit for this endpoint",
    "retry_after_seconds": 60
  }
}
```

---

## API Versioning Strategy

### Current Version: v1

- **URL Versioning**: `/api/v1/...`
- **Breaking Changes**: New major version (v2) for breaking changes
- **Deprecation**: 6-month notice for deprecated endpoints
- **Sunset Header**: `Sunset: Sat, 31 Dec 2025 23:59:59 GMT`

### Version Headers

Clients can optionally specify version via header:

```http
X-API-Version: 1
```

### Deprecation Notice

Deprecated endpoints include deprecation headers:

```http
X-API-Deprecated: true
X-API-Deprecation-Date: 2025-12-31
X-API-Sunset-Date: 2026-06-30
X-API-Successor: /api/v2/new-endpoint
```

---

## Webhook Support (Future)

### Webhook Events

Future support for webhooks on:
- `sync.completed`: Garmin data sync completed
- `analysis.completed`: AI analysis completed
- `recommendation.created`: New recommendation generated
- `plan.workout_due`: Workout scheduled for today

### Webhook Payload Example

```json
{
  "event_type": "analysis.completed",
  "event_id": "evt_abc123",
  "timestamp": "2025-10-15T08:00:00Z",
  "data": {
    "analysis_id": "analysis_abc123",
    "user_id": "usr_abc123",
    "status": "completed"
  }
}
```

---

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Testing the API

### Using cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Get health metrics (with auth)
curl -X GET "http://localhost:8000/api/v1/health/metrics?start_date=2025-10-01&end_date=2025-10-15" \
  -H "Authorization: Bearer <your_token>"
```

### Using Python Requests

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = response.json()["data"]["access_token"]

# Get health metrics
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/health/metrics",
    params={"start_date": "2025-10-01", "end_date": "2025-10-15"},
    headers=headers
)
print(response.json())
```

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request data or parameters |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (duplicate) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `GARMIN_AUTH_FAILED` | 502 | Garmin authentication failed |
| `GARMIN_API_ERROR` | 502 | Garmin API error |
| `GARMIN_RATE_LIMITED` | 429 | Garmin API rate limited |
| `CLAUDE_API_ERROR` | 502 | Claude AI API error |
| `CLAUDE_TOKEN_LIMIT` | 400 | Claude token limit exceeded |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
