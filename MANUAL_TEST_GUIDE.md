# Manual Testing Guide

## Quick Start

```bash
# 1. Make sure you have your OpenAI API key
export OPENAI_API_KEY=sk-your-key-here

# 2. Run the manual test script
python test_manual.py
```

## What to Expect

### Step 1: Configuration (30 seconds)

The script will ask you:

```
1. Workflow Name (e.g., 'Sales_Analysis'):
   → Enter: My_Test_Workflow

2. Workflow Description (What should this workflow do?)
   → Enter: Analyze sales data and calculate totals by vendor

3. CSV File Path
   Available test file: tests/fixtures/sample_csvs/FBL3N.csv
   → Press Enter to use default

4. Output Filename (e.g., 'result.csv'):
   → Enter: my_test_output.csv
```

### Step 2: Planning Phase (2-3 minutes)

The Planner will ask you questions. Example conversation:

```
Planner's Question:
--------------------------------------------------------------------------------
Hello! I'll help you analyze your sales data.

Based on the FBL3N.csv file structure, I can see columns like:
- Document_No, Posting_Date, Document_Date
- Vendor_No, Vendor_Name
- Amount, Currency

Question 1: What is the main goal of this analysis?
A) Calculate totals by vendor
B) Find specific transactions
C) Date-based analysis
D) Other (please specify)
--------------------------------------------------------------------------------

Your answer: A

✓ Question 1 answered

[... more questions ...]

✅ Business Logic Plan has been generated!
```

**Tips for answering**:
- Read each question carefully
- Choose the option that best matches your goal (A, B, C, D)
- Or type your own detailed answer
- The Planner will ask 3-5 questions typically

### Step 3: Plan Review (1 minute)

Review the generated plan:

```
================================================================================
                          PHASE 2: PLAN REVIEW
================================================================================

Here is the Business Logic Plan:

--------------------------------------------------------------------------------
Business Logic Plan
--------------------------------------------------------------------------------

# Business Logic Plan

## **Workflow Purpose**
Analyze sales data from FBL3N.csv and calculate totals by vendor

## **Required Files**
1. FBL3N.csv
   - Columns: Document_No, Vendor_No, Vendor_Name, Amount, ...

## **Business Logic**
1. Load FBL3N data
2. Apply IRA preprocessing (dates, strings, numerics)
3. Group by Vendor_Name
4. Calculate total Amount per vendor
5. Sort by total Amount descending

## **Output DataFrame Structure**
- Vendor_Name (string)
- Total_Amount (numeric)
- Transaction_Count (numeric)

--------------------------------------------------------------------------------

What would you like to do?
  1. Approve and generate code
  2. Request changes to the plan
  3. Cancel

Your choice (1/2/3): 1

✓ Plan approved! Moving to code generation...
```

### Step 4: Code Generation (30-60 seconds)

Watch as code is generated and executed:

```
================================================================================
                    PHASE 3: CODE GENERATION & EXECUTION
================================================================================

Generating Python code and executing it...
This may take 30-60 seconds...

✅ Code generated and executed successfully!

✓ Phase: output_review
✓ Code iterations: 1
✓ Output file: ./data/outputs/My_Test_Workflow/my_test_output.csv
✓ Code saved to: ./storage/generated_code/My_Test_Workflow_20251016_143022.py

--------------------------------------------------------------------------------
Output Preview (first 10 rows)
--------------------------------------------------------------------------------
   Vendor_Name  Total_Amount  Transaction_Count
0  ABC Corp     125000.00     45
1  XYZ Ltd      98500.00      32
2  Acme Inc     75200.00      28
3  Global Co    62300.00      21
4  Tech Store   54100.00      19
...

--------------------------------------------------------------------------------
Output Summary
--------------------------------------------------------------------------------
  Rows: 15
  Columns: 3
  Column Names: Vendor_Name, Total_Amount, Transaction_Count
```

### Step 5: Output Review (1-2 minutes per refinement)

Review and refine the output:

```
================================================================================
                          PHASE 4: OUTPUT REVIEW
================================================================================

The code has been executed and output has been generated.
You can now review the output and request changes if needed.

What would you like to do?
  1. Approve output and complete workflow ✅
  2. Request changes to the output 🔄
     (Refinements used: 0/3)

Your choice (1/2): 2
```

#### Refinement Example 1:

```
Describe what changes you'd like to make to the output.
Examples:
  - Add a new column showing percentages
  - Sort by amount in descending order
  - Filter to only show records above 1000
  - Add average calculation per group

Your feedback: Add a column showing each vendor's percentage of total sales

🔄 Refining output (attempt 1/3)...
This may take 30-60 seconds...

✅ Output refined successfully!

✓ Refinement iteration: 1
✓ Updated code saved to: ./storage/generated_code/My_Test_Workflow_20251016_143045.py
✓ Updated output: ./data/outputs/My_Test_Workflow/my_test_output.csv

--------------------------------------------------------------------------------
Updated Output Preview
--------------------------------------------------------------------------------
   Vendor_Name  Total_Amount  Transaction_Count  Percentage
0  ABC Corp     125000.00     45                23.5%
1  XYZ Ltd      98500.00      32                18.5%
2  Acme Inc     75200.00      28                14.1%
...
```

#### Refinement Example 2:

```
What would you like to do?
  1. Approve output and complete workflow ✅
  2. Request changes to the output 🔄
     (Refinements used: 1/3)

Your choice (1/2): 2

Your feedback: Also add the average transaction amount per vendor

🔄 Refining output (attempt 2/3)...

✅ Output refined successfully!

--------------------------------------------------------------------------------
Updated Output Preview
--------------------------------------------------------------------------------
   Vendor_Name  Total_Amount  Transaction_Count  Percentage  Avg_Amount
0  ABC Corp     125000.00     45                23.5%       2777.78
1  XYZ Ltd      98500.00      32                18.5%       3078.13
2  Acme Inc     75200.00      28                14.1%       2685.71
...
```

