# Project Reorganization Summary

## Overview
The project has been reorganized into three main directories: `ai/`, `backend/`, and `frontend/` with clear separation of concerns:
- **ai/** - All AI/LLM-related code, agents, orchestration, and tests
- **backend/** - Only API layer (FastAPI routes, models, services)
- **frontend/** - Next.js application (unchanged)

## New Directory Structure

```
workflow_builder_v4/
├── ai/                          # AI/LLM code and tests
│   ├── __init__.py
│   ├── ira_builder/            # Core AI/LLM package
│   │   ├── __init__.py
│   │   ├── agents/             # AI agents (Planner, Coder)
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── planner.py
│   │   │   └── coder.py
│   │   ├── orchestrator.py     # Main workflow orchestrator
│   │   ├── tools/              # Agent tools (CSV, validation, code execution)
│   │   ├── executor/           # Code execution engine
│   │   ├── executors/          # Legacy executors
│   │   ├── workflows/          # Workflow definitions
│   │   ├── models/             # Data models
│   │   ├── exceptions/         # Custom exceptions
│   │   ├── storage/            # State persistence
│   │   └── utils/              # Utilities (logger, config)
│   ├── examples/               # Example scripts
│   │   └── planner_demo.py
│   ├── tests/                  # Unit tests
│   │   ├── unit/
│   │   │   ├── test_planner.py
│   │   │   └── test_csv_tools.py
│   │   └── fixtures/
│   ├── test_orchestrator.py    # Integration tests
│   ├── test_orchestrator_with_output_review.py
│   ├── test_coder_agent.py
│   ├── test_code_executor.py
│   └── ...
│
├── backend/                     # Backend API layer only
│   ├── __init__.py
│   └── api/                    # FastAPI application
│       ├── __init__.py
│       ├── app.py              # Main FastAPI app
│       ├── routes/             # API route handlers
│       │   ├── __init__.py
│       │   ├── workflows.py
│       │   └── websockets.py
│       ├── models/             # API request/response models
│       │   ├── __init__.py
│       │   ├── requests.py
│       │   └── responses.py
│       ├── services/           # Business logic layer
│       │   ├── __init__.py
│       │   └── workflow_manager.py
│       └── middleware/         # API middleware
│           └── __init__.py
│
└── frontend/                    # Next.js frontend application
    ├── src/
    │   ├── app/                # Next.js app router pages
    │   ├── components/         # React components
    │   ├── hooks/              # Custom React hooks
    │   └── lib/                # Utility libraries
    ├── public/                 # Static assets
    ├── package.json
    ├── tsconfig.json
    └── next.config.ts
```

## Key Changes

### 1. Clear Separation of Concerns

#### AI Directory (`ai/`)
Contains all AI/LLM-related components:
- **Agents**: Planner Agent, Coder Agent with OpenAI integration
- **Orchestrator**: Main workflow orchestration logic
- **Tools**: Agent tools for CSV processing, validation, code execution
- **Executor**: Code execution engine
- **Tests**: All integration and unit tests

#### Backend Directory (`backend/`)
Contains ONLY API layer:
- **FastAPI Application**: API endpoints and routing
- **Request/Response Models**: API data models
- **Services**: Thin service layer that calls AI components
- **Middleware**: API middleware (CORS, logging, etc.)

#### Frontend Directory (`frontend/`)
- Remains unchanged
- Next.js application with React components

### 2. Import Path Updates

#### Backend API Files
All imports in backend API files now reference AI components from `ai.ira_builder`:
```python
# backend/api/app.py
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.config import get_config

# backend/api/services/workflow_manager.py
from ai.ira_builder.orchestrator import create_orchestrator
```

#### AI Components
All imports within AI directory use `ai.ira_builder`:
```python
# ai/ira_builder/orchestrator.py
from ai.ira_builder.agents import PlannerAgent, CoderAgent
from ai.ira_builder.utils.logger import get_logger
```

#### Test Files
Test files import from `ai.ira_builder`:
```python
# ai/test_orchestrator.py
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai.ira_builder.orchestrator import create_orchestrator
from ai.ira_builder.agents.planner import PlannerResponseType
```

### 3. Start Scripts Updated

Both start scripts have been updated to use the new API path:

**start_backend.sh**
```bash
python -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

**start_backend_visible.sh**
```bash
python -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup.py Configuration

Updated to recognize packages from the root directory:
```python
packages=find_packages(where="."),
package_dir={"": "."},
```

## Running the Application

### Backend API
```bash
# From project root
./start_backend.sh
# or for visible logs
./start_backend_visible.sh
```

The API will start on http://localhost:8000

### Frontend
```bash
cd frontend
npm install  # if not already done
npm run dev
```

The frontend will start on http://localhost:3000

### Tests
```bash
# Run from project root
cd ai
python test_orchestrator.py

# Or run unit tests
pytest tests/unit/
```

## Benefits of New Structure

1. **Clear Separation**:
   - AI/LLM logic completely separated from API layer
   - Backend only handles HTTP requests/responses
   - Frontend remains independent

2. **Better Organization**:
   - Easy to understand what code belongs where
   - AI components can be tested independently
   - API layer is thin and focused

3. **Scalability**:
   - AI components can be deployed separately (e.g., as microservice)
   - API can be scaled independently
   - Each directory can have its own deployment pipeline

4. **Modularity**:
   - AI package: `from ai.ira_builder import ...`
   - Backend API: `from backend.api import ...`
   - Clear module boundaries

5. **Development**:
   - Teams can work independently on AI vs API
   - Easier testing and debugging
   - Better code ownership

## Import Path Reference

### For Backend API Files
```python
# Import AI/LLM components
from ai.ira_builder.orchestrator import create_orchestrator
from ai.ira_builder.agents import PlannerAgent, CoderAgent
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.config import get_config

# Import API models (local)
from backend.api.models.requests import WorkflowRequest
from backend.api.models.responses import WorkflowResponse
```

### For AI Components
```python
# Import from within AI package
from ai.ira_builder.agents.base import BaseAgent
from ai.ira_builder.tools.csv_tools import CSVTools
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.models import WorkflowState
```

### For Test Files
```python
# Add parent to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import AI components
from ai.ira_builder.orchestrator import create_orchestrator
from ai.ira_builder.agents.planner import PlannerAgent
```

## Migration Notes

- The old `src/ira_builder/` directory structure has been split:
  - AI/LLM components → `ai/ira_builder/`
  - API components → `backend/api/`
- All tests have been moved to `ai/` directory
- Import paths have been systematically updated across all files
- No functionality has been removed, only reorganized
- Frontend was already in its own directory and remains unchanged
- Old `backend/ira_builder/` directory can be deleted after verification

## Old vs New Paths

| Component | Old Path | New Path |
|-----------|----------|----------|
| Agents | `src/ira_builder/agents/` | `ai/ira_builder/agents/` |
| Orchestrator | `src/ira_builder/orchestrator.py` | `ai/ira_builder/orchestrator.py` |
| Tools | `src/ira_builder/tools/` | `ai/ira_builder/tools/` |
| API | `src/ira_builder/api/` | `backend/api/` |
| Tests | `tests/` | `ai/tests/` |
| Examples | `examples/` | `ai/examples/` |
| Test scripts | `test_*.py` (root) | `ai/test_*.py` |
| Frontend | `frontend/` | `frontend/` (unchanged) |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                     (Next.js + React)                        │
│                   localhost:3000                             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│                    (FastAPI Layer)                           │
│                   localhost:8000                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes → Services → Calls AI Components             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ Python imports
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI Components                           │
│                  (ai.ira_builder)                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Orchestrator → Agents → Tools → LLM APIs            │  │
│  │  - Planner Agent (OpenAI)                            │  │
│  │  - Coder Agent (OpenAI)                              │  │
│  │  - CSV Tools, Validation, Execution                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ Test the application to ensure all imports work correctly
2. ✅ Verify API starts successfully
3. ✅ Run integration tests
4. Consider cleanup:
   - Delete `backend/ira_builder/` (old structure)
   - Delete `src/` directory (if still exists)
5. Update CI/CD pipelines if necessary
6. Consider future enhancements:
   - Separate requirements.txt for ai/ and backend/
   - Docker containers for each component
   - Microservice deployment options
