"""
Unit tests for CSV analysis tools.

Tests the functionality of CSV analysis, validation, and summarization tools.
"""

import pytest
from pathlib import Path
from ira_builder.tools.csv_tools import (
    analyze_csv_structure,
    get_csv_summary,
    validate_column_references,
    get_column_data_preview,
    compare_csv_schemas,
    detect_data_quality_issues,
)
from ira_builder.exceptions.errors import ValidationException


# Get the path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_csvs"
SALES_CSV = str(FIXTURES_DIR / "sales_data.csv")
PRODUCTS_CSV = str(FIXTURES_DIR / "products.csv")
CUSTOMERS_CSV = str(FIXTURES_DIR / "customers.csv")


class TestAnalyzeCSVStructure:
    """Tests for analyze_csv_structure function."""

    def test_analyze_valid_csv(self):
        """Test analyzing a valid CSV file."""
        result = analyze_csv_structure(SALES_CSV)

        assert result["filename"] == "sales_data.csv"
        assert result["row_count"] == 30
        assert result["column_count"] == 9
        assert "date" in result["columns"]
        assert "product_id" in result["columns"]
        assert "total_amount" in result["columns"]

    def test_analyze_csv_metadata(self):
        """Test that all metadata fields are present."""
        result = analyze_csv_structure(SALES_CSV)

        required_fields = [
            "filename",
            "path",
            "columns",
            "dtypes",
            "row_count",
            "column_count",
            "sample_data",
            "statistics",
            "missing_values",
            "categorical_info",
            "type_summary",
            "analyzed_at",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_analyze_csv_sample_data(self):
        """Test that sample data is included."""
        result = analyze_csv_structure(SALES_CSV)

        assert len(result["sample_data"]) == 5
        assert isinstance(result["sample_data"], list)
        assert isinstance(result["sample_data"][0], dict)

    def test_analyze_csv_statistics(self):
        """Test statistical analysis of numerical columns."""
        result = analyze_csv_structure(SALES_CSV)

        assert "quantity" in result["statistics"]
        assert "total_amount" in result["statistics"]

        # Check quantity statistics structure
        qty_stats = result["statistics"]["quantity"]
        assert "mean" in qty_stats
        assert "std" in qty_stats
        assert "min" in qty_stats
        assert "max" in qty_stats

    def test_analyze_csv_categorical_info(self):
        """Test categorical column analysis."""
        result = analyze_csv_structure(SALES_CSV)

        assert "category" in result["categorical_info"]
        cat_info = result["categorical_info"]["category"]

        assert "unique_count" in cat_info
        assert "top_values" in cat_info
        assert isinstance(cat_info["top_values"], dict)

    def test_analyze_nonexistent_file(self):
        """Test handling of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            analyze_csv_structure("nonexistent_file.csv")

    def test_analyze_invalid_extension(self):
        """Test handling of invalid file extension."""
        with pytest.raises(ValidationException):
            analyze_csv_structure("somefile.txt")


class TestGetCSVSummary:
    """Tests for get_csv_summary function."""

    def test_summary_single_file(self):
        """Test generating summary for a single CSV file."""
        summary = get_csv_summary([SALES_CSV])

        assert "sales_data.csv" in summary
        assert "Rows:" in summary
        assert "Columns:" in summary

    def test_summary_multiple_files(self):
        """Test generating summary for multiple CSV files."""
        summary = get_csv_summary([SALES_CSV, PRODUCTS_CSV])

        assert "sales_data.csv" in summary
        assert "products.csv" in summary

    def test_summary_includes_column_info(self):
        """Test that summary includes column information."""
        summary = get_csv_summary([SALES_CSV])

        # Should include column names
        assert "date" in summary
        assert "product_id" in summary
        assert "total_amount" in summary

    def test_summary_empty_list(self):
        """Test handling of empty file list."""
        summary = get_csv_summary([])
        assert isinstance(summary, str)


class TestValidateColumnReferences:
    """Tests for validate_column_references function."""

    def test_validate_all_columns_exist(self):
        """Test validation when all columns exist."""
        available = ["date", "product", "amount"]
        referenced = ["date", "amount"]

        result = validate_column_references(referenced, available)

        assert result["valid"] is True
        assert len(result["missing_columns"]) == 0
        assert result["match_percentage"] == 100.0

    def test_validate_missing_columns(self):
        """Test validation when some columns are missing."""
        available = ["date", "product", "amount"]
        referenced = ["date", "price", "quantity"]

        result = validate_column_references(referenced, available)

        assert result["valid"] is False
        assert "price" in result["missing_columns"]
        assert "quantity" in result["missing_columns"]
        assert result["match_percentage"] < 100.0

    def test_validate_extra_columns(self):
        """Test identification of unreferenced columns."""
        available = ["date", "product", "amount", "quantity"]
        referenced = ["date", "amount"]

        result = validate_column_references(referenced, available)

        assert "product" in result["extra_columns"]
        assert "quantity" in result["extra_columns"]

    def test_validate_empty_references(self):
        """Test validation with no referenced columns."""
        available = ["date", "product"]
        referenced = []

        result = validate_column_references(referenced, available)

        assert result["match_percentage"] == 0.0
        assert result["total_referenced"] == 0


class TestGetColumnDataPreview:
    """Tests for get_column_data_preview function."""

    def test_preview_existing_column(self):
        """Test getting preview of an existing column."""
        result = get_column_data_preview(SALES_CSV, "product_name", num_samples=5)

        assert result["column"] == "product_name"
        assert len(result["samples"]) <= 5
        assert result["unique_count"] > 0
        assert "Widget A" in result["samples"]

    def test_preview_numerical_column(self):
        """Test getting preview of numerical column."""
        result = get_column_data_preview(SALES_CSV, "quantity", num_samples=10)

        assert result["column"] == "quantity"
        assert all(isinstance(x, (int, float)) for x in result["samples"])

    def test_preview_nonexistent_column(self):
        """Test handling of nonexistent column."""
        with pytest.raises(ValidationException):
            get_column_data_preview(SALES_CSV, "nonexistent_column")

    def test_preview_includes_null_count(self):
        """Test that preview includes null count."""
        result = get_column_data_preview(SALES_CSV, "product_name")

        assert "null_count" in result
        assert isinstance(result["null_count"], int)


class TestCompareCSVSchemas:
    """Tests for compare_csv_schemas function."""

    def test_compare_two_files(self):
        """Test comparing schemas of two CSV files."""
        result = compare_csv_schemas([SALES_CSV, PRODUCTS_CSV])

        assert "product_id" in result["common_columns"]
        assert result["schema_compatibility"] is True

    def test_compare_identifies_unique_columns(self):
        """Test identification of unique columns per file."""
        result = compare_csv_schemas([SALES_CSV, PRODUCTS_CSV])

        assert "unique_columns" in result
        assert "sales_data.csv" in result["unique_columns"]
        assert "products.csv" in result["unique_columns"]

    def test_compare_suggests_join_keys(self):
        """Test suggestion of potential join keys."""
        result = compare_csv_schemas([SALES_CSV, PRODUCTS_CSV])

        assert "suggested_join_keys" in result
        assert "product_id" in result["suggested_join_keys"]

    def test_compare_single_file(self):
        """Test comparison with single file."""
        result = compare_csv_schemas([SALES_CSV])

        assert result["schema_compatibility"] is False
        assert "Need at least 2 files" in result["message"]


class TestDetectDataQualityIssues:
    """Tests for detect_data_quality_issues function."""

    def test_detect_no_issues(self):
        """Test detection when data quality is good."""
        result = detect_data_quality_issues(SALES_CSV)

        # Sales data should be clean
        assert isinstance(result["has_issues"], bool)
        assert isinstance(result["issues"], list)

    def test_detect_issue_structure(self):
        """Test structure of detected issues."""
        result = detect_data_quality_issues(SALES_CSV)

        for issue in result["issues"]:
            assert "type" in issue
            assert "severity" in issue
            assert "description" in issue
            assert "recommendation" in issue

    def test_detect_includes_summary(self):
        """Test that summary is included."""
        result = detect_data_quality_issues(SALES_CSV)

        assert "summary" in result
        assert isinstance(result["summary"], str)
        assert "issue" in result["summary"].lower()


# Fixtures for pytest
@pytest.fixture
def sample_csv_path():
    """Fixture providing path to sample CSV."""
    return SALES_CSV


@pytest.fixture
def sample_metadata():
    """Fixture providing sample CSV metadata."""
    return analyze_csv_structure(SALES_CSV)


def test_csv_tools_integration(sample_csv_path, sample_metadata):
    """Integration test using multiple CSV tools together."""
    # Analyze structure
    metadata = analyze_csv_structure(sample_csv_path)
    assert metadata["row_count"] > 0

    # Get summary
    summary = get_csv_summary([sample_csv_path])
    assert len(summary) > 0

    # Validate columns
    columns_to_check = ["date", "product_id"]
    validation = validate_column_references(
        columns_to_check,
        metadata["columns"]
    )
    assert validation["valid"] is True

    # Check data quality
    quality = detect_data_quality_issues(sample_csv_path)
    assert "has_issues" in quality
