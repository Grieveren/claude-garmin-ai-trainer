# AI-Powered Training Optimization System

**Intelligent fitness training optimizer powered by Garmin data and Claude AI**

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)

---

## Overview

An AI-powered fitness training optimization system that automatically fetches your Garmin health data, analyzes your recovery status using Claude AI, and generates personalized daily workout recommendations. Think of it as having an AI coach that understands your body's signals and adapts your training in real-time.

---

## Key Features

- **Automatic Garmin Data Syncing** - Fetches sleep, HRV, heart rate, and activity data daily
- **AI-Powered Daily Workout Recommendations** - Claude AI analyzes your recovery and suggests optimal workouts
- **Training Load Tracking** - Prevents overtraining with ACWR monitoring and injury risk assessment
- **Performance Trend Analysis** - Track improvements in VO2 max, pace efficiency, and fitness markers
- **Adaptive Training Plan Generation** - Creates personalized training plans that adapt to your body's response
- **Smart Notifications and Alerts** - Get morning recommendations and overtraining warnings via email/SMS
- **Web Dashboard** - Mobile-friendly interface to view recommendations, analytics, and training plans

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Active Garmin Connect account
- Claude API key (from anthropic.com)
- 20-30 minutes for setup

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/training-optimizer.git
cd training-optimizer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Garmin credentials and Claude API key

# 5. Initialize database
python scripts/initial_setup.py

# 6. Run application
uvicorn app.main:app --reload

# 7. Open browser
# Navigate to http://localhost:8000
```

For detailed setup instructions, see [docs/setup.md](docs/setup.md).

---

## Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite (upgradeable to PostgreSQL)
- **AI Engine**: Claude Sonnet 4.5 (Anthropic API)
- **Data Source**: garminconnect library (unofficial)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Scheduling**: APScheduler
- **Frontend**: Jinja2 templates, HTML/CSS/JavaScript

---

## How It Works

### Daily Workflow

1. **8:00 AM** - System automatically syncs yesterday's Garmin data
2. **8:05 AM** - AI analyzes your recovery status (sleep, HRV, training load)
3. **8:10 AM** - You receive morning notification with workout recommendation
4. **Anytime** - Check dashboard for detailed insights and training plan
5. **Post-workout** - Garmin syncs your completed workout
6. **Overnight** - System prepares tomorrow's recommendation

### AI Analysis

Claude AI examines:
- Last night's sleep quality and duration
- Morning HRV vs 7-day and 30-day baseline
- Resting heart rate trends
- Recent training load and cumulative stress
- Acute:Chronic Workload Ratio (injury risk)
- Current training plan context

Then recommends:
- Readiness score (0-100)
- Workout intensity (high/moderate/easy/rest)
- Specific workout with structure and pacing
- Alternative options if you feel tired
- Recovery optimization tips

---

## Screenshot Preview

```
Today's Training Dashboard
┌─────────────────────────────────────────────┐
│  READY TO TRAIN                              │
│  Readiness Score: 82/100                     │
│                                               │
│  TODAY'S WORKOUT: Tempo Run - 45 minutes     │
│  • 10min warm-up (easy)                      │
│  • 25min at threshold pace (4:45-5:00/km)    │
│  • 10min cool-down (easy)                    │
│                                               │
│  Why: Your recovery is excellent. Time for   │
│  quality work to improve race pace endurance.│
│                                               │
│  KEY FACTORS:                                │
│  ✓ Sleep: 8.2 hours (85% quality)           │
│  ✓ HRV: 62ms (vs 7-day avg 58ms)            │
│  ✓ Resting HR: 48 bpm (baseline)            │
│  ✓ Training load: Stable                     │
└─────────────────────────────────────────────┘
```

---

## Important Disclaimers

### Unofficial Garmin API
This system uses the `garminconnect` Python library, which reverse-engineers Garmin's web API.

- **Not endorsed by Garmin** - May violate Terms of Service
- **Could break anytime** - Garmin updates may cause failures
- **Personal use only** - Not for commercial deployment
- **Workaround exists** - Manual FIT file import if API breaks
- **Actively maintained** - Community keeps library updated

**Alternative**: Consider Apple HealthKit for iOS-only implementation.

### Not Medical Advice
AI recommendations are for informational purposes only:
- Consult healthcare professionals for medical concerns
- Use your judgment and listen to your body
- System cannot detect all health issues
- Designed for healthy individuals engaged in training

### Claude AI Costs
Estimated monthly costs:
- Daily readiness analysis: $3-6/month
- Weekly insights: $2-3/month
- Training plan generation: $1-2 per plan
- Chat queries: $1-3/month
- **Total estimate: $5-15/month** for regular use

Costs are optimized through:
- Automatic prompt caching
- Response caching (24-hour)
- Efficient data context windowing

---

## Configuration

### Required Environment Variables

```bash
# Garmin Account
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Claude AI
ANTHROPIC_API_KEY=sk-ant-your-api-key

