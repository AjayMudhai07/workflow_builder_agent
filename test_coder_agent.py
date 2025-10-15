"""
Test script for Coder Agent.

This script tests the complete Coder Agent workflow:
1. Initialize with Business Logic Plan
2. Generate Python code
3. Execute code
4. Handle errors and iterate
5. Validate output
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ira_builder.agents.coder import create_coder_agent
from ira_builder.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


# Sample Business Logic Plan (from Planner Agent)
SAMPLE_BUSINESS_LOGIC_PLAN = """

# Business Logic Plan

## **Workflow Purpose**
Identify potential accounting irregularities where the Document Date falls in a later accounting month than the Posting Date for the same line item. This flags possible backdating, improper period cut-off, or data entry errors that can distort financial reporting across periods. The workflow evaluates every line item and outputs an Exception_Flag along with the month difference and sufficient business context for review.

## **Required Files**

```json
[
  {
    "file_name": "FBL3N.csv",
    "required_columns": [
      "Company Code",
      "Document Number",
      "Document Type",
      "G/L Account",
      "G/L Acct Long Text",
      "G/L Acct Long Text.1",
      "Cost Center",
      "Profit Center",
      "Document Date",
      "Posting Date",
      "Posting Key",
      "Year/month",
      "Amount in local currency",
      "Local Currency",
      "Amount in doc. curr.",
      "Document currency",
      "Text",
      "Document Header Text",
      "Reference",
      "Reference Key 1",
      "Reference Key 2",
      "Reference Key 3",
      "Entry Date",
      "User Name",
      "Offsett.account type",
      "Offsetting acct no.",
      "Purchasing Document",
      "Supplier",
      "Material",
      "Plant"
    ]
  }
]
```

**Column Descriptions:**
- Company Code: Legal entity/company identifier for the transaction.
- Document Number: Unique identifier of the accounting document.
- Document Type: Type/category of the accounting document (e.g., journal, accrual, etc.).
- G/L Account: General Ledger account number posted.
- G/L Acct Long Text: Description/name for the G/L account.
- G/L Acct Long Text.1: Additional G/L account description or categorization.
- Cost Center: Cost center associated with the posting (operational responsibility).
- Profit Center: Profit center associated with the posting (management responsibility).
- Document Date: The date printed/recorded on the source document.
- Posting Date: The date the transaction was posted to the books.
- Posting Key: Indicator of debit/credit and line-item function.
- Year/month: Period indicator provided in the source for reference (e.g., 2023/01).
- Amount in local currency: Amount posted in local currency.
- Local Currency: Local currency code of the posting.
- Amount in doc. curr.: Amount in original document currency.
- Document currency: Document currency code.
- Text: Line-item text/narrative.
- Document Header Text: Header-level narrative for the document.
- Reference: Additional reference identifier or note.
- Reference Key 1: Auxiliary reference field 1.
- Reference Key 2: Auxiliary reference field 2.
- Reference Key 3: Auxiliary reference field 3.
- Entry Date: Date the entry was captured in the system.
- User Name: User who posted the transaction.
- Offsett.account type: Type of offset account (e.g., vendor, customer, G/L).
- Offsetting acct no.: Number of the offsetting account.
- Purchasing Document: Related purchasing document number (if any).
- Supplier: Supplier/vendor number (if any).
- Material: Material code (if any).
- Plant: Plant/location identifier (if any).

## **Requirements**
Conversation summary showing the questions asked and responses given:

**Q1: How should we define which records count as “expense transactions” before checking for timing mismatches between Document Date and Posting Date?**
- User Response: Include all records in FBL3N.csv (no pre-filter).

**Q2: To define the timing mismatch, which period basis should we use when comparing Document Date vs Posting Date?**
- User Response: Month-based: flag if Year-Month(Document Date) > Year-Month(Posting Date).

**Q3: Should we include both debit and credit line items in the exceptions, or limit to one side?**
- User Response: Include both debit and credit entries (no filter on Posting Key).

**Q4: Do you want any tolerance so we only flag larger timing gaps?**
- User Response: No tolerance: flag any difference > 0 months (default).

**Q5: Should the earlier Posting Date be limited to the immediately preceding month, or can it be any earlier month?**
- User Response: Flag if Posting Date is any earlier month regardless of fiscal year (no limit).

**Q6: Do you want to exclude reversal/cancellation entries from exceptions?**
- User Response: No — include reversals/cancellations as potential exceptions.

**Q7: Do you want to apply a materiality threshold on Amount in local currency to limit flags to meaningful values?**
- User Response: No threshold — include all amounts.

