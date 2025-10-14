# IRA Workflow Builder 🤖

**Interactive Requirements Analyzer** - An AI-powered workflow builder for generating analysis code on CSV files using Microsoft Agent Framework.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 Overview

IRA Workflow Builder enables users to interact with AI agents to automatically generate Python analysis code for CSV files. The system uses a multi-agent architecture with human-in-the-loop approvals to ensure the generated code meets business requirements.

### Key Features

- 🤝 **Interactive Requirements Gathering**: AI agent asks 5-10 clarifying questions to understand your needs
- 📝 **Business Logic Documentation**: Generates comprehensive business logic reports for approval
- 💻 **Automatic Code Generation**: Creates production-ready Python pandas code
- ✅ **Iterative Refinement**: Continue refining until you're satisfied with results
- 🔄 **State Management**: Checkpointing and conversation history for long-running workflows
- 🎨 **Modern API**: FastAPI with WebSocket support for real-time updates

---

## 🏗️ Architecture

The system uses **Microsoft Agent Framework** with two main agents:

1. **Planner Agent (IRA-Planner)**: Gathers requirements and creates business logic documents
2. **Coder Agent (IRA-Coder)**: Generates and executes Python code based on approved logic

```
User Upload CSV → Planner Q&A → Business Logic → Approval →
Code Generation → Execution → Results → Approval → ✓ Complete
         ↑                       ↓              ↓
         └──── Refinement Loop ──┴──────────────┘
```

See [IRA_WORKFLOW_ARCHITECTURE.md](IRA_WORKFLOW_ARCHITECTURE.md) for detailed architecture.

---

## 📋 Prerequisites

- **Python 3.10+** (avoid 3.12+ for compatibility)
- **OpenAI API Key** or **Azure OpenAI** access
- **pandas**, **numpy** for data processing
- **Microsoft Agent Framework**

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
cd workflow_builder_v4

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# At minimum, set:
# OPENAI_API_KEY=sk-your-key-here
```

### 3. Run the Application

```bash
# Start the API server
uvicorn ira.api.app:app --reload

# Or use the CLI
python -m ira.api.app
```

The API will be available at `http://localhost:8000`

### 4. Test with Sample Data

```bash
# Create sample CSV files
python scripts/seed_data.py

# Run tests
pytest tests/
```

---

## 📖 Usage

### Using the API

```python
import asyncio
from ira import IRAWorkflow

async def main():
    # Create workflow
    workflow = IRAWorkflow(
        workflow_name="Sales Analysis Q4",
        workflow_description="Analyze Q4 sales to identify top performers",
        csv_filepaths=["data/uploads/sales_q4.csv"]
    )

    # Execute workflow with streaming
    async for event in workflow.run_stream():
        print(f"Event: {event.type}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the REST API

```bash
# Upload CSV file
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -F "file=@sales_data.csv"

# Create workflow
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Analysis",
    "description": "Analyze quarterly sales",
    "csv_files": ["sales_data.csv"]
  }'

# Get workflow status
curl "http://localhost:8000/api/v1/workflows/{workflow_id}"
```

### Using WebSocket for Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflow/{workflow_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Workflow event:', data);
};
```

---

## 📁 Project Structure

```
workflow_builder_v4/
├── src/ira/                    # Main package
│   ├── agents/                 # Agent implementations
│   ├── workflows/              # Workflow orchestration
│   ├── tools/                  # Agent tools
│   ├── models/                 # Data models
│   ├── storage/                # Storage backends
│   ├── api/                    # FastAPI application
│   └── utils/                  # Utilities
├── tests/                      # Test suite
├── config/                     # Configuration files
├── data/                       # Data directory (gitignored)
├── storage/                    # Persistent storage (gitignored)
├── docs/                       # Documentation
└── scripts/                    # Utility scripts
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure.

---

## 🧪 Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests with coverage
pytest --cov=ira --cov-report=html

# Format code
black src/ tests/
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all checks
pre-commit run --all-files
```

---

## 📚 Documentation

- **[Architecture Design](IRA_WORKFLOW_ARCHITECTURE.md)** - Detailed system architecture
- **[Project Structure](PROJECT_STRUCTURE.md)** - Directory layout and organization
- **[Agent Framework Reference](AGENT_FRAMEWORK_REFERENCE.md)** - Microsoft Agent Framework guide
- **[API Documentation](docs/API.md)** - REST API reference (coming soon)
- **[User Guide](docs/USER_GUIDE.md)** - End-user documentation (coming soon)
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment (coming soon)

---

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key
OPENAI_CHAT_MODEL_ID=gpt-4o

# Application
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Workflow Settings
MAX_QUESTIONS=10
MAX_CODE_EXECUTION_TIME=120
MAX_FILE_SIZE_MB=100
```

### Configuration Files

- `config/development.yaml` - Development settings
- `config/production.yaml` - Production settings
- `config/logging.yaml` - Logging configuration

---

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t ira-workflow-builder .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  ira-workflow-builder
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes

```bash
# Apply configurations
kubectl apply -f deployment/kubernetes/

# Check status
kubectl get pods -n ira
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- Powered by OpenAI GPT-4o
- Uses FastAPI for the API layer
- Data processing with pandas

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ira-workflow-builder/issues)
- **Documentation**: [Read the Docs](https://ira-workflow-builder.readthedocs.io)
- **Email**: team@ira-workflow.com

---

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Core agent implementation
- [x] Basic workflow orchestration
- [x] HITL integration
- [ ] REST API endpoints

### Phase 2
- [ ] Frontend UI (React)
- [ ] User authentication
- [ ] Workflow templates
- [ ] Advanced error handling

### Phase 3
- [ ] Multi-user support
- [ ] Workflow versioning
- [ ] Analytics dashboard
- [ ] Workflow marketplace

### Phase 4
- [ ] A/B testing for agents
- [ ] Reinforcement learning from feedback
- [ ] Enterprise features
- [ ] Cloud deployment

---

**Made with ❤️ by the IRA Team**
