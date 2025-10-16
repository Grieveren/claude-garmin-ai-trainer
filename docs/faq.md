# Frequently Asked Questions (FAQ)

Common questions about the AI-Powered Training Optimization System.

---

## General Questions

### What is this system?

The AI-Powered Training Optimization System is a personalized fitness coach that:
- Automatically fetches your health data from Garmin devices
- Uses Claude AI to analyze your recovery status daily
- Generates personalized workout recommendations
- Creates adaptive training plans
- Helps prevent overtraining and injury

Think of it as having an AI running coach that monitors your body 24/7 and tells you what workout to do each day based on your recovery status.

---

### Who is this for?

This system is designed for:
- **Runners** training for races (5K to marathon)
- **Athletes** who want data-driven training decisions
- **Garmin users** with compatible devices
- **Tech-savvy individuals** comfortable with Python and APIs
- **People willing to invest time** in setup (~4-8 hours initially)

**Not recommended for**:
- Complete beginners to running/training
- People without Garmin devices
- Those wanting plug-and-play solutions (requires technical setup)
- Commercial/professional use (for personal use only)

---

### How much does it cost?

**One-time costs**:
- **$0** - The software is free and open source
- **Garmin device** - If you don't have one ($200-$500 typically)

**Monthly costs**:
- **Claude AI API**: $5-15/month for typical usage
  - Daily readiness analysis: ~$3-6/month
  - Training plans: ~$1-2 per plan
  - Chat queries: ~$1-3/month
  - Costs vary with usage

**Optional**:
- Cloud hosting (if not running locally): $5-20/month
- SMS notifications (Twilio): $1-5/month

**Total monthly estimate**: $5-15 for most users

---

### What Garmin devices are supported?

Any Garmin device that syncs to Garmin Connect should work:

**Confirmed working**:
- Forerunner series (245, 255, 265, 745, 945, 965)
- Fenix series (6, 7)
- Epix
- Venu series
- Vivoactive series

**Key requirements**:
- Device must measure HRV (most modern Garmin watches do)
- Must sync to Garmin Connect automatically
- Preferably worn during sleep for sleep tracking

**Not supported**:
- Basic activity trackers without HR monitoring
- Very old Garmin devices (pre-2018)
- Non-Garmin devices (Apple Watch, Fitbit, etc.)

---

### Can I use this with Apple Watch or Fitbit?

**Currently**: No, only Garmin devices are supported.

**Why**: The system uses the `garminconnect` Python library which is specific to Garmin's API.

**Alternatives**:
- **Apple Watch**: Could build iOS version using HealthKit API (significant development required)
- **Fitbit**: Fitbit API is available but would require new integration
- **Strava**: If you sync Garmin → Strava, some data available via Strava API

**Future**: Apple Watch support via HealthKit is being considered for a future version.

---

## Setup & Configuration

### How long does setup take?

**Initial setup**: 4-8 hours total
- **Basic setup**: 30-60 minutes
  - Install Python, clone repo, install dependencies
  - Configure .env file
  - Initialize database

- **Backfilling data**: 1-2 hours
  - Import 30-90 days of historical data
  - Establish HRV and RHR baselines

- **Learning and customization**: 2-4 hours
  - Understanding the system
  - Adjusting settings to your preferences
  - Testing features

**Daily usage**: 5 minutes
- Check morning recommendation
- Review dashboard
- System is mostly automated

---

### Do I need programming experience?

**Minimum required**:
- Basic command line usage (cd, ls, running commands)
- Understanding of environment variables
- Ability to edit text files
- Willingness to read documentation

**Helpful but not required**:
- Python knowledge (for customization)
- API concepts
- Database basics
- Git/GitHub familiarity

**If you can**:
- Install Python packages
- Copy/paste commands into terminal
- Edit configuration files
- Follow step-by-step guides

**Then you can set this up!**

---

### Why do I need a Claude API key?

The AI analysis engine uses Claude (by Anthropic) to:
- Analyze your recovery status
- Generate workout recommendations
- Create training plans
- Answer your training questions via chat

Claude is chosen because:
- Best-in-class reasoning capabilities
- Understands context and nuance
- Provides detailed, thoughtful recommendations
- Relatively affordable ($5-15/month)

**Can't I use ChatGPT instead?**
- Theoretically yes, but would require code changes
- Claude Sonnet 4.5 is currently more capable for this use case
- You could contribute an OpenAI integration if interested!

---

## Privacy & Security

### Is my data safe?

**Data storage**:
- All data stored locally in SQLite database on your computer
- No cloud storage by default
- You control all data

