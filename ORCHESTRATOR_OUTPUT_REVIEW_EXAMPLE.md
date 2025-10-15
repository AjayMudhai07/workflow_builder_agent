# IRA Orchestrator - Output Review Feature

## Overview

The IRA Orchestrator now includes an **Output Review** phase that allows users to:
1. Review the generated output dataframe
2. Approve and complete the workflow, OR
3. Provide feedback for refinements

This creates a feedback loop where the Coder Agent can iteratively refine the output based on user requirements.

## New Workflow Phases

```
NOT_STARTED → PLANNING → PLAN_REVIEW → CODING → OUTPUT_REVIEW → COMPLETED
                                            ↑            ↓
                                            └────────────┘
                                          (refinement loop)
```

## Usage Example

### Basic Output Review Workflow

```python
import asyncio
from ira_builder.orchestrator import create_orchestrator

async def main():
    # Create orchestrator
    orchestrator = create_orchestrator(
        workflow_name="Sales Analysis",
        workflow_description="Analyze Q4 sales data",
        csv_filepaths=["data/sales.csv"],
        output_filename="sales_result.csv"
    )

    # ========================================
    # PHASE 1: PLANNING
    # ========================================
    result = await orchestrator.start()
    print(result['response'])

    # Answer Planner's questions
    while orchestrator.state.phase == "planning":
        user_answer = input("Your answer: ")
        result = await orchestrator.process_user_input(user_answer)
        print(result['response'])

        if orchestrator.is_plan_ready():
            break

    # ========================================
    # PHASE 2: PLAN REVIEW
    # ========================================
    print("\n✅ Business Logic Plan:")
    print(orchestrator.state.business_logic_plan)

    approve_plan = input("\nApprove plan? (yes/no): ")

    if approve_plan.lower() == 'yes':
        # ====================================
        # PHASE 3: CODE GENERATION
        # ====================================
        result = await orchestrator.approve_plan_and_generate_code()

        if result['status'] == 'success':
            # ================================
            # PHASE 4: OUTPUT REVIEW (NEW!)
            # ================================
            print("\n" + "="*80)
            print("OUTPUT REVIEW PHASE")
            print("="*80)

            print(f"\n✅ Code generated successfully!")
            print(f"Output saved to: {result['output_path']}")

            # Show output preview
            print("\n📊 Output Preview:")
            print(result.get('output_preview', 'No preview available'))

            # Show output summary
            if result.get('output_summary'):
                summary = result['output_summary']
                print(f"\n📈 Output Summary:")
                print(f"  - Rows: {summary.get('row_count', 'N/A'):,}")
                print(f"  - Columns: {summary.get('column_count', 'N/A')}")
                print(f"  - Column Names: {', '.join(summary.get('columns', []))}")

            # User decision: approve or provide feedback
            print("\n" + "="*80)
            print("What would you like to do?")
            print("  1. Approve and complete workflow")
            print("  2. Request changes/refinements")
            print("="*80)

            choice = input("\nYour choice (1/2): ")

            if choice == "1":
                # Approve output and complete
                final_result = await orchestrator.approve_output_and_complete()

                if final_result['status'] == 'success':
                    print(f"\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
                    print(f"Execution time: {final_result['execution_time']:.2f} seconds")
                    print(f"Output file: {final_result['output_path']}")

            elif choice == "2":
                # Request refinements
                feedback = input("\nDescribe what you'd like to change: ")

                refine_result = await orchestrator.refine_output(feedback)

                if refine_result['status'] == 'success':
                    print(f"\n✅ Output refined successfully!")
                    print(f"New output saved to: {refine_result['output_path']}")

                    # Show new preview
                    print("\n📊 Updated Output Preview:")
                    print(refine_result.get('output_preview', 'No preview available'))

                    # Can approve or refine again
                    final_approve = input("\nApprove this output? (yes/no): ")

                    if final_approve.lower() == 'yes':
                        final_result = await orchestrator.approve_output_and_complete()
                        print(f"\n✅ WORKFLOW COMPLETED!")
                else:
                    print(f"\n❌ Refinement failed: {refine_result.get('error')}")

asyncio.run(main())
```

## New API Methods

### 1. `approve_output_and_complete()`

Approve the output and complete the workflow.

```python
result = await orchestrator.approve_output_and_complete()

# Returns:
{
    "status": "success",
    "phase": "completed",
    "output_path": "/path/to/output.csv",
    "execution_time": 45.23,
    "is_successful": True
}
```

