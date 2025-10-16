# Contributing to AI Training Optimizer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Setup](#development-setup)
4. [Pull Request Process](#pull-request-process)
5. [Coding Standards](#coding-standards)
6. [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience
- Nationality, personal appearance, race
- Religion, sexual identity and orientation

### Our Standards

**Positive behavior includes**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behavior includes**:
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### Enforcement

Violations may be reported to [your.email@example.com]. All complaints will be reviewed and investigated, resulting in a response deemed necessary and appropriate.

---

## How to Contribute

### Types of Contributions

We welcome:

1. **Bug Reports**
   - Found a bug? Let us know!
   - See [Issue Guidelines](#issue-guidelines)

2. **Feature Requests**
   - Have an idea? We'd love to hear it!
   - Discuss in GitHub Discussions first

3. **Code Contributions**
   - Bug fixes
   - New features
   - Performance improvements
   - Test coverage improvements

4. **Documentation**
   - Improve existing docs
   - Add examples and tutorials
   - Fix typos and clarify confusing sections

5. **Community Support**
   - Answer questions in Discussions
   - Help others troubleshoot issues
   - Share your success stories

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Garmin Connect account
- Claude API key

### Fork and Clone

```bash
# Fork repository on GitHub first
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/training-optimizer.git
cd training-optimizer

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/training-optimizer.git
```

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env.dev

# Initialize test database
python scripts/initial_setup.py --env dev
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_garmin_service.py -v
```

---

## Pull Request Process

### Before Submitting

1. **Check existing issues/PRs**
   - Ensure your contribution isn't already in progress
   - Reference related issues in your PR

2. **Create an issue first** (for major changes)
   - Discuss the change before implementing
   - Get feedback on approach
   - Avoid wasted effort on rejected PRs

3. **Keep PRs focused**
   - One feature/fix per PR
   - Smaller PRs are easier to review
   - Break large changes into multiple PRs

### Creating a Pull Request

1. **Create feature branch**
   ```bash
   # Update your fork
   git checkout main
   git pull upstream main

   # Create branch
   git checkout -b feature/my-awesome-feature
   # Or: fix/bug-description
   # Or: docs/improve-setup-guide
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation
   - Follow coding standards

3. **Test thoroughly**
   ```bash
   # Run tests
   pytest

   # Check code style
   black app/ tests/
   flake8 app/ tests/

   # Type checking
   mypy app/
   ```

4. **Commit changes**
   ```bash
   # Stage changes
   git add .

   # Commit with clear message
   git commit -m "feat: add overtraining detection algorithm"

   # Follow conventional commits format:
   # feat: New feature
   # fix: Bug fix
   # docs: Documentation
   # test: Tests
   # refactor: Code refactoring
   # style: Formatting
   # chore: Maintenance
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/my-awesome-feature
   ```

6. **Open Pull Request on GitHub**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Fill out PR template
   - Link related issues

### PR Template

When opening PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Related Issues
Fixes #123
Related to #456

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
Describe how you tested your changes:
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings generated
```

### Review Process

1. **Automated checks**
   - Tests must pass
   - Code style checks must pass
   - Coverage should not decrease

2. **Code review**
   - Maintainer will review your code
   - May request changes
   - Discussion via PR comments

3. **Making changes**
   ```bash
   # Make requested changes
   # Commit and push to same branch
   git add .
   git commit -m "fix: address review comments"
   git push origin feature/my-awesome-feature
   # PR updates automatically
   ```

4. **Approval and merge**
   - Once approved, maintainer merges
   - PR will be squashed and merged
   - Your contribution is now part of the project!

---

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:

```python
# Line length: 100 characters
# Use Black for formatting
# Use flake8 for linting

# Good
def calculate_hrv_baseline(
    hrv_data: List[float],
    days: int = 7
) -> float:
    """
    Calculate HRV baseline from recent data.

    Args:
        hrv_data: List of HRV values
        days: Number of days to average

    Returns:
        Baseline HRV value
    """
    if len(hrv_data) < days:
        raise ValueError(f"Insufficient data: need {days} days")

    return sum(hrv_data[-days:]) / days
```

### Naming Conventions

```python
# Classes: PascalCase
class TrainingPlanner:
    pass

# Functions/methods: snake_case
def generate_training_plan():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_HEART_RATE = 188

# Private: _leading_underscore
def _internal_helper():
    pass
```

### Type Hints

Always use type hints:

```python
from typing import List, Optional, Dict
from datetime import date

def fetch_activities(
    start_date: date,
    end_date: date,
    activity_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    pass
```

### Documentation

Use Google-style docstrings:

```python
def analyze_readiness(date: str) -> DailyReadiness:
    """
    Analyze athlete's readiness for specified date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        DailyReadiness object with score and recommendation

    Raises:
        ValueError: If date format invalid
        InsufficientDataError: If not enough data

    Example:
        >>> result = analyze_readiness("2025-10-15")
        >>> print(result.readiness_score)
        82
    """
    pass
```

### Testing

Write tests for all new code:

```python
# tests/test_my_feature.py
import pytest

def test_calculate_hrv_baseline():
    """Test HRV baseline calculation."""
    data = [60, 58, 62, 61, 59, 60, 63]
    result = calculate_hrv_baseline(data, days=7)

    assert result == 60.43
    assert isinstance(result, float)

def test_calculate_hrv_baseline_insufficient_data():
    """Test error handling for insufficient data."""
    data = [60, 58]

    with pytest.raises(ValueError, match="Insufficient data"):
        calculate_hrv_baseline(data, days=7)
```

### Commit Messages

Follow conventional commits:

```bash
# Format: <type>(<scope>): <subject>

feat(ai): add overtraining detection
fix(garmin): handle missing HRV data
docs(setup): update installation steps
test(analysis): add readiness scenario tests
refactor(database): optimize query performance
style(format): apply black formatting
chore(deps): update dependencies
```

---

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 13.0]
- Python version: [e.g., 3.10.5]
- App version: [e.g., 1.0.0]

**Logs**
```
Paste relevant logs here
```

**Screenshots**
If applicable, add screenshots
```

### Feature Requests

Use the feature request template:

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How would you solve it?

**Alternatives Considered**
What other approaches did you consider?

**Additional Context**
Any other context or screenshots
```

### Good Issue Practices

- **Search first**: Check if issue already exists
- **Clear title**: Descriptive and specific
- **Complete information**: Fill out template fully
- **One issue per topic**: Don't combine multiple issues
- **Follow up**: Respond to questions from maintainers

---

## First-Time Contributors

### Good First Issues

Look for issues labeled:
- `good first issue`: Simple tasks for beginners
- `help wanted`: Community input desired
- `documentation`: Doc improvements

### Getting Help

Don't hesitate to ask for help:
- Comment on issue: "I'd like to work on this, but need guidance on X"
- GitHub Discussions: Ask questions
- Draft PRs: Open PR early with "WIP:" prefix to get feedback

### Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [pytest Documentation](https://docs.pytest.org)
- [Git Basics](https://git-scm.com/book/en/v2)

---

## Recognition

### Contributors

All contributors are recognized:
- Added to `CONTRIBUTORS.md`
- Mentioned in release notes
- Public thank you in GitHub Discussions

### Hall of Fame

Top contributors get special recognition:
- Featured in README
- Special badge on profile
- Invitation to maintainer team (for sustained contributions)

---

## Questions?

- **General questions**: GitHub Discussions
- **Bug reports**: GitHub Issues
- **Security issues**: Email [security@example.com]
- **Code questions**: Comment on relevant issue/PR

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing! Together we're building better training tools.**
