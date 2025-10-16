# Architecture Documentation Index

## Complete System Architecture for Garmin AI Training Optimization System

This document serves as the master index for all architecture documentation.

---

## Quick Start

**New to the project?** Start here:
1. Read [Architecture Summary](./docs/ARCHITECTURE_SUMMARY.md) for a high-level overview
2. Review [System Architecture Diagram](./docs/diagrams/system_architecture.mmd)
3. Explore [API Design](./docs/api_design.md) for endpoint specifications

**Implementing a feature?** Refer to:
- [Service Layer Design](#service-layer) for business logic patterns
- [API Endpoints](#api-endpoints) for endpoint specifications
- [Exception Handling](#exception-handling) for error patterns

**Setting up the project?** See:
- [Development Setup](./docs/development.md)
- [Database Schema](./docs/database_schema.md)

---

## Documentation Structure

### 📋 Overview Documents

| Document | Description | Audience |
|----------|-------------|----------|
| [ARCHITECTURE_SUMMARY.md](./docs/ARCHITECTURE_SUMMARY.md) | High-level architecture summary, quick reference | Everyone |
| [architecture.md](./docs/architecture.md) | Complete detailed architecture documentation | Developers, Architects |
| [api_design.md](./docs/api_design.md) | Comprehensive API endpoint specifications | Frontend Developers, API Consumers |

### 📊 Visual Diagrams

| Diagram | Type | Purpose |
|---------|------|---------|
| [system_architecture.mmd](./docs/diagrams/system_architecture.mmd) | Component Diagram | Complete system structure |
| [data_flow.mmd](./docs/diagrams/data_flow.mmd) | Sequence Diagram | Data flow through the system |
| [authentication_flow.mmd](./docs/diagrams/authentication_flow.mmd) | Sequence Diagram | Authentication and authorization |
| [service_interactions.mmd](./docs/diagrams/service_interactions.mmd) | Dependency Graph | Service dependencies |

📖 [Diagram Viewing Guide](./docs/diagrams/README.md)

### 💻 Implementation Reference

| File | Description | Purpose |
|------|-------------|---------|
| [app/core/exceptions.py](./app/core/exceptions.py) | Exception hierarchy implementation | Error handling patterns |
| [docs/database_schema.md](./docs/database_schema.md) | Database schema design | Data model reference |
| [docs/development.md](./docs/development.md) | Development workflow guide | Developer onboarding |

---

## Architecture Components

### Service Layer

The service layer contains all business logic, organized by responsibility:

#### Core Services

| Service | File Location (Future) | Responsibility | Documentation |
|---------|----------------------|----------------|---------------|
| **GarminService** | `app/services/garmin_service.py` | Garmin API integration | [Architecture §3.3](./docs/architecture.md#33-service-layer) |
| **AIAnalyzer** | `app/services/ai_analyzer.py` | Claude AI integration | [Architecture §3.3](./docs/architecture.md#33-service-layer) |
| **DataProcessor** | `app/services/data_processor.py` | Metrics calculation | [Architecture §3.3](./docs/architecture.md#33-service-layer) |
| **TrainingPlanner** | `app/services/training_planner.py` | Training plan generation | [Architecture §3.3](./docs/architecture.md#33-service-layer) |
| **NotificationService** | `app/services/notification_service.py` | Email/SMS notifications | [Architecture §3.3](./docs/architecture.md#33-service-layer) |
| **SchedulerService** | `app/services/scheduler_service.py` | Background job orchestration | [Architecture §3.3](./docs/architecture.md#33-service-layer) |

**Design Pattern**: Service-Repository Pattern
**Documentation**: [Architecture - Service Layer](./docs/architecture.md#service-layer-design-pattern)

### API Endpoints

All API endpoints follow RESTful conventions and are organized by resource:

| Resource | Base Path | Endpoints | Documentation |
|----------|-----------|-----------|---------------|
| Authentication | `/api/v1/auth/*` | register, login, logout, refresh | [API Design - Auth](./docs/api_design.md#1-authentication--user-management) |
| Health Metrics | `/api/v1/health/*` | metrics, sleep, stress, body | [API Design - Health](./docs/api_design.md#2-health-metrics-apiv1health) |
| Activities | `/api/v1/activities/*` | list, details, summary | [API Design - Activities](./docs/api_design.md#3-activities--workouts-apiv1activities) |
| Training Plans | `/api/v1/training/*` | plans, workouts | [API Design - Training](./docs/api_design.md#4-training-plans-apiv1training) |
| Recommendations | `/api/v1/recommendations/*` | list, details | [API Design - Recommendations](./docs/api_design.md#5-ai-recommendations-apiv1recommendations) |
| Analysis | `/api/v1/analysis/*` | generate, results | [API Design - Analysis](./docs/api_design.md#6-ai-analysis-apiv1analysis) |
| Sync | `/api/v1/sync/*` | trigger, status, schedule | [API Design - Sync](./docs/api_design.md#7-data-synchronization-apiv1sync) |
| Export | `/api/v1/export/*` | activities, health | [API Design - Export](./docs/api_design.md#8-data-export-apiv1export) |

**API Standard**: RESTful with JSON responses
**Documentation**: [Complete API Design](./docs/api_design.md)

### Exception Handling

Custom exception hierarchy for comprehensive error handling:

```
AppException (Base)
├── ExternalAPIError
│   ├── GarminAPIError (GarminAuthenticationError, GarminConnectionError, GarminRateLimitError)
│   └── AIAnalysisError (ClaudeAPIError, ClaudeTokenLimitError, ClaudeParsingError)
├── DataError (DataValidationError, DataProcessingError, DataNotFoundError)
├── DatabaseError (DatabaseConnectionError, DatabaseIntegrityError)
└── AuthenticationError / AuthorizationError
```

**Implementation**: [app/core/exceptions.py](./app/core/exceptions.py)
**Documentation**: [Architecture - Error Handling](./docs/architecture.md#error-handling-strategy)

### Data Access Layer

Repository pattern for database abstraction:

| Repository | Entity | Operations |
|-----------|--------|-----------|
| UserRepository | User | CRUD, authentication |
| HealthMetricsRepository | HealthMetrics | Save, query by date range |
| ActivityRepository | Activity | Save, query, aggregate |
| RecommendationRepository | Recommendation | Save, query, update status |
| TrainingPlanRepository | TrainingPlan | CRUD, query by user |
| AnalysisRepository | Analysis | Save, query |

**Design Pattern**: Repository Pattern
**Documentation**: [Architecture - Data Access Layer](./docs/architecture.md#4-data-access-layer)

---

## Architecture Patterns

### 1. Service-Repository-Entity Pattern

```python
# Controller/Router (FastAPI)
@router.get("/health/metrics")
async def get_health_metrics(
    garmin_service: GarminService = Depends(get_garmin_service)
):
    return await garmin_service.get_health_metrics()

# Service Layer (Business Logic)
class GarminService:
    def __init__(self, health_repo: HealthMetricsRepository):
        self.health_repo = health_repo

    async def get_health_metrics(self):
        # Business logic here
        return await self.health_repo.get_metrics()

# Repository Layer (Data Access)
class HealthMetricsRepository:
    async def get_metrics(self):
        # Database operations
        pass
```

**Documentation**: [Architecture - Service Layer Design](./docs/architecture.md#service-layer-design-pattern)

### 2. Retry with Exponential Backoff

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(GarminConnectionError)
)
async def fetch_garmin_data():
    # API call with automatic retry
    pass
```

**Documentation**: [Architecture - Error Handling](./docs/architecture.md#2-error-handling-patterns)

### 3. Circuit Breaker Pattern

```python
@circuit_breaker(failure_threshold=5, recovery_timeout=60)
async def call_claude_api(prompt: str):
    # Prevents cascading failures
    pass
```

**Documentation**: [Architecture - Resilience Patterns](./docs/architecture.md#circuit-breaker-pattern)

### 4. Graceful Degradation

```python
try:
    return await garmin_service.fetch_latest_data(user_id)
except GarminAPIError:
    # Fallback to cached data
    return await cache.get_cached_data(user_id)
```

**Documentation**: [Architecture - Error Handling](./docs/architecture.md#graceful-degradation)

---

## Security Architecture

### Authentication Flow
1. User registers → Password hashed with bcrypt
2. User logs in → JWT access token (15 min) + refresh token (7 days)
3. API requests → Bearer token in Authorization header
4. Token expires → Refresh using refresh token
5. Logout → Invalidate refresh token

**Diagram**: [Authentication Flow](./docs/diagrams/authentication_flow.mmd)
**Documentation**: [Architecture - Security](./docs/architecture.md#security-considerations)

### Data Protection
- **Passwords**: bcrypt hashing with salt
- **Garmin Credentials**: Fernet symmetric encryption
- **API Keys**: Environment variables only
- **Database**: SQLAlchemy ORM (SQL injection prevention)

**Documentation**: [Architecture - Security Considerations](./docs/architecture.md#security-considerations)

---

## Data Flow Examples

### Daily Automated Sync
```
Scheduler → GarminService → Garmin API → Database
         ↓
   DataProcessor → Calculate Metrics → Database
         ↓
    AIAnalyzer → Claude AI → Recommendations → Database
         ↓
NotificationService → Email User
```

**Diagram**: [Data Flow - Daily Sync](./docs/diagrams/data_flow.mmd)

### User Dashboard Request
```
User → Dashboard → API → DataProcessor → Database → JSON Response
```

**Diagram**: [Data Flow - Dashboard View](./docs/diagrams/data_flow.mmd)

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | FastAPI | Latest | Web framework |
| **Language** | Python | 3.11+ | Programming language |
| **Database** | SQLite → PostgreSQL | Latest | Data persistence |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Authentication** | python-jose | Latest | JWT handling |
| **Validation** | Pydantic | v2 | Request/response validation |
| **Logging** | structlog | Latest | Structured logging |
| **Testing** | pytest | Latest | Test framework |

**Documentation**: [Architecture - Technology Stack](./docs/architecture.md#technology-stack-summary)

---

## Performance Targets

| Metric | Target | Current | Monitoring |
|--------|--------|---------|-----------|
| API Response Time (p95) | < 200ms | TBD | Application metrics |
| Dashboard Load Time | < 2 seconds | TBD | Frontend performance |
| Data Sync Duration | < 30 seconds | TBD | Background job logs |
| AI Analysis Generation | < 10 seconds | TBD | Claude API metrics |

**Documentation**: [Architecture - Performance Targets](./docs/architecture.md#performance-targets)

---

## Deployment Architecture

### Development Environment
- Single Docker container
- FastAPI + SQLite
- Hot reload enabled
- Port 8000

### Production Environment (Phase 1)
- Docker Compose / Kubernetes
- Nginx reverse proxy (SSL/TLS)
- FastAPI application container
- PostgreSQL database container
- Background worker container
- Redis cache (optional)

**Documentation**: [Architecture - Deployment Architecture](./docs/architecture.md#deployment-architecture)

---

## Development Workflow

### Setting Up Development Environment
1. Clone repository
2. Set up Python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables (`.env`)
5. Initialize database: `alembic upgrade head`
6. Run application: `uvicorn app.main:app --reload`

**Documentation**: [Development Setup](./docs/development.md)

### Making Changes
1. Create feature branch
2. Implement changes following service layer pattern
3. Update tests
4. Run tests: `pytest`
5. Update documentation if needed
6. Submit pull request

**Documentation**: [Development Workflow](./docs/development.md)

---

## Testing Strategy

### Test Levels
- **Unit Tests**: Test individual services and functions
- **Integration Tests**: Test API endpoints and database interactions
- **Contract Tests**: Test API response schemas
- **End-to-End Tests**: Test complete user workflows

**Test Coverage Target**: > 80%

**Documentation**: [Architecture - Testing Strategies](./docs/architecture.md#testing-strategies)

---

## Monitoring & Observability

### Health Checks
- `/health` - Basic health check
- `/health/detailed` - Component health status

### Logging
- **Development**: Pretty console logs
- **Production**: JSON logs → CloudWatch/ELK
- **Correlation**: Request ID tracking

### Metrics (Future)
- API request rate and latency
- Error rates by endpoint
- External API success rates
- Background job completion rates

**Documentation**: [Architecture - Monitoring & Observability](./docs/architecture.md#monitoring--observability)

---

## Roadmap

### Phase 1: MVP (Current)
- ✅ Architecture design complete
- ⬜ Core services implementation
- ⬜ API endpoints
- ⬜ Authentication
- ⬜ Garmin integration
- ⬜ Claude AI integration
- ⬜ Basic dashboard

### Phase 2: Multi-User
- ⬜ PostgreSQL migration
- ⬜ Redis caching
- ⬜ Horizontal scaling
- ⬜ Advanced analytics

### Phase 3: Advanced Features
- ⬜ Mobile app
- ⬜ Social features
- ⬜ Advanced training plans
- ⬜ Coach collaboration

**Documentation**: [Architecture - Scalability Path](./docs/architecture.md#scalability-considerations)

---

## Additional Resources

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Claude AI API Documentation](https://docs.anthropic.com/)
- [Garmin Connect Python Library](https://github.com/cyberjunky/python-garminconnect)

### Internal Documentation
- [Setup Guide](./docs/setup.md)
- [FAQ](./docs/faq.md)
- [Troubleshooting](./docs/troubleshooting.md)

---

## Getting Help

### Documentation Navigation
1. **High-level overview**: Start with [ARCHITECTURE_SUMMARY.md](./docs/ARCHITECTURE_SUMMARY.md)
2. **Detailed architecture**: Read [architecture.md](./docs/architecture.md)
3. **API reference**: Consult [api_design.md](./docs/api_design.md)
4. **Visual understanding**: Review [diagrams](./docs/diagrams/)
5. **Implementation details**: Check [exceptions.py](./app/core/exceptions.py)

### Common Questions
- "Where do I add business logic?" → Service layer (see [Service Layer Design](./docs/architecture.md#service-layer-design-pattern))
- "How do I handle errors?" → Use custom exceptions (see [exceptions.py](./app/core/exceptions.py))
- "How do I add a new API endpoint?" → Follow API design patterns (see [API Design](./docs/api_design.md))
- "Where is the database schema?" → See [database_schema.md](./docs/database_schema.md)

---

## Document Maintenance

This index should be updated whenever:
- New architecture documents are added
- Major architectural changes are made
- New services or endpoints are implemented
- Documentation structure changes

**Last Updated**: 2025-10-15
**Version**: 1.0
**Maintained By**: Architecture Team