**API security**:
- Garmin credentials stored in `.env` file (not committed to Git)
- Claude API key stored securely
- No data shared with third parties
- System runs on your machine or your server

**Privacy considerations**:
- Health data is sensitive - take backups seriously
- Encrypt backups if storing in cloud
- Use strong passwords
- Don't share API keys or screenshots with credentials

**What data is sent to Anthropic (Claude AI)?**:
- Aggregated health metrics (HRV, RHR, sleep scores)
- Recent workout data (types, durations, intensities)
- Training load metrics
- **No personally identifiable information** (name, email, etc.)
- Data used only for generating your recommendations

---

### What happens to my data if I stop using the system?

**You own all your data**:
- Stored in `data/training_data.db` on your machine
- Can export anytime: `curl http://localhost:8000/api/export/csv`
- Can backup database file
- No vendor lock-in

**Exporting data**:
```bash
# Export everything to CSV
python scripts/export_all_data.py --output my_training_data.csv

# Export to JSON
curl http://localhost:8000/api/export/json > data.json

# Backup database
cp data/training_data.db ~/Backups/
```

---

### Will Garmin ban my account?

**Risk level**: Low but possible

**The situation**:
- This system uses unofficial Garmin API (reverse-engineered)
- Violates Garmin's Terms of Service technically
- Garmin could theoretically ban accounts using it

**Reality**:
- Thousands use `garminconnect` library without issues
- Garmin has not actively banned users
- Activity looks like normal web browser usage
- For personal use only - don't abuse (no excessive requests)

**Mitigations**:
- Use rate limiting (built-in)
- Don't sync more than once per hour
- Respectful API usage
- Don't use for commercial purposes

**Alternative if concerned**:
- Manual FIT file export/import workflow
- Use official Garmin Health API (requires developer account, limited data)

---

## Functionality Questions

### How does the AI know what workout to recommend?

The AI analyzes multiple factors:

**Recovery indicators**:
- HRV vs 7-day and 30-day baseline (primary indicator)
- Resting heart rate vs baseline
- Sleep quality and duration
- Body battery (if available)

**Training history**:
- Last 7 days of workouts
- Training load (acute vs chronic)
- Recent intensity distribution
- Recovery time since last hard workout

**Training plan context**:
- Your current goal (marathon, 5K, etc.)
- What workout is next in your plan
- Phase of training (base, build, peak, taper)

**Personal factors**:
- Your fitness level
- Injury history
- Preferences and constraints

**The AI then**:
- Determines readiness score (0-100)
- Recommends intensity (high/moderate/easy/rest)
- Selects specific workout from library
- Provides detailed rationale
- Suggests alternatives

---

### Can I override the AI recommendations?

**Absolutely!** The AI is a guide, not a dictator.

**You should override if**:
- You feel tired despite good metrics
- You have race or event that day
- Life circumstances change (stress, travel, illness)
- You simply want to do different workout

**How to override**:
```bash
# Web interface
# Go to dashboard → click "Adjust Today's Workout"

# API
curl -X POST http://localhost:8000/api/training/override \
  -d '{"date": "2025-10-15", "workout_type": "rest"}'
```

**The AI learns**:
- System tracks when you override recommendations
- AI can learn your preferences over time
- "You tend to prefer rest days on Mondays"

**Listen to your body first!**
- AI doesn't feel your legs
- You know your body best
- Use AI as informed second opinion

---

### What if I miss a workout?

**No problem!** The system adapts:

1. **Plan automatically adjusts**:
   - Next day's recommendation accounts for missed workout
   - Training plan reshuffles remaining workouts
   - No rigid adherence required

2. **No guilt trips**:
   - AI understands life happens
   - Recommends how to best proceed
   - Maintains progression despite setbacks

3. **Smart catch-up**:
   - Doesn't try to "make up" all missed work
   - Adjusts training load appropriately
   - Prevents overtraining from cramming

**Example**:
```
You missed: Tuesday intervals
AI response: "Let's keep today (Wednesday) as easy run.
We'll do modified intervals on Friday with one less rep.
This maintains quality while respecting your current state."
```

---

### How accurate are the AI recommendations?

**Accuracy depends on**:
- Data quality (garbage in = garbage out)
- Baseline establishment (needs 7-14 days)
- How well you know yourself
- Quality of your inputs (goals, preferences)

**The AI is good at**:
- Detecting overtraining patterns (HRV drops)
- Identifying recovery status
- Balancing training load
- Preventing injury from excessive load

