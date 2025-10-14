# Microsoft Agent Framework - Reference Guide

## Repository Location
**Path**: `/Users/ajay/Documents/agent-framework`

## Quick Reference

### Installation
```bash
# Full installation (all packages)
pip install agent-framework --pre

# Core only
pip install agent-framework-core --pre

# With visualization support
pip install agent-framework[viz] --pre
```

### Key Directories

#### Python Packages
- **Core**: `/Users/ajay/Documents/agent-framework/python/packages/core/`
- **A2A**: `/Users/ajay/Documents/agent-framework/python/packages/a2a/`
- **Azure AI**: `/Users/ajay/Documents/agent-framework/python/packages/azure-ai/`
- **DevUI**: `/Users/ajay/Documents/agent-framework/python/packages/devui/`
- **Lab** (Experimental): `/Users/ajay/Documents/agent-framework/python/packages/lab/`

#### Samples
- **Getting Started**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/`
- **Agents**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/agents/`
- **Workflows**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/workflows/`
- **Chat Client**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/chat_client/`
- **DevUI**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/devui/`
- **Middleware**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/middleware/`
- **Tools**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/tools/`
- **Observability**: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/observability/`

#### .NET
- **Source**: `/Users/ajay/Documents/agent-framework/dotnet/src/`
- **Samples**: `/Users/ajay/Documents/agent-framework/dotnet/samples/GettingStarted/`

#### Documentation
- **Design Docs**: `/Users/ajay/Documents/agent-framework/docs/design/`
- **Decisions**: `/Users/ajay/Documents/agent-framework/docs/decisions/`
- **Specs**: `/Users/ajay/Documents/agent-framework/docs/specs/`

### Core Implementation Files (Python)

Located in: `/Users/ajay/Documents/agent-framework/python/packages/core/agent_framework/`

- `_agents.py` - Agent implementations (ChatAgent, etc.)
- `_clients.py` - Chat client abstractions and protocols
- `_tools.py` - Tool definitions and function calling (69KB)
- `_types.py` - Core type definitions (126KB)
- `_workflows/` - Workflow orchestration system
- `_middleware.py` - Middleware system (60KB)
- `_mcp.py` - Model Context Protocol integration (40KB)
- `_threads.py` - Thread/conversation management
- `_memory.py` - Memory system
- `observability.py` - OpenTelemetry integration (68KB)

### Quick Start Examples

#### Basic Agent
```python
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient

agent = ChatAgent(
    chat_client=OpenAIChatClient(),
    instructions="You are a helpful assistant.",
    tools=[get_weather, get_menu_specials]
)
result = await agent.run("What's the weather in Seattle?")
```

#### Agent with Tools
```python
from typing import Annotated
from pydantic import Field

def get_weather(
    location: Annotated[str, Field(description="City name")],
) -> str:
    """Get current weather."""
    return f"Weather in {location}: 72°F, sunny"

agent = ChatAgent(
    chat_client=OpenAIChatClient(),
    tools=[get_weather]
)
```

#### Basic Workflow
```python
from agent_framework.workflows import WorkflowBuilder

workflow = (WorkflowBuilder()
    .add_agent("writer", writer_agent)
    .add_agent("reviewer", reviewer_agent)
    .add_edge("writer", "reviewer")
    .build())

result = await workflow.run(input_message)
```

#### DevUI
```python
from agent_framework.devui import serve

# Launch DevUI programmatically
serve(entities=[agent1, agent2], auto_open=True)
```

Or via CLI:
```bash
cd /Users/ajay/Documents/agent-framework/python/samples/getting_started/agents
devui . --port 8080 --tracing framework
```

### Development Setup

#### Python Development
```bash
cd /Users/ajay/Documents/agent-framework/python

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup environment
uv venv --python 3.10
uv sync --dev
uv run poe install
uv run poe pre-commit-install

# Run tests
uv run poe test

# Run checks (format, lint, type check)
uv run poe check

# Build docs
uv run poe docs-build
uv run poe docs-serve
```

### Environment Variables

