"""
Validation tools for business logic and workflow configuration.

This module provides tools for validating business logic documents,
workflow configurations, and ensuring completeness before code generation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError
import re

from ira.utils.logger import get_logger
from ira.exceptions.errors import ValidationException

logger = get_logger(__name__)


class BusinessLogicValidator(BaseModel):
    """Validator for business logic document structure."""

    summary: str = Field(..., min_length=10, description="Summary of analysis objective")
    data_sources: List[str] = Field(..., min_items=1, description="List of CSV files")
    requirements: List[str] = Field(..., min_items=1, description="Detailed requirements")
    analysis_steps: List[str] = Field(..., min_items=1, description="Step-by-step logic")
    expected_output: str = Field(..., min_length=10, description="Output description")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    constraints: List[str] = Field(default_factory=list, description="Constraints")


def validate_business_logic(business_logic: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a business logic document for completeness and correctness.

    Ensures the business logic contains all required sections and that
    they are sufficiently detailed for code generation.

    Args:
        business_logic: Dictionary containing business logic document

    Returns:
        Dictionary containing:
            - valid: Boolean indicating if validation passed
            - errors: List of validation errors (if any)
            - warnings: List of potential issues
            - completeness_score: Score from 0-100 indicating completeness
            - suggestions: List of suggestions for improvement

    Example:
        >>> logic = {
        ...     "summary": "Analyze sales data",
        ...     "data_sources": ["sales.csv"],
        ...     "requirements": ["Calculate total revenue"],
        ...     "analysis_steps": ["Load data", "Sum amounts"],
        ...     "expected_output": "Total revenue value"
        ... }
        >>> result = validate_business_logic(logic)
        >>> print(result["valid"])
        True
    """
    logger.info("Validating business logic document")

    errors = []
    warnings = []
    suggestions = []

    # Try to validate with Pydantic model
    try:
        BusinessLogicValidator(**business_logic)
        logger.debug("Business logic structure validation passed")
    except ValidationError as e:
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })
        logger.warning(f"Business logic validation failed: {len(errors)} errors")

    # Check for sufficient detail in requirements
    if "requirements" in business_logic:
        requirements = business_logic["requirements"]
        if len(requirements) < 3:
            warnings.append({
                "field": "requirements",
                "message": "Only {} requirement(s) specified. Consider adding more detail.".format(
                    len(requirements)
                ),
            })

        # Check if requirements are too vague
        vague_words = ["some", "various", "etc", "several", "maybe"]
        for req in requirements:
            if any(word in req.lower() for word in vague_words):
                warnings.append({
                    "field": "requirements",
                    "message": f"Requirement '{req[:50]}...' may be too vague",
                })

    # Check for sufficient analysis steps
    if "analysis_steps" in business_logic:
        steps = business_logic["analysis_steps"]
        if len(steps) < 3:
            warnings.append({
                "field": "analysis_steps",
                "message": "Only {} analysis step(s) specified. More steps may be needed.".format(
                    len(steps)
                ),
            })

    # Check if data sources are referenced in requirements or steps
    if "data_sources" in business_logic:
        data_sources = business_logic["data_sources"]
        requirements_text = " ".join(business_logic.get("requirements", []))
        steps_text = " ".join(business_logic.get("analysis_steps", []))

        for source in data_sources:
            source_name = source.replace(".csv", "").replace("_", " ")
            if source_name.lower() not in requirements_text.lower() and \
               source_name.lower() not in steps_text.lower():
                warnings.append({
                    "field": "data_sources",
                    "message": f"Data source '{source}' not clearly referenced in requirements or steps",
                })

    # Check expected output detail
    if "expected_output" in business_logic:
        output = business_logic["expected_output"]
        if len(output) < 50:
            suggestions.append({
                "field": "expected_output",
                "message": "Consider adding more detail about the expected output format",
            })

        # Check if output mentions format (CSV, DataFrame, etc.)
        if not any(fmt in output.lower() for fmt in ["csv", "dataframe", "table", "file"]):
            suggestions.append({
                "field": "expected_output",
                "message": "Consider specifying the output file format (e.g., CSV)",
            })

    # Calculate completeness score
    required_fields = ["summary", "data_sources", "requirements", "analysis_steps", "expected_output"]
    optional_fields = ["assumptions", "constraints"]

    score = 0
    # Required fields (60 points)
    for field in required_fields:
        if field in business_logic and business_logic[field]:
            if isinstance(business_logic[field], list):
                score += 12 if len(business_logic[field]) >= 3 else 8
            else:
                score += 12 if len(business_logic[field]) >= 50 else 8

    # Optional fields (20 points)
    for field in optional_fields:
        if field in business_logic and business_logic[field]:
            score += 10

    # Detail bonus (20 points)
    if "requirements" in business_logic and len(business_logic["requirements"]) >= 5:
        score += 10
    if "analysis_steps" in business_logic and len(business_logic["analysis_steps"]) >= 5:
        score += 10

    score = min(100, score)  # Cap at 100

    # Overall validity
    valid = len(errors) == 0 and score >= 60

    result = {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "completeness_score": score,
        "summary": _generate_validation_summary(valid, score, len(errors), len(warnings)),
    }

    if valid:
        logger.info(f"Business logic validation passed with score {score}/100")
    else:
        logger.warning(f"Business logic validation failed with {len(errors)} errors")

    return result


