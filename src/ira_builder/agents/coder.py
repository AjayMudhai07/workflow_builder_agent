"""
Coder Agent (IRA-Coder) Implementation

This agent generates production-ready Python pandas code based on approved
Business Logic Plans, executes the code, handles errors, and iterates
until successful execution.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework._memory import ContextProvider, Context
from agent_framework._types import ChatMessage

from ira_builder.tools.code_executor_tools import (
    execute_python_code,
    validate_python_syntax,
    extract_code_from_markdown,
    preview_dataframe,
    validate_output_dataframe,
    analyze_execution_error,
    get_dataframe_summary
)
from ira_builder.tools.csv_tools import analyze_csv_structure, get_csv_summary
from ira_builder.utils.logger import get_logger
from ira_builder.utils.config import get_config

logger = get_logger(__name__)

# =============================================================================
# CODER AGENT INSTRUCTIONS
# =============================================================================

CODER_INSTRUCTIONS = """
You are IRA-Coder, an expert Python developer specializing in data analysis with pandas and the IRA preprocessing library.

## Your Role

Generate clean, efficient, production-ready Python code based on approved Business Logic Plans.
Your code will be executed automatically, so it must be correct, robust, and handle edge cases.

## Input You Will Receive

1. **Business Logic Plan**: A comprehensive document describing:
   - Workflow purpose and objectives
   - Required files with exact column names (in JSON format)
   - Business requirements from user Q&A
   - Step-by-step business logic
   - Expected output dataframe structure

2. **CSV File Paths**: Absolute paths to input CSV files
3. **Output Path**: Where to save the result CSV

## Code Generation Guidelines

### 1. Code Structure (MANDATORY - 3 PARTS)

Your code MUST follow this exact three-part structure:

**PART 1: IMPORTS AND FILE PATHS**
```python
# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = csv_files[0]
vendor_master_path = csv_files[1]
output_file_path = output_path
```

**CRITICAL RULES for File Paths:**
1. **Variable names MUST match CSV filenames** from Business Logic Plan:
   - "FBL3N.csv" → `fbl3n_path = csv_files[0]`
   - "Vendor_Master.csv" → `vendor_master_path = csv_files[1]`
   - "BSEG.csv" → `bseg_path = csv_files[2]`

2. **ONLY include file path variables for files mentioned in Business Logic Plan**
   - If Plan mentions 1 file → ONLY create 1 file path variable
   - If Plan mentions 2 files → ONLY create 2 file path variables
   - Do NOT create variables for files not required

3. **Naming convention**: Use lowercase with underscores matching the filename

4. **CRITICAL - Output Path Variable**:
   - ✅ CORRECT: `output_file_path = output_path` (using the placeholder variable)
   - ❌ WRONG: `output_file_path = 'data/outputs/...'` (hardcoded string path)
   - The variable `output_path` is provided to you - YOU MUST USE IT AS-IS
   - DO NOT write the actual path as a string - use the variable reference `output_path`

**PART 2: LOAD DATA & IRA PREPROCESSING**
```python
# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Posting_Date', 'Document_Date']
SAME_COLS_FBLSN = ['Document_No', 'Vendor_No']
UPPER_COLS_FBLSN = ['Status', 'Currency']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = ['Vendor_Name']
NUMERIC_COLS_FBLSN = ['Amount', 'Tax_Amount']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, SAME_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, UPPER_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")
```

**PART 3: BUSINESS LOGIC**
```python
# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Filter records where Amount > 1000
result_df = df_fbl3n[df_fbl3n['Amount'] > 1000].copy()
print(f"✓ Filtered {len(result_df):,} records with Amount > 1000")

# Calculate total amount
result_df['Total_Amount'] = result_df['Amount'] * result_df['Quantity']
print(f"✓ Calculated Total_Amount")

# Group by Vendor_Name and aggregate
result_df = result_df.groupby('Vendor_Name').agg({
    'Amount': 'sum',
    'Quantity': 'sum'
}).reset_index()
print(f"✓ Aggregated by Vendor_Name: {len(result_df):,} vendors")

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")
```

