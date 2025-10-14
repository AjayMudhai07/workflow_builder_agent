"""
Pytest configuration and shared fixtures for IRA Workflow Builder tests.

This module provides common test fixtures and configuration used across
all test modules.
"""

import pytest
from pathlib import Path
import sys

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_csvs_dir(fixtures_dir):
    """Path to sample CSV files."""
    return fixtures_dir / "sample_csvs"


@pytest.fixture
def sales_csv_path(sample_csvs_dir):
    """Path to sales_data.csv fixture."""
    return str(sample_csvs_dir / "sales_data.csv")


@pytest.fixture
def products_csv_path(sample_csvs_dir):
    """Path to products.csv fixture."""
    return str(sample_csvs_dir / "products.csv")


@pytest.fixture
def customers_csv_path(sample_csvs_dir):
    """Path to customers.csv fixture."""
    return str(sample_csvs_dir / "customers.csv")


@pytest.fixture
def all_csv_paths(sales_csv_path, products_csv_path, customers_csv_path):
    """List of all sample CSV paths."""
    return [sales_csv_path, products_csv_path, customers_csv_path]


@pytest.fixture
def sample_business_logic():
    """Sample business logic document for testing."""
    return {
        "summary": "Analyze sales data to identify top performing products",
        "data_sources": ["sales_data.csv", "products.csv"],
        "requirements": [
            "Calculate total revenue by product",
            "Calculate total quantity sold by product",
            "Join sales data with product information",
            "Filter out discontinued products",
            "Sort results by total revenue descending",
        ],
        "analysis_steps": [
            "Load sales data and product data",
            "Join datasets on product_id",
            "Filter out rows where discontinued = 'Yes'",
            "Group by product_name and product_id",
            "Calculate sum of total_amount and sum of quantity",
            "Sort by total revenue in descending order",
            "Save results to CSV",
        ],
        "expected_output": (
            "CSV file with columns: product_id, product_name, total_revenue, "
            "total_quantity_sold, sorted by total_revenue descending"
        ),
        "assumptions": [
            "All product_ids in sales data exist in products data",
            "total_amount field represents actual revenue",
            "Discontinued products should be excluded from analysis",
        ],
        "constraints": [
            "Only include products with at least 1 sale",
            "Revenue values should be non-negative",
        ],
    }


@pytest.fixture
def sample_workflow_config():
    """Sample workflow configuration for testing."""
    return {
        "workflow_name": "Q1 Sales Analysis",
        "workflow_description": "Analyze first quarter sales to identify trends and top performers",
        "csv_files": ["sales_data.csv", "products.csv"],
    }


@pytest.fixture
def mock_csv_metadata():
    """Mock CSV metadata for testing."""
    return [
        {
            "filename": "sales_data.csv",
            "columns": ["date", "product_id", "product_name", "quantity", "total_amount"],
            "row_count": 100,
            "dtypes": {
                "date": "object",
                "product_id": "object",
                "product_name": "object",
                "quantity": "int64",
                "total_amount": "float64",
            },
        },
        {
            "filename": "products.csv",
            "columns": ["product_id", "product_name", "category", "price"],
            "row_count": 50,
            "dtypes": {
                "product_id": "object",
                "product_name": "object",
                "category": "object",
                "price": "float64",
            },
        },
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