**The AI is less reliable for**:
- Very individual responses (you might be different)
- Detecting illness (overlaps with fatigue)
- Accounting for life stress not in data
- Optimizing peak performance (needs more data)

**Best results**:
- Use system for 2-4 weeks to calibrate
- Provide feedback when recommendations miss
- Combine AI insights with your intuition
- Track subjective feel alongside metrics

**Validation**:
- System uses research-backed training principles
- ACWR methodology validated in studies
- HRV-guided training shows benefits in research
- But individual response varies!

---

## Technical Questions

### Why SQLite? Can I use PostgreSQL?

**SQLite is default because**:
- Zero configuration
- Perfect for single-user
- Fast for this data volume
- No server required
- Easy backups (single file)

**When to use PostgreSQL**:
- Multiple users accessing same data
- Very large data volumes (years of data)
- Running on cloud with managed database
- Need advanced query features
- Want better concurrent access

**Switching to PostgreSQL**:
```bash
# In .env
DATABASE_URL=postgresql://user:password@localhost/training_optimizer

# Install PostgreSQL driver
pip install psycopg2-binary

# Run migrations
alembic upgrade head
```

---

### Can I run this on a Raspberry Pi?

**Yes!** Perfect use case:

**Setup**:
1. Raspberry Pi 3B+ or 4 (2GB+ RAM recommended)
2. Raspberry Pi OS (64-bit)
3. Follow normal installation steps

**Benefits**:
- Runs 24/7 for automated daily sync
- Low power consumption
- Access dashboard from phone/computer
- No need to keep laptop running

**Considerations**:
- Slightly slower than desktop (30-60 sec for AI analysis)
- Ensure stable internet connection
- Set up SSH for remote access
- Consider UPS for power reliability

**Performance**:
- Daily sync: 3-5 minutes
- AI analysis: 30-60 seconds
- Dashboard loads: 2-3 seconds
- Perfectly usable!

---

### Can I access this from my phone?

**Yes, via web browser**:

**Local network access**:
```bash
# Run server on all interfaces
uvicorn app.main:app --host 0.0.0.0 --port 8000

# From phone browser (on same WiFi)
http://YOUR_COMPUTER_IP:8000
```

**Remote access** (advanced):
- Set up reverse proxy (nginx)
- Use ngrok for temporary access
- Deploy to cloud server
- Set up VPN to home network

**Mobile optimization**:
- Dashboard is mobile-responsive
- Works on phone browsers
- No native app (yet)

**Future**:
- Native iOS/Android apps possible
- React Native mobile interface
- Progressive Web App (PWA)

---

### What if garminconnect library breaks?

**This is a real risk!** Garmin could change their API anytime.

**When it happens**:

1. **Check for updates**:
   ```bash
   pip install --upgrade garminconnect
   ```

2. **Check GitHub issues**:
   - Visit: https://github.com/cyberjunky/python-garminconnect/issues
   - Community usually has quick fixes
   - Watch for pull requests with fixes

3. **Temporary workaround**:
   ```bash
   # Manual FIT file import
   # 1. Export from Garmin Connect web
   # 2. Import into system
   python scripts/import_fit_files.py --dir ~/Downloads/garmin_data
   ```

4. **Long-term solutions**:
   - Community maintains library actively
   - Multiple forks available if needed
   - Consider Apple HealthKit alternative
   - Official Garmin API (limited data)

**Staying informed**:
- Star the garminconnect repository on GitHub
- Watch for issues
- Join discussions if breakage occurs

---

## Training & Coaching

### Can this replace a human coach?

**No, it's a supplement, not a replacement.**

**AI strengths**:
- 24/7 data monitoring
- Objective recovery analysis
- Pattern recognition in metrics
- Consistent application of training principles
- No human bias or bad days

**Human coach strengths**:
- Understands complex context
- Emotional support and motivation
- Technique and form coaching
- Race day strategy and tactics
- Interpersonal relationship and accountability
- Handling complex situations (injury, burnout)

**Best use**:
- Solo athletes without coach access
- Supplement to coaching (coach sets plan, AI adjusts daily)
- Learning training principles yourself
- Affordable alternative when starting out

**If you have a coach**:
- Discuss using this system with them
- Share AI insights with coach
- Let coach make final decisions
- Use for daily fine-tuning

---

### Will this help me run faster?

**Likely yes, if**:
- You've been training without structure
- You tend to overtrain
- You don't track recovery metrics
- You're inconsistent with training
- You ignore fatigue signals

