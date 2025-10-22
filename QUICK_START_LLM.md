# Quick Start: LLM Configuration

## Current Configuration

Your system is currently configured in **Hybrid Mode**:
- **Planning Phase**: OpenAI (gpt-5)
- **Coding Phase**: Groq (openai/gpt-oss-120b)

## How to Change Providers

### Option 1: Switch Planning Phase to Groq

Edit `.env` file and change:
```bash
PLANNER_PROVIDER=groq   # Change from "openai" to "groq"
```

Then restart: `./start_backend.sh`

### Option 2: Switch Coding Phase to OpenAI

Edit `.env` file and change:
```bash
CODER_PROVIDER=openai   # Change from "groq" to "openai"
```

Then restart: `./start_backend.sh`

### Option 3: Use All OpenAI

Edit `.env` file:
```bash
PLANNER_PROVIDER=openai
CODER_PROVIDER=openai
```

Then restart: `./start_backend.sh`

### Option 4: Use All Groq

Edit `.env` file:
```bash
PLANNER_PROVIDER=groq
CODER_PROVIDER=groq
```

Then restart: `./start_backend.sh`

## Configuration Summary

| Phase | What it does | Current Provider | Alternative |
|-------|--------------|------------------|-------------|
| **Planning** | Requirements gathering, business logic plan | OpenAI (gpt-5) | Groq |
| **Coding** | Code generation, analysis reports | Groq (openai/gpt-oss-120b) | OpenAI |

## When to Use Which Provider

### Use OpenAI when:
- Complex reasoning required
- Need precise business logic understanding
- Working with ambiguous requirements
- Quality over speed

### Use Groq when:
- Fast iteration needed
- Code generation and execution
- Cost optimization
- Open-source model preference

## Verification

After changing configuration, check the startup logs:

```
LLM Configuration:
  📋 Planning Phase: openai
  💻 Coding Phase:   groq

🔄 Hybrid Mode Enabled:
   Using openai for planning (better reasoning)
   Using groq for coding (faster execution)
```

## Files to Edit

- **`.env`** - Main configuration file (edit PLANNER_PROVIDER and CODER_PROVIDER)
- **DO NOT EDIT**: `start_backend.sh` (automatically reads from .env)

## Quick Commands

```bash
# View current configuration
cat .env | grep -E "(PLANNER|CODER)_PROVIDER"

# Edit configuration
nano .env  # or use your preferred editor

# Restart backend
./start_backend.sh
```

---

For detailed documentation, see `LLM_CONFIGURATION.md`
