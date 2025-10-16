# Architecture Quick Reference Card

## File Locations

### Core Documentation
```
docs/architecture.md              - Complete architecture (750+ lines)
docs/api_design.md                - API design (1,300+ lines)
docs/ARCHITECTURE_SUMMARY.md      - Quick reference (650+ lines)
ARCHITECTURE_INDEX.md             - Master index (550+ lines)
```

### Diagrams
```
docs/diagrams/system_architecture.mmd      - Component diagram
docs/diagrams/data_flow.mmd                - Sequence diagrams
docs/diagrams/authentication_flow.mmd      - Auth flows
docs/diagrams/service_interactions.mmd     - Dependencies
```

### Code
```
app/core/exceptions.py            - Exception hierarchy (650+ lines)
```

---

## Service Layer (8 Services)

| Service | Responsibility | External API |
|---------|---------------|--------------|
| **GarminService** | Fetch Garmin data, auth, rate limiting | Garmin Connect |
| **AIAnalyzer** | Claude AI analysis & recommendations | Claude AI |
| **DataProcessor** | Calculate TSS/CTL/ATL/TSB, aggregate | - |
| **TrainingPlanner** | Generate & adapt training plans | - |
| **NotificationService** | Email/SMS notifications | Email/SMS providers |
| **SchedulerService** | Background job orchestration | - |
| **ExportService** | Data export (CSV, JSON) | - |
| **AuthService** | User auth, JWT tokens | - |

---

## API Endpoints (50+)

| Resource | Base Path | Key Endpoints |
|----------|-----------|---------------|
| Auth | `/api/v1/auth/*` | register, login, logout, refresh |
| Health | `/api/v1/health/*` | metrics, sleep, stress, body |
| Activities | `/api/v1/activities/*` | list, details, summary |
| Training | `/api/v1/training/*` | plans, workouts |
| Recommendations | `/api/v1/recommendations/*` | list, details |
| Analysis | `/api/v1/analysis/*` | generate, results |
| Sync | `/api/v1/sync/*` | trigger, status, schedule |
| Export | `/api/v1/export/*` | activities, health, download |

---

## Exception Hierarchy

```
AppException
├── ExternalAPIError
│   ├── GarminAPIError (Auth, Connection, RateLimit)
│   └── AIAnalysisError (API, TokenLimit, Parsing)
├── DataError (Validation, Processing, NotFound)
├── DatabaseError (Connection, Integrity, Query)
└── AuthenticationError / AuthorizationError
```

**File**: `app/core/exceptions.py`

---

## Architecture Layers

```
Presentation → API → Service → Repository → Database
              ↓
         External APIs
```

1. **Presentation**: Web Dashboard (React/Vue)
2. **API**: FastAPI + Middleware (auth, rate limiting, logging)
3. **Service**: Business logic (8 services)
4. **Repository**: Data access (7 repositories)
5. **Database**: SQLite → PostgreSQL

---

## Data Flow (Daily Sync)

```
Scheduler
   ↓
GarminService → Garmin API → Database
   ↓
DataProcessor → Calculate Metrics → Database
   ↓
AIAnalyzer → Claude AI → Recommendations → Database
   ↓
NotificationService → Email User
```

---

## Authentication (JWT)

```
Login → Generate Tokens
   ├── Access Token (15 min)
   └── Refresh Token (7 days)

Request → Verify Access Token → Allow/Deny

Token Expired → Use Refresh Token → New Access Token
```

---

## Error Handling Patterns

1. **Retry with Exponential Backoff** (Garmin API, Claude API)
2. **Circuit Breaker** (External APIs)
3. **Graceful Degradation** (Use cached data)
4. **Structured Logging** (Request ID correlation)

---

## Security Measures

- JWT authentication (access + refresh tokens)
- bcrypt password hashing
- Fernet credential encryption
- Rate limiting (per-user, per-endpoint)
- CORS policies
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

---

## Caching Strategy

