# Contributing to IRA Workflow Builder

Thank you for your interest in contributing to IRA Workflow Builder! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We expect all contributors to:

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community

---

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- OpenAI API key (for testing)
- Familiarity with Microsoft Agent Framework

### Setup Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ira-workflow-builder.git
cd ira-workflow-builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Copy environment file
cp .env.example .env
# Add your API keys to .env
```

---

## Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our [coding standards](#coding-standards)
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests**
   ```bash
   pytest
   ```

4. **Check Code Quality**
   ```bash
   # Format code
   black src/ tests/

   # Lint
   ruff check src/ tests/ --fix

   # Type check
   mypy src/
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

---

## Coding Standards

### Python Style

We follow PEP 8 with these specifics:

- **Line length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff
- **Type hints**: Required for public APIs
- **Docstrings**: Google style

### Example

```python
from typing import List, Optional

def analyze_csv_structure(
    filepath: str,
    encoding: str = "utf-8"
) -> dict[str, Any]:
    """
    Analyze CSV file structure and return metadata.

    This function reads a CSV file and extracts information about its structure,
    including columns, data types, and basic statistics.

    Args:
        filepath: Path to the CSV file to analyze
        encoding: File encoding to use (default: utf-8)

    Returns:
        Dictionary containing:
            - columns: List of column names
            - dtypes: Dictionary of column data types
            - row_count: Number of rows
            - sample_data: First 5 rows as list of dicts

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid CSV

    Example:
        >>> metadata = analyze_csv_structure("data/sales.csv")
        >>> print(metadata["columns"])
        ['date', 'product', 'amount']
    """
    # Implementation here
    pass
```

### Import Order

```python
# Standard library
import os
from typing import List

# Third-party
import pandas as pd
from fastapi import FastAPI

# Local
from ira.agents import PlannerAgent
from ira.utils import get_logger
```

---

## Testing

### Writing Tests

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Use fixtures for common setup

### Test Structure

```python
import pytest
from ira.agents import PlannerAgent

class TestPlannerAgent:
    """Test suite for PlannerAgent"""

    @pytest.fixture
    def planner_agent(self):
        """Create a planner agent for testing"""
        return PlannerAgent(model="gpt-4o")

    def test_analyze_csv_structure(self, planner_agent):
        """Test CSV structure analysis"""
        result = planner_agent.analyze_csv("test_data.csv")
        assert "columns" in result
        assert len(result["columns"]) > 0

    @pytest.mark.asyncio
    async def test_async_operation(self, planner_agent):
        """Test async operation"""
        result = await planner_agent.run("test query")
        assert result is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents.py

# Run with coverage
pytest --cov=ira --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

---

## Documentation

### Docstrings

Use Google-style docstrings for all public APIs:

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Short one-line summary.

    Longer description if needed, explaining the function's purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this is raised
        TypeError: Description of when this is raised

    Example:
        >>> result = function_name("test", 5)
        >>> print(result)
        True
    """
```

### README Updates

If your change affects user-facing functionality:
- Update README.md
- Add examples if applicable
- Update the roadmap if relevant

---

## Pull Request Process

### Before Submitting

- [ ] Tests pass: `pytest`
- [ ] Code formatted: `black src/ tests/`
- [ ] Linting clean: `ruff check src/ tests/`
- [ ] Type checking passes: `mypy src/`
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted and linted
- [ ] No breaking changes (or documented)
```

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address all review comments
4. Maintainer will merge when approved

---

## Areas for Contribution

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- Test coverage improvements
- Bug fixes with clear reproduction steps

### Feature Development

- Frontend UI (React/TypeScript)
- Additional LLM provider support
- Workflow templates
- Advanced analytics

### Infrastructure

- CI/CD improvements
- Deployment configurations
- Monitoring and observability
- Performance optimization

---

## Questions?

- Open a [Discussion](https://github.com/yourusername/ira-workflow-builder/discussions)
- Check existing [Issues](https://github.com/yourusername/ira-workflow-builder/issues)
- Email: team@ira-workflow.com

---

Thank you for contributing! 🎉
