"""
Test script for code executor tools.

This script tests the code execution functionality that will be used
by the Coder Agent to run generated Python code.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ira_builder.tools.code_executor_tools import (
    execute_python_code,
    validate_python_syntax,
    extract_code_from_markdown,
    preview_dataframe,
    validate_output_dataframe,
    analyze_execution_error,
    get_dataframe_summary
)
from ira_builder.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


async def test_1_simple_execution():
    """Test 1: Simple Python code execution"""
    print("\n" + "="*80)
    print("TEST 1: Simple Python Code Execution")
    print("="*80)

    code = """
import pandas as pd

# Create a simple dataframe
data = {'Name': ['Alice', 'Bob', 'Charlie'], 'Age': [25, 30, 35]}
df = pd.DataFrame(data)

print("Created dataframe:")
print(df)
print(f"\\nDataframe shape: {df.shape}")
"""

    work_dir = "./data/test_executor/test1"

    print(f"\n📝 Code to execute:")
    print(code)

    print(f"\n🚀 Executing in: {work_dir}")
    result = await execute_python_code(code, work_dir=work_dir, timeout=30)

    print(f"\n✅ Execution Result:")
    print(f"   Status: {result['status']}")
    print(f"   Exit Code: {result['exit_code']}")
    print(f"\n📤 Output:")
    print(result['output'])

    return result['status'] == 'success'


async def test_2_csv_processing():
    """Test 2: CSV file processing (like what Coder Agent will do)"""
    print("\n" + "="*80)
    print("TEST 2: CSV Processing with Output File")
    print("="*80)

    # First, create a sample CSV to work with
    setup_code = """
import pandas as pd

# Create sample input CSV
sample_data = {
    'Product': ['Widget A', 'Widget B', 'Widget C', 'Widget A', 'Widget B'],
    'Quantity': [10, 20, 15, 25, 30],
    'Price': [100, 200, 150, 100, 200]
}
df = pd.DataFrame(sample_data)
df.to_csv('input_data.csv', index=False)
print("✓ Created input_data.csv")
"""

    work_dir = "./data/test_executor/test2"

    print("\n📝 Setting up test data...")
    setup_result = await execute_python_code(setup_code, work_dir=work_dir)

    if setup_result['status'] != 'success':
        print("❌ Failed to create test data")
        return False

    # Now run the actual analysis code
    analysis_code = """
import pandas as pd

# Load the CSV
df = pd.read_csv('input_data.csv')

print("Original data:")
print(df)

# Perform analysis: Calculate total revenue by product
df['Revenue'] = df['Quantity'] * df['Price']
result = df.groupby('Product').agg({
    'Quantity': 'sum',
    'Revenue': 'sum'
}).reset_index()

print("\\nAggregated results:")
print(result)

# Save output
result.to_csv('output_result.csv', index=False)
print("\\n✓ Saved results to output_result.csv")
"""

    print(f"\n📝 Analysis code:")
    print(analysis_code)

    print(f"\n🚀 Executing analysis...")
    result = await execute_python_code(analysis_code, work_dir=work_dir, timeout=30)

    print(f"\n✅ Execution Result:")
    print(f"   Status: {result['status']}")
    print(f"   Exit Code: {result['exit_code']}")
    print(f"\n📤 Output:")
    print(result['output'])

    # Validate the output file
    if result['status'] == 'success':
        output_path = Path(work_dir) / 'output_result.csv'
        validation = validate_output_dataframe(str(output_path))

        print(f"\n🔍 Output Validation:")
        print(f"   Valid: {validation['valid']}")
        print(f"   Rows: {validation['row_count']}")
        print(f"   Columns: {validation['column_count']}")
        print(f"   Column Names: {validation['columns']}")

        # Preview the output
        if validation['valid']:
            print(f"\n👀 Output Preview:")
            preview = preview_dataframe(str(output_path), rows=10)
            print(preview)

            # Get summary
            print(f"\n📊 Output Summary:")
            summary = get_dataframe_summary(str(output_path))
            print(f"   Columns: {summary['columns']}")
            print(f"   Data Types: {summary['dtypes']}")

        return validation['valid']

    return False


async def test_3_syntax_validation():
    """Test 3: Syntax validation before execution"""
    print("\n" + "="*80)
    print("TEST 3: Syntax Validation")
    print("="*80)

    # Valid code
    valid_code = "print('Hello, World!')"
    print(f"\n✓ Valid code: {valid_code}")
    result = validate_python_syntax(valid_code)
    print(f"   Validation: {result['valid']}")

    # Invalid code
    invalid_code = "print('Hello, World'"  # Missing closing quote
    print(f"\n✗ Invalid code: {invalid_code}")
    result = validate_python_syntax(invalid_code)
    print(f"   Validation: {result['valid']}")
    print(f"   Error: {result['error']}")
    if result['line']:
        print(f"   Line: {result['line']}")

    return True


async def test_4_markdown_extraction():
    """Test 4: Extract code from markdown blocks"""
    print("\n" + "="*80)
    print("TEST 4: Markdown Code Extraction")
    print("="*80)

    markdown_text = """