### 2. Best Practices (FOLLOW STRICTLY)

**IRA Preprocessing (CRITICAL):**
- ✅ ALWAYS import ira library at the top
- ✅ ALWAYS categorize columns into: DATE_COLS, SAME_COLS, UPPER_COLS, LOWER_COLS, TITLE_COLS, NUMERIC_COLS
- ✅ ALWAYS apply IRA preprocessing in this order:
  1. Date columns: `ira.convert_date_column()`
  2. String columns: `ira.clean_strings_batch()` (by case type)
  3. Numeric columns: `ira.clean_numeric_batch()`
- ✅ Use descriptive DataFrame names (df_sales, df_vendor, not df1, df2) when multiple files
- ✅ For multiple DataFrames, use suffix numbers: DATE_COLS_1, DATE_COLS_2, etc.

**Column Categorization Guide:**
- **DATE_COLS**: All date/datetime columns → use `ira.convert_date_column()`
- **SAME_COLS**: IDs, codes, reference numbers → preserve original case
- **UPPER_COLS**: Status, priority, country codes → uppercase for consistency
- **LOWER_COLS**: Emails, websites, URLs → lowercase
- **TITLE_COLS**: Names (vendor, customer, employee) → title case
- **NUMERIC_COLS**: Amounts, quantities, prices → currency-aware cleaning
- **Boolean columns**: DO NOT include in any cleaning lists (skip them entirely)

**File Path Variables:**
- ✅ Variable names MUST match CSV filenames: FBL3N.csv → `fbl3n_path`, Vendor_Master.csv → `vendor_master_path`
- ✅ Use lowercase with underscores for file path variables
- ✅ DataFrame names should match file: `fbl3n_path` → `df_fbl3n`
- ✅ Column category suffix should match file: `DATE_COLS_FBLSN`, `NUMERIC_COLS_FBLSN`
- ✅ Use `output_file_path` for the output path variable

**Data Loading:**
- ✅ Always use `low_memory=False` in pd.read_csv()
- ✅ Print confirmation messages with :, format for row counts
- ✅ Use descriptive DataFrame names matching the file: df_fbl3n, df_vendor_master
- ✅ NO unnecessary try-except blocks - keep code clean and production-ready
- ✅ NO placeholder comments - write actual implementation

**Column Handling:**
- ✅ ALWAYS verify columns exist before using them
- ✅ Build required_columns list from all column category lists
- ✅ Use .copy() when creating filtered dataframes to avoid SettingWithCopyWarning
- ✅ Be case-sensitive with column names (match exactly as in Business Logic Plan)

**Data Type Conversions:**
- ✅ Use IRA library for ALL date/string/numeric conversions (NOT pandas)
- ✅ After IRA preprocessing, dates are datetime64, strings are object, numerics are float64
- ✅ IRA handles conversion errors gracefully (no need for errors='coerce')

**Business Logic Implementation:**
- ✅ Implement requirements in the exact order specified
- ✅ Add a comment before each major step explaining the business rule
- ✅ Print status after each operation (e.g., "✓ Applied filter: 1,234 rows")
- ✅ Use :, formatting for numbers in print statements

**Error Prevention:**
- ✅ Check for empty dataframes before operations
- ✅ Use .reset_index() after groupby operations
- ✅ Handle potential division by zero
- ✅ IRA preprocessing handles NaN values automatically

**Output:**
- ✅ Final dataframe MUST have columns specified in Business Logic Plan
- ✅ MUST save to the exact output_path provided
- ✅ MUST use index=False in to_csv()

### 3. Common Pitfalls to AVOID

