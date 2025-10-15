"""
CSV analysis tools for Planner Agent.

This module provides tools for analyzing CSV files, extracting metadata,
and generating summaries for the Planner Agent to understand data structure.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from ira_builder.utils.logger import get_logger
from ira_builder.exceptions.errors import ValidationException, StorageException

logger = get_logger(__name__)


def analyze_csv_structure(filepath: str) -> Dict[str, Any]:
    """
    Analyze CSV file structure and return comprehensive metadata.

    This function reads a CSV file and extracts detailed information about its
    structure including columns, data types, row count, sample data, and
    statistical summaries for numerical columns.

    Args:
        filepath: Absolute path to the CSV file to analyze

    Returns:
        Dictionary containing:
            - filename: Name of the file
            - path: Full path to the file
            - columns: List of column names
            - dtypes: Dictionary mapping column names to data types
            - row_count: Total number of rows
            - sample_data: First 5 rows as list of dictionaries
            - statistics: Statistical summary for numerical columns
            - missing_values: Count of missing values per column
            - file_size_mb: File size in megabytes
            - analyzed_at: Timestamp of analysis

    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValidationException: If the file is not a valid CSV
        StorageException: If there's an error reading the file

    Example:
        >>> metadata = analyze_csv_structure("data/sales.csv")
        >>> print(metadata["columns"])
        ['date', 'product', 'amount', 'quantity']
        >>> print(metadata["row_count"])
        1000
    """
    logger.info(f"Analyzing CSV structure: {filepath}")

    # Validate file exists
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    if not file_path.suffix.lower() in ['.csv', '.txt']:
        raise ValidationException(f"File is not a CSV: {filepath}")

    try:
        # Read CSV file
        df = pd.read_csv(filepath)
        logger.debug(f"Successfully read CSV with {len(df)} rows and {len(df.columns)} columns")

        # Basic metadata
        metadata = {
            "filename": file_path.name,
            "path": str(file_path.absolute()),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "row_count": len(df),
            "column_count": len(df.columns),
            "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            "analyzed_at": datetime.now().isoformat(),
        }

        # Sample data (first 5 rows)
        metadata["sample_data"] = df.head(5).to_dict(orient="records")

        # Missing values
        missing = df.isnull().sum()
        metadata["missing_values"] = {
            col: int(count) for col, count in missing.items() if count > 0
        }
        metadata["missing_percentage"] = {
            col: round((count / len(df)) * 100, 2)
            for col, count in missing.items() if count > 0
        }

        # Statistics for numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numerical_cols:
            stats_df = df[numerical_cols].describe()
            metadata["statistics"] = {
                col: {
                    "count": int(stats_df[col]["count"]),
                    "mean": round(float(stats_df[col]["mean"]), 2),
                    "std": round(float(stats_df[col]["std"]), 2),
                    "min": round(float(stats_df[col]["min"]), 2),
                    "25%": round(float(stats_df[col]["25%"]), 2),
                    "50%": round(float(stats_df[col]["50%"]), 2),
                    "75%": round(float(stats_df[col]["75%"]), 2),
                    "max": round(float(stats_df[col]["max"]), 2),
                }
                for col in numerical_cols
            }
        else:
            metadata["statistics"] = {}

        # Categorical columns info
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if categorical_cols:
            metadata["categorical_info"] = {
                col: {
                    "unique_count": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(5).to_dict(),
                }
                for col in categorical_cols
            }
        else:
            metadata["categorical_info"] = {}

        # Data type summary
        metadata["type_summary"] = {
            "numerical": numerical_cols,
            "categorical": categorical_cols,
            "datetime": df.select_dtypes(include=["datetime64"]).columns.tolist(),
        }

        logger.info(f"CSV analysis complete: {metadata['filename']}")
        return metadata

    except pd.errors.EmptyDataError:
        raise ValidationException(f"CSV file is empty: {filepath}")
    except pd.errors.ParserError as e:
        raise ValidationException(f"Invalid CSV format: {str(e)}")
    except Exception as e:
        logger.error(f"Error analyzing CSV: {str(e)}")
        raise StorageException(f"Failed to analyze CSV file: {str(e)}")


def get_csv_summary(filepaths: List[str]) -> str:
    """
    Generate a human-readable summary of one or more CSV files.

    This function creates a formatted text summary that the Planner Agent
    can use to understand the available data sources.

    Args:
        filepaths: List of absolute paths to CSV files

    Returns:
        Formatted string summary containing file information, column details,
        row counts, and data type information

    Raises:
        FileNotFoundError: If any file doesn't exist
        ValidationException: If any file is not a valid CSV

    Example:
        >>> summary = get_csv_summary(["data/sales.csv", "data/products.csv"])
        >>> print(summary)
        File: sales.csv
        Path: /path/to/data/sales.csv
        Rows: 1,000 | Columns: 4 | Size: 0.15 MB
        ...
    """
    logger.info(f"Generating CSV summary for {len(filepaths)} file(s)")

    summaries = []

    for filepath in filepaths:
        try:
            metadata = analyze_csv_structure(filepath)

            # Build formatted summary
            summary_parts = [
                f"📄 File: {metadata['filename']}",
                f"   Path: {metadata['path']}",
                f"   Rows: {metadata['row_count']:,} | Columns: {metadata['column_count']} | Size: {metadata['file_size_mb']} MB",
                "",
                "   Columns:",
            ]

            # Add column information with types
            for col in metadata["columns"]:
                dtype = metadata["dtypes"][col]
                missing = metadata["missing_values"].get(col, 0)
                missing_pct = metadata["missing_percentage"].get(col, 0)

                col_info = f"      • {col} ({dtype})"
                if missing > 0:
                    col_info += f" - {missing:,} missing ({missing_pct}%)"
                summary_parts.append(col_info)

            # Add numerical statistics summary
            if metadata["statistics"]:
                summary_parts.append("")
                summary_parts.append("   Numerical Columns Summary:")
                for col, stats in metadata["statistics"].items():
                    summary_parts.append(
                        f"      • {col}: min={stats['min']}, max={stats['max']}, "
                        f"mean={stats['mean']}, std={stats['std']}"
                    )

            # Add categorical info
            if metadata["categorical_info"]:
                summary_parts.append("")
                summary_parts.append("   Categorical Columns:")
                for col, info in metadata["categorical_info"].items():
                    summary_parts.append(
                        f"      • {col}: {info['unique_count']} unique values"
                    )
                    top_values = ", ".join(
                        f"{k} ({v})" for k, v in list(info["top_values"].items())[:3]
                    )
                    summary_parts.append(f"        Top values: {top_values}")

            summaries.append("\n".join(summary_parts))

        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")
            summaries.append(f"❌ Error analyzing {filepath}: {str(e)}")

    return "\n\n" + "=" * 80 + "\n\n".join(summaries)


def validate_column_references(
    column_names: List[str],
    available_columns: List[str]
) -> Dict[str, Any]:
    """
    Validate that referenced columns exist in the available columns.

    This tool helps the Planner Agent verify that business logic references
    valid column names from the uploaded CSV files.

    Args:
        column_names: List of column names referenced in business logic
        available_columns: List of columns actually present in CSV files

    Returns:
        Dictionary containing:
            - valid: Boolean indicating if all columns are valid
            - missing_columns: List of columns that don't exist
            - extra_columns: Columns available but not referenced
            - match_percentage: Percentage of valid references

    Example:
        >>> result = validate_column_references(
        ...     ["amount", "quantity", "price"],
        ...     ["date", "product", "amount", "quantity"]
        ... )
        >>> print(result["valid"])
        False
        >>> print(result["missing_columns"])
        ['price']
    """
    logger.debug(f"Validating {len(column_names)} column references")

    # Find missing columns
    missing = [col for col in column_names if col not in available_columns]

    # Find extra columns (available but not referenced)
    extra = [col for col in available_columns if col not in column_names]

    # Calculate match percentage
    if column_names:
        valid_count = len([col for col in column_names if col in available_columns])
        match_percentage = round((valid_count / len(column_names)) * 100, 2)
    else:
        match_percentage = 0.0

    result = {
        "valid": len(missing) == 0,
        "missing_columns": missing,
        "extra_columns": extra,
        "match_percentage": match_percentage,
        "total_referenced": len(column_names),
        "total_available": len(available_columns),
    }

    if not result["valid"]:
        logger.warning(
            f"Column validation failed: {len(missing)} missing columns - {missing}"
        )
    else:
        logger.info("Column validation successful: all columns found")

    return result


def get_column_data_preview(
    filepath: str,
    column_name: str,
    num_samples: int = 10
) -> Dict[str, Any]:
    """
    Get preview of data from a specific column.

    Useful for the Planner Agent to show examples of data values
    when asking clarifying questions.

    Args:
        filepath: Path to CSV file
        column_name: Name of column to preview
        num_samples: Number of sample values to return (default: 10)

    Returns:
        Dictionary containing:
            - column: Column name
            - dtype: Data type
            - samples: List of sample values
            - unique_count: Number of unique values
            - null_count: Number of missing values

    Raises:
        ValidationException: If column doesn't exist

    Example:
        >>> preview = get_column_data_preview("data/sales.csv", "product")
        >>> print(preview["samples"][:3])
        ['Widget A', 'Widget B', 'Widget C']
    """
    logger.debug(f"Getting column preview: {column_name} from {filepath}")

    df = pd.read_csv(filepath)

    if column_name not in df.columns:
        raise ValidationException(
            f"Column '{column_name}' not found in {Path(filepath).name}"
        )

    column_data = df[column_name]

    # Get samples (drop NaN for cleaner display)
    samples = column_data.dropna().head(num_samples).tolist()

    # Convert numpy types to Python types for JSON serialization
    samples = [
        item.item() if isinstance(item, (np.integer, np.floating)) else item
        for item in samples
    ]

    return {
        "column": column_name,
        "dtype": str(column_data.dtype),
        "samples": samples,
        "unique_count": int(column_data.nunique()),
        "null_count": int(column_data.isnull().sum()),
        "total_count": len(column_data),
    }


def compare_csv_schemas(filepaths: List[str]) -> Dict[str, Any]:
    """
    Compare schemas of multiple CSV files to identify common columns.

    Useful when working with multiple related CSV files to understand
    potential join keys and relationships.

    Args:
        filepaths: List of CSV file paths to compare

    Returns:
        Dictionary containing:
            - common_columns: Columns present in all files
            - unique_columns: Columns unique to each file
            - schema_compatibility: Boolean indicating if files can be joined
            - suggested_join_keys: Potential columns for joining

    Example:
        >>> result = compare_csv_schemas(["sales.csv", "products.csv"])
        >>> print(result["common_columns"])
        ['product_id']
        >>> print(result["suggested_join_keys"])
        ['product_id']
    """
    logger.info(f"Comparing schemas of {len(filepaths)} CSV files")

    if len(filepaths) < 2:
        return {
            "common_columns": [],
            "unique_columns": {},
            "schema_compatibility": False,
            "message": "Need at least 2 files to compare",
        }

    # Get columns from each file
    file_columns = {}
    for filepath in filepaths:
        df = pd.read_csv(filepath, nrows=0)  # Read only headers
        filename = Path(filepath).name
        file_columns[filename] = set(df.columns.tolist())

    # Find common columns
    common_columns = set.intersection(*file_columns.values())

    # Find unique columns per file
    unique_columns = {}
    for filename, cols in file_columns.items():
        unique_columns[filename] = list(cols - common_columns)

    # Suggest potential join keys
    # Look for columns with "id" in name or columns that are common
    suggested_join_keys = [
        col for col in common_columns
        if "id" in col.lower() or "key" in col.lower() or "code" in col.lower()
    ]

    return {
        "common_columns": sorted(list(common_columns)),
        "unique_columns": unique_columns,
        "schema_compatibility": len(common_columns) > 0,
        "suggested_join_keys": suggested_join_keys,
        "file_column_counts": {
            filename: len(cols) for filename, cols in file_columns.items()
        },
    }


def detect_data_quality_issues(filepath: str) -> Dict[str, Any]:
    """
    Detect potential data quality issues in a CSV file.

    Identifies common data quality problems that might affect analysis.

    Args:
        filepath: Path to CSV file

    Returns:
        Dictionary containing:
            - has_issues: Boolean indicating if issues were found
            - issues: List of detected issues with descriptions
            - recommendations: Suggested fixes

    Example:
        >>> issues = detect_data_quality_issues("data/sales.csv")
        >>> for issue in issues["issues"]:
        ...     print(issue["type"], "-", issue["description"])
    """
    logger.info(f"Detecting data quality issues in: {filepath}")

    df = pd.read_csv(filepath)
    issues = []

    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        issues.append({
            "type": "duplicate_rows",
            "severity": "medium",
            "description": f"Found {duplicates} duplicate rows ({(duplicates/len(df)*100):.1f}%)",
            "recommendation": "Consider removing duplicate rows before analysis",
        })

    # Check for columns with all missing values
    for col in df.columns:
        if df[col].isnull().all():
            issues.append({
                "type": "empty_column",
                "severity": "high",
                "column": col,
                "description": f"Column '{col}' has all missing values",
                "recommendation": f"Consider removing column '{col}' as it contains no data",
            })

    # Check for columns with high percentage of missing values
    for col in df.columns:
        missing_pct = (df[col].isnull().sum() / len(df)) * 100
        if 50 < missing_pct < 100:  # Between 50% and 100%
            issues.append({
                "type": "high_missing_values",
                "severity": "medium",
                "column": col,
                "description": f"Column '{col}' has {missing_pct:.1f}% missing values",
                "recommendation": f"Consider handling missing values in '{col}' before analysis",
            })

    # Check for columns with only one unique value
    for col in df.columns:
        if df[col].nunique() == 1:
            issues.append({
                "type": "constant_column",
                "severity": "low",
                "column": col,
                "description": f"Column '{col}' has only one unique value",
                "recommendation": f"Column '{col}' may not be useful for analysis",
            })

    # Check for potential date columns that aren't parsed as dates
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(100)
        if len(sample) > 0:
            # Simple heuristic: check if values contain date-like patterns
            date_like = sample.astype(str).str.contains(
                r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}',
                regex=True
            ).sum()
            if date_like > len(sample) * 0.5:  # More than 50% look like dates
                issues.append({
                    "type": "unparsed_dates",
                    "severity": "low",
                    "column": col,
                    "description": f"Column '{col}' appears to contain dates but is stored as text",
                    "recommendation": f"Consider parsing '{col}' as datetime for time-based analysis",
                })

    return {
        "has_issues": len(issues) > 0,
        "issue_count": len(issues),
        "issues": issues,
        "summary": f"Found {len(issues)} potential data quality issues",
    }
