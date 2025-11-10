# LLM Monitoring & Observability

This project uses **OpenTelemetry** via Microsoft's agent-framework to automatically track all LLM calls.

## What Gets Tracked Automatically

Every agent call is automatically traced with:
- **Agent name** and **model** used
- **Token usage** (input/output tokens)
- **Cost** calculated from token usage
- **Latency** (how long each call took)
- **Call chain** (which agent called which agent)
- **Input/Output data** (when `ENABLE_SENSITIVE_DATA=true`)
- **Errors** with full stack traces

## How to View Traces

### Option 1: Aspire Dashboard (Recommended for Local Dev)

**1. Install .NET Aspire Dashboard:**
```bash
# Using Docker (easiest)
docker run --rm -it -p 18888:18888 -p 4317:18889 \
  --name aspire-dashboard \
  mcr.microsoft.com/dotnet/aspire-dashboard:9.0

# Or install .NET 9 SDK and run:
dotnet tool install -g Microsoft.DotNet.AspireDashboard
aspire-dashboard
```

**2. Access the dashboard:**
- Open browser: http://localhost:18888
- View traces in real-time
- Filter by agent name, model, or time range
- See token usage and costs

**3. What you'll see:**
```
orchestrator.process_user_input (5.2s)
├─ IntentAgent.run (1.1s)
│  └─ groq.chat.completions (0.9s)
│     - input_tokens: 523
│     - output_tokens: 147
│     - cost: $0.001
├─ CoderAgent.run (3.8s)
│  └─ openai.chat.completions (3.5s)
│     - input_tokens: 2341
│     - output_tokens: 1523
│     - cost: $0.018
└─ Total: $0.019
```

### Option 2: Console Output (Simple)

If you don't set `OTLP_ENDPOINT`, traces are printed to console:

```bash
# In .env, comment out or remove:
# OTLP_ENDPOINT=http://localhost:4317

# Traces will appear in backend logs:
2025-11-10 14:32:15 [info] LLM_CALL agent=CoderAgent model=gpt-5 tokens=2341→1523 cost=$0.018
```

### Option 3: Azure Monitor / Application Insights (Production)

**1. Create Application Insights resource in Azure**

**2. Get connection string from Azure Portal**

**3. Add to .env:**
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=xxxxx;..."
```

**4. View in Azure Portal:**
- Go to Application Insights → Logs
- Query traces:
```kusto
traces
| where customDimensions.gen_ai_agent_name != ""
| project timestamp, agentName=customDimensions.gen_ai_agent_name,
          model=customDimensions.gen_ai_request_model,
          inputTokens=customDimensions.gen_ai_usage_input_tokens,
          outputTokens=customDimensions.gen_ai_usage_output_tokens
| order by timestamp desc
```

### Option 4: Grafana + OpenTelemetry Collector (Self-Hosted)

**1. Run OpenTelemetry Collector:**
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  prometheus:
    endpoint: "0.0.0.0:9090"

processors:
  batch:

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

```bash
docker run -p 4317:4317 -p 4318:4318 -p 9090:9090 \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

**2. Run Grafana:**
```bash
docker run -d -p 3001:3000 --name=grafana grafana/grafana
```

**3. Add Prometheus data source in Grafana**

**4. Query metrics:**
- `gen_ai_client_token_usage` - Token usage histogram
- `gen_ai_client_operation_duration` - Latency histogram
- `agent_framework_function_invocation_duration` - Tool execution time

## Configuration

### Environment Variables (.env)

```bash
# Enable OpenTelemetry
ENABLE_OTEL=true

# Include prompts/responses (DEV ONLY - security risk in production!)
ENABLE_SENSITIVE_DATA=true

# Where to send traces
OTLP_ENDPOINT=http://localhost:4317

# Optional: Azure Monitor
APPLICATIONINSIGHTS_CONNECTION_STRING=...
```

### What Each Setting Does

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_OTEL` | Enable OpenTelemetry tracking | `false` |
| `ENABLE_SENSITIVE_DATA` | Include prompts/responses in traces | `false` |
| `OTLP_ENDPOINT` | Where to send traces (Aspire, Collector, etc.) | Console output |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Azure Monitor connection | None |

## Querying Metrics

### Available Metrics

**Token Usage:**
```
gen_ai.client.token.usage
  - gen_ai.request.model = "gpt-5"
  - gen_ai.usage.input_tokens = 2341
  - gen_ai.usage.output_tokens = 1523
