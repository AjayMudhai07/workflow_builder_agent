"""
Code execution tools for Coder Agent using PythonScriptExecutor.

This module provides wrapper functions around the PythonScriptExecutor
to execute generated Python code safely with timeout, error handling,
and result validation.
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from ira_builder.executor import PythonScriptExecutor, CodeBlock
from ira_builder.utils.logger import get_logger
from ira_builder.exceptions.errors import ValidationException

logger = get_logger(__name__)


def extract_code_from_markdown(text: str) -> str:
    """
    Extract Python code from markdown code blocks.

    Handles formats like:
    - ```python\\ncode\\n```
    - ```\\ncode\\n```

    Args:
        text: Text containing markdown code blocks

    Returns:
        Extracted Python code (without markdown markers)

    Example:
        >>> text = "Here's the code:\\n```python\\nprint('Hello')\\n```"
        >>> code = extract_code_from_markdown(text)
        >>> print(code)
        print('Hello')
    """
    logger.debug("Extracting code from markdown")

    # Try with python language specifier
    pattern = r"```python\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()
        logger.debug(f"Extracted {len(code)} characters of Python code")
        return code

    # Try without language specifier
    pattern = r"```\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        # Check if it looks like Python
        if _looks_like_python(code):
            logger.debug(f"Extracted {len(code)} characters of code (no language tag)")
            return code

    # No markdown blocks found, return as-is
    logger.debug("No markdown code blocks found, returning text as-is")
    return text.strip()


def _looks_like_python(code: str) -> bool:
    """
    Quick heuristic to check if code looks like Python.

    Args:
        code: Code string to check

    Returns:
        True if code contains Python keywords
    """
    python_keywords = [
        'import ', 'from ', 'def ', 'class ',
        'if ', 'for ', 'while ', 'try:', 'except:',
        'pd.', 'np.', 'print('
    ]
    return any(keyword in code for keyword in python_keywords)


async def execute_python_code(
    code: str,
    work_dir: str,
    timeout: int = 120,
    auto_cleanup: bool = True
) -> Dict[str, Any]:
    """
    Execute Python code using PythonScriptExecutor.

    This is the main execution tool for the Coder Agent. It runs the
    generated Python code in an isolated subprocess with timeout control.

    Args:
        code: Python code to execute
        work_dir: Working directory for execution (where files will be saved)
        timeout: Execution timeout in seconds (default: 120)
        auto_cleanup: Whether to clean up temporary files (default: True)

    Returns:
        Dictionary with:
            - status: "success" | "error" | "timeout" | "cancelled"
            - exit_code: int (0 = success, 124 = timeout, 125 = cancelled)
            - output: stdout + stderr combined
            - code_file: Path to executed file (for debugging)
            - error_message: Detailed error message if status != "success"

    Example:
        >>> code = '''
        ... import pandas as pd
        ... df = pd.DataFrame({'a': [1, 2, 3]})
        ... print(df)
        ... '''
        >>> result = await execute_python_code(code, work_dir="./output")
        >>> print(result['status'])
        success
    """
    logger.info(f"Executing Python code in {work_dir} (timeout: {timeout}s)")

    # Ensure work_dir exists
    work_path = Path(work_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    # Create executor
    executor = PythonScriptExecutor(
        timeout=timeout,
        work_dir=work_path,
        auto_cleanup=auto_cleanup
    )

    # Execute code
    try:
        code_block = CodeBlock(language="python", code=code)
        result = await executor.execute_code_blocks([code_block])

        # Determine status based on exit code
        if result.exit_code == 0:
            status = "success"
            error_message = None
        elif result.exit_code == 124:
            status = "timeout"
            error_message = f"Execution timed out after {timeout} seconds"
        elif result.exit_code == 125:
            status = "cancelled"
            error_message = "Execution was cancelled"
        else:
            status = "error"
            error_message = _extract_error_from_output(result.output)

        logger.info(f"Execution completed with status: {status}, exit_code: {result.exit_code}")

        return {
            "status": status,
            "exit_code": result.exit_code,
            "output": result.output,
            "code_file": result.code_file,
            "error_message": error_message
        }

    except asyncio.TimeoutError:
        logger.error(f"Code execution timed out after {timeout} seconds")
        return {
            "status": "timeout",
            "exit_code": 124,
            "output": f"Execution timed out after {timeout} seconds",
            "code_file": None,
            "error_message": f"Code execution exceeded timeout of {timeout} seconds"
        }
    except asyncio.CancelledError:
        logger.warning("Code execution was cancelled")
        return {
            "status": "cancelled",
            "exit_code": 125,
            "output": "Execution was cancelled by user or system",
            "code_file": None,
            "error_message": "Execution was cancelled"
        }
    except Exception as e:
        logger.error(f"Code execution error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "exit_code": 1,
            "output": str(e),
            "code_file": None,
            "error_message": f"Execution failed: {str(e)}"
        }


def _extract_error_from_output(output: str) -> str:
    """
    Extract the most relevant error message from execution output.

    Args:
        output: Full stdout/stderr output

    Returns:
        Extracted error message
    """
    lines = output.split('\n')

    # Look for common error patterns
    for i, line in enumerate(lines):
        # Python exceptions
        if 'Error:' in line or 'Exception:' in line:
            # Get the error and a few lines of context
            error_lines = lines[max(0, i-2):min(len(lines), i+3)]
            return '\n'.join(error_lines)

        # Traceback
        if 'Traceback (most recent call last)' in line:
            # Get from traceback to the end
            return '\n'.join(lines[i:])

    # If no specific error found, return last 10 lines
    return '\n'.join(lines[-10:]) if len(lines) > 10 else output


def validate_python_syntax(code: str) -> Dict[str, Any]:
    """
    Validate Python code syntax without executing it.

    This is a pre-execution check to catch syntax errors early.

    Args:
        code: Python code to validate

    Returns:
        Dictionary with:
            - valid: Boolean indicating if syntax is valid
            - error: Error message if invalid (None if valid)
            - line: Line number of syntax error (if applicable)
            - offset: Column offset of syntax error (if applicable)
            - text: Line of code with error (if applicable)

    Example:
        >>> result = validate_python_syntax("print('Hello')")
        >>> print(result['valid'])
        True

        >>> result = validate_python_syntax("print('Hello'")
        >>> print(result['valid'])
        False
        >>> print(result['error'])
        EOL while scanning string literal
    """
    logger.debug("Validating Python syntax")

    try:
        compile(code, '<string>', 'exec')
        logger.debug("Syntax validation passed")
        return {
            "valid": True,
            "error": None,
            "line": None,
            "offset": None,
            "text": None
        }
    except SyntaxError as e:
        logger.warning(f"Syntax error at line {e.lineno}: {e.msg}")
        return {
            "valid": False,
            "error": e.msg,
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text.strip() if e.text else None
        }
    except Exception as e:
        logger.warning(f"Unexpected error during syntax validation: {str(e)}")
        return {
            "valid": False,
            "error": str(e),
            "line": None,
            "offset": None,
            "text": None
        }


def preview_dataframe(filepath: str, rows: int = 20) -> str:
    """
    Generate markdown preview of CSV file.

    This is used to show the user what the code produced.

    Args:
        filepath: Path to CSV file to preview
        rows: Number of rows to include in preview (default: 20)

    Returns:
        Markdown formatted table string with row count header

    Example:
        >>> preview = preview_dataframe("output.csv", rows=5)
        >>> print(preview)
        Preview (100 total rows):

        | col1 | col2 |
        |------|------|
        | val1 | val2 |
        ...
    """
    logger.debug(f"Generating preview for {filepath}")

    try:
        df = pd.read_csv(filepath)
        total_rows = len(df)

        # Generate markdown table
        preview_df = df.head(rows)
        table = preview_df.to_markdown(index=False)

        header = f"**Preview ({total_rows:,} total rows, showing first {min(rows, total_rows)}):**\n\n"

        logger.debug(f"Preview generated: {total_rows} total rows")
        return header + table

    except FileNotFoundError:
        error_msg = f"❌ Error: File not found: {filepath}"
        logger.error(error_msg)
        return error_msg
    except pd.errors.EmptyDataError:
        error_msg = f"❌ Error: File is empty: {filepath}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ Error reading file: {str(e)}"
        logger.error(error_msg)
        return error_msg


def validate_output_dataframe(filepath: str) -> Dict[str, Any]:
    """
    Validate that output CSV was created and is valid.

    This is used to verify that code execution succeeded in creating output.

    Args:
        filepath: Path to expected output CSV file

    Returns:
        Dictionary with:
            - valid: Boolean indicating if file exists and is valid
            - error: Error message if invalid (None if valid)
            - row_count: Number of rows in dataframe
            - column_count: Number of columns in dataframe
            - columns: List of column names
            - file_size_mb: File size in megabytes

    Example:
        >>> result = validate_output_dataframe("output.csv")
        >>> if result['valid']:
        ...     print(f"Output has {result['row_count']} rows")
    """
    logger.debug(f"Validating output dataframe: {filepath}")

    path = Path(filepath)

    # Check if file exists
    if not path.exists():
        logger.warning(f"Output file not found: {filepath}")
        return {
            "valid": False,
            "error": "Output file was not created",
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "file_size_mb": 0.0
        }

    # Try to read and validate the CSV
    try:
        df = pd.read_csv(filepath)

        # Check if dataframe is empty
        if len(df) == 0:
            logger.warning(f"Output dataframe is empty: {filepath}")
            return {
                "valid": False,
                "error": "Output file is empty (0 rows)",
                "row_count": 0,
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2)
            }

        logger.info(f"Output validated: {len(df)} rows, {len(df.columns)} columns")
        return {
            "valid": True,
            "error": None,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2)
        }

    except pd.errors.EmptyDataError:
        logger.warning(f"Output file is empty: {filepath}")
        return {
            "valid": False,
            "error": "Output file is empty",
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "file_size_mb": 0.0
        }
    except pd.errors.ParserError as e:
        logger.error(f"Invalid CSV format: {str(e)}")
        return {
            "valid": False,
            "error": f"Invalid CSV format: {str(e)}",
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"Error reading output file: {str(e)}")
        return {
            "valid": False,
            "error": f"Error reading output file: {str(e)}",
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else 0.0
        }


def analyze_execution_error(
    error_output: str,
    code: str
) -> Dict[str, Any]:
    """
    Analyze execution error and provide debugging information.

    This helps the Coder Agent understand what went wrong and how to fix it.

    Args:
        error_output: stderr/stdout from failed execution
        code: The Python code that was executed

    Returns:
        Dictionary with:
            - error_type: Type of error (e.g., "KeyError", "ValueError")
            - line_number: Line number where error occurred (if available)
            - error_message: The actual error message
            - code_context: Lines of code around the error
            - suggested_fix: Suggested fix for common errors

    Example:
        >>> error = "KeyError: 'column_name'"
        >>> analysis = analyze_execution_error(error, code)
        >>> print(analysis['suggested_fix'])
        "Column 'column_name' not found. Check available columns..."
    """
    logger.debug("Analyzing execution error")

    error_type = "Unknown"
    line_number = None
    error_message = ""
    code_context = []

    # Extract error type
    error_patterns = [
        r'(\w+Error): (.+)',
        r'(\w+Exception): (.+)'
    ]

    for pattern in error_patterns:
        match = re.search(pattern, error_output)
        if match:
            error_type = match.group(1)
            error_message = match.group(2)
            break

    # Extract line number
    line_patterns = [
        r'line (\d+)',
        r'File "<string>", line (\d+)',
    ]

    for pattern in line_patterns:
        match = re.search(pattern, error_output, re.IGNORECASE)
        if match:
            line_number = int(match.group(1))
            break

    # Get code context if we have a line number
    if line_number:
        code_lines = code.split('\n')
        start = max(0, line_number - 3)
        end = min(len(code_lines), line_number + 2)
        code_context = code_lines[start:end]

    # Generate suggested fix
    suggested_fix = _get_error_suggestion(error_type, error_message, code)

    return {
        "error_type": error_type,
        "line_number": line_number,
        "error_message": error_message,
        "code_context": code_context,
        "suggested_fix": suggested_fix,
        "full_error": error_output
    }


def _get_error_suggestion(error_type: str, error_message: str, code: str) -> str:
    """
    Generate suggested fix based on error type.

    Args:
        error_type: Type of error
        error_message: Error message
        code: The code that failed

    Returns:
        Suggested fix as string
    """
    suggestions = {
        "KeyError": "Column not found in DataFrame. Check column names with df.columns and verify spelling.",
        "ValueError": "Invalid value or type conversion. Check data types and value ranges.",
        "FileNotFoundError": "File not found. Verify file path is correct and file exists.",
        "NameError": "Variable or function not defined. Check for typos and ensure imports are correct.",
        "TypeError": "Invalid type operation. Check data types and method signatures.",
        "AttributeError": "Attribute or method not found. Verify object type and available methods.",
        "IndexError": "Index out of range. Check array/list length before accessing.",
        "ImportError": "Module not found. Ensure required packages are installed.",
        "SyntaxError": "Invalid Python syntax. Check for missing colons, parentheses, or quotes.",
        "IndentationError": "Incorrect indentation. Ensure consistent use of spaces or tabs.",
    }

    base_suggestion = suggestions.get(error_type, "Check the error message and traceback for details.")

    # Add context-specific suggestions
    if "column" in error_message.lower() or "key" in error_message.lower():
        return f"{base_suggestion}\n\nTip: Use df.columns.tolist() to see available columns."

    return base_suggestion


# Helper function to get dataframe summary statistics
def get_dataframe_summary(filepath: str) -> Dict[str, Any]:
    """
    Get summary statistics for a dataframe.

    Args:
        filepath: Path to CSV file

    Returns:
        Dictionary with summary statistics
    """
    logger.debug(f"Generating summary for {filepath}")

    try:
        df = pd.read_csv(filepath)

        # Basic info
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }

        # Missing values
        missing = df.isnull().sum()
        summary["missing_values"] = {
            col: int(count) for col, count in missing.items() if count > 0
        }

        # Numerical statistics
        numerical_cols = df.select_dtypes(include=['number']).columns
        if len(numerical_cols) > 0:
            summary["numerical_summary"] = df[numerical_cols].describe().to_dict()

        logger.debug(f"Summary generated for {len(df)} rows")
        return summary

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {
            "error": str(e),
            "row_count": 0,
            "column_count": 0
        }
