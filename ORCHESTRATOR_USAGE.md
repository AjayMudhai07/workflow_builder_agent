# IRA Orchestrator - Usage Guide

## Overview

The IRA Orchestrator provides a complete end-to-end workflow for building data analysis pipelines:
1. **Planning Phase**: Gather requirements through AI-powered interview
2. **Plan Review**: Review and approve the generated Business Logic Plan
3. **Coding Phase**: Automatically generate and execute production-ready Python code
4. **Completion**: Receive executable code and processed data

## Quick Start

### Basic Usage

```python
import asyncio
from ira_builder.orchestrator import create_orchestrator

async def main():
    # Create orchestrator
    orchestrator = create_orchestrator(
        workflow_name="Sales Analysis",
        workflow_description="Analyze Q4 sales data to identify top products",
        csv_filepaths=["data/sales_q4.csv", "data/products.csv"],
        output_filename="sales_analysis_result.csv",
        model="gpt-4o"
    )

    # Start planning phase
    result = await orchestrator.start()
    print(result['response'])

    # Answer Planner's questions
    while orchestrator.state.phase == "planning":
        user_answer = input("Your answer: ")
        result = await orchestrator.process_user_input(user_answer)
        print(result['response'])

        # Check if Business Logic Plan is ready
        if orchestrator.is_plan_ready():
            print("\n✅ Business Logic Plan ready for review!")
            break

    # Review and approve plan
    print("\nBusiness Logic Plan:")
    print(orchestrator.state.business_logic_plan)

    approve = input("\nApprove and generate code? (yes/no): ")
    if approve.lower() == 'yes':
        # Generate and execute code
        result = await orchestrator.approve_plan_and_generate_code()

        if result['status'] == 'success':
            print(f"\n✅ SUCCESS!")
            print(f"Generated code: {result['code_filepath']}")
            print(f"Output data: {result['output_path']}")
        else:
            print(f"\n❌ FAILED: {result['error']}")

asyncio.run(main())
```

## Advanced Features

### Callbacks for UI Integration

```python
def on_phase_change(phase):
    print(f"📍 Workflow phase changed to: {phase.value}")

def on_planner_response(response, response_type):
    print(f"💬 Planner responded ({response_type.value})")

def on_coder_progress(iteration, max_iterations):
    print(f"🔄 Code generation iteration {iteration}/{max_iterations}")

orchestrator = create_orchestrator(
    workflow_name="My Workflow",
    workflow_description="Process financial data",
    csv_filepaths=["data/transactions.csv"],
    on_phase_change=on_phase_change,
    on_planner_response=on_planner_response,
    on_coder_progress=on_coder_progress
)
```

### State Persistence

```python
# Workflow state is automatically saved to:
# ./storage/workflows/{workflow_name}_state.json

# Check workflow status
summary = orchestrator.get_workflow_summary()
print(f"Phase: {summary['phase']}")
print(f"Started: {summary['started_at']}")
print(f"Planner questions asked: {summary['planner_summary']['questions_asked']}")
```

### Generated Code Persistence

```python
# Generated code is automatically saved to:
# ./storage/generated_code/{workflow_name}_{timestamp}.py

# The code contains absolute paths and is ready for production use
# It can be executed directly or modified as needed
```

## Workflow Phases

| Phase | Description | Methods Available |
|-------|-------------|-------------------|
| `NOT_STARTED` | Initial state | `start()` |
| `PLANNING` | Gathering requirements | `process_user_input()` |
| `PLAN_REVIEW` | Reviewing Business Logic Plan | `approve_plan_and_generate_code()`, `refine_plan()` |
| `CODING` | Generating and executing code | (automatic) |
| `COMPLETED` | Successfully finished | `get_workflow_summary()` |
| `FAILED` | Encountered error | `get_workflow_summary()` |

## API Reference

### Orchestrator Methods

#### `start()` → `Dict[str, Any]`
Initialize workflow and start planning phase.

**Returns:**
```python
{
    "status": "success",
    "phase": "planning",
    "response": "First question from Planner...",
    "response_type": "question"
}
```

#### `process_user_input(answer: str)` → `Dict[str, Any]`
Process user's answer to Planner's question.

**Parameters:**
- `answer` (str): User's response

**Returns:**
```python
{
    "status": "success",
    "phase": "planning",
    "response": "Next question...",
    "response_type": "question",
    "questions_asked": 3
}
```

#### `approve_plan_and_generate_code()` → `Dict[str, Any]`
Approve Business Logic Plan and start code generation.

**Returns (success):**
```python
{
    "status": "success",
    "phase": "completed",
    "code": "# Generated Python code...",
    "code_filepath": "./storage/generated_code/Sales_Analysis_20251016_143022.py",
    "output_path": "./data/outputs/Sales_Analysis/result.csv",
    "output_preview": "DataFrame preview...",
    "iterations": 1,
    "execution_time": 45.23
}
```

#### `refine_plan(feedback: str)` → `Dict[str, Any]`
Refine Business Logic Plan based on feedback.

**Parameters:**
- `feedback` (str): User's feedback on the plan

**Returns:**
```python
{
    "status": "success",
    "business_logic_plan": "Refined plan..."
}
```

#### `get_workflow_summary()` → `Dict[str, Any]`
Get complete workflow summary.

