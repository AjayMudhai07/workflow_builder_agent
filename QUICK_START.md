# IRA Workflow Builder - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1️⃣ Setup Environment (2 minutes)

```bash
# Run automated setup
bash scripts/setup_dev.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 2️⃣ Configure API Keys (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI key
# Minimum required:
OPENAI_API_KEY=sk-your-key-here
OPENAI_CHAT_MODEL_ID=gpt-4o
```

### 3️⃣ Verify Setup (1 minute)

```bash
# Check installation
python -c "import ira; print('✓ IRA package installed')"

# Run tests
pytest tests/ -v
```

### 4️⃣ Start Development (1 minute)

```bash
# Option 1: Start API server
uvicorn ira.api.app:app --reload

# Option 2: Run workflow directly
python -m ira.workflows.ira_workflow

# Option 3: Interactive Python
python
>>> from ira import IRAWorkflow
>>> # Your code here
```

---

## 📋 Essential Commands

### Development
```bash
# Activate environment
source venv/bin/activate

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type check
mypy src/

# Run tests
pytest
pytest --cov=ira --cov-report=html
```

### Testing
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_agents.py

# With coverage
pytest --cov=ira --cov-report=term-missing
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn ira.api.app:app --reload --port 8000

# Production server
uvicorn ira.api.app:app --host 0.0.0.0 --port 8000 --workers 4

# With custom config
API_CONFIG=config/production.yaml uvicorn ira.api.app:app
```

---

## 📁 Project Organization

```
workflow_builder_v4/
├── src/ira/              # Main source code
│   ├── agents/           # Planner & Coder agents
│   ├── workflows/        # Workflow orchestration
│   ├── tools/            # CSV & code tools
│   ├── models/           # Data models
│   └── api/              # FastAPI app
├── tests/                # Test suite
├── config/               # Configuration files
└── docs/                 # Documentation
```

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `IRA_WORKFLOW_ARCHITECTURE.md` | Complete system design |
| `AGENT_FRAMEWORK_REFERENCE.md` | Agent Framework guide |
| `docs/API.md` | API documentation |
| `.env` | Your API keys (create from `.env.example`) |

---

## 🎯 Next Implementation Steps

### Phase 1: Core Components
1. Implement `src/ira/agents/planner.py`
2. Implement `src/ira/agents/coder.py`
3. Implement `src/ira/tools/csv_tools.py`
4. Implement `src/ira/tools/code_tools.py`
5. Implement `src/ira/workflows/ira_workflow.py`

### Phase 2: API Layer
1. Implement `src/ira/api/app.py`
2. Implement `src/ira/api/routes/workflows.py`
3. Implement `src/ira/api/routes/files.py`
4. Add WebSocket support

### Phase 3: Testing
1. Write unit tests for all components
2. Write integration tests for workflows
3. Write E2E API tests

---

## 💡 Usage Example

```python
import asyncio
from ira import IRAWorkflow

async def main():
    # Create workflow
    workflow = IRAWorkflow(
        workflow_name="Sales Analysis Q4",
        workflow_description="Analyze Q4 sales data",
        csv_filepaths=["data/uploads/sales_q4.csv"]
    )

    # Execute with streaming
    async for event in workflow.run_stream():
        print(f"Event: {event.type}")

        if event.type == "question_asked":
            answer = input(f"Q: {event.question}\nA: ")
            await workflow.answer_question(event.question_id, answer)

        elif event.type == "business_logic_ready":
            print(event.business_logic)
            decision = input("Approve? (y/n): ")
            await workflow.approve_logic(decision == 'y')

        elif event.type == "results_ready":
            print(f"Results: {event.result_path}")
            decision = input("Approve? (y/n): ")
            await workflow.approve_results(decision == 'y')

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🐛 Troubleshooting

### Import Errors
```bash
# Reinstall in editable mode
pip install -e .
```

### API Key Issues
```bash
# Verify .env file
cat .env | grep OPENAI_API_KEY

# Test API key
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### Port Already in Use
```bash
# Use different port
uvicorn ira.api.app:app --port 8001
```

---

## 📚 Learning Resources

1. **Microsoft Agent Framework**
   - Docs: https://learn.microsoft.com/agent-framework/
   - Repo: https://github.com/microsoft/agent-framework
   - Local: `AGENT_FRAMEWORK_REFERENCE.md`

2. **Project Documentation**
   - Architecture: `IRA_WORKFLOW_ARCHITECTURE.md`
   - API Reference: `docs/API.md`
   - Contributing: `CONTRIBUTING.md`

3. **External Resources**
   - FastAPI: https://fastapi.tiangolo.com/
   - Pydantic: https://docs.pydantic.dev/
   - pytest: https://docs.pytest.org/

---

## 🤝 Getting Help

1. Check documentation in `docs/`
2. Review architecture in `IRA_WORKFLOW_ARCHITECTURE.md`
3. See examples in code comments
4. Open an issue on GitHub

---

**Ready to build? Start with `bash scripts/setup_dev.sh`! 🚀**