**Q8: What output granularity do you prefer?**
- User Response: Line-item level: output each flagged row from FBL3N.csv as-is (one row per original line item).

**Q9: To have Exception_Flag show both True and False, should the output include all line items or only exceptions?**
- User Response: Include all line items from FBL3N.csv with Exception_Flag (True/False) and Month_Diff computed for every row.

## **Business Logic**
Detailed step-by-step logic to generate the answer dataframe:

1. **Load Data:**
   - Load FBL3N.csv.
   - Ensure the following columns are available for processing and output: Company Code, Document Number, Document Type, G/L Account, G/L Acct Long Text, G/L Acct Long Text.1, Cost Center, Profit Center, Document Date, Posting Date, Posting Key, Year/month, Amount in local currency, Local Currency, Amount in doc. curr., Document currency, Text, Document Header Text, Reference, Reference Key 1, Reference Key 2, Reference Key 3, Entry Date, User Name, Offsett.account type, Offsetting acct no., Purchasing Document, Supplier, Material, Plant.

2. **Filter Records:**
   - Include all records; no pre-filter by account type, document type, cost center, amount, or reversals.
   - Include both debit and credit entries (no filter on Posting Key).
   - No fiscal-year restriction; cross-year comparisons are allowed.

3. **Apply Business Rules:**
   - Period basis: Month-level comparison between Document Date and Posting Date.
   - Define “Exception” if the document month is later than the posting month:
     - Exception condition: Year-Month(Document Date) > Year-Month(Posting Date).
     - No tolerance: any positive month difference is flagged.
     - No limit on how early the Posting Date can be relative to Document Date (can span multiple years).

4. **Create Derived Columns:**
   - Doc_YearMonth: Year-Month extracted from Document Date.
   - Post_YearMonth: Year-Month extracted from Posting Date.
   - Month_Diff: Number of months between Document Date and Posting Date, computed as:
     - Month_Diff = 12 × (Year(Document Date) − Year(Posting Date)) + (Month(Document Date) − Month(Posting Date))
   - Exception_Flag:
     - True if Month_Diff > 0 (i.e., Doc_YearMonth > Post_YearMonth); otherwise False.
   - Exception_Reason:
     - “Document month later than posting month” when Exception_Flag = True; blank otherwise.

5. **Final Dataset:**
   - Output all original line items (no filtering-out of non-exceptions).
   - Include all identification, business logic, and context columns listed below, plus derived columns: Doc_YearMonth, Post_YearMonth, Month_Diff, Exception_Flag, Exception_Reason.
   - Each row remains at line-item granularity (one output row per input row).

## **Output Dataframe Structure**
List all columns in the output CSV with their descriptions:

| Column Name | Description | Source/Calculation |
|-------------|-------------|-------------------|
| Company Code | Legal entity/company identifier | From input |
| Document Number | Unique identifier of the accounting document | From input |
| Document Type | Type/category of the accounting document | From input |
| G/L Account | General Ledger account number posted | From input |
| G/L Acct Long Text | G/L account description | From input |
| G/L Acct Long Text.1 | Additional G/L account description/category | From input |
| Cost Center | Cost center associated with the posting | From input |
| Profit Center | Profit center associated with the posting | From input |
| Document Date | Date on the source document | From input |
| Posting Date | Date posted to the books | From input |
| Posting Key | Debit/credit indicator and line item function | From input |
| Year/month | Original period indicator from source (e.g., 2023/01) | From input |
| Amount in local currency | Amount posted in local currency | From input |
| Local Currency | Local currency code | From input |
| Amount in doc. curr. | Amount in the original document currency | From input |
| Document currency | Document currency code | From input |
| Text | Line-item text/narrative | From input |
| Document Header Text | Header-level narrative | From input |
| Reference | Additional reference identifier | From input |
| Reference Key 1 | Auxiliary reference field 1 | From input |
| Reference Key 2 | Auxiliary reference field 2 | From input |
| Reference Key 3 | Auxiliary reference field 3 | From input |
| Entry Date | Date the entry was captured | From input |
| User Name | User who posted the transaction | From input |
| Offsett.account type | Type of offset account | From input |
| Offsetting acct no. | Offsetting account number | From input |
| Purchasing Document | Related purchasing document number | From input |
| Supplier | Supplier/vendor number | From input |
| Material | Material code | From input |
| Plant | Plant/location identifier | From input |
| Doc_YearMonth | Year-Month derived from Document Date | Calculated: Year-Month(Document Date) |
| Post_YearMonth | Year-Month derived from Posting Date | Calculated: Year-Month(Posting Date) |
| Month_Diff | Month difference between Document and Posting dates | Calculated: 12×(Year(Document Date)−Year(Posting Date)) + (Month(Document Date)−Month(Posting Date)) |
| Exception_Flag | True if Doc_YearMonth > Post_YearMonth, else False | Calculated: Month_Diff > 0 |
| Exception_Reason | Reason text when flagged | Calculated: “Document month later than posting month” if Exception_Flag else blank |