def _generate_validation_summary(
    valid: bool,
    score: int,
    error_count: int,
    warning_count: int
) -> str:
    """Generate a human-readable validation summary."""
    if valid:
        if score >= 90:
            return f"✓ Excellent! Business logic is comprehensive (score: {score}/100)"
        elif score >= 75:
            return f"✓ Good! Business logic is well-defined (score: {score}/100)"
        else:
            return f"✓ Acceptable. Business logic meets minimum requirements (score: {score}/100)"
    else:
        return f"✗ Validation failed with {error_count} error(s) and {warning_count} warning(s)"


def validate_workflow_config(
    workflow_name: str,
    workflow_description: str,
    csv_files: List[str]
) -> Dict[str, Any]:
    """
    Validate workflow configuration before starting.

    Args:
        workflow_name: Name of the workflow
        workflow_description: Description of what the workflow should do
        csv_files: List of CSV file paths

    Returns:
        Dictionary containing:
            - valid: Boolean indicating if configuration is valid
            - errors: List of validation errors
            - warnings: List of warnings

    Example:
        >>> result = validate_workflow_config(
        ...     "Sales Analysis",
        ...     "Analyze Q4 sales data",
        ...     ["sales.csv", "products.csv"]
        ... )
        >>> print(result["valid"])
        True
    """
    logger.info("Validating workflow configuration")

    errors = []
    warnings = []

    # Validate workflow name
    if not workflow_name or len(workflow_name.strip()) == 0:
        errors.append({
            "field": "workflow_name",
            "message": "Workflow name is required",
        })
    elif len(workflow_name) < 3:
        errors.append({
            "field": "workflow_name",
            "message": "Workflow name must be at least 3 characters",
        })
    elif len(workflow_name) > 100:
        errors.append({
            "field": "workflow_name",
            "message": "Workflow name must be less than 100 characters",
        })

    # Validate workflow description
    if not workflow_description or len(workflow_description.strip()) == 0:
        errors.append({
            "field": "workflow_description",
            "message": "Workflow description is required",
        })
    elif len(workflow_description) < 10:
        warnings.append({
            "field": "workflow_description",
            "message": "Workflow description is very short. Consider adding more detail.",
        })
    elif len(workflow_description) > 500:
        warnings.append({
            "field": "workflow_description",
            "message": "Workflow description is very long. Consider summarizing.",
        })

    # Validate CSV files
    if not csv_files or len(csv_files) == 0:
        errors.append({
            "field": "csv_files",
            "message": "At least one CSV file is required",
        })
    else:
        # Check for valid CSV file extensions
        for csv_file in csv_files:
            if not csv_file.lower().endswith(('.csv', '.txt')):
                errors.append({
                    "field": "csv_files",
                    "message": f"File '{csv_file}' does not have a valid CSV extension",
                })

        # Check for duplicate files
        if len(csv_files) != len(set(csv_files)):
            warnings.append({
                "field": "csv_files",
                "message": "Duplicate CSV files detected",
            })

    valid = len(errors) == 0

    result = {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "csv_file_count": len(csv_files) if csv_files else 0,
    }

    if valid:
        logger.info("Workflow configuration validation passed")
    else:
        logger.warning(f"Workflow configuration validation failed: {len(errors)} errors")

    return result


def validate_column_operations(
    operations: List[Dict[str, Any]],
    available_columns: List[str]
) -> Dict[str, Any]:
    """
    Validate that proposed operations reference valid columns.

    Args:
        operations: List of operations to validate, each with:
            - type: Operation type (filter, group, aggregate, etc.)
            - columns: List of columns involved
            - description: Human-readable description
        available_columns: List of available column names

    Returns:
        Dictionary containing validation results

    Example:
        >>> operations = [
        ...     {"type": "filter", "columns": ["amount"], "description": "Filter by amount"},
        ...     {"type": "group", "columns": ["product"], "description": "Group by product"}
        ... ]
        >>> result = validate_column_operations(operations, ["product", "amount", "date"])
        >>> print(result["valid"])
        True
    """
    logger.info(f"Validating {len(operations)} operations")

    errors = []
    warnings = []

    for i, operation in enumerate(operations):
        op_type = operation.get("type", "unknown")
        columns = operation.get("columns", [])

        # Check if columns exist
        for col in columns:
            if col not in available_columns:
                errors.append({
                    "operation": i + 1,
                    "type": op_type,
                    "message": f"Column '{col}' not found in available columns",
                })

        # Type-specific validations
        if op_type == "aggregate" and len(columns) == 0:
            warnings.append({
                "operation": i + 1,
                "message": "Aggregate operation should specify columns to aggregate",
            })

        if op_type == "group" and len(columns) > 5:
            warnings.append({
                "operation": i + 1,
                "message": f"Grouping by {len(columns)} columns may be too many",
            })

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "operations_checked": len(operations),
    }