Create `.env` file in your project root:

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL_ID=gpt-4o-mini
OPENAI_RESPONSES_MODEL_ID=gpt-4o

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://....openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=...
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=...
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=...
AZURE_AI_MODEL_DEPLOYMENT_NAME=...

# Anthropic
ANTHROPIC_API_KEY=...
```

### Key Concepts

1. **Agents**: AI entities with instructions and tools
2. **Chat Clients**: Interface to LLM providers (OpenAI, Azure, etc.)
3. **Workflows**: Graph-based orchestration of agents and functions
4. **Executors**: Processing units in workflows (agents, functions)
5. **Edges**: Connections between executors (with optional conditions)
6. **Tools**: Functions that agents can call
7. **Middleware**: Request/response processing pipeline
8. **Checkpointing**: Save and resume workflow state
9. **HITL**: Human-in-the-loop for approvals/feedback
10. **MCP**: Model Context Protocol for external tools

### Workflow Patterns

Located in: `/Users/ajay/Documents/agent-framework/python/samples/getting_started/workflows/`

- **Sequential**: Chain agents in order
- **Concurrent**: Fan-out to multiple agents, aggregate results
- **Conditional**: Route based on conditions
- **Loops**: Iterative refinement
- **Checkpointing**: Save/resume state
- **HITL**: Human approval/feedback
- **Magentic**: Multi-agent orchestration with planning

### Supported LLM Providers

- OpenAI (Chat & Responses API)
- Azure OpenAI (Chat & Responses API)
- Azure AI Foundry
- Anthropic Claude
- Ollama (local models)
- Microsoft Copilot Studio
- Custom (via protocol implementation)

### Documentation Resources

- **Official Docs**: https://learn.microsoft.com/agent-framework/
- **Repository**: https://github.com/microsoft/agent-framework
- **Main README**: `/Users/ajay/Documents/agent-framework/README.md`
- **Python README**: `/Users/ajay/Documents/agent-framework/python/README.md`
- **Dev Setup**: `/Users/ajay/Documents/agent-framework/python/DEV_SETUP.md`
- **Contributing**: `/Users/ajay/Documents/agent-framework/CONTRIBUTING.md`
- **Transparency FAQ**: `/Users/ajay/Documents/agent-framework/TRANSPARENCY_FAQ.md`

### Package Information

- **Status**: Preview/Beta
- **Version**: 1.0.0b251007 (as of latest check)
- **Python**: 3.10+ required (avoid 3.12+ for compatibility)
- **License**: MIT
- **PyPI**: https://pypi.org/project/agent-framework/
- **NuGet**: https://www.nuget.org/profiles/MicrosoftAgentFramework/

### Important Notes

1. Framework is currently in **preview/beta**
2. Some orchestration patterns still "coming soon" for Python
3. Maintain 80%+ test coverage for contributions
4. Use `uv` for dependency management
5. Pre-commit hooks enforce code quality
6. Google-style docstrings required
7. OpenTelemetry built-in for observability
8. DevUI is a sample app, not for production

### Common Commands

```bash
# Run minimal sample
cd /Users/ajay/Documents/agent-framework/python/samples/getting_started
python minimal_sample.py

# Run specific workflow sample
cd /Users/ajay/Documents/agent-framework/python/samples/getting_started/workflows
python _start-here/step1_executors_and_edges.py

# Launch DevUI for agents
cd /Users/ajay/Documents/agent-framework/python/samples/getting_started/agents
devui . --port 8080

# Run tests for core package
cd /Users/ajay/Documents/agent-framework/python
uv run poe --directory packages/core test

# Format code
uv run poe fmt

# Type check
uv run poe pyright
```

### Architecture Highlights

- **Multi-language**: Python & C#/.NET with consistent APIs
- **Graph-based workflows**: Connect agents and functions
- **Streaming**: Real-time event streaming
- **Middleware**: Flexible request/response processing
- **Observability**: Built-in OpenTelemetry
- **Extensibility**: MCP, A2A, native functions, OpenAPI
- **Developer Tools**: DevUI for testing/debugging

---

**Created**: 2025-10-15
**Repository Path**: `/Users/ajay/Documents/agent-framework`
**Current Working Directory**: `/Users/ajay/Documents/workflow_builder_v4`
