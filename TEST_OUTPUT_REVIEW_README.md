# Testing the Complete Workflow with Output Review

## Quick Start

### Run Automated Test (Recommended)

```bash
python test_orchestrator_with_output_review.py
# Select mode: 1 (Automated)
```

This will automatically:
1. ✅ Answer Planner's questions
2. ✅ Approve Business Logic Plan
3. ✅ Generate and execute code
4. ✅ Review initial output
5. ✅ Apply refinement feedback #1 (add columns, sort, calculate percentages)
6. ✅ Apply refinement feedback #2 (add transaction count, filter)
7. ✅ Approve final output
8. ✅ Complete workflow

### Run Interactive Test

```bash
python test_orchestrator_with_output_review.py
# Select mode: 2 (Interactive)
```

This allows you to:
- Manually answer Planner's questions
- Review and approve the Business Logic Plan
- Review generated output
- Provide custom refinement feedback
- Approve when satisfied

## Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: PLANNING                        │
│  - Planner asks questions                                   │
│  - Automated answers: ["A", "A", "A", "A", "A"]            │
│  - Business Logic Plan generated                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  PHASE 2: PLAN REVIEW                       │
│  - Display Business Logic Plan preview                      │
│  - Auto-approve plan                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 3: CODE GENERATION                       │
│  - Coder Agent generates Python code                        │
│  - Code is validated and executed                           │
│  - Output CSV created                                       │
│  - Display output preview and summary                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            PHASE 4: OUTPUT REVIEW (Initial)                 │
│  - Show output preview (first 10 rows)                      │
│  - Show output summary (row count, columns)                 │
│  - Simulate user feedback for refinement                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              REFINEMENT #1 - Apply Feedback                 │
│  Feedback:                                                  │
│  1. Add 'average_amount' column                            │
│  2. Sort by total amount descending                         │
│  3. Add percentage contribution column                      │
│                                                             │
│  - Coder regenerates code                                   │
│  - New output generated                                     │
│  - Display updated preview                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              REFINEMENT #2 - Additional Changes             │
│  Feedback:                                                  │
│  1. Add 'transaction_count' column                         │
│  2. Filter: only show vendors with total > 100             │
│                                                             │
│  - Coder regenerates code again                            │
│  - New output generated                                     │
│  - Display final preview                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            PHASE 5: FINAL APPROVAL & COMPLETION             │
│  - User approves final output                               │
│  - Workflow marked as COMPLETED                             │
│  - Display execution time and summary                       │
└─────────────────────────────────────────────────────────────┘
```

## Expected Output

### Phase 1 - Planning
```
================================================================================
PHASE 1: PLANNING - Gathering Requirements
================================================================================

✓ Workflow started successfully

Planner's First Question:
--------------------------------------------------------------------------------
Hello! I'll help you create a data analysis workflow...
[Question content]
--------------------------------------------------------------------------------

Iteration 1: Answering 'A'
  ✓ Questions asked: 1
  ✓ Response type: question

[... more iterations ...]

✓ Business Logic Plan generated!
```

### Phase 2 - Plan Review
```
================================================================================
PHASE 2: PLAN REVIEW
================================================================================

Business Logic Plan (preview):
--------------------------------------------------------------------------------
# Business Logic Plan

## **Workflow Purpose**
Load FBL3N CSV, group by vendor, calculate totals...

[... plan content ...]
--------------------------------------------------------------------------------

✓ Approving Business Logic Plan...
```

### Phase 3 - Code Generation
```
================================================================================
PHASE 3: CODE GENERATION & EXECUTION
================================================================================

✅ Code generated and executed successfully!

✓ Phase: output_review
✓ Iterations: 1
✓ Output path: ./data/outputs/Sales_Summary_Test/sales_summary_output.csv
✓ Code saved to: ./storage/generated_code/Sales_Summary_Test_20251016_143022.py

📊 Output Preview:
--------------------------------------------------------------------------------
   Vendor_Name  Total_Amount  Transaction_Count
0  Vendor A     15000.00      25
1  Vendor B     12000.00      20
...
--------------------------------------------------------------------------------

📈 Output Summary:
  - Rows: 10
  - Columns: 3
  - Column Names: Vendor_Name, Total_Amount, Transaction_Count
```

### Phase 4 - Output Review & Refinement
```
================================================================================
PHASE 4: OUTPUT REVIEW - Initial Review
================================================================================

✓ Output is ready for review!

Simulating user feedback for refinement...

User Feedback:
--------------------------------------------------------------------------------
I noticed the output needs some improvements:
1. Add a new column called 'average_amount'...
2. Sort the results by total amount in descending order...
3. Add a column showing the percentage each vendor contributes...
--------------------------------------------------------------------------------

================================================================================
REFINEMENT #1 - Applying User Feedback
================================================================================

✅ Output refined successfully!

✓ Refinement iteration: 1
✓ Output path: ./data/outputs/Sales_Summary_Test/sales_summary_output.csv
✓ Updated code saved to: ./storage/generated_code/Sales_Summary_Test_20251016_143045.py