❌ **DON'T** use pd.to_datetime() or pd.to_numeric() - use IRA preprocessing instead
❌ **DON'T** clean boolean columns with IRA (exclude them from all lists)
❌ **DON'T** forget to categorize ALL columns used in the workflow
❌ **DON'T** skip IRA preprocessing - it's mandatory for all workflows
❌ **DON'T** mix up column category suffixes (use _1, _2, _3 consistently)
❌ **DON'T** iterate over rows (use vectorized operations)
❌ **DON'T** use df['col'] = value without .copy() on filtered dataframes
❌ **DON'T** assume columns exist without checking
❌ **DON'T** forget to reset_index() after groupby
❌ **DON'T** use hardcoded file paths (use the provided variables)
❌ **DON'T** redefine csv_files or output_path - they are already provided for you!
❌ **DON'T** write `output_file_path = 'string/path'` - MUST use `output_file_path = output_path` variable reference

### 4. When Execution Fails

If your code fails:

1. **Analyze the error message carefully**
   - Is it a column name mismatch? Check spelling and case
   - Is it a data type issue? Add proper conversions
   - Is it a missing file? Check the file path

2. **Fix the issue and regenerate COMPLETE code**
   - Don't just provide a snippet
   - Provide the full executable code
   - Include all sections (load, validate, logic, save)

3. **Add defensive checks**
   - If KeyError: Add column existence check
   - If ValueError: Add data type conversion
   - If empty result: Add data quality checks

## Output Format

ALWAYS wrap your code in markdown code blocks:

```python
# Your complete code here
```

## Important Reminders

1. **Production Code Quality**: Generate CLEAN, MINIMAL code - NO unnecessary comments, NO try-except for every operation
2. **File Path Variables**: MUST use actual CSV filenames (fbl3n_path, vendor_master_path, NOT file1_path, file2_path)
3. **DataFrame Names**: MUST match files (df_fbl3n, df_vendor_master, NOT df1, df2)
4. **Column Categories**: Suffix MUST match file (DATE_COLS_FBLSN, NOT DATE_COLS_1)
5. **Output Path**: CRITICAL - MUST write `output_file_path = output_path` (variable reference), NOT `output_file_path = 'data/outputs/...'` (string)
6. **Print Statements**: Use them strategically for major steps, NOT for every line
7. **NEVER use placeholder comments** like "# Add code here" - write actual implementation
8. **Business Logic**: Implement based on Business Logic Plan requirements

## Success Criteria

Your code is successful when:
- ✅ It executes without errors
- ✅ It produces an output CSV file
- ✅ The output has the correct structure (columns match Business Logic Plan)
- ✅ The output contains meaningful data (not empty unless expected)
- ✅ All business rules are correctly implemented

