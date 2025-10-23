"""
Test script for the enhanced Data Analyzer with categorical enrichment.

This script tests the new categorical enrichment feature that intelligently
selects and expands categorical column values based on workflow descriptions.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.ira_builder.agents.data_analyser import create_dataset_analyzer
from ai.ira_builder.utils.logger import get_logger

logger = get_logger(__name__)


async def test_categorical_enrichment():
    """Test the categorical enrichment feature with a sample workflow"""

    print("=" * 80)
    print("TESTING DATA ANALYZER WITH CATEGORICAL ENRICHMENT")
    print("=" * 80)
    print()

    # Sample workflow description (similar to the real use case)
    workflow_description = """
    Highlight cases of duplicate vouchers. Consider standard and credit document type only.
    Filter out cancelled and Null cases from Invoice Validation Status.
    Also exclude vendor name containing word "Income Tax".
    Exclude rows wherein Supplier Invoice No is blank.
    After that create a new column sanitised Vendor Supplier Invoice No means remove any
    special characters from it, starting or trailing spaces from it.
    After that create a key by concat the sanitised supplier invoice number, Vendor Number,
    and Invoice Amount and highlight the cases where against the key there more than 1
    distinct Voucher Number also create a column case id on the basis of key using dense_rank.
    Share the cases with duplicate cases only (Also in the output if any row is coming as
    duplicate with all the same information, remove that as well)
    """

    # You'll need to replace this with an actual CSV file path
    # For testing, you can create a sample CSV with these columns:
    # Document Type, Invoice Validation Status, Vendor Name, Supplier Invoice No, etc.
    csv_file_path = "path/to/your/test/file.csv"

    # Check if file exists
    if not Path(csv_file_path).exists():
        print(f"⚠️  Test CSV file not found: {csv_file_path}")
        print()
        print("To test this feature, create a CSV file with columns like:")
        print("  - Document Type (with values: STANDARD, CREDIT, Stndrd, CANCELLED)")
        print("  - Invoice Validation Status (with values: Validated, Cancelled, Pending)")
        print("  - Vendor Name (with various vendor names including some with 'Income Tax')")
        print("  - Supplier Invoice No, Vendor Number, Invoice Amount, Voucher Number")
        print()
        print("Then update the csv_file_path variable in this script.")
        return

    try:
        # Create the analyzer
        print("📊 Creating Data Analyzer...")
        analyzer = create_dataset_analyzer(model="gpt-4o", provider="openai")
        print("✅ Data Analyzer created successfully")
        print()

        # Analyze the dataset
        print("🔍 Analyzing dataset with categorical enrichment...")
        print(f"   File: {csv_file_path}")
        print(f"   Workflow: {workflow_description[:100]}...")
        print()

        dataset_intel = await analyzer.analyze_dataset(
            csv_filepaths=[csv_file_path],
            workflow_description=workflow_description
        )

        print("✅ Analysis complete!")
        print()

        # Display results
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        print()

        print(f"📁 Dataset Summary: {dataset_intel.dataset_summary}")
        print(f"🏢 Business Domain: {dataset_intel.business_domain}")
        print()

        # Show file intelligence
        for file_intel in dataset_intel.files:
            print(f"📄 File: {file_intel.filename}")
            print(f"   Rows: {file_intel.row_count:,}")
            print(f"   Columns: {file_intel.column_count}")
            print(f"   Business Domain: {file_intel.inferred_business_domain}")
            print()

            # Show categorical enrichment results (the main feature we're testing)
            if file_intel.categorical_enrichment:
                print("   🎯 CATEGORICAL ENRICHMENT RESULTS:")
                print("   " + "-" * 70)
                for col_name, enrichment_data in file_intel.categorical_enrichment.items():
                    values = enrichment_data.get('values', [])
                    method = enrichment_data.get('method', 'unknown')
                    search_keyword = enrichment_data.get('search_keyword')

                    print(f"   • Column: {col_name}")
                    print(f"     Method: {method}")
                    if search_keyword:
                        print(f"     Search Keyword: '{search_keyword}'")
                    print(f"     Values Found: {len(values)}")
                    print(f"     Values: {', '.join(map(str, values[:15]))}")
                    if len(values) > 15:
                        print(f"     ... and {len(values) - 15} more")
                    print()
            else:
                print("   ⚠️  No categorical enrichment data (workflow may not have filter requirements)")
                print()

        # Show the formatted context (what RAA will see)
        print("=" * 80)
        print("FORMATTED CONTEXT FOR RAA")
        print("=" * 80)
        print()
        print(dataset_intel.formatted_context)
        print()

        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_categorical_enrichment())