# User Profile
ATHLETE_AGE=30
MAX_HEART_RATE=188
RESTING_HEART_RATE=48
TRAINING_GOAL=marathon

# Optional: Notifications
SMTP_USERNAME=your_email@gmail.com
NOTIFICATION_EMAIL=your_email@gmail.com
```

See `.env.example` for complete configuration options.

---

## Documentation

- [Setup Guide](docs/setup.md) - Detailed installation and configuration
- [Development Guide](docs/development.md) - Contributing and development workflow
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [FAQ](docs/faq.md) - Frequently asked questions
- [API Reference](docs/api_reference.md) - API endpoint documentation

---

## Common Issues

### Garmin Login Fails
1. Verify credentials in `.env` file
2. Check if Garmin account is active
3. 2FA not supported - disable if enabled
4. Update library: `pip install --upgrade garminconnect`
5. See [docs/troubleshooting.md](docs/troubleshooting.md) for details

### Database Errors
```bash
# Reset database
rm data/training_data.db
python scripts/initial_setup.py
```

### AI Analysis Too Expensive
```bash
# Enable aggressive caching in .env
AI_CACHE_HOURS=48
# Reduce analysis frequency
SYNC_HOUR=6  # Run less frequently
```

For more solutions, see [docs/troubleshooting.md](docs/troubleshooting.md).

---

## Usage Examples

### View Today's Recommendation
```bash
curl http://localhost:8000/api/recommendations/today
```

### Chat with AI Coach
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why am I not improving my 10K time?"}'
```

### Export Training Data
```bash
curl http://localhost:8000/api/export/csv?start_date=2025-01-01 \
  > my_training_data.csv
```

---

## Project Status

**Current Phase**: In Development
**Target**: MVP by Week 3
**Next Milestone**: Core AI analysis implementation

### Roadmap

- [x] Project specification complete
- [x] Implementation plan created
- [ ] Database schema implemented
- [ ] Garmin integration working
- [ ] AI analysis engine built
- [ ] Web dashboard deployed
- [ ] Automated daily workflow
- [ ] Full testing complete

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed timeline.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Pull request process
- Coding standards

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_garmin_service.py -v
```

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

**Important**: While this code is open source, be aware that:
- Using unofficial Garmin API may violate their TOS
- Claude AI costs are your responsibility
- System is provided as-is without warranties
- For personal use only

---

## Acknowledgments

- [garminconnect](https://github.com/cyberjunky/python-garminconnect) - Community-maintained Garmin API library
- [Anthropic](https://anthropic.com) - Claude AI platform
- Training science resources and research papers
- Open source community

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/training-optimizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/training-optimizer/discussions)
- **Email**: your.email@example.com

---

## Security

Report security vulnerabilities to: security@example.com

Do not:
- Commit `.env` file with credentials
- Share your Claude API key
- Expose health data publicly

---

## Performance

Typical performance benchmarks:
- Daily sync: 2-3 minutes
- AI analysis: 15-30 seconds
- Dashboard load: <2 seconds
- API response: <500ms

---

## System Requirements

**Minimum**:
- Python 3.10+
- 2GB RAM
- 500MB disk space
- Internet connection

**Recommended**:
- Python 3.11+
- 4GB RAM
- 2GB disk space (for data storage)
- Stable internet (for Garmin/Claude APIs)

---

## What's Next?

After initial setup:
1. Backfill 90 days of historical data for baseline
2. Use system for 1-2 weeks to calibrate AI
3. Generate your first training plan
4. Review and adjust based on your preferences
5. Let the system adapt to your body over time

---

## Getting Help

1. Check [docs/troubleshooting.md](docs/troubleshooting.md)
2. Review [docs/faq.md](docs/faq.md)
3. Search [GitHub Issues](https://github.com/yourusername/training-optimizer/issues)
4. Open new issue with details
5. Join community discussions

---

**Built with passion for runners, by runners. Train smarter, not just harder.**