Here's the code to analyze the data:

```python
import pandas as pd

df = pd.read_csv('data.csv')
print(df.head())
```

This code will load and display the data.
"""

    print("\n📝 Markdown text:")
    print(markdown_text)

    extracted = extract_code_from_markdown(markdown_text)

    print("\n✂️ Extracted code:")
    print(extracted)

    # Verify it's valid Python
    validation = validate_python_syntax(extracted)
    print(f"\n✅ Extracted code is valid: {validation['valid']}")

    return validation['valid']


async def test_5_error_handling():
    """Test 5: Error handling and analysis"""
    print("\n" + "="*80)
    print("TEST 5: Error Handling")
    print("="*80)

    # Code with intentional error
    error_code = """
import pandas as pd

# This will cause a KeyError
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print(df['C'])  # Column 'C' doesn't exist!
"""

    work_dir = "./data/test_executor/test5"

    print(f"\n📝 Code with intentional error:")
    print(error_code)

    print(f"\n🚀 Executing (should fail)...")
    result = await execute_python_code(error_code, work_dir=work_dir, timeout=30)

    print(f"\n✅ Execution Result:")
    print(f"   Status: {result['status']}")
    print(f"   Exit Code: {result['exit_code']}")
    print(f"\n📤 Error Output:")
    print(result['output'])

    # Analyze the error
    if result['status'] == 'error':
        print(f"\n🔍 Error Analysis:")
        analysis = analyze_execution_error(result['output'], error_code)
        print(f"   Error Type: {analysis['error_type']}")
        print(f"   Error Message: {analysis['error_message']}")
        print(f"   Line Number: {analysis['line_number']}")
        print(f"\n💡 Suggested Fix:")
        print(f"   {analysis['suggested_fix']}")

        return analysis['error_type'] == 'KeyError'

    return False


async def test_6_timeout_handling():
    """Test 6: Timeout handling"""
    print("\n" + "="*80)
    print("TEST 6: Timeout Handling")
    print("="*80)

    # Code that takes too long
    timeout_code = """
import time

print("Starting long operation...")
time.sleep(10)  # Sleep for 10 seconds
print("Finished!")
"""

    work_dir = "./data/test_executor/test6"

    print(f"\n📝 Code that will timeout:")
    print(timeout_code)

    print(f"\n🚀 Executing with 3 second timeout...")
    result = await execute_python_code(timeout_code, work_dir=work_dir, timeout=3)

    print(f"\n✅ Execution Result:")
    print(f"   Status: {result['status']}")
    print(f"   Exit Code: {result['exit_code']}")
    print(f"   Error: {result['error_message']}")

    return result['status'] == 'timeout'


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CODE EXECUTOR TOOLS - TEST SUITE")
    print("="*80)
    print("\nTesting the code execution functionality for Coder Agent\n")

    tests = [
        ("Simple Execution", test_1_simple_execution),
        ("CSV Processing", test_2_csv_processing),
        ("Syntax Validation", test_3_syntax_validation),
        ("Markdown Extraction", test_4_markdown_extraction),
        ("Error Handling", test_5_error_handling),
        ("Timeout Handling", test_6_timeout_handling),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' raised exception: {str(e)}", exc_info=True)
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Code executor is ready for Coder Agent.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")


if __name__ == "__main__":
    asyncio.run(main())