### 2. `refine_output(feedback, max_refinement_iterations=3)`

Refine the output based on user feedback.

```python
feedback = "Add a column showing percentage of total sales"
result = await orchestrator.refine_output(feedback)

# Returns:
{
    "status": "success",
    "phase": "output_review",
    "code": "# Updated code...",
    "code_filepath": "/path/to/code.py",
    "output_path": "/path/to/output.csv",
    "output_preview": "DataFrame preview...",
    "output_summary": {...},
    "refinement_iteration": 1
}
```

### 3. `is_output_ready()`

Check if output is ready for review.

```python
if orchestrator.is_output_ready():
    print("Output is ready for review!")
```

### 4. `get_output_review_summary()`

Get summary of output review phase.

```python
summary = orchestrator.get_output_review_summary()

# Returns:
{
    "output_approved": False,
    "refinement_iterations": 1,
    "feedback_history": [
        {
            "timestamp": "2025-10-16T...",
            "feedback": "Add percentage column",
            "iteration": 1
        }
    ],
    "output_path": "/path/to/output.csv"
}
```

## Refinement Examples

### Example 1: Add Calculations

```python
feedback = """
Add two new columns:
1. 'percentage_of_total' - each amount as % of total
2. 'cumulative_sum' - running total of amounts
"""

result = await orchestrator.refine_output(feedback)
```

### Example 2: Change Filtering

```python
feedback = """
The filter is too restrictive. Instead of Amount > 1000,
please use Amount > 500 to capture more transactions.
"""

result = await orchestrator.refine_output(feedback)
```

### Example 3: Modify Grouping

```python
feedback = """
Instead of grouping by Vendor_Name only,
group by both Vendor_Name and Category,
then sort by total Amount descending.
"""

result = await orchestrator.refine_output(feedback)
```

### Example 4: Add/Remove Columns

```python
feedback = """
Please add these columns to the output:
- Transaction_Count: number of transactions per vendor
- Average_Amount: average transaction amount
- First_Transaction_Date: earliest transaction date

And remove the 'Internal_ID' column as it's not needed.
"""

result = await orchestrator.refine_output(feedback)
```

## Configuration

### Maximum Refinement Iterations

By default, you can refine output up to 3 times. You can configure this:

```python
result = await orchestrator.refine_output(
    feedback="Make changes...",
    max_refinement_iterations=5  # Allow up to 5 refinements
)
```

### Callbacks for Output Review

You can add callbacks to monitor the output review phase:

```python
def on_phase_change(phase):
    if phase == "output_review":
        print("📊 Output is ready for review!")
    elif phase == "completed":
        print("✅ Workflow completed!")

orchestrator = create_orchestrator(
    ...,
    on_phase_change=on_phase_change
)
```

## Workflow State Tracking

The workflow state now includes output review information:

```python
state = orchestrator.get_workflow_summary()

print(f"Phase: {state['phase']}")
print(f"Output approved: {state['output_review_summary']['output_approved']}")
print(f"Refinement iterations: {state['output_review_summary']['refinement_iterations']}")
```

## Error Handling

```python
# Handle refinement errors
result = await orchestrator.refine_output(feedback)

if result['status'] == 'error':
    print(f"Refinement failed: {result['error']}")

    # Check if max iterations reached
    if "Maximum refinement iterations" in result['error']:
        print("Too many refinement attempts. Approving current output.")
        await orchestrator.approve_output_and_complete()
```

## Best Practices

1. **Review Before Approving**: Always check the output preview before approving
2. **Be Specific in Feedback**: Provide clear, detailed feedback for refinements
3. **Limit Iterations**: Don't exceed 3-5 refinement iterations
4. **Save State**: Workflow state is automatically saved, including refinement history
5. **Check Summary**: Use `get_output_review_summary()` to track refinement progress

## Integration with UI

For web/desktop UIs, use the output review phase to:

1. Display output preview in a table
2. Show summary statistics
3. Provide "Approve" and "Request Changes" buttons
4. Show refinement history
5. Track refinement iterations

## Next Steps

After implementing output review, you might want to:

1. Add data visualization for output preview
2. Implement side-by-side comparison of refinements
3. Add export options (CSV, Excel, JSON)
4. Implement undo/redo for refinements
5. Add output validation rules