**Returns:**
```python
{
    "workflow_name": "Sales Analysis",
    "phase": "completed",
    "started_at": "2025-10-16T14:30:00",
    "completed_at": "2025-10-16T14:35:23",
    "is_successful": True,
    "planner_summary": {
        "questions_asked": 5,
        "business_logic_plan": "...",
        "plan_approved": True
    },
    "coder_summary": {
        "iterations": 1,
        "generated_code": "...",
        "output_path": "..."
    }
}
```

## Testing

### Run the Orchestrator Test

```bash
# Automated mode (pre-defined answers)
python test_orchestrator.py
# Select mode: 1

# Interactive mode (manual input)
python test_orchestrator.py
# Select mode: 2
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
OPENAI_CHAT_MODEL_ID=gpt-4o
MAX_QUESTIONS=10
CODE_EXECUTION_TIMEOUT=120
```

### Orchestrator Parameters

```python
orchestrator = create_orchestrator(
    workflow_name="My Workflow",              # Required
    workflow_description="What it does",      # Required
    csv_filepaths=["data/file1.csv"],        # Required
    output_filename="result.csv",             # Default: "result.csv"
    model="gpt-4o",                          # Default: "gpt-4o"
    max_planner_questions=10,                # Default: 10
    max_coder_iterations=5,                  # Default: 5
    code_execution_timeout=120,              # Default: 120 seconds
    state_persistence_dir="./storage/workflows",  # Default
    on_phase_change=callback_fn,             # Optional
    on_planner_response=callback_fn,         # Optional
    on_coder_progress=callback_fn            # Optional
)
```

## Output Structure

### Generated Code File
```
./storage/generated_code/
└── {workflow_name}_{timestamp}.py
```

**Contents:**
- Part 1: Imports and file paths (with absolute paths)
- Part 2: Data loading and IRA preprocessing
- Part 3: Business logic implementation
- Production-ready, standalone Python code

### Output Data File
```
./data/outputs/{workflow_name}/
└── {output_filename}
```

### Workflow State File
```
./storage/workflows/
└── {workflow_name}_state.json
```

**Contains:**
- Complete conversation history
- Business Logic Plan
- Generated code
- Execution results
- Timestamps and metadata

## Error Handling

The orchestrator handles errors gracefully:

```python
result = await orchestrator.approve_plan_and_generate_code()

if result['status'] == 'error':
    print(f"Error: {result['error']}")
    print(f"Phase: {result['phase']}")

    # Check if we have partial results
    if result.get('last_code'):
        print("Last generated code:", result['last_code'])

    # Get workflow summary for debugging
    summary = orchestrator.get_workflow_summary()
```

## Best Practices

1. **Always check phase before calling methods**
   ```python
   if orchestrator.is_plan_ready():
       await orchestrator.approve_plan_and_generate_code()
   ```

2. **Use callbacks for real-time monitoring**
   ```python
   def log_phase_change(phase):
       logger.info(f"Phase changed to: {phase.value}")

   orchestrator = create_orchestrator(..., on_phase_change=log_phase_change)
   ```

3. **Save workflow state periodically**
   - State is automatically saved after each phase change
   - Can be loaded later for resume capability

4. **Review generated code before production use**
   - Code is production-ready but should be reviewed
   - Check for edge cases specific to your data

5. **Test with sample data first**
   - Use small CSV files for initial testing
   - Verify Business Logic Plan is correct before coding

## Examples

### Example 1: Financial Data Analysis

```python
orchestrator = create_orchestrator(
    workflow_name="Expense_Date_Mismatch",
    workflow_description="Flag transactions where document month > posting month",
    csv_filepaths=["data/FBL3N.csv"],
    output_filename="expense_mismatches.csv"
)

# Run the workflow...
```

### Example 2: Multi-File Joining

```python
orchestrator = create_orchestrator(
    workflow_name="Vendor_Sales_Analysis",
    workflow_description="Join vendor master with sales data and calculate totals",
    csv_filepaths=["data/vendors.csv", "data/sales.csv"],
    output_filename="vendor_sales_summary.csv"
)

# Run the workflow...
```

### Example 3: Data Quality Checks

```python
orchestrator = create_orchestrator(
    workflow_name="Data_Quality_Report",
    workflow_description="Identify records with missing values, duplicates, or invalid formats",
    csv_filepaths=["data/customer_master.csv"],
    output_filename="data_quality_issues.csv"
)

# Run the workflow...
```

## Troubleshooting

### Issue: API Key Error
**Solution:** Update `OPENAI_API_KEY` in `.env` file

### Issue: Workflow Stuck in Planning
**Solution:** Check `max_planner_questions` limit, or manually request plan generation:
```python
await orchestrator.request_plan_generation(force=True)
```

### Issue: Code Generation Fails
**Solution:**
- Check `max_coder_iterations` setting
- Review Business Logic Plan for clarity
- Check CSV files are accessible
- Verify IRA library is installed

### Issue: Output File Not Created
**Solution:**
- Check code execution logs in workflow summary
- Verify output directory permissions
- Check for runtime errors in generated code

## Support

For issues and questions:
- Check `current_progress.md` for system status
- Review test scripts for usage examples
- Check logs in `./logs/` directory
- Review workflow state JSON for debugging

---

**Version**: 0.4.0
**Last Updated**: 2025-10-16
**Status**: Production-Ready
