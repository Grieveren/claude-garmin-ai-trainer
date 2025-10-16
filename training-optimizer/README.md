# AI-Powered Training Optimization System

An intelligent training analysis system that syncs with Garmin Connect, analyzes your training data using Claude AI, and provides personalized training recommendations.

## Features

- **Automatic Garmin Sync**: Daily synchronization of training activities from Garmin Connect
- **AI-Powered Analysis**: Advanced training insights using Claude AI (Sonnet 4.5)
- **Personalized Recommendations**: Tailored training advice based on your goals and performance
- **Web Dashboard**: Interactive dashboard to view activities, analysis, and recommendations
- **Scheduled Analysis**: Automatic daily analysis and recommendations
- **Training Goals**: Support for marathon, half-marathon, 5k, 10k, and general fitness goals

## Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **AI**: Anthropic Claude AI (Sonnet 4.5)
- **Data Source**: Garmin Connect (unofficial API)
- **Database**: SQLite with SQLAlchemy ORM
- **Scheduler**: APScheduler for automated tasks
- **Frontend**: Jinja2 templates with Tailwind CSS
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Garmin Connect account
- Anthropic API key (for Claude AI)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd training-optimizer
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run setup wizard**:
   ```bash
   python scripts/initial_setup.py
   ```

   The setup wizard will:
   - Create necessary directories
   - Guide you through configuration
   - Test Garmin and Claude AI connections
   - Initialize the database

5. **Start the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

   Or simply:
   ```bash
   python -m app.main
   ```

6. **Access the dashboard**:
   Open your browser to: http://localhost:8000

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required Variables**:
- `GARMIN_EMAIL`: Your Garmin Connect email
- `GARMIN_PASSWORD`: Your Garmin Connect password
- `ANTHROPIC_API_KEY`: Your Anthropic API key

**Optional Variables**:
- `ATHLETE_NAME`: Your name (default: "Athlete")
- `ATHLETE_AGE`: Your age (default: 30)
- `MAX_HEART_RATE`: Maximum heart rate (default: 188)
- `RESTING_HEART_RATE`: Resting heart rate (default: 48)
- `TRAINING_GOAL`: Your training goal (default: "general_fitness")
- `TARGET_RACE_DATE`: Target race date (format: YYYY-MM-DD)
- `SYNC_HOUR`: Hour for daily sync (default: 8)
- `SYNC_MINUTE`: Minute for daily sync (default: 0)

### Getting API Keys

**Anthropic API Key**:
1. Sign up at https://console.anthropic.com/
2. Navigate to API Keys section
3. Create a new API key
4. Add to `.env` file

## Project Structure

```
training-optimizer/
├── app/                    # Application code
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   └── logger.py      # Logging setup
│   ├── models/            # Data models
│   │   └── schemas.py     # Pydantic schemas
│   ├── services/          # Business logic services
│   ├── routers/           # API routes
│   ├── templates/         # HTML templates
│   └── static/            # Static files (CSS, JS)
├── scripts/               # Utility scripts
│   ├── initial_setup.py   # Setup wizard
│   └── sync_data.py       # Manual sync
├── tests/                 # Test suite
├── data/                  # Local data storage
├── logs/                  # Application logs
└── requirements.txt       # Python dependencies
```

## Usage

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Manual Data Sync

```bash
# Sync last 7 days of activities
python scripts/sync_data.py

# Sync last 30 days
python scripts/sync_data.py 30
```

### API Documentation

When running in debug mode, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Development

### Code Style

This project follows modern Python best practices:

- **Formatting**: Black and Ruff
- **Type Hints**: Throughout the codebase
- **Docstrings**: Google style
- **Testing**: Pytest with >90% coverage goal

### Running with Auto-reload

```bash
uvicorn app.main:app --reload --log-level debug
```

### Adding New Dependencies

```bash
pip install <package>
pip freeze > requirements.txt
```

## Roadmap

### Phase 1: Foundation (Current)
- [x] Project scaffolding
- [x] Configuration management
- [x] Logging setup
- [ ] Database models
- [ ] Garmin service
- [ ] Claude AI service

### Phase 2: Core Features
- [ ] Activity sync
- [ ] AI analysis
- [ ] Recommendations engine
- [ ] Web dashboard

### Phase 3: Advanced Features
- [ ] Training plan generation
- [ ] Performance predictions
- [ ] Injury risk assessment
- [ ] Email notifications

### Phase 4: Enhancements
- [ ] Multi-user support
- [ ] Mobile app
- [ ] Integration with other platforms
- [ ] Advanced visualizations

## Troubleshooting

### Garmin Connection Issues

If you experience issues connecting to Garmin:

1. Verify your credentials in `.env`
2. Check if Garmin is having service issues
3. Try logging in via the Garmin website
4. Run the setup wizard again: `python scripts/initial_setup.py`

### Claude AI Issues

If Claude AI isn't working:

1. Verify your API key in `.env`
2. Check your API usage at https://console.anthropic.com/
3. Ensure you have sufficient credits

### Database Issues

If you encounter database errors:

1. Delete the database file: `rm data/training_data.db`
2. Run the setup wizard again
3. Check logs in `logs/training_optimizer.log`

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **Garmin Connect**: For providing training data
- **Anthropic**: For Claude AI capabilities
- **FastAPI**: For the excellent web framework
- **garminconnect**: For the unofficial Garmin API library

## Support

For issues or questions:
1. Check the logs: `tail -f logs/training_optimizer.log`
2. Run setup wizard: `python scripts/initial_setup.py`
3. Review documentation in `docs/`

---

**Built with ❤️ for athletes who want to train smarter, not just harder.**
