"""
Simple test script for Coder Agent using same configuration as Planner Agent.

This script creates a minimal Business Logic Plan and tests the Coder Agent
with a simple workflow to verify it works correctly.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ira_builder.agents.coder import create_coder_agent
from ira_builder.utils.logger import setup_logging, get_logger
from ira_builder.utils.config import get_config

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


# Simple Business Logic Plan for testing
SIMPLE_BUSINESS_LOGIC_PLAN = """
# Business Logic Plan - Simple Test

## **Workflow Purpose**
Load a CSV file, perform basic filtering, and save the result.
This is a simple test to verify the Coder Agent can generate and execute code.

## **Required Files**

```json
[
  {
    "file_name": "FBL3N.csv",
    "required_columns": ["Document_Date", "Posting_Date", "Amount"]
  }
]
```

**Column Descriptions:**
- **Document_Date**: The document date
- **Posting_Date**: The posting date
- **Amount**: Transaction amount

## **Requirements**

**Q1: What should the code do?**
- User Response: Load the CSV, convert dates to datetime format, and save all records to output

## **Business Logic**

1. **Load Data:**
   - Load FBL3N.csv
   - Print number of rows loaded

2. **Convert Date Columns:**
   - Convert Document_Date to datetime
   - Convert Posting_Date to datetime
   - Handle any conversion errors

3. **Basic Validation:**
   - Check that we have data
   - Print column names

4. **Save Output:**
   - Save all records to output file
   - Print confirmation

## **Output Dataframe Structure**

| Column Name | Description | Source/Calculation |
|-------------|-------------|-------------------|
| Document_Date | Document date | From input (converted) |
| Posting_Date | Posting date | From input (converted) |
| Amount | Transaction amount | From input |

All other columns from the input file should also be included.
"""


async def test_coder_simple():
    """Simple test of Coder Agent functionality."""

    print("\n" + "="*80)
    print("CODER AGENT - SIMPLE TEST")
    print("="*80)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return False

    print(f"✓ Found API key: {api_key[:20]}...")
    print()

    # Get configuration
    config = get_config()
    model = config.openai_chat_model_id
    print(f"Using model: {model}")
    print()

    # Verify test CSV exists
    csv_file = "tests/fixtures/sample_csvs/FBL3N.csv"
    if not Path(csv_file).exists():
        print(f"❌ ERROR: Test CSV not found: {csv_file}")
        return False

    print(f"✓ Test CSV found: {csv_file}")
    print()

    # Create Coder Agent with same model as Planner
    print("Creating Coder Agent...")
    try:
        coder = create_coder_agent(
            model=model,  # Use same model as Planner
            temperature=0.3,
            max_iterations=3,
            execution_timeout=120
        )
        print("✓ Coder Agent created")
        print()
    except Exception as e:
        print(f"❌ Failed to create Coder Agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Initialize workflow
    print("Initializing workflow...")
    try:
        init_result = await coder.initialize_workflow(
            workflow_name="Simple_Test_Workflow",
            business_logic_plan=SIMPLE_BUSINESS_LOGIC_PLAN,
            csv_filepaths=[csv_file],
            output_filename="simple_test_result.csv"
        )
        print(f"✓ Workflow initialized")
        print(f"  Work Dir: {init_result['work_dir']}")
        print(f"  Output: {init_result['output_path']}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Generate and execute code
    print("-" * 80)
    print("Generating and Executing Code...")
    print("-" * 80)
    print()
    print("This will:")
    print("  1. Generate Python pandas code")
    print("  2. Validate syntax")
    print("  3. Execute the code")
    print("  4. Validate output")
    print("  5. Retry if errors (up to 3 times)")
    print()
    print("Please wait...\n")

    try:
        result = await coder.generate_and_execute_code()

        print("\n" + "="*80)
        print("RESULT")
        print("="*80)
        print()

        if result['status'] == 'success':
            print("✅ SUCCESS - Code generated and executed!")
            print()
            print(f"Iterations: {result['iterations']}")
            print(f"Output File: {result['output_path']}")
            print()

            # Output validation
            val = result['output_validation']
            print("Output Validation:")
            print(f"  Valid: {val['valid']}")
            print(f"  Rows: {val['row_count']:,}")
            print(f"  Columns: {val['column_count']}")
            print(f"  Column Names: {', '.join(val['columns'][:5])}{'...' if len(val['columns']) > 5 else ''}")
            print()

            # Show generated code
            print("-" * 80)
            print("Generated Code:")
            print("-" * 80)
            code_lines = result['code'].split('\n')
            # Show first 50 lines
            for i, line in enumerate(code_lines[:50], 1):
                print(f"{i:3d} | {line}")
            if len(code_lines) > 50:
                print(f"... ({len(code_lines) - 50} more lines)")
            print()

            # Show preview
            print("-" * 80)
            print("Output Preview:")
            print("-" * 80)
            print(result['output_preview'])
            print()

            return True

        else:
            print("❌ FAILED - Could not generate working code")
            print()
            print(f"Error: {result.get('error')}")
            print(f"Iterations: {result.get('iterations', 0)}")
            print()

            if result.get('last_execution_result'):
                last = result['last_execution_result']
                print("Last Execution:")
                print(f"  Status: {last['status']}")
                print(f"  Exit Code: {last.get('exit_code')}")
                if last.get('error_message'):
                    print(f"  Error: {last['error_message']}")
                print()

            if result.get('last_code'):
                print("-" * 80)
                print("Last Generated Code (first 30 lines):")
                print("-" * 80)
                code_lines = result['last_code'].split('\n')
                for i, line in enumerate(code_lines[:30], 1):
                    print(f"{i:3d} | {line}")
                print()

            return False

    except Exception as e:
        print(f"❌ Exception during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""

    print("\n" + "="*80)
    print("CODER AGENT TEST")
    print("="*80)
    print()

    success = await test_coder_simple()

    print("\n" + "="*80)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("="*80)
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
