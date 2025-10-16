# Architecture Summary

## Overview

This document provides a high-level summary of the Garmin AI Training Optimization System architecture. For detailed information, refer to the linked documentation.

## Architecture Documents

1. **[architecture.md](./architecture.md)** - Complete system architecture documentation
2. **[api_design.md](./api_design.md)** - Comprehensive API endpoint specifications
3. **[diagrams/](./diagrams/)** - Visual architecture diagrams (Mermaid format)

## Quick Reference

### System Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer                                         │
│  - Web Dashboard (React/Vue.js)                            │
│  - Mobile App (Future)                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  API Layer (FastAPI)                                        │
│  - Authentication & Authorization (JWT)                    │
│  - Rate Limiting                                           │
│  - Request/Response Validation                             │
│  - OpenAPI Documentation                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Service Layer (Business Logic)                            │
│  - GarminService         - AIAnalyzer                      │
│  - DataProcessor         - TrainingPlanner                 │
│  - NotificationService   - SchedulerService                │
│  - ExportService         - AuthService                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Repository Layer (Data Access)                            │
│  - UserRepository        - HealthMetricsRepository         │
│  - ActivityRepository    - RecommendationRepository        │
│  - TrainingPlanRepository - AnalysisRepository             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer                                      │
│  - SQLite/PostgreSQL Database                             │
│  - Redis Cache (Future)                                   │
│  - File Storage                                           │
└─────────────────────────────────────────────────────────────┘
```

### Key Services

| Service | Responsibility | External Dependencies |
|---------|---------------|----------------------|
| **GarminService** | Fetch data from Garmin Connect, handle authentication, rate limiting | Garmin Connect API |
| **AIAnalyzer** | Generate AI-powered analysis and recommendations using Claude | Claude AI API |
| **DataProcessor** | Calculate training metrics (TSS, CTL, ATL, TSB), aggregate data | None |
| **TrainingPlanner** | Generate and adapt training plans, track progress | AIAnalyzer |
| **NotificationService** | Send email/SMS notifications to users | Email/SMS providers |
| **SchedulerService** | Orchestrate background jobs (daily sync, weekly analysis) | All services |
| **ExportService** | Export user data in various formats (CSV, JSON) | None |
| **AuthService** | User authentication, JWT token management | None |

### API Endpoint Categories

| Category | Base Path | Purpose | Auth Required |
|----------|-----------|---------|--------------|
| Authentication | `/api/v1/auth/*` | User registration, login, logout, token refresh | No (except logout) |
| Health Metrics | `/api/v1/health/*` | Access health data (HR, HRV, sleep, stress) | Yes |
| Activities | `/api/v1/activities/*` | Access workout/activity data | Yes |
| Training Plans | `/api/v1/training/*` | Create and manage training plans | Yes |
| Recommendations | `/api/v1/recommendations/*` | AI-generated recommendations | Yes |
| Analysis | `/api/v1/analysis/*` | AI-powered analysis generation | Yes |
| Sync | `/api/v1/sync/*` | Trigger and monitor Garmin data sync | Yes |
| Export | `/api/v1/export/*` | Export data in various formats | Yes |

### Data Flow Overview

```
┌──────────────┐
│ Garmin Watch │ (Device syncs to Garmin Connect)
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│ Garmin Connect   │
│ API              │
└──────┬───────────┘
       │
       ↓ (Scheduled sync: Daily 8:00 AM)
┌──────────────────┐
│ GarminService    │ → Fetch health metrics, activities
└──────┬───────────┘
       │
       ↓ (Save raw data)
┌──────────────────┐
│ Database         │
│ (SQLite/PG)      │
└──────┬───────────┘
       │
       ↓ (Process and aggregate)
┌──────────────────┐
│ DataProcessor    │ → Calculate TSS, CTL, ATL, TSB, trends
└──────┬───────────┘
       │
       ↓ (Analyze with AI)
┌──────────────────┐
│ AIAnalyzer       │ → Generate insights and recommendations
└──────┬───────────┘
       │
       ↓ (Save analysis)
┌──────────────────┐
│ Database         │
└──────┬───────────┘
       │
       ↓ (Notify user)
┌──────────────────┐
│ Notifications    │ → Email summary to user
└──────────────────┘
```

### Error Handling Strategy

#### Exception Hierarchy

```
AppException (Base)
├── ExternalAPIError
│   ├── GarminAPIError
│   │   ├── GarminAuthenticationError
│   │   ├── GarminConnectionError
│   │   └── GarminRateLimitError
│   └── AIAnalysisError
│       ├── ClaudeAPIError
│       ├── ClaudeTokenLimitError
│       └── ClaudeParsingError
├── DataError
│   ├── DataValidationError
│   ├── DataProcessingError
│   └── DataNotFoundError
├── DatabaseError
│   ├── DatabaseConnectionError
│   └── DatabaseIntegrityError
└── AuthenticationError / AuthorizationError
```

#### Error Handling Patterns

1. **Retry with Exponential Backoff**
   - Garmin API connection failures
   - Claude API temporary failures
   - Database connection issues

2. **Circuit Breaker**
   - External API calls (prevent cascading failures)
   - Background job execution

3. **Graceful Degradation**
   - Use cached data if Garmin API unavailable
   - Skip AI analysis if Claude API unavailable
   - Provide basic metrics if processing fails

4. **Comprehensive Logging**
   - Structured logging with request IDs
   - Error tracking and monitoring
   - User-friendly error messages

### Security Measures

| Layer | Security Measure | Implementation |
|-------|-----------------|----------------|
| **Transport** | HTTPS/TLS | Nginx reverse proxy, TLS 1.3 |
| **Authentication** | JWT Tokens | Access token (15 min), Refresh token (7 days) |
| **Password Storage** | Hashing | bcrypt with salt |
| **Garmin Credentials** | Encryption | Fernet symmetric encryption |
| **API Security** | Rate Limiting | Per-user and per-endpoint limits |
| **Input Validation** | Schema Validation | Pydantic models |
| **CORS** | Origin Policies | Strict allowed origins |
| **SQL Injection** | Parameterized Queries | SQLAlchemy ORM |
| **Secrets** | Environment Variables | No hardcoded secrets |

### Caching Strategy

| Cache Type | TTL | Purpose | Technology |
|-----------|-----|---------|-----------|
| **Dashboard Summary** | 5 minutes | Reduce database load for frequent views | Redis/In-memory |
| **Health Metrics (Historical)** | 1 hour | Historical data rarely changes | Redis |
| **AI Analysis** | 24 hours | Expensive to generate | Redis |
| **Training Plans** | Until modified | User-specific data | Redis |
| **Aggregated Stats** | 30 minutes | Calculated metrics | Redis |

### Performance Targets

| Metric | Target | Monitoring |
|--------|--------|-----------|
| API Response Time (p95) | < 200ms | Application metrics |
| Dashboard Load Time | < 2 seconds | Frontend performance |
| Data Sync Duration | < 30 seconds | Background job logs |
| AI Analysis Generation | < 10 seconds | Claude API metrics |
| Database Query Time (p95) | < 50ms | Query logging |

### Scalability Path

#### Phase 1: Single User (Current)
- Single FastAPI instance
- SQLite database
- In-memory caching
- Single server deployment

#### Phase 2: Multi-User (Future)
- Multiple FastAPI instances + load balancer
- PostgreSQL with connection pooling
- Redis cluster for distributed caching
- Celery for background jobs
- Separate worker processes

#### Phase 3: High Scale (Future)
- Kubernetes orchestration
- Read replicas for database
- Message queue (RabbitMQ/Kafka)
- CDN for static assets
- Microservices separation (optional)

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | FastAPI | Latest | Web framework |
| **Language** | Python | 3.11+ | Programming language |
| **Database** | SQLite → PostgreSQL | Latest | Data persistence |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Authentication** | python-jose | Latest | JWT handling |
| **Validation** | Pydantic | v2 | Request/response validation |
| **HTTP Client** | httpx | Latest | Async HTTP client |
| **Background Jobs** | APScheduler | Latest | Task scheduling |
| **Logging** | structlog | Latest | Structured logging |
| **Caching** | Redis (future) | Latest | Distributed cache |
| **Testing** | pytest | Latest | Test framework |

### Monitoring & Observability

#### Health Checks
- `/health` - Basic health check (uptime, version)
- `/health/detailed` - Component health (DB, Garmin API, Claude API)
- `/metrics` - Prometheus-compatible metrics (future)

#### Key Metrics to Monitor
- API request rate and latency (per endpoint)
- Error rates (by type and endpoint)
- External API success rates (Garmin, Claude)
- Background job completion rates
- Database connection pool usage
- Cache hit rates

#### Logging Strategy
- **Development**: Pretty-printed console logs
- **Production**: JSON-formatted logs → CloudWatch/ELK
- **Log Levels**: DEBUG (dev), INFO (prod), WARNING, ERROR, CRITICAL
- **Correlation**: Request ID tracked across all operations

#### Alerting Triggers
- High error rate (> 5% of requests)
- External API failures (> 3 consecutive)
- Background job failures
- Database connection pool exhaustion
- Unusual spike in traffic

### Deployment Architecture

#### Development Environment
```
┌─────────────────────────────────────┐
│  Docker Container                   │
│  ┌───────────────────────────────┐  │
│  │  FastAPI Application          │  │
│  │  - Port 8000                  │  │
│  │  - Hot Reload Enabled         │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  SQLite Database              │  │
│  │  - Volume mounted             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

#### Production Environment (Phase 1)
```
┌─────────────────────────────────────────────────────────┐
│  Docker Compose / Kubernetes                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Nginx       │  │  FastAPI     │  │  Background  │  │
│  │  Reverse     │→ │  Container   │  │  Worker      │  │
│  │  Proxy       │  │              │  │  Container   │  │
│  │  (SSL/TLS)   │  │  Port 8000   │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                  ↓                  ↓         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  PostgreSQL Database Container                  │  │
│  │  - Persistent Volume                            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Redis Cache Container (Optional)               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Next Implementation Steps

1. **Week 1-2: Core Infrastructure**
   - Set up FastAPI project structure
   - Implement exception hierarchy (`app/core/exceptions.py`)
   - Configure structured logging
   - Set up SQLAlchemy models and database

2. **Week 3-4: Authentication & User Management**
   - Implement AuthService and JWT handling
   - Create user registration/login endpoints
   - Set up password hashing and token management
   - Add authentication middleware

3. **Week 5-6: Garmin Integration**
   - Implement GarminService
   - Set up Garmin API client (garminconnect)
   - Create health metrics and activity repositories
   - Implement retry logic and error handling

4. **Week 7-8: Data Processing**
   - Implement DataProcessor service
   - Add TSS/CTL/ATL/TSB calculations
   - Create aggregation functions
   - Add caching layer

5. **Week 9-10: AI Analysis**
   - Implement AIAnalyzer service
   - Integrate Claude AI API
   - Create prompt templates
   - Implement response parsing and validation

6. **Week 11-12: API Endpoints**
   - Implement all REST API endpoints
   - Add request/response validation (Pydantic)
   - Set up rate limiting
   - Generate OpenAPI documentation

7. **Week 13-14: Background Jobs**
   - Implement SchedulerService
   - Set up daily sync job
   - Add weekly analysis job
   - Implement notification service

8. **Week 15-16: Testing & Deployment**
   - Write comprehensive tests (unit, integration)
   - Set up CI/CD pipeline
   - Create Docker containers
   - Deploy to production environment

### API Response Examples

#### Success Response
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "user@example.com"
  },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

#### Error Response
```json
{
  "success": false,
  "error": {
    "code": "GARMIN_AUTH_FAILED",
    "message": "Unable to authenticate with Garmin Connect",
    "details": "Invalid credentials or session expired",
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

#### Validation Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "validation_errors": [
      {
        "field": "start_date",
        "message": "Invalid date format",
        "type": "value_error.date"
      }
    ],
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## Key Design Decisions

### 1. Service-Repository Pattern
- **Why**: Clear separation of business logic from data access
- **Benefit**: Easier testing, maintainability, future database migration

### 2. JWT Authentication
- **Why**: Stateless authentication for scalability
- **Benefit**: No server-side session storage, works with load balancers

### 3. Async/Await Throughout
- **Why**: Non-blocking I/O for better concurrency
- **Benefit**: Handle multiple requests efficiently with fewer resources

### 4. SQLite → PostgreSQL Migration Path
- **Why**: Start simple, upgrade when needed
- **Benefit**: Faster initial development, easy local setup

### 5. Repository Pattern for Data Access
- **Why**: Abstract database operations from services
- **Benefit**: Testable services, database-agnostic code

### 6. Structured Logging
- **Why**: Machine-readable logs for better monitoring
- **Benefit**: Easy log aggregation, filtering, and analysis

### 7. Retry with Exponential Backoff
- **Why**: Handle transient external API failures gracefully
- **Benefit**: Improved reliability without manual intervention

### 8. Circuit Breaker Pattern
- **Why**: Prevent cascading failures to external services
- **Benefit**: Faster failure detection, reduced load on failing services

## Documentation Quick Links

- **[Complete Architecture](./architecture.md)** - Detailed architecture documentation
- **[API Design](./api_design.md)** - Complete API endpoint specifications
- **[System Diagram](./diagrams/system_architecture.mmd)** - Visual system architecture
- **[Data Flow](./diagrams/data_flow.mmd)** - Data flow sequence diagrams
- **[Authentication Flow](./diagrams/authentication_flow.mmd)** - Authentication sequences
- **[Service Interactions](./diagrams/service_interactions.mmd)** - Service dependency graph
- **[Exception Hierarchy](../app/core/exceptions.py)** - Custom exception implementations

## Questions or Feedback?

For questions about the architecture or suggestions for improvements, please:
1. Review the detailed documentation linked above
2. Check the diagrams for visual understanding
3. Refer to the exception hierarchy for error handling patterns
4. Consult the API design document for endpoint specifications