Note: Each row in the output represents one original line item from FBL3N.csv, evaluated for timing mismatch between Document Date and Posting Date, with an Exception_Flag indicating whether it is an exception.
"""


async def test_coder_agent():
    """Test the Coder Agent with a sample Business Logic Plan."""
    print("\n" + "="*80)
    print("CODER AGENT TEST")
    print("="*80)
    print("\nTesting code generation and execution workflow\n")

    # Configuration
    WORKFLOW_NAME = "Expense Date Mismatch Analysis"
    CSV_FILES = ["tests/fixtures/sample_csvs/FBL3N.csv"]
    MODEL = "o3-mini"
    MAX_ITERATIONS = 4

    print(f"Workflow: {WORKFLOW_NAME}")
    print(f"Model: {MODEL}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"CSV Files: {CSV_FILES}")
    print()

    # Verify CSV files exist
    print("Verifying CSV files...")
    for csv_file in CSV_FILES:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"❌ ERROR: File not found: {csv_file}")
            print(f"   Please ensure test CSV files are available.")
            return
        print(f"  ✓ Found: {csv_file}")
    print()

    # Step 1: Create Coder Agent
    print("-" * 80)
    print("Step 1: Creating Coder Agent")
    print("-" * 80)
    print()

    try:
        coder = create_coder_agent(
            model=MODEL,
            temperature=0.3,
            max_iterations=MAX_ITERATIONS,
            execution_timeout=120
        )
        print("✓ Coder Agent created successfully\n")
    except Exception as e:
        print(f"❌ ERROR creating agent: {str(e)}")
        print("\nPossible issues:")
        print("  1. OPENAI_API_KEY not set (check .env file)")
        print("  2. Invalid model name")
        print("  3. Network connection issue")
        return

    # Step 2: Initialize Workflow
    print("-" * 80)
    print("Step 2: Initializing Workflow")
    print("-" * 80)
    print()

    try:
        init_result = await coder.initialize_workflow(
            workflow_name=WORKFLOW_NAME,
            business_logic_plan=SAMPLE_BUSINESS_LOGIC_PLAN,
            csv_filepaths=CSV_FILES,
            output_filename="expense_mismatches.csv"
        )

        print("✓ Workflow initialized")
        print(f"  - Status: {init_result['status']}")
        print(f"  - Work Directory: {init_result['work_dir']}")
        print(f"  - Output Path: {init_result['output_path']}")
        print()

    except Exception as e:
        print(f"❌ ERROR initializing workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Generate and Execute Code
    print("-" * 80)
    print("Step 3: Generating and Executing Code")
    print("-" * 80)
    print()
    print("This may take a minute as the agent:")
    print("  1. Generates Python code from Business Logic Plan")
    print("  2. Validates syntax")
    print("  3. Executes the code")
    print("  4. Validates output")
    print("  5. Retries if errors occur (up to max iterations)")
    print()

    try:
        result = await coder.generate_and_execute_code()

        print("\n" + "=" * 80)
        print("EXECUTION RESULT")
        print("=" * 80)
        print()

        print(f"Status: {result['status']}")
        print()

        if result['status'] == 'success':
            print("✓ CODE EXECUTED SUCCESSFULLY!")
            print()

            # Show execution details
            print(f"Iterations Required: {result['iterations']}")
            print(f"Output File: {result['output_path']}")
            print()

            # Show output validation
            validation = result['output_validation']
            print("Output Validation:")
            print(f"  - Valid: {validation['valid']}")
            print(f"  - Row Count: {validation['row_count']:,}")
            print(f"  - Column Count: {validation['column_count']}")
            print(f"  - Columns: {', '.join(validation['columns'])}")
            print(f"  - File Size: {validation['file_size_mb']} MB")
            print()

            # Show preview
            print("Output Preview:")
            print(result['output_preview'])
            print()

            # Show generated code
            print("-" * 80)
            print("Generated Code:")
            print("-" * 80)
            print(result['code'])
            print()

        else:
            print("❌ CODE GENERATION FAILED")
            print()

            print(f"Error: {result['error']}")
            print(f"Iterations: {result['iterations']}")
            print()

            if result.get('last_execution_result'):
                print("Last Execution Result:")
                last_result = result['last_execution_result']
                print(f"  - Status: {last_result['status']}")
                print(f"  - Exit Code: {last_result['exit_code']}")
                if last_result.get('error_message'):
                    print(f"  - Error: {last_result['error_message']}")
                print()

            if result.get('last_code'):
                print("-" * 80)
                print("Last Generated Code:")
                print("-" * 80)
                print(result['last_code'])
                print()

    except Exception as e:
        print(f"❌ ERROR during code generation/execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Show Execution Summary
    print("-" * 80)
    print("Execution Summary")
    print("-" * 80)
    print()

    summary = coder.get_execution_summary()
    print(f"Workflow: {summary['workflow_name']}")
    print(f"Total Iterations: {summary['total_iterations']}/{summary['max_iterations']}")
    print()

    if summary['attempts']:
        print("Attempt History:")
        for attempt in summary['attempts']:
            status_icon = "✓" if attempt['status'] == 'success' else "✗"
            print(f"  {status_icon} Iteration {attempt['iteration']}: {attempt['status']}")
    print()

    # Final status
    print("=" * 80)
    if result['status'] == 'success':
        print("✓ TEST PASSED - Coder Agent successfully generated and executed code!")
    else:
        print("✗ TEST FAILED - Coder Agent could not generate working code")
    print("=" * 80)
    print()


async def test_coder_with_intentional_error():
    """Test Coder Agent's error handling with a Business Logic Plan that has issues."""
    print("\n" + "="*80)
    print("CODER AGENT ERROR HANDLING TEST")
    print("="*80)
    print("\nTesting error detection and recovery\n")

    # Business Logic Plan with column name that doesn't exist
    BAD_BUSINESS_LOGIC = """
# Business Logic Plan

## **Workflow Purpose**
Test error handling by requesting a non-existent column.

## **Required Files**

```json
[
  {
    "file_name": "FBL3N.csv",
    "required_columns": ["NonExistentColumn", "Amount"]
  }
]
```

## **Business Logic**

1. Load FBL3N.csv
2. Filter by NonExistentColumn > 100
3. Save result
"""

    CSV_FILES = ["tests/fixtures/sample_csvs/FBL3N.csv"]

    # Verify CSV exists
    if not Path(CSV_FILES[0]).exists():
        print(f"❌ Test CSV not found: {CSV_FILES[0]}")
        return

    print("Creating Coder Agent for error handling test...")
    coder = create_coder_agent(
        model="gpt-4o",
        max_iterations=2,  # Limit iterations for faster test
        execution_timeout=60
    )

    print("Initializing with Business Logic Plan containing errors...")
    await coder.initialize_workflow(
        workflow_name="Error Handling Test",
        business_logic_plan=BAD_BUSINESS_LOGIC,
        csv_filepaths=CSV_FILES
    )

    print("\nGenerating and executing code (should detect error)...")
    result = await coder.generate_and_execute_code()

    print("\n" + "=" * 80)
    print("ERROR HANDLING RESULT")
    print("=" * 80)
    print()

    # The agent should detect the error and try to recover
    # Even if it fails, it should provide useful error information

    print(f"Status: {result['status']}")
    print(f"Iterations: {result.get('iterations', 0)}")

    if result.get('last_execution_result'):
        print(f"\nLast Execution:")
        print(f"  Status: {result['last_execution_result']['status']}")
        if result['last_execution_result'].get('error_message'):
            print(f"  Error: {result['last_execution_result']['error_message'][:200]}...")

    print()
    print("=" * 80)
    print("✓ Error handling test complete")
    print("=" * 80)
    print()


def main():
    """Main entry point."""
    import os

    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        print("=" * 80)
        print("ERROR: No API key configured!")
        print("=" * 80)
        print()
        print("Please add your OpenAI API key to the .env file:")
        print()
        print("  1. Open the .env file in the project root")
        print("  2. Add or update: OPENAI_API_KEY=sk-your-key-here")
        print()
        sys.exit(1)

    # Run tests
    try:
        print("\n" + "="*80)
        print("CODER AGENT TEST SUITE")
        print("="*80)
        print()

        # Test 1: Normal workflow
        asyncio.run(test_coder_agent())

        # Test 2: Error handling (optional, uncomment to run)
        # print("\n" + "="*80)
        # print("Running Error Handling Test...")
        # print("="*80)
        # asyncio.run(test_coder_with_intentional_error())

        print("\n" + "="*80)
        print("ALL TESTS COMPLETE")
        print("="*80)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
