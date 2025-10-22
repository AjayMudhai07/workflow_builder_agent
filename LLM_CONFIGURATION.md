# LLM Provider Configuration Guide

This guide explains how to configure different LLM providers for the IRA Workflow Builder.

## Overview

The IRA Workflow Builder supports multiple LLM providers and allows you to use different providers for different workflow phases (Hybrid Mode).

## Supported Providers

1. **OpenAI** - Best for complex reasoning and planning
   - Models: gpt-4o, gpt-5, gpt-4-turbo
   - Recommended for: Planning phase

2. **Groq** - Fastest inference with open-source models
   - Models: llama-3.3-70b-versatile, openai/gpt-oss-120b
   - Recommended for: Coding and analysis report generation

## Configuration Options

### Option 1: Single Provider Mode (Simple)

Use the same provider for all phases:

```bash
# In .env file
LLM_PROVIDER=openai  # or "groq"
```

### Option 2: Hybrid Mode (Recommended)

Use different providers for different phases:

```bash
# In .env file
PLANNER_PROVIDER=openai   # For planning phase (requirements & business logic)
CODER_PROVIDER=groq       # For coding phase (code generation & analysis)
```

**Benefits of Hybrid Mode:**
- Better reasoning in planning phase with OpenAI
- Faster code generation with Groq
- Cost optimization
- Best of both worlds

## Workflow Phases

### Planning Phase (uses PLANNER_PROVIDER)
- Initial user conversation
- Requirements gathering
- CSV analysis
- Business Logic Plan generation

### Coding Phase (uses CODER_PROVIDER)
- Python code generation
- Code execution and debugging
- Output refinement
- Analysis report instructions generation
- Analysis report generation

## Configuration Examples

### Example 1: All OpenAI
```bash
PLANNER_PROVIDER=openai
CODER_PROVIDER=openai

OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

### Example 2: All Groq
```bash
PLANNER_PROVIDER=groq
CODER_PROVIDER=groq

GROQ_API_KEY=gsk-your-key-here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Example 3: Hybrid (Recommended)
```bash
PLANNER_PROVIDER=openai
CODER_PROVIDER=groq

OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-5

GROQ_API_KEY=gsk-your-key-here
GROQ_MODEL=openai/gpt-oss-120b
```

## Switching Providers

You can easily switch providers by editing the `.env` file:

1. Open `.env` file in a text editor
2. Update `PLANNER_PROVIDER` and/or `CODER_PROVIDER`
3. Save the file
4. Restart the backend: `./start_backend.sh`

The startup script will automatically:
- Validate your API keys
- Display the configuration
- Show "Hybrid Mode Enabled" message if using different providers

## Checking Current Configuration

When you start the backend, you'll see:

```
LLM Configuration:
  📋 Planning Phase: openai
  💻 Coding Phase:   groq

🔄 Hybrid Mode Enabled:
   Using openai for planning (better reasoning)
   Using groq for coding (faster execution)
```

## API Keys

### OpenAI
Get your API key from: https://platform.openai.com/api-keys

### Groq
Get your API key from: https://console.groq.com/keys

## Troubleshooting

### Provider validation fails
- Ensure API key is set correctly in `.env`
- Check that the key starts with the correct prefix:
  - OpenAI: `sk-`
  - Groq: `gsk_`

### Model not available
- Check the provider's documentation for available models
- Update the model name in `.env`
- Some models may require special access

### Hybrid mode not working
- Ensure both API keys are configured
- Check that providers are spelled correctly: "openai" or "groq" (lowercase)
- Restart the backend after changing configuration

## Best Practices

1. **Use Hybrid Mode** for optimal performance and cost
2. **OpenAI for Planning** - Better at understanding complex requirements
3. **Groq for Coding** - Faster code generation with open models
4. **Keep API keys secure** - Never commit `.env` file to version control
5. **Monitor usage** - Track API usage on provider dashboards

## Questions?

If you have issues with LLM configuration, check:
- `.env` file has correct API keys
- Backend logs for detailed error messages
- Provider status pages for outages