### Step 6: Final Approval

```
What would you like to do?
  1. Approve output and complete workflow ✅
  2. Request changes to the output 🔄
     (Refinements used: 2/3)

Your choice (1/2): 1

✓ Approving output and completing workflow...

================================================================================
                          WORKFLOW COMPLETED!
================================================================================

✅ SUCCESS!

✓ Execution time: 187.45 seconds
✓ Output file: ./data/outputs/My_Test_Workflow/my_test_output.csv
✓ Workflow status: Completed

--------------------------------------------------------------------------------
Workflow Summary
--------------------------------------------------------------------------------
Workflow Name: My_Test_Workflow
Phase: completed
Started: 2025-10-16T14:30:00
Completed: 2025-10-16T14:33:07
Success: True

Planner Summary:
  - Questions asked: 4
  - Plan approved: True

Coder Summary:
  - Code iterations: 1
  - Output path: ./data/outputs/My_Test_Workflow/my_test_output.csv

Output Review Summary:
  - Output approved: True
  - Refinement iterations: 2

Refinement History:
  [1] Add a column showing each vendor's percentage of total sales
  [2] Also add the average transaction amount per vendor

================================================================================
                    ✅ TEST COMPLETED SUCCESSFULLY
================================================================================
```

## Common Refinement Requests

### Add Columns
```
Your feedback: Add columns for:
1. Average transaction amount
2. Maximum transaction amount
3. Minimum transaction amount
```

### Filtering
```
Your feedback: Filter to only show vendors with total amount > 50000
```

### Sorting
```
Your feedback: Sort by Total_Amount in descending order, then by Vendor_Name alphabetically
```

### Calculations
```
Your feedback: Add a cumulative sum column showing running total of amounts
```

### Date Operations
```
Your feedback: Add columns showing:
1. Earliest transaction date per vendor
2. Latest transaction date per vendor
3. Number of days between first and last transaction
```

### Grouping Changes
```
Your feedback: Instead of grouping by vendor, group by both vendor and currency
```

### Column Renaming
```
Your feedback: Rename columns to be more descriptive:
- Total_Amount → Total_Sales_Amount
- Transaction_Count → Number_of_Transactions
```

## Tips for Best Results

### 1. Be Specific
❌ Bad: "Make it better"
✅ Good: "Add a percentage column and sort by amount descending"

### 2. One Change at a Time (or group related changes)
❌ Bad: "Add percentage, sort, filter, rename, and change grouping"
✅ Good (Refinement 1): "Add percentage column and sort by amount"
✅ Good (Refinement 2): "Filter to show only amounts > 1000"

### 3. Use Clear Column Names
❌ Bad: "Add that thing we discussed"
✅ Good: "Add Average_Amount column showing average per vendor"

### 4. Reference Existing Columns
✅ Good: "Calculate percentage using Total_Amount / sum of all Total_Amount"

## Keyboard Shortcuts

- **Ctrl+C**: Cancel test at any time (state is saved)
- **Enter**: Use default values during configuration

## Output Files

After completion, check these locations:

```bash
# Generated code (all versions)
ls -la ./storage/generated_code/

# Output CSV
cat ./data/outputs/My_Test_Workflow/my_test_output.csv

# Workflow state (complete history)
cat ./storage/workflows/My_Test_Workflow_state.json
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
```bash
# Check .env file
cat .env

# Add key if missing
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### Issue: "CSV file not found"
```bash
# Check file exists
ls tests/fixtures/sample_csvs/FBL3N.csv

# Or use absolute path
# Path: /full/path/to/your/file.csv
```

### Issue: Refinement fails
- Try simplifying your request
- Make sure column names are spelled correctly
- Check if request is achievable with the data

### Issue: Code execution timeout
- Default timeout is 120 seconds
- For large CSV files, this might not be enough
- The orchestrator will retry automatically

## Example Test Session (5 minutes)

```bash
# Start
python test_manual.py

# Configuration (30s)
Workflow Name: Quick_Test
Description: Calculate vendor totals
CSV: [press Enter for default]
Output: test_output.csv

# Planning (90s)
Q1: What's the goal? → Answer: A
Q2: Which columns? → Answer: A
Q3: Any filters? → Answer: B
Q4: Output format? → Answer: A
✅ Plan generated

# Plan Review (15s)
Review plan... → Choice: 1 (Approve)

# Code Generation (45s)
Generating code... ✅ Success
Shows output preview

# Output Review (60s)
Choice: 2 (Refine)
Feedback: Add percentage column
✅ Refined

# Final Approval (5s)
Choice: 1 (Approve)
✅ Completed!

Total time: ~4-5 minutes
```

## Next Steps After Testing

1. **Review Generated Code**:
   ```bash
   code ./storage/generated_code/My_Test_Workflow_*.py
   ```

2. **Check Output Data**:
   ```bash
   open ./data/outputs/My_Test_Workflow/my_test_output.csv
   ```

3. **Review Workflow State**:
   ```bash
   cat ./storage/workflows/My_Test_Workflow_state.json | jq '.'
   ```

4. **Test with Your Own Data**:
   - Replace CSV path with your file
   - Describe your analysis goal
   - Follow the same process

## Support

If you encounter issues:
- Check logs in `./logs/` directory
- Review `IMPLEMENTATION_SUMMARY.md` for features
- Check `ORCHESTRATOR_OUTPUT_REVIEW_EXAMPLE.md` for examples
- Review `current_progress.md` for system status

---

**Ready to test?**

```bash
python test_manual.py
```

Have fun! 🚀