```

**Latency:**
```
gen_ai.client.operation.duration
  - gen_ai.agent.name = "CoderAgent"
  - duration_seconds = 3.5
```

**Function Calls:**
```
agent_framework.function.invocation.duration
  - function_name = "execute_python"
  - duration_seconds = 0.8
```

### Example Queries

**Total tokens used today:**
```promql
sum(gen_ai_client_token_usage_total{time > "today"})
```

**Average latency by model:**
```promql
avg(gen_ai_client_operation_duration) by (gen_ai_request_model)
```

**Cost per agent (assuming $1.25/$10 per 1M tokens for gpt-5):**
```promql
sum(gen_ai_usage_input_tokens * 0.00000125) +
sum(gen_ai_usage_output_tokens * 0.00001000)
by (gen_ai_agent_name)
```

## Troubleshooting

### No traces appearing?

1. **Check OpenTelemetry is enabled:**
   ```bash
   # Should see in backend logs:
   ✅ OpenTelemetry observability enabled
   ```

2. **Verify OTLP endpoint is reachable:**
   ```bash
   curl http://localhost:4317
   # Should get "method not allowed" (means it's listening)
   ```

3. **Check agent-framework version:**
   ```bash
   pip show agent-framework
   # Should be >= 1.0.0b251007
   ```

4. **Install OpenTelemetry packages:**
   ```bash
   pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
   ```

### Traces show 0 tokens?

- Ensure `ENABLE_SENSITIVE_DATA=true` in development
- Token metrics come from LLM provider responses
- Some providers don't return token counts (Azure sometimes)

### Performance impact?

- OpenTelemetry is async and non-blocking
- Typical overhead: <5ms per call
- Can disable in production if needed: `ENABLE_OTEL=false`

## Best Practices

### Development
- ✅ Use `ENABLE_SENSITIVE_DATA=true` to debug prompts
- ✅ Use Aspire Dashboard for visual debugging
- ✅ Console output is fine for quick checks

### Production
- ⚠️ Set `ENABLE_SENSITIVE_DATA=false` (security!)
- ✅ Use Application Insights or hosted OTLP receiver
- ✅ Set up alerts for:
  - High token usage (cost control)
  - High latency (performance)
  - Error rate spikes (reliability)

### Cost Monitoring
- Track `gen_ai_client_token_usage` metric
- Calculate costs using pricing tables
- Set budget alerts in your observability platform

## Example: Full Agent Call Chain

When you create a workflow, you'll see traces like:

```
POST /api/v1/workflows/create (8.2s)
└─ IRAOrchestrator.start_with_raa (8.0s)
   ├─ DatasetAnalyzer.run (1.2s)
   │  └─ groq.openai/gpt-oss-120b (0.9s)
   │     input: 523 tokens, output: 147 tokens, cost: $0.0002
   │
   ├─ IntentAgent.run (1.5s)
   │  └─ groq.openai/gpt-oss-120b (1.2s)
   │     input: 842 tokens, output: 234 tokens, cost: $0.0003
   │
   └─ CoderAgent.run (4.8s)
      ├─ openai.gpt-5 (3.5s)
      │  input: 2341 tokens, output: 1523 tokens, cost: $0.0182
      │
      └─ PythonREPL.execute (0.8s)
         result: success

Total: 8.2s, $0.0187
```

This gives you full visibility into:
- Which agents were called
- In what order
- How long each took
- Token usage and costs
- Where bottlenecks are

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Aspire Dashboard:**
   ```bash
   docker run --rm -it -p 18888:18888 -p 4317:18889 \
     --name aspire-dashboard \
     mcr.microsoft.com/dotnet/aspire-dashboard:9.0
   ```

3. **Start backend:**
   ```bash
   ./start_backend.sh
   ```

4. **Create a workflow** and watch traces appear at http://localhost:18888

## Resources

- [Microsoft Agent Framework Observability Docs](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-observability)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Aspire Dashboard](https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/dashboard/overview)
- [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/)
