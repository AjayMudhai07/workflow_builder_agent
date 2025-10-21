# Backend Monitoring Guide

This guide shows you how to see what's happening in your IRA Workflow Builder backend.

## 1. View Real-Time Backend Logs

### Option A: Check Background Process Output
The backend is running in a background process. You can view its output anytime:

```bash
# In Claude Code, use BashOutput tool with bash_id: 5f06ee
# This shows all output from the backend since it started
```

### Option B: View Live Logs in Terminal
Open a new terminal and run:

```bash
cd /Users/ajay/Documents/workflow_builder_v4
tail -f logs/app.log  # If log files are configured
```

### Option C: Use the Running Process
Since the backend auto-reloads, you'll see:
- Server restarts when files change
- HTTP requests with status codes
- INFO/WARNING/ERROR messages
- Workflow state changes

## 2. Filter for Specific Information

### View Only Errors and Warnings
```bash
# Using BashOutput with filter parameter
# Filter: "ERROR|WARNING|error|warning"
```

### View Specific Workflow Activity
```bash
# Filter for a specific workflow ID
# Filter: "342c2eb3-98bb-4f82-ab85-9bc2e3a5a060"
```

### View API Requests
```bash
# Filter: "Request started|Request completed"
```

## 3. Check Backend Status

### Is Backend Running?
```bash
lsof -ti:8000
# If returns a process ID, backend is running
# Current backend is on process 90263
```

### Test Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### View All Running Bashes
```bash
# In Claude Code, use: /bashes
# Shows all background processes with their IDs
```

## 4. Inspect Workflow States

### List Recent Workflows
```bash
ls -lt storage/workflows/*.json | head -10
```

### View Specific Workflow State
```bash
cat storage/workflows/<workflow-id>_state.json | jq .
# Or without jq:
cat storage/workflows/<workflow-id>_state.json
```

### Check Workflow Phase
```bash
cat storage/workflows/<workflow-id>_state.json | jq '.phase'
```

## 5. Common Log Patterns

### Workflow Creation
```
[info] Created workflow: <workflow-id>
[info] Orchestrator initialized for workflow: <name>
```

### Planning Phase
```
[info] STARTING WORKFLOW: <name>
[info] Workflow phase: not_started → planning
[info] Processing user input: <answer>
[info] Questions asked: 5/10
```

### Plan Generation
```
[info] Planner signaled GENERATE_PLAN
[info] Generating business logic plan
[info] Workflow phase: planning → plan_review
```

### Code Generation
```
[info] Workflow phase: plan_review → coding
[info] Generating code for workflow
[info] Code generated successfully
```

### Errors to Watch For
```
[error] Error generating business logic: ...
[error] HTTP error occurred
[error] Failed to ...
```

## 6. Quick Diagnostic Commands

### Check Backend Port
```bash
lsof -ti:8000
```

### View Last 20 API Requests
```bash
# Filter logs for: "Request started|Request completed"
```

### Check for Errors
```bash
# Filter logs for: "error|ERROR|warning|WARNING"
```

### View Workflow Files
```bash
# List workflows:
ls storage/workflows/

# View workflow state:
cat storage/workflows/<id>_state.json

# Count workflows:
ls storage/workflows/*.json | wc -l
```

## 7. Key Log Levels

- **`[info]`** - Normal operation (workflow progress, API requests)
- **`[warning]`** - Non-critical issues (e.g., "Only 1 questions asked")
- **`[error]`** - Critical problems that need attention
- **`[debug]`** - Detailed information for troubleshooting

## 8. Backend Auto-Reload

The backend automatically reloads when you change:
- `src/ira_builder/agents/*.py`
- `src/ira_builder/api/routes/*.py`
- `src/ira_builder/orchestrator.py`
- Any Python file in the project

You'll see:
```
WARNING: WatchFiles detected changes in '<file>'
INFO: Shutting down
INFO: Started server process [<new-pid>]
INFO: Application startup complete
```

## 9. Current Backend Status

**Process ID**: 90263
**Port**: 8000
**Status**: Running ✅
**Auto-reload**: Enabled
**Model**: gpt-5
**Environment**: development

## 10. Troubleshooting

### Backend Not Responding?
1. Check if process is running: `lsof -ti:8000`
2. View recent logs for errors
3. Restart if needed: Kill process and run `./start_backend.sh`

### Can't See Logs?
1. Use BashOutput tool with bash_id: `5f06ee`
2. Check that backend is running
3. Look in `storage/workflows/` for workflow state files

### HTTP Errors?
1. Check backend logs for error messages
2. Verify endpoint exists in `src/ira_builder/api/routes/workflows.py`
3. Check workflow phase matches expected phase

---

## Example: Monitoring a Workflow End-to-End

1. **Create Workflow**
   ```
   Look for: "Created workflow: <id>"
   ```

2. **Start Planning**
   ```
   Look for: "STARTING WORKFLOW"
   Look for: "Workflow phase: not_started → planning"
   ```

3. **Answer Questions**
   ```
   Look for: "Processing user input"
   Look for: "Questions asked: X/10"
   ```

4. **Generate Plan**
   ```
   Look for: "GENERATE_PLAN"
   Look for: "Workflow phase: planning → plan_review"
   ```

5. **Generate Code**
   ```
   Look for: "Workflow phase: plan_review → coding"
   Look for: "Code generated successfully"
   ```

6. **Review Output**
   ```
   Look for: "Workflow phase: coding → output_review"
   ```

7. **Complete**
   ```
   Look for: "Workflow phase: output_review → completed"
   ```
