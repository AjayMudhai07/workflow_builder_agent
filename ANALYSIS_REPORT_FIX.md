# Analysis Report Generation Fix

## Problem Summary

The analysis report generation was producing CSV files instead of .txt files with analysis reports. The root cause was that the Coder agent's strong system instructions for workflow generation were overriding the analysis report template.

## Root Cause

The Coder agent is designed with strong system instructions for:
1. Using IRA preprocessing (ira.convert_date_column, ira.clean_strings_batch, etc.)
2. Implementing business logic transformations
3. Saving output as CSV files using `df.to_csv()`
4. Following a 3-part structure: Import → Load & Preprocess → Business Logic

When used for analysis report generation, these instructions would override the analysis template, causing it to generate workflow code instead of analysis code.

## Changes Made

### 1. File Type Check in Coder Agent
**File:** `ai/ira_builder/agents/coder.py` (lines 680-728)

Added check to skip CSV validation for non-CSV outputs like .txt files:
```python
is_csv_output = self.memory.output_path.endswith('.csv')

if is_csv_output:
    # Validate output CSV file
    output_validation = validate_output_dataframe(self.memory.output_path)
else:
    # For non-CSV outputs (e.g., .txt analysis reports), skip validation
    logger.info(f"✓ Non-CSV output file created: {self.memory.output_path}")
```

### 2. Enhanced Code Template with Warnings
**File:** `ai/ira_builder/orchestrator.py` (lines 1397-1536)

Updated the analysis report template to explicitly prohibit workflow operations:
- ❌ DO NOT use IRA preprocessing
- ❌ DO NOT use df.to_csv()
- ❌ DO NOT perform data transformations
- ✅ MUST use open() and write() for .txt output
- ✅ MUST build report as list of strings
- ✅ MUST analyze already-processed CSV data

### 3. Simplified Code Generation Prompt
**File:** `ai/ira_builder/orchestrator.py` (lines 1610-1662)

Created `simple_code_prompt` that:
- Explicitly states "THIS IS NOT A WORKFLOW CODE GENERATION TASK"
- Removes confusing context (Business Logic Plan, Generated Code references)
- Provides minimal, focused template
- Uses strong visual markers (⚠️ ❌ ✅) to emphasize key points

The simplified prompt is now used instead of passing the full Business Logic Plan, which was confusing the Coder into thinking it should regenerate workflow code.

## How to Test

1. **Start the backend** (if not already running):
   ```bash
   ./start_backend_visible.sh
   ```

2. **Create a new workflow** through the frontend that includes analysis report generation

3. **Wait for the workflow to complete** all phases including the Analysis Report Generation phase

4. **Check the output:**
   - The analysis report should be a `.txt` file, NOT a `.csv` file
   - The report should contain human-readable text analysis, NOT CSV data
   - The report should NOT include IRA preprocessing code
   - The report should NOT use `df.to_csv()`

5. **Look for these indicators in the generated code:**
   ✅ Should have: `import pandas as pd` (without `import ira`)
   ✅ Should have: `df = pd.read_csv(csv_files[0])`
   ✅ Should have: `report_lines = []`
   ✅ Should have: `with open(output_path, 'w') as f: f.write(report_content)`
   ❌ Should NOT have: `import ira`
   ❌ Should NOT have: `ira.convert_date_column`
   ❌ Should NOT have: `ira.clean_strings_batch`
   ❌ Should NOT have: `df.to_csv(output_file_path, index=False)`

## Expected Output

The analysis report should look like this:

```
================================================================================
WORKFLOW ANALYSIS REPORT
Workflow: [Workflow Name]
Description: [Workflow Description]
Generated on: 2025-10-22 16:45:30
================================================================================

1. EXCEPTION COUNT
--------------------------------------------------------------------------------
   Total Exceptions Identified: 1,234

2. KEY TRENDS AND PATTERNS
--------------------------------------------------------------------------------
   Top 3 Company Codes:
      1. 1000: 456 exceptions
      2. 2000: 345 exceptions
      3. 3000: 234 exceptions

... [more analysis sections]

================================================================================
END OF ANALYSIS
================================================================================
```

## Alternative Solution (If This Fails)

If the current fix doesn't work, consider these alternatives:

1. **Create a dedicated AnalysisReportAgent** - A new agent class specifically designed for analysis reports, without workflow generation instructions

2. **Use ChatAgent instead of Coder** - Bypass the Coder agent entirely and use a simple ChatAgent for analysis report generation

3. **Modify Coder's system instructions** - Add logic to detect analysis tasks and adjust behavior accordingly

## Files Modified

1. `/Users/ajay/Documents/workflow_builder_v4/ai/ira_builder/agents/coder.py`
2. `/Users/ajay/Documents/workflow_builder_v4/ai/ira_builder/orchestrator.py`

## Testing Checklist

- [ ] Backend starts successfully
- [ ] New workflow can be created
- [ ] Workflow completes Planning phase
- [ ] Workflow completes Coding phase
- [ ] Workflow completes Output Review phase
- [ ] Workflow completes Analysis Report Generation phase
- [ ] Analysis report file is `.txt` (not `.csv`)
- [ ] Analysis report contains text analysis (not CSV data)
- [ ] Generated analysis code does NOT use IRA preprocessing
- [ ] Generated analysis code does NOT use `df.to_csv()`
- [ ] Generated analysis code uses `open()` and `write()` for output

## Troubleshooting

If the issue persists:

1. **Check the generated analysis code** in storage/generated_code/ directory
2. **Look for these patterns** that indicate the fix didn't work:
   - `import ira`
   - `ira.convert_date_column`
   - `df.to_csv(output_file_path, index=False)`
3. **Check backend logs** for any errors during analysis report generation
4. **Verify the simple_code_prompt** is being used (look for the ⚠️ warnings in logs)

## Next Steps

After testing, if the fix works:
- ✅ Mark this issue as resolved
- ✅ Update documentation with analysis report generation details
- ✅ Consider adding automated tests for analysis report generation

If the fix doesn't work:
- ❌ Implement Alternative Solution #1 (dedicated AnalysisReportAgent)
- ❌ Document specific failure patterns
- ❌ Investigate Coder agent's system instructions further
