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

from ai.ira_builder.executor import PythonScriptExecutor, CodeBlock
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.exceptions.errors import ValidationException

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


def preview_dataframe(filepath: str, rows: int = 20, total_row_count: int = None) -> str:
    """
    Generate markdown preview of CSV file or text file.

    This is used to show the user what the code produced.

    Args:
        filepath: Path to CSV or text file to preview
        rows: Number of rows to include in preview (default: 20)
        total_row_count: Optional pre-computed total row count (avoids re-counting for large files)

    Returns:
        Markdown formatted table string with row count header (for CSV)
        or text preview (for .txt files)

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

    # Handle .txt files differently (e.g., analysis reports)
    if Path(filepath).suffix.lower() == '.txt':
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Show first 2000 characters of text file
            max_chars = 2000
            if len(content) > max_chars:
                preview_content = content[:max_chars] + "\n\n... (truncated)"
            else:
                preview_content = content

            header = f"**Text File Preview ({len(content)} characters):**\n\n"
            logger.debug(f"Text preview generated: {len(content)} characters")
            return header + "```\n" + preview_content + "\n```"

        except FileNotFoundError:
            error_msg = f"❌ Error: File not found: {filepath}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error reading file: {str(e)}"
            logger.error(error_msg)
            return error_msg

    # Handle CSV files
    try:
        # Import the helper function
        from ai.ira_builder.tools.csv_tools import read_csv_with_encoding

        # ALWAYS read first N rows for preview (works regardless of file size)
        # This is fast even for huge files since we only read what we need
        df = read_csv_with_encoding(filepath, nrows=rows)

        # Use pre-computed row count if provided (avoids slow re-counting for large files)
        if total_row_count is not None:
            # Handle string row_count (from timeout fallback)
            if isinstance(total_row_count, str):
                total_rows_display = total_row_count
                logger.debug(f"Using fallback row count: {total_rows_display}")
            else:
                total_rows = total_row_count
                total_rows_display = f"{total_rows:,}"
                logger.debug(f"Using pre-computed row count: {total_rows}")
        else:
            # For preview-only calls without validation, skip counting entirely
            # Just show that we're displaying first N rows
            total_rows_display = "Unknown (showing first rows only)"
            logger.debug("Preview without row count - skipping count for speed")

        # Generate markdown table (ALWAYS works, even for huge files)
        table = df.to_markdown(index=False)

        header = f"**Preview ({total_rows_display} total rows, showing first {len(df)}):**\n\n"

        logger.debug(f"Preview generated: showing {len(df)} rows")
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


def _count_csv_rows_with_timeout(filepath: str, timeout_seconds: int = 10) -> int:
    """
    Count CSV rows with timeout. Returns -1 if timeout occurs.

    Args:
        filepath: Path to CSV file
        timeout_seconds: Maximum time to spend counting (default: 10)

    Returns:
        Row count or -1 if timeout/error
    """
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Row counting timed out")

    try:
        # Set timeout alarm (Unix only, but that's okay for server)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                row_count = sum(1 for _ in f) - 1  # Subtract 1 for header
            signal.alarm(0)  # Cancel alarm
            return row_count
        except TimeoutError:
            logger.warning(f"Row counting timed out after {timeout_seconds}s for {filepath}")
            return -1
        finally:
            signal.alarm(0)  # Ensure alarm is cancelled

    except Exception as e:
        logger.error(f"Error counting rows: {str(e)}")
        return -1


def validate_output_dataframe(filepath: str, timeout_seconds: int = 10) -> Dict[str, Any]:
    """
    Validate that output CSV was created and is valid.

    This is used to verify that code execution succeeded in creating output.

    Args:
        filepath: Path to expected output CSV file
        timeout_seconds: Maximum time to spend counting rows (default: 10s)

    Returns:
        Dictionary with:
            - valid: Boolean indicating if file exists and is valid
            - error: Error message if invalid (None if valid)
            - row_count: Number of rows in dataframe (or "Not Calculated" if too large)
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

    # For .txt files (analysis reports), just validate existence and size
    if path.suffix.lower() == '.txt':
        file_size = path.stat().st_size
        if file_size == 0:
            logger.warning(f"Output text file is empty: {filepath}")
            return {
                "valid": False,
                "error": "Output file is empty (0 bytes)",
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "file_size_mb": 0.0
            }
        logger.info(f"Text output validated: {round(file_size / (1024 * 1024), 2)} MB")
        return {
            "valid": True,
            "error": None,
            "row_count": 0,  # Not applicable for text files
            "column_count": 0,  # Not applicable for text files
            "columns": [],  # Not applicable for text files
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }

    # Try to read and validate the CSV
    try:
        from ai.ira_builder.tools.csv_tools import read_csv_with_encoding

        # For large files, only read headers and use file operations for row count
        file_size = path.stat().st_size
        file_size_mb = round(file_size / (1024 * 1024), 2)

        # Read only first few rows to get column info (much faster for large files)
        df_sample = read_csv_with_encoding(filepath, nrows=5)
        columns = df_sample.columns.tolist()
        column_count = len(columns)

        # For row count, use timeout-protected counting (max 10 seconds)
        # For very large files, we'll skip counting and just validate file exists
        row_count = _count_csv_rows_with_timeout(filepath, timeout_seconds=timeout_seconds)

        # If row counting timed out (file too large), use fallback
        if row_count == -1:
            logger.warning(f"Row counting timed out for large file ({file_size_mb} MB). Using fallback.")
            return {
                "valid": True,  # File exists and has columns, so it's valid
                "error": None,
                "warning": f"File too large to count rows ({file_size_mb} MB). Row count not calculated.",
                "row_count": "Not Calculated (Data too large)",  # Fallback value for frontend
                "column_count": column_count,
                "columns": columns,
                "file_size_mb": file_size_mb,
                "timeout": True  # Indicate timeout occurred
            }

        # Check if dataframe is empty - this is VALID for filter/search operations
        if row_count == 0:
            logger.info(f"Output dataframe is empty (0 rows) - this is valid for filter/search operations: {filepath}")
            return {
                "valid": True,  # Empty results are valid (e.g., no duplicates found, no matches, etc.)
                "error": None,
                "warning": "Output contains 0 rows - this may indicate no matches found (valid result)",
                "row_count": 0,
                "column_count": column_count,
                "columns": columns,
                "file_size_mb": file_size_mb
            }

        logger.info(f"Output validated: {row_count} rows, {column_count} columns ({file_size_mb} MB)")
        return {
            "valid": True,
            "error": None,
            "row_count": row_count,
            "column_count": column_count,
            "columns": columns,
            "file_size_mb": file_size_mb
        }

    except pd.errors.EmptyDataError:
        logger.info(f"Output file is empty (no data/headers) - treating as valid empty result: {filepath}")
        return {
            "valid": True,  # Empty CSV is valid for filter/search operations
            "error": None,
            "warning": "Output file is completely empty (no headers/data) - this may indicate no matches found",
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
def get_dataframe_summary(filepath: str, total_row_count: int = None) -> Dict[str, Any]:
    """
    Get summary statistics for a dataframe or text file.

    Args:
        filepath: Path to CSV or text file
        total_row_count: Optional pre-computed total row count (avoids re-counting for large files)

    Returns:
        Dictionary with summary statistics
    """
    logger.debug(f"Generating summary for {filepath}")

    # Handle .txt files differently (e.g., analysis reports)
    if Path(filepath).suffix.lower() == '.txt':
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Basic text file info
            lines = content.split('\n')
            words = content.split()

            summary = {
                "file_type": "text",
                "character_count": len(content),
                "line_count": len(lines),
                "word_count": len(words),
                "file_size_mb": round(Path(filepath).stat().st_size / (1024 * 1024), 2)
            }

            logger.debug(f"Text summary generated: {len(lines)} lines, {len(words)} words")
            return summary

        except Exception as e:
            logger.error(f"Error generating text summary: {str(e)}")
            return {
                "error": str(e),
                "file_type": "text",
                "character_count": 0
            }

    # Handle CSV files
    try:
        from ai.ira_builder.tools.csv_tools import read_csv_with_encoding

        # For summary statistics, sample the data instead of loading everything
        # Use first 1000 rows for statistics (representative for large files)
        sample_size = 1000
        df_sample = read_csv_with_encoding(filepath, nrows=sample_size)

        # Use pre-computed row count if provided (avoids slow re-counting for large files)
        if total_row_count is not None:
            # Handle string row_count (from timeout fallback)
            if isinstance(total_row_count, str):
                total_rows = total_row_count  # Keep as string for display
                sampled = True  # Assume large file if row count is string
                logger.debug(f"Using fallback row count: {total_rows}")
            else:
                total_rows = total_row_count
                sampled = total_rows > sample_size
                logger.debug(f"Using pre-computed row count: {total_rows}")
        else:
            # Get accurate row count efficiently with timeout
            row_count = _count_csv_rows_with_timeout(filepath, timeout_seconds=10)
            if row_count == -1:
                total_rows = "Not Calculated (Data too large)"
                sampled = True
                logger.debug("Row counting timed out")
            else:
                total_rows = row_count
                sampled = total_rows > sample_size
                logger.debug(f"Counted rows: {total_rows}")

        # Basic info
        summary = {
            "file_type": "csv",
            "row_count": total_rows,  # May be int or string
            "column_count": len(df_sample.columns),
            "columns": df_sample.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df_sample.dtypes.items()},
            "sampled": sampled,
            "sample_size": min(sample_size, len(df_sample)) if isinstance(total_rows, str) else min(sample_size, total_rows)
        }

        # Missing values (from sample)
        missing = df_sample.isnull().sum()
        summary["missing_values"] = {
            col: int(count) for col, count in missing.items() if count > 0
        }

        # Numerical statistics (from sample)
        numerical_cols = df_sample.select_dtypes(include=['number']).columns
        if len(numerical_cols) > 0:
            summary["numerical_summary"] = df_sample[numerical_cols].describe().to_dict()

        # Log summary generation (handle string row_count)
        if isinstance(total_rows, str):
            logger.debug(f"Summary generated from sample of {len(df_sample)} rows (total: {total_rows})")
        else:
            logger.debug(f"Summary generated for {total_rows} rows (sampled {min(sample_size, total_rows)} rows)")
        return summary

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {
            "error": str(e),
            "file_type": "csv",
            "row_count": 0,
            "column_count": 0
        }