You are an expert - write code that works on the first try!
"""

# =============================================================================
# CODER AGENT STATE MANAGEMENT
# =============================================================================

class CoderMemory(ContextProvider):
    """
    Context provider that maintains code generation state and history.

    This keeps track of:
    - Business Logic Plan
    - CSV file information
    - Previous code attempts
    - Execution errors
    - Iteration count
    """

    def __init__(self):
        self.business_logic_plan: Optional[str] = None
        self.csv_filepaths: List[str] = []
        self.csv_metadata: List[Dict[str, Any]] = []
        self.output_path: Optional[str] = None
        self.workflow_name: Optional[str] = None

        # Code generation history
        self.code_attempts: List[Dict[str, Any]] = []
        self.current_code: Optional[str] = None
        self.execution_results: List[Dict[str, Any]] = []

        # Iteration tracking
        self.iteration_count: int = 0
        self.max_iterations: int = 5

    def set_business_logic_plan(
        self,
        business_logic_plan: str,
        csv_filepaths: List[str],
        output_path: str,
        workflow_name: str
    ):
        """Set the business logic plan and related information."""
        self.business_logic_plan = business_logic_plan
        self.csv_filepaths = csv_filepaths
        self.output_path = output_path
        self.workflow_name = workflow_name

        # Analyze CSV files to get metadata
        self.csv_metadata = []
        for filepath in csv_filepaths:
            try:
                metadata = analyze_csv_structure(filepath)
                self.csv_metadata.append(metadata)
                logger.info(f"Loaded CSV metadata: {metadata['filename']}")
            except Exception as e:
                logger.error(f"Error analyzing CSV {filepath}: {str(e)}")

    def add_code_attempt(self, code: str, execution_result: Dict[str, Any]):
        """Record a code generation attempt and its result."""
        self.iteration_count += 1

        attempt = {
            "iteration": self.iteration_count,
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "execution_result": execution_result
        }

        self.code_attempts.append(attempt)
        self.current_code = code
        self.execution_results.append(execution_result)

        logger.info(f"Recorded code attempt #{self.iteration_count}: {execution_result['status']}")

    def get_previous_failures(self) -> str:
        """Get a summary of previous failed attempts for context."""
        if not self.code_attempts:
            return ""

        failures = [
            attempt for attempt in self.code_attempts
            if attempt['execution_result']['status'] != 'success'
        ]

        if not failures:
            return ""

        summary_parts = ["**Previous Failed Attempts:**\n"]

        for attempt in failures[-2:]:  # Last 2 failures only
            summary_parts.append(f"\n**Attempt #{attempt['iteration']}:**")
            result = attempt['execution_result']
            summary_parts.append(f"- Status: {result['status']}")
            if result.get('error_message'):
                summary_parts.append(f"- Error: {result['error_message']}")

        summary_parts.append("\n**Learn from these errors and avoid repeating them!**\n")

        return "\n".join(summary_parts)

    async def invoking(self, messages, **kwargs):
        """Inject context before each agent invocation."""
        if not self.business_logic_plan:
            return Context()

        context_parts = []

        # Add business logic plan
        context_parts.append("=" * 80)
        context_parts.append("BUSINESS LOGIC PLAN")
        context_parts.append("=" * 80)
        context_parts.append(self.business_logic_plan)
        context_parts.append("")

        # Add CSV file information
        context_parts.append("=" * 80)
        context_parts.append("CSV FILE INFORMATION")
        context_parts.append("=" * 80)

        for i, metadata in enumerate(self.csv_metadata):
            context_parts.append(f"\n**File {i+1}: {metadata['filename']}**")
            context_parts.append(f"- Path: {metadata['path']}")
            context_parts.append(f"- Rows: {metadata['row_count']:,}")
            context_parts.append(f"- Columns ({len(metadata['columns'])}): {', '.join(metadata['columns'])}")
            context_parts.append(f"- Data Types: {json.dumps(metadata['dtypes'], indent=2)}")

        context_parts.append("")

        # Add output path
        context_parts.append("=" * 80)
        context_parts.append("OUTPUT CONFIGURATION")
        context_parts.append("=" * 80)
        context_parts.append(f"Output Path: {self.output_path}")
        context_parts.append("")

        # Add previous failures if any
        failures_summary = self.get_previous_failures()
        if failures_summary:
            context_parts.append(failures_summary)

        # Add iteration warning if nearing max
        if self.iteration_count >= self.max_iterations - 1:
            context_parts.append("⚠️  WARNING: This is your last attempt! Make it count!\n")

        return Context(instructions="\n".join(context_parts))

    async def invoked(self, **kwargs):
        """Called after agent invocation."""
        pass

    async def thread_created(self, **kwargs):
        """Called when thread is created."""
        pass

    def reset(self):
        """Reset the memory state."""
        self.code_attempts = []
        self.current_code = None
        self.execution_results = []
        self.iteration_count = 0
        logger.info("Coder memory reset")


# =============================================================================
# CODER AGENT CLASS
# =============================================================================

class CoderAgent:
    """
    Coder Agent for generating and executing Python code based on Business Logic Plans.

    This agent:
    1. Reads Business Logic Plan
    2. Generates Python pandas code
    3. Validates syntax
    4. Executes code with timeout
    5. Analyzes errors if execution fails
    6. Iterates to fix issues (up to max_iterations)
    7. Returns execution results
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_iterations: int = 5,
        execution_timeout: int = 120
    ):
        """
        Initialize Coder Agent.

        Args:
            model: OpenAI model to use (default: gpt-4o)
            temperature: Temperature for code generation (default: 0.3 - more deterministic)
            max_iterations: Maximum code generation attempts (default: 5)
            execution_timeout: Timeout for code execution in seconds (default: 120)
        """
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.execution_timeout = execution_timeout

        # Create chat client
        config = get_config()
        chat_client = OpenAIChatClient(
            model_id=model,
            # temperature handled in ChatAgent
        )

        # Create memory provider
        self.memory = CoderMemory()
        self.memory.max_iterations = max_iterations

        # Create agent
        self.agent = ChatAgent(
            name="IRA-Coder",
            chat_client=chat_client,
            instructions=CODER_INSTRUCTIONS,
            tools=[
                # Code validation and execution tools
                validate_python_syntax,
                # Note: We don't give the agent direct access to execute_python_code
                # We control execution in the workflow
            ],
            context_providers=[self.memory]
        )

        # Thread for conversation
        self.thread = None

        # State
        self.workflow_name: Optional[str] = None
        self.work_dir: Optional[Path] = None

        logger.info(f"Coder Agent initialized with model: {model}")

    async def initialize_workflow(
        self,
        workflow_name: str,
        business_logic_plan: str,
        csv_filepaths: List[str],
        output_filename: str = "result.csv"
    ) -> Dict[str, Any]:
        """
        Initialize the coding workflow with Business Logic Plan.

        Args:
            workflow_name: Name of the workflow
            business_logic_plan: The approved Business Logic Plan from Planner Agent
            csv_filepaths: List of absolute paths to CSV files
            output_filename: Name for output file (default: result.csv)

        Returns:
            Dictionary with initialization status
        """
        logger.info(f"Initializing Coder Agent workflow: {workflow_name}")

        self.workflow_name = workflow_name

        # Create work directory
        self.work_dir = Path("./data/outputs") / workflow_name.replace(" ", "_")
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Set output path
        output_path = str(self.work_dir / output_filename)

        # Initialize memory
        self.memory.set_business_logic_plan(
            business_logic_plan=business_logic_plan,
            csv_filepaths=csv_filepaths,
            output_path=output_path,
            workflow_name=workflow_name
        )

        # Create conversation thread
        self.thread = self.agent.get_new_thread()

        logger.info(f"Workflow initialized. Output will be saved to: {output_path}")

        return {
            "status": "initialized",
            "workflow_name": workflow_name,
            "work_dir": str(self.work_dir),
            "output_path": output_path,
            "csv_files": csv_filepaths
        }

    async def generate_and_execute_code(self) -> Dict[str, Any]:
        """
        Generate code from Business Logic Plan and execute it.

        This is the main workflow:
        1. Generate code
        2. Validate syntax
        3. Execute code
        4. Check output
        5. If errors, analyze and retry (up to max_iterations)

        Returns:
            Dictionary with final execution result and code
        """
        logger.info("Starting code generation and execution workflow")

        if not self.memory.business_logic_plan:
            return {
                "status": "error",
                "error": "No Business Logic Plan provided. Call initialize_workflow first."
            }

        # Iterative code generation loop
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"=== Code Generation Attempt {iteration}/{self.max_iterations} ===")

            # Step 1: Generate code
            code_result = await self._generate_code(iteration)

            if code_result['status'] == 'error':
                logger.error(f"Code generation failed: {code_result.get('error')}")
                continue

            generated_code = code_result['code']

            # Step 2: Validate syntax
            syntax_check = validate_python_syntax(generated_code)

            if not syntax_check['valid']:
                logger.warning(f"Syntax validation failed: {syntax_check['error']}")

                # Ask agent to fix syntax error
                await self._request_syntax_fix(syntax_check, generated_code)
                continue

            logger.info("✓ Syntax validation passed")

            # Step 3: Execute code
            exec_result = await self._execute_code(generated_code)

            # Record this attempt
            self.memory.add_code_attempt(generated_code, exec_result)

            # Step 4: Check if successful
            if exec_result['status'] == 'success':
                logger.info("✓ Code executed successfully!")

                # Validate output file
                output_validation = validate_output_dataframe(self.memory.output_path)

                if output_validation['valid']:
                    logger.info(f"✓ Output file validated: {output_validation['row_count']} rows")

                    # Get preview and summary
                    preview = preview_dataframe(self.memory.output_path, rows=10)
                    summary = get_dataframe_summary(self.memory.output_path)

                    # Replace csv_files and output_path with absolute paths in final code
                    final_code = self._replace_paths_in_code(generated_code)

                    return {
                        "status": "success",
                        "code": final_code,  # Return code with absolute paths
                        "execution_result": exec_result,
                        "output_path": self.memory.output_path,
                        "output_validation": output_validation,
                        "output_preview": preview,
                        "output_summary": summary,
                        "iterations": iteration
                    }
                else:
                    logger.warning(f"Output validation failed: {output_validation['error']}")
                    # Request fix for output issues
                    await self._request_output_fix(output_validation, generated_code)
                    continue

            else:
                # Execution failed - analyze error and request fix
                logger.warning(f"Execution failed: {exec_result['error_message']}")
                await self._request_execution_fix(exec_result, generated_code)
                continue

        # Max iterations reached without success
        logger.error(f"Failed to generate working code after {self.max_iterations} attempts")

        return {
            "status": "error",
            "error": f"Failed to generate working code after {self.max_iterations} attempts",
            "iterations": self.max_iterations,
            "last_code": self.memory.current_code,
            "last_execution_result": self.memory.execution_results[-1] if self.memory.execution_results else None,
            "all_attempts": self.memory.code_attempts
        }

    async def _generate_code(self, iteration: int) -> Dict[str, Any]:
        """Generate code from Business Logic Plan."""
        try:
            if iteration == 1:
                prompt = """
Generate complete Python pandas code to implement the Business Logic Plan above.

Remember:
- Follow the mandatory code structure (3 parts)
- CRITICAL: In Part 1, write `output_file_path = output_path` (use variable reference, NOT a hardcoded string path)
- CRITICAL: Use `csv_files[0]`, `csv_files[1]` etc. for input CSV path variables
- Include all sections (Load, Validate, Convert, Logic, Output, Save)
- Print status messages for each step
- Handle errors gracefully
- Save output to the exact path specified

Provide ONLY the code wrapped in ```python ... ``` markdown block.
"""
            else:
                prompt = f"""
The previous code attempt failed. Generate CORRECTED code that fixes the issues.

Iteration {iteration}/{self.max_iterations}

Provide the COMPLETE corrected code (not just a snippet).
"""

            # Get response from agent
            response = await self.agent.run(prompt, thread=self.thread)

            # Extract code from response
            code = extract_code_from_markdown(response.text)

            logger.info(f"Generated code: {len(code)} characters")

            return {
                "status": "success",
                "code": code,
                "raw_response": response.text
            }

        except Exception as e:
            logger.error(f"Error generating code: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def _replace_paths_in_code(self, code: str) -> str:
        """
        Replace csv_files[i] and output_path references with actual absolute paths.
        This makes the generated code standalone and production-ready.
        """
        # Convert CSV file paths to absolute
        csv_files_abs = [str(Path(fp).resolve()) for fp in self.memory.csv_filepaths]

        # Convert output_path to absolute path
        output_path_abs = str(Path(self.memory.output_path).resolve())

        # Replace csv_files[i] references with actual absolute paths
        modified_code = code
        for i, abs_path in enumerate(csv_files_abs):
            modified_code = modified_code.replace(
                f'csv_files[{i}]',
                f'"{abs_path}"'
            )

        # Replace output_path with actual absolute path
        modified_code = modified_code.replace(
            'output_path',
            f'"{output_path_abs}"'
        )

        return modified_code

    async def _execute_code(self, code: str) -> Dict[str, Any]:
        """Execute the generated code."""
        logger.info(f"Executing code in work directory: {self.work_dir}")

        try:
            # Replace csv_files[i] and output_path with absolute paths for execution
            modified_code = self._replace_paths_in_code(code)

            # Execute the modified code (now with absolute paths embedded)
            result = await execute_python_code(
                code=modified_code,
                work_dir=str(self.work_dir),
                timeout=self.execution_timeout
            )

            return result

        except Exception as e:
            logger.error(f"Error executing code: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "exit_code": 1,
                "output": str(e),
                "error_message": f"Execution exception: {str(e)}"
            }

    async def _request_syntax_fix(self, syntax_check: Dict[str, Any], code: str):
        """Ask agent to fix syntax errors."""
        error_msg = f"""
❌ SYNTAX ERROR DETECTED

Your code has a syntax error and cannot be executed.

Error: {syntax_check['error']}
Line: {syntax_check['line']}
{f"Text: {syntax_check['text']}" if syntax_check.get('text') else ""}

Please fix the syntax error and provide the COMPLETE corrected code.
"""

        await self.agent.run(error_msg, thread=self.thread)

    async def _request_execution_fix(self, exec_result: Dict[str, Any], code: str):
        """Ask agent to fix execution errors."""
        # Analyze the error
        error_analysis = analyze_execution_error(exec_result['output'], code)

        error_msg = f"""
❌ EXECUTION ERROR

Your code failed during execution.

Status: {exec_result['status']}
Exit Code: {exec_result['exit_code']}

Error Type: {error_analysis['error_type']}
Error Message: {error_analysis['error_message']}
{f"Line Number: {error_analysis['line_number']}" if error_analysis['line_number'] else ""}

Suggested Fix: {error_analysis['suggested_fix']}

Error Output:
{exec_result['output'][-500:]}  # Last 500 chars

Please fix the error and provide the COMPLETE corrected code.
Do NOT just provide a snippet - provide the full working code.
"""

        await self.agent.run(error_msg, thread=self.thread)

    async def _request_output_fix(self, validation: Dict[str, Any], code: str):
        """Ask agent to fix output validation issues."""
        error_msg = f"""
❌ OUTPUT VALIDATION FAILED

Your code executed without errors, but the output file has issues.

Problem: {validation['error']}
Expected output path: {self.memory.output_path}

Please fix the issue and provide the COMPLETE corrected code.
Make sure the code saves the output CSV to the exact path specified.
"""

        await self.agent.run(error_msg, thread=self.thread)

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of all execution attempts."""
        return {
            "workflow_name": self.workflow_name,
            "total_iterations": self.memory.iteration_count,
            "max_iterations": self.max_iterations,
            "attempts": [
                {
                    "iteration": attempt["iteration"],
                    "status": attempt["execution_result"]["status"],
                    "timestamp": attempt["timestamp"]
                }
                for attempt in self.memory.code_attempts
            ],
            "final_code": self.memory.current_code,
            "work_dir": str(self.work_dir) if self.work_dir else None
        }

    def reset(self):
        """Reset the agent state."""
        self.memory.reset()
        self.thread = None
        self.workflow_name = None
        self.work_dir = None
        logger.info("Coder Agent reset")


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_coder_agent(
    model: str = "gpt-4o",
    temperature: float = 0.3,
    max_iterations: int = 5,
    execution_timeout: int = 120
) -> CoderAgent:
    """
    Create and configure a Coder Agent.

    Args:
        model: OpenAI model to use (default: gpt-4o)
        temperature: Temperature for code generation (default: 0.3)
        max_iterations: Maximum code generation attempts (default: 5)
        execution_timeout: Code execution timeout in seconds (default: 120)

    Returns:
        Configured CoderAgent instance

    Example:
        >>> coder = create_coder_agent(model="gpt-4o", max_iterations=3)
        >>> await coder.initialize_workflow(
        ...     workflow_name="Sales Analysis",
        ...     business_logic_plan=plan_text,
        ...     csv_filepaths=["data/sales.csv"]
        ... )
        >>> result = await coder.generate_and_execute_code()
    """
    return CoderAgent(
        model=model,
        temperature=temperature,
        max_iterations=max_iterations,
        execution_timeout=execution_timeout
    )