**How it helps**:
- Prevents overtraining (consistent training = progress)
- Ensures adequate recovery
- Maintains training load progression
- Avoids injury from excessive spikes
- Keeps you consistent

**What it won't do**:
- Make up for poor nutrition
- Replace actual training (you still have to run!)
- Improve running form
- Provide race day tactics
- Instantly make you faster

**Realistic expectations**:
- Better consistency → better results over time
- Fewer injuries → more training → faster
- Optimized training load → better adaptation
- This is a long game (months, not weeks)

---

### What's a good readiness score?

**Score ranges**:
- **85-100**: Excellent - Ready for hard training
- **70-84**: Good - Moderate to hard workout appropriate
- **55-69**: Fair - Easy to moderate workout recommended
- **40-54**: Poor - Easy workout or active recovery
- **Below 40**: Very poor - Rest day strongly recommended

**Context matters**:
- Score after rest day should be higher
- Score after hard workout should be lower (normal)
- Trend more important than single score
- Your baseline may differ from others

**What if always low?**:
- May need more recovery time generally
- Check for underlying health issues
- Possibly overreaching chronically
- Adjust training volume/intensity
- Consult healthcare provider

**What if always high?**:
- Lucky you! Good recovery
- Or possibly not training hard enough
- Or HRV baseline needs recalibration
- Verify data accuracy

---

## Troubleshooting

### My HRV is all over the place. Is this normal?

**Yes, HRV variability is normal!**

**Factors affecting HRV**:
- **Sleep quality** (biggest factor)
- **Alcohol** (suppresses HRV significantly)
- **Stress** (work, relationships, life events)
- **Training load** (previous day's workout)
- **Illness** (even before symptoms)
- **Hydration** status
- **Time of day** (measure consistently)
- **Measurement technique**

**Tips for consistent HRV**:
- Measure same time each day (on waking)
- Avoid alcohol night before
- Ensure good sleep environment
- Stay hydrated
- Track 7-day average, not daily value

**When to worry**:
- Sustained drop >15% for 3+ days
- Accompanied by elevated RHR
- Feeling unusually fatigued
- Could indicate overtraining or illness

---

### The AI recommended rest but I feel great. Why?

**Possible reasons**:

1. **Preventive rest**:
   - High training load last week
   - ACWR approaching risky levels
   - Preventing injury before it happens
   - "Feel great" often comes before crash

2. **Subtle fatigue signals**:
   - HRV slightly down (you may not feel it yet)
   - RHR slightly elevated
   - Sleep quality lower than usual
   - Data sees patterns you don't feel

3. **Training plan design**:
   - Rest day scheduled in periodization
   - Preparing for hard workout tomorrow
   - Part of planned recovery week

**Should you rest?**:
- If readiness score >70: Probably safe to do easy workout
- If score <60: Rest is probably wise
- Trust your body but also trust the data
- When in doubt, easy day beats rest beats hard workout

**Override if needed**:
- You know your body
- Context matters (race coming up, etc.)
- But track how you feel next day
- Learn if AI was right in retrospect

---

## Getting Help

### Where can I get help if stuck?

1. **Documentation first**:
   - Check [troubleshooting guide](troubleshooting.md)
   - Review [setup guide](setup.md)
   - Read this FAQ

2. **Search existing issues**:
   - GitHub Issues: [github.com/username/training-optimizer/issues](https://github.com/username/training-optimizer/issues)
   - Someone may have had same problem

3. **Check logs**:
   ```bash
   tail -100 logs/training_optimizer.log
   # Often reveals the issue
   ```

4. **Community help**:
   - GitHub Discussions
   - Discord/Slack channel
   - Reddit: r/runningdata

5. **Open new issue**:
   - Provide error message
   - Steps to reproduce
   - Your setup (OS, Python version)
   - Relevant logs (remove secrets!)

6. **Email support**:
   - Last resort for sensitive issues
   - your-support@example.com

---

### Can I contribute to the project?

**Yes! Contributions welcome!**

**Ways to contribute**:

1. **Code**:
   - Fix bugs
   - Add features
   - Improve performance
   - See [development guide](development.md)

2. **Documentation**:
   - Improve guides
   - Add examples
   - Create tutorials
   - Fix typos

3. **Testing**:
   - Report bugs
   - Test new features
   - Provide feedback

4. **Community**:
   - Answer questions
   - Share your experience
   - Write blog posts
   - Create videos

**Getting started**:
```bash
# Fork repository
# Create feature branch
git checkout -b feature/my-contribution

# Make changes
# Run tests
pytest

# Submit pull request
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

**Have a question not answered here? Open an issue on GitHub!**