📊 Updated Output Preview:
--------------------------------------------------------------------------------
   Vendor_Name  Total_Amount  Transaction_Count  Average_Amount  Percentage
0  Vendor A     15000.00      25                600.00         35.7%
1  Vendor B     12000.00      20                600.00         28.6%
...
--------------------------------------------------------------------------------
```

### Phase 5 - Completion
```
================================================================================
PHASE 5: FINAL APPROVAL & COMPLETION
================================================================================

User approves the output...

✅ WORKFLOW COMPLETED SUCCESSFULLY!

✓ Phase: completed
✓ Execution time: 67.45 seconds
✓ Output path: ./data/outputs/Sales_Summary_Test/sales_summary_output.csv
✓ Is successful: True
```

### Final Summary
```
================================================================================
WORKFLOW SUMMARY
================================================================================

Workflow Name: Sales_Summary_Test
Phase: completed
Started: 2025-10-16T14:30:00
Completed: 2025-10-16T14:31:07
Successful: True

Planner Summary:
  - Questions asked: 5
  - Plan approved: True

Coder Summary:
  - Code iterations: 1
  - Output path: ./data/outputs/Sales_Summary_Test/sales_summary_output.csv

Output Review Summary:
  - Output approved: True
  - Refinement iterations: 2
  - Feedback entries: 2

Refinement History:
  [1] 2025-10-16T14:30:45
      Feedback: I noticed the output needs some improvements...

  [2] 2025-10-16T14:30:58
      Feedback: Great! Now please also...

================================================================================
✅ TEST PASSED
================================================================================
```

## Configuration

### Customize Test Data

Edit the configuration in `test_orchestrator_with_output_review.py`:

```python
# Workflow configuration
TEST_WORKFLOW_NAME = "Your_Workflow_Name"
TEST_WORKFLOW_DESCRIPTION = "Your workflow description"
TEST_CSV_FILES = ["path/to/your/csv.csv"]
TEST_OUTPUT_FILENAME = "your_output.csv"

# Planner answers
PLANNER_AUTOMATED_ANSWERS = [
    "A",  # Modify as needed
    "B",
    "A",
    # ...
]

# Refinement feedback
OUTPUT_REFINEMENT_FEEDBACK = """
Your custom feedback here...
"""
```

### Adjust Iterations

```python
orchestrator = create_orchestrator(
    ...,
    max_planner_questions=10,      # Maximum Planner questions
    max_coder_iterations=3,        # Maximum code generation attempts
    code_execution_timeout=120,    # Code execution timeout (seconds)
)

# In refine_output call
result = await orchestrator.refine_output(
    feedback,
    max_refinement_iterations=3    # Maximum refinements (default: 3)
)
```

## Debugging

### Enable Verbose Logging

In the test script:

```python
setup_logging(log_level="DEBUG", pretty_print=True)
```

### Check Generated Files

After running the test:

```bash
# View generated code
ls -la ./storage/generated_code/

# View output CSV
ls -la ./data/outputs/Sales_Summary_Test/

# View workflow state
cat ./storage/workflows/Sales_Summary_Test_state.json
```

### Check Logs

```bash
# View logs
ls -la ./logs/

# Tail logs in real-time
tail -f ./logs/ira_builder.log
```

## Troubleshooting

### Issue: API Key Error

**Error**: `OPENAI_API_KEY not found`

**Solution**:
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Set environment variable
export OPENAI_API_KEY=your-key-here
```

### Issue: CSV Not Found

**Error**: `Test CSV not found: tests/fixtures/sample_csvs/FBL3N.csv`

**Solution**:
```bash
# Check if CSV exists
ls tests/fixtures/sample_csvs/

# Update TEST_CSV_FILES in script to correct path
```

### Issue: Refinement Fails

**Error**: `Refinement failed: Maximum refinement iterations (3) reached`

**Solution**: Either approve the current output or increase max iterations:
```python
result = await orchestrator.refine_output(
    feedback,
    max_refinement_iterations=5  # Increase limit
)
```

### Issue: Code Execution Timeout

**Error**: `Code execution timeout`

**Solution**: Increase timeout:
```python
orchestrator = create_orchestrator(
    ...,
    code_execution_timeout=300  # 5 minutes
)
```

## Next Steps

After successful test:

1. **Integrate with Frontend**:
   - Create API endpoints for each phase
   - Build UI components for output review
   - Add real-time progress indicators

2. **Add More Test Cases**:
   - Multi-file workflows
   - Complex business logic
   - Error scenarios
   - Edge cases

3. **Performance Testing**:
   - Large CSV files (>1GB)
   - Multiple concurrent workflows
   - Memory usage profiling

4. **Production Deployment**:
   - Containerize with Docker
   - Set up CI/CD pipeline
   - Configure monitoring and alerting
   - Deploy to cloud platform

## Support

For issues or questions:
- Check `current_progress.md` for system status
- Review `ORCHESTRATOR_USAGE.md` for API reference
- Review `ORCHESTRATOR_OUTPUT_REVIEW_EXAMPLE.md` for examples