| Cache Type | TTL | Purpose |
|-----------|-----|---------|
| Dashboard Summary | 5 min | Reduce DB load |
| Health Metrics | 1 hour | Historical data |
| AI Analysis | 24 hours | Expensive to generate |
| Training Plans | Until modified | User-specific |
| Aggregated Stats | 30 min | Calculated metrics |

---

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite → PostgreSQL
- **ORM**: SQLAlchemy 2.0 (async)
- **Auth**: JWT (python-jose)
- **Validation**: Pydantic v2
- **Logging**: structlog
- **Testing**: pytest
- **Background Jobs**: APScheduler

---

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response (p95) | < 200ms |
| Dashboard Load | < 2 seconds |
| Data Sync | < 30 seconds |
| AI Analysis | < 10 seconds |

---

## Repository Pattern

```python
# Service uses Repository
class GarminService:
    def __init__(self, health_repo: HealthMetricsRepository):
        self.health_repo = health_repo

    async def get_metrics(self):
        return await self.health_repo.get_metrics()

# Repository handles DB
class HealthMetricsRepository:
    async def get_metrics(self):
        # SQLAlchemy query
        pass
```

---

## Standard API Response

### Success
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Additional context",
    "timestamp": "2025-10-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## Deployment Architecture

### Development
```
Docker Container
├── FastAPI (port 8000)
└── SQLite
```

### Production
```
Docker Compose
├── Nginx (SSL/TLS)
├── FastAPI Container
├── Background Worker
├── PostgreSQL Container
└── Redis Container (optional)
```

---

## Viewing Diagrams

**GitHub**: View `.mmd` files directly (auto-rendered)
**VS Code**: Install "Mermaid Preview" extension
**Online**: https://mermaid.live (paste diagram code)
**CLI**: `mmdc -i diagram.mmd -o diagram.png`

---

## Implementation Roadmap

**Weeks 1-2**: Core infrastructure, exception hierarchy
**Weeks 3-4**: Authentication & user management
**Weeks 5-6**: Garmin integration
**Weeks 7-8**: Data processing
**Weeks 9-10**: AI analysis
**Weeks 11-12**: API endpoints
**Weeks 13-14**: Background jobs
**Weeks 15-16**: Testing & deployment

---

## Common Tasks

### Add a New Service
1. Create `app/services/new_service.py`
2. Define service class with `__init__(dependencies)`
3. Implement business logic methods
4. Add dependency injection in `app/core/dependencies.py`
5. Update architecture docs

### Add a New API Endpoint
1. Create route in `app/api/routes/resource.py`
2. Define Pydantic request/response models
3. Add dependency injection for services
4. Implement endpoint logic (call service)
5. Add to OpenAPI docs
6. Update `docs/api_design.md`

### Add a New Exception
1. Define exception in `app/core/exceptions.py`
2. Inherit from appropriate base class
3. Set error code and status code
4. Use in service/repository code
5. Test error handling

### Add Background Job
1. Define job function in `app/services/scheduler_service.py`
2. Configure schedule (cron or interval)
3. Add error handling and logging
4. Test job execution
5. Document in architecture

---

## Key Files to Understand

1. **Start**: `ARCHITECTURE_INDEX.md`
2. **Overview**: `docs/ARCHITECTURE_SUMMARY.md`
3. **Deep Dive**: `docs/architecture.md`
4. **API Spec**: `docs/api_design.md`
5. **Errors**: `app/core/exceptions.py`
6. **Diagrams**: `docs/diagrams/`

---

## Scalability Path

**Phase 1** (Current): Single instance, SQLite, in-memory cache
**Phase 2** (Multi-user): Load balancer, PostgreSQL, Redis
**Phase 3** (High scale): Kubernetes, read replicas, message queue

---

## Questions?

📖 Full documentation: `ARCHITECTURE_INDEX.md`
📊 Visual diagrams: `docs/diagrams/`
💬 FAQ: `docs/faq.md`
🐛 Troubleshooting: `docs/troubleshooting.md`