def check_analysis_feasibility(
    business_logic: Dict[str, Any],
    csv_metadata: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Check if the proposed analysis is feasible given the available data.

    Args:
        business_logic: Business logic document
        csv_metadata: List of CSV metadata dictionaries

    Returns:
        Dictionary containing:
            - feasible: Boolean indicating feasibility
            - blockers: List of critical issues preventing analysis
            - concerns: List of potential concerns
            - recommendations: List of recommendations

    Example:
        >>> result = check_analysis_feasibility(business_logic, csv_metadata)
        >>> if result["feasible"]:
        ...     print("Analysis can proceed")
    """
    logger.info("Checking analysis feasibility")

    blockers = []
    concerns = []
    recommendations = []

    # Extract all available columns from CSV metadata
    all_columns = []
    for metadata in csv_metadata:
        all_columns.extend(metadata.get("columns", []))

    # Check if requirements mention columns that don't exist
    requirements_text = " ".join(business_logic.get("requirements", []))
    steps_text = " ".join(business_logic.get("analysis_steps", []))
    combined_text = requirements_text + " " + steps_text

    # Look for column references in requirements (words in quotes or all caps)
    potential_column_refs = re.findall(r'"([^"]+)"', combined_text)
    potential_column_refs += re.findall(r'\b[A-Z][A-Z_]+\b', combined_text)

    missing_columns = [
        col for col in potential_column_refs
        if col not in all_columns and col.lower() not in [c.lower() for c in all_columns]
    ]

    if missing_columns:
        concerns.append({
            "type": "potential_missing_columns",
            "message": f"Requirements mention columns that may not exist: {', '.join(missing_columns[:5])}",
            "severity": "medium",
        })

    # Check for sufficient data
    total_rows = sum(metadata.get("row_count", 0) for metadata in csv_metadata)
    if total_rows == 0:
        blockers.append({
            "type": "no_data",
            "message": "CSV files appear to be empty",
            "severity": "critical",
        })
    elif total_rows < 10:
        concerns.append({
            "type": "insufficient_data",
            "message": f"Only {total_rows} total rows available. Results may not be meaningful.",
            "severity": "high",
        })

    # Check for joins if multiple files
    if len(csv_metadata) > 1:
        # Look for common columns for joining
        column_sets = [set(m.get("columns", [])) for m in csv_metadata]
        common_columns = set.intersection(*column_sets)

        if not common_columns:
            concerns.append({
                "type": "no_join_keys",
                "message": "Multiple CSV files but no common columns found for joining",
                "severity": "medium",
            })
            recommendations.append({
                "type": "specify_join_logic",
                "message": "Consider specifying how to relate data from different files",
            })

    # Check for data quality issues
    for metadata in csv_metadata:
        filename = metadata.get("filename", "unknown")

        # High missing values
        missing_pct = metadata.get("missing_percentage", {})
        high_missing = [col for col, pct in missing_pct.items() if pct > 50]

        if high_missing:
            concerns.append({
                "type": "high_missing_values",
                "file": filename,
                "message": f"Columns with >50% missing values: {', '.join(high_missing)}",
                "severity": "medium",
            })

    # Determine feasibility
    feasible = len(blockers) == 0

    return {
        "feasible": feasible,
        "blockers": blockers,
        "concerns": concerns,
        "recommendations": recommendations,
        "summary": _generate_feasibility_summary(feasible, len(blockers), len(concerns)),
    }


def _generate_feasibility_summary(
    feasible: bool,
    blocker_count: int,
    concern_count: int
) -> str:
    """Generate a human-readable feasibility summary."""
    if feasible:
        if concern_count == 0:
            return "✓ Analysis is feasible with no concerns"
        elif concern_count <= 2:
            return f"✓ Analysis is feasible with {concern_count} minor concern(s)"
        else:
            return f"⚠ Analysis is feasible but has {concern_count} concern(s) to address"
    else:
        return f"✗ Analysis cannot proceed: {blocker_count} critical blocker(s)"
