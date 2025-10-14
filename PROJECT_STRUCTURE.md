# IRA Workflow Builder - Project Structure

## Directory Layout

```
workflow_builder_v4/
├── README.md                          # Project overview and setup
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
├── setup.py                           # Package installation script
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md               # System architecture (already exists)
│   ├── API.md                        # API documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   └── USER_GUIDE.md                 # User guide
│
├── src/                               # Source code
│   └── ira/                          # Main package
│       ├── __init__.py
│       │
│       ├── agents/                   # Agent implementations
│       │   ├── __init__.py
│       │   ├── planner.py           # Planner agent
│       │   ├── coder.py             # Coder agent
│       │   └── base.py              # Base agent utilities
│       │
│       ├── workflows/                # Workflow orchestration
│       │   ├── __init__.py
│       │   ├── ira_workflow.py      # Main workflow
│       │   ├── builders.py          # Workflow builders
│       │   └── state.py             # State management
│       │
│       ├── tools/                    # Agent tools
│       │   ├── __init__.py
│       │   ├── csv_tools.py         # CSV analysis tools
│       │   ├── code_tools.py        # Code execution tools
│       │   └── validation_tools.py   # Validation utilities
│       │
│       ├── models/                   # Data models
│       │   ├── __init__.py
│       │   ├── workflow.py          # Workflow models
│       │   ├── messages.py          # HITL message models
│       │   └── schemas.py           # API schemas
│       │
│       ├── storage/                  # Storage backends
│       │   ├── __init__.py
│       │   ├── csv_storage.py       # CSV file storage
│       │   ├── checkpoint_storage.py # Checkpoint management
│       │   └── conversation_storage.py # Conversation history
│       │
│       ├── api/                      # API layer
│       │   ├── __init__.py
│       │   ├── app.py               # FastAPI application
│       │   ├── routes/              # API routes
│       │   │   ├── __init__.py
│       │   │   ├── workflows.py     # Workflow endpoints
│       │   │   ├── files.py         # File upload endpoints
│       │   │   └── websocket.py     # WebSocket handlers
│       │   └── middleware/          # API middleware
│       │       ├── __init__.py
│       │       ├── auth.py          # Authentication
│       │       └── logging.py       # Request logging
│       │
│       ├── executors/                # Custom executors
│       │   ├── __init__.py
│       │   ├── hitl_executors.py    # HITL executors
│       │   └── function_executors.py # Function executors
│       │
│       ├── utils/                    # Utilities
│       │   ├── __init__.py
│       │   ├── logger.py            # Logging setup
│       │   ├── config.py            # Configuration management
│       │   └── helpers.py           # Helper functions
│       │
│       └── exceptions/               # Custom exceptions
│           ├── __init__.py
│           └── errors.py            # Error definitions
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration
│   │
│   ├── unit/                        # Unit tests
│   │   ├── __init__.py
│   │   ├── test_agents.py
│   │   ├── test_tools.py
│   │   ├── test_models.py
│   │   └── test_storage.py
│   │
│   ├── integration/                 # Integration tests
│   │   ├── __init__.py
│   │   ├── test_workflow.py
│   │   ├── test_api.py
│   │   └── test_end_to_end.py
│   │
│   └── fixtures/                    # Test fixtures
│       ├── __init__.py
│       ├── sample_csvs/            # Sample CSV files
│       │   ├── sales_data.csv
│       │   └── products.csv
│       └── mock_data.py            # Mock data generators
│
├── scripts/                          # Utility scripts
│   ├── setup_dev.sh                 # Development setup script
│   ├── run_tests.sh                 # Test runner script
│   ├── deploy.sh                    # Deployment script
│   └── seed_data.py                 # Seed test data
│
├── config/                           # Configuration files
│   ├── development.yaml             # Development config
│   ├── production.yaml              # Production config
│   └── logging.yaml                 # Logging config
│
├── data/                             # Data directory (gitignored)
│   ├── uploads/                     # User uploaded CSV files
│   │   └── .gitkeep
│   ├── outputs/                     # Generated result files
│   │   └── .gitkeep
│   └── temp/                        # Temporary files
│       └── .gitkeep
│
├── storage/                          # Persistent storage (gitignored)
│   ├── checkpoints/                 # Workflow checkpoints
│   │   └── .gitkeep
│   ├── conversations/               # Conversation history
│   │   └── .gitkeep
│   └── metadata/                    # Workflow metadata
│       └── .gitkeep
│
├── logs/                             # Application logs (gitignored)
│   └── .gitkeep
│
├── frontend/                         # Frontend application (optional)
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   └── public/
│
└── deployment/                       # Deployment configurations
    ├── docker/
    │   ├── Dockerfile
    │   └── docker-compose.yml
    ├── kubernetes/
    │   ├── deployment.yaml
    │   └── service.yaml
    └── terraform/
        └── main.tf
```

## Key Directories Explained

### `/src/ira/` - Main Package
Core application code organized by functionality.

### `/src/ira/agents/`
Agent implementations (Planner, Coder) with their specific configurations and tools.

### `/src/ira/workflows/`
Workflow orchestration logic, state management, and workflow builders.

### `/src/ira/tools/`
Tool functions that agents can use (CSV analysis, code execution, validation).

### `/src/ira/models/`
Pydantic models for data structures, API schemas, and workflow state.

### `/src/ira/storage/`
Storage layer abstractions for CSV files, checkpoints, and conversation history.

### `/src/ira/api/`
FastAPI application with REST endpoints and WebSocket handlers.

### `/tests/`
Comprehensive test suite with unit, integration, and end-to-end tests.

### `/data/`
Runtime data directory for uploads, outputs, and temporary files (gitignored).

### `/storage/`
Persistent storage for checkpoints and conversation history (gitignored).

### `/scripts/`
Utility scripts for development, testing, and deployment.

### `/config/`
Environment-specific configuration files.

### `/docs/`
Project documentation including architecture, API docs, and user guides.

### `/deployment/`
Deployment configurations for Docker, Kubernetes, and cloud platforms.

## File Naming Conventions

- **Python modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions**: `lowercase_with_underscores()`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Test files**: `test_*.py`
- **Config files**: `lowercase.yaml` or `lowercase.json`

## Import Structure

```python
# Import from package root
from ira.agents import PlannerAgent, CoderAgent
from ira.workflows import IRAWorkflow
from ira.tools import analyze_csv_structure, execute_python_code
from ira.models import WorkflowState, BusinessLogic

# Import submodules
from ira.storage.csv_storage import CSVStorage
from ira.api.app import create_app
```

## Package Installation

```bash
# Development installation
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install with all extras
pip install -e ".[all]"
```
