# Documentation Overview

Welcome to the AI-Powered Training Optimization System documentation.

---

## Quick Links

### Getting Started
- [Main README](../README.md) - Project overview and quick start
- [Setup Guide](setup.md) - Detailed installation instructions
- [FAQ](faq.md) - Frequently asked questions

### Using the System
- [User Guide](user_guide.md) - Complete user manual (coming soon)
- [Training Science](training_science.md) - Understanding the methodology (coming soon)
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

### Development
- [Development Guide](development.md) - Contributing and development workflow
- [Architecture](architecture.md) - System architecture overview (to be created by architect)
- [API Reference](api_reference.md) - API endpoint documentation (to be created)
- [Database Schema](database_schema.md) - Database design (to be created by db architect)

### Contributing
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute
- [Code of Conduct](../CONTRIBUTING.md#code-of-conduct) - Community standards

---

## Documentation Structure

```
docs/
├── README.md (this file)        # Documentation overview
├── setup.md                     # Installation and configuration
├── development.md               # Development guide
├── troubleshooting.md           # Common issues
├── faq.md                       # Frequently asked questions
│
├── architecture.md              # System architecture (future)
├── api_reference.md             # API documentation (future)
├── database_schema.md           # Database design (future)
├── user_guide.md                # Complete user manual (future)
├── training_science.md          # Training methodology (future)
│
└── diagrams/                    # Architecture diagrams (future)
    ├── architecture.mmd
    ├── data_flow.mmd
    ├── workflows.mmd
    └── erd.mmd
```

---

## Documentation by Topic

### Installation & Setup

**New to the project?** Start here:
1. Read [Main README](../README.md) for project overview
2. Check [Prerequisites](setup.md#prerequisites) to ensure you have what you need
3. Follow [Installation Steps](setup.md#installation-steps) to get running
4. Configure using [Configuration Guide](setup.md#configuration)
5. Verify with [First Run](setup.md#first-run) instructions

**Having issues?** See [Troubleshooting Setup](setup.md#troubleshooting-setup)

---

### Daily Usage

**Once installed**, your daily workflow:
1. **Morning** - Check email/dashboard for today's recommendation
2. **Pre-workout** - Review workout details and adjust if needed
3. **Post-workout** - Garmin syncs automatically
4. **Evening** - System prepares tomorrow's analysis

**Features**:
- View readiness score and key factors
- Get specific workout recommendations
- Chat with AI about training questions
- Review performance trends
- Export training data

See [User Guide](user_guide.md) for detailed usage instructions (coming soon).

---

### Understanding the System

**How it works**:
- [System Architecture](architecture.md) - Technical overview (future)
- [Training Science](training_science.md) - Scientific methodology (future)
- [AI Analysis](../AI_Training_Optimizer_Specification.md#ai-analysis-engine-core-feature) - How AI makes decisions
- [Database Design](database_schema.md) - Data structure (future)

**Key Concepts**:
- **HRV (Heart Rate Variability)** - Primary recovery indicator
- **ACWR (Acute:Chronic Workload Ratio)** - Injury risk management
- **Training Load** - Fitness/Fatigue/Form model
- **Periodization** - Training plan structure

---

### Development & Contributing

**Want to contribute?** Great!
1. Read [Contributing Guidelines](../CONTRIBUTING.md)
2. Set up [Development Environment](development.md#development-environment-setup)
3. Understand [Code Organization](development.md#code-organization)
4. Follow [Code Style Guidelines](development.md#code-style-guidelines)
5. Submit [Pull Requests](development.md#pull-request-process)

**Development topics**:
- [Adding New Features](development.md#adding-new-features)
- [Running Tests](development.md#running-tests)
- [Debugging Tips](development.md#debugging-tips)
- [Database Migrations](development.md#database-migrations)

---

### Troubleshooting

Having problems? Check these first:

**Common Issues**:
- [Garmin Connection Failures](troubleshooting.md#garmin-connection-issues) - Authentication and API problems
- [Database Errors](troubleshooting.md#database-errors) - Database locks and migrations
- [API Errors](troubleshooting.md#api-errors) - Claude AI and rate limiting
- [Configuration Issues](troubleshooting.md#configuration-issues) - Environment variables and settings
- [Performance Issues](troubleshooting.md#performance-issues) - Slow syncs and analysis

**Quick Fixes**:
- Restart application: `Ctrl+C` then `uvicorn app.main:app --reload`
- Reset database: `rm data/training_data.db && python scripts/initial_setup.py`
- Check logs: `tail -100 logs/training_optimizer.log`
- Update dependencies: `pip install --upgrade -r requirements.txt`

---

### FAQ

**Frequently asked questions**:

**General**:
- [What is this system?](faq.md#what-is-this-system)
- [Who is this for?](faq.md#who-is-this-for)
- [How much does it cost?](faq.md#how-much-does-it-cost)
- [What Garmin devices are supported?](faq.md#what-garmin-devices-are-supported)

**Setup**:
- [How long does setup take?](faq.md#how-long-does-setup-take)
- [Do I need programming experience?](faq.md#do-i-need-programming-experience)
- [Why do I need a Claude API key?](faq.md#why-do-i-need-a-claude-api-key)

**Privacy**:
- [Is my data safe?](faq.md#is-my-data-safe)
- [Will Garmin ban my account?](faq.md#will-garmin-ban-my-account)

**Functionality**:
- [How does AI know what workout to recommend?](faq.md#how-does-the-ai-know-what-workout-to-recommend)
- [Can I override AI recommendations?](faq.md#can-i-override-the-ai-recommendations)
- [How accurate are recommendations?](faq.md#how-accurate-are-the-ai-recommendations)

**Technical**:
- [Can I run this on Raspberry Pi?](faq.md#can-i-run-this-on-a-raspberry-pi)
- [Can I access from my phone?](faq.md#can-i-access-this-from-my-phone)
- [What if garminconnect breaks?](faq.md#what-if-garminconnect-library-breaks)

---

## Additional Resources

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com) - Web framework
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org) - Database ORM
- [Anthropic API Reference](https://docs.anthropic.com) - Claude AI
- [Garmin Connect API (unofficial)](https://github.com/cyberjunky/python-garminconnect) - Data source

### Training Science Resources
- [Training Peaks Blog](https://www.trainingpeaks.com/blog/) - Training theory
- [Science of Ultra Podcast](https://www.scienceofultra.com) - Running science
- [Physiology of Sport and Exercise](https://us.humankinetics.com/products/physiology-of-sport-and-exercise-8th-edition) - Textbook

### Community
- [GitHub Issues](https://github.com/username/training-optimizer/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/username/training-optimizer/discussions) - General discussion
- [Reddit r/runningdata](https://reddit.com/r/runningdata) - Running data community

---

## Documentation Status

### Completed
- [x] Main README
- [x] Setup Guide
- [x] Troubleshooting Guide
- [x] FAQ
- [x] Development Guide
- [x] Contributing Guidelines

### In Progress
- [ ] User Guide
- [ ] Training Science Guide
- [ ] API Reference

### Planned
- [ ] Architecture Documentation
- [ ] Database Schema Documentation
- [ ] Architecture Diagrams
- [ ] Video Tutorials
- [ ] Example Workflows

---

## Contributing to Documentation

Documentation improvements are always welcome!

**Ways to help**:
- Fix typos and grammar
- Add missing information
- Improve clarity and examples
- Create diagrams and screenshots
- Write tutorials
- Translate to other languages

**How to contribute**:
1. Fork repository
2. Edit documentation files (Markdown)
3. Submit pull request
4. See [Contributing Guidelines](../CONTRIBUTING.md)

---

## Documentation Conventions

### Formatting
- Use Markdown for all docs
- Use code blocks with language hints: \`\`\`python
- Include examples for complex concepts
- Link between related documentation
- Keep line length <100 characters when possible

### Structure
- Start with overview/introduction
- Use clear headings hierarchy
- Include table of contents for long docs
- End with "Next Steps" or related links
- Add "Last Updated" date for technical docs

### Code Examples
- Make examples copy-pasteable
- Include expected output
- Show both success and error cases
- Comment complex code
- Use realistic but simple examples

---

## Getting Help

Can't find what you're looking for?

1. **Search documentation**: Use browser search (Ctrl+F)
2. **Check FAQ**: [faq.md](faq.md)
3. **Search issues**: [GitHub Issues](https://github.com/username/training-optimizer/issues)
4. **Ask community**: [GitHub Discussions](https://github.com/username/training-optimizer/discussions)
5. **Open issue**: Report missing or unclear documentation

---

## License

Documentation is licensed under [MIT License](../LICENSE), same as the code.

---

**Happy training! Train smarter with AI.**
