# IRA - Intelligent Record Analyzer 🧠

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](https://github.com/AjayMudhai07/ira)
[![Version](https://img.shields.io/badge/version-0.5.1-orange.svg)](https://github.com/AjayMudhai07/ira)

**IRA (Intelligent Record Analyzer)** is a simple, powerful Python library for CSV data processing workflows, offering four focused modules:

1. **📅 Date/Time Conversion**: Universal date format handling with Excel, timezone, and time-only value support
2. **🧹 String Cleaning**: Simple, predictable string normalization - remove .0 artifacts, fix whitespace, standardize case
3. **🔢 Numeric Cleaning**: Production-ready numeric data cleaning - currency, percentages, formatting, null handling
4. **🔍 CSV Comparison**: Fast, accurate comparison of CSV files with detailed difference reporting


## ✨ What's New in v0.5.1

🔍 **NEW: CSV Comparison Module**: Fast, accurate file comparison with detailed reporting
- ✅ Simple True/False comparison: `ira.compare_csv(file1, file2)`
- ✅ Detailed difference reports: `ira.compare_csv_detailed(file1, file2)`
- ✅ Test assertions: `ira.assert_csv_equal(file1, file2)`
- ✅ NaN-aware comparison (treats NaN == NaN by default)
- ✅ Numeric tolerance support for floating-point comparisons
- ✅ Column order flexibility (can ignore column order)
- ✅ Dtype comparison options
- ✅ Fast-path optimization for large files

## ✨ What's New in v0.5.0

🔢 **Numeric Data Cleaning Module**: Production-ready numeric column cleaning
- ✅ Currency symbol removal ($, €, ₹, USD, EUR, etc.)
- ✅ Thousands separator handling (1,234.56)
- ✅ Negative format conversion: (1234) → -1234, 1234- → -1234
- ✅ Percentage handling (12.5% → 0.125 or 12.5)
- ✅ Null value normalization (N/A, TBD, -, NULL → NaN)
- ✅ Text extraction ("Total: 1234.56" → 1234.56)
- ✅ 10-50x faster than .apply() with vectorized operations
- ✅ Returns numeric dtype (float64/Int64) directly - no extra conversion needed!

## 🚀 Key Features

### 📅 Date/Time Processing (Phase 2 Smart Sampling - DEFAULT)
- **⚡ Phase 2 Smart Sampling**: 7-10x faster with intelligent format detection (default since v0.3.0)
- **🔍 Universal Date Conversion**: Handles 100+ date/time formats automatically
- **📊 Excel Date Support**: Perfect conversion of Excel serial dates (1900/1904 systems)
- **🌍 Timezone Intelligence**: Comprehensive timezone conversion and normalization
- **⏰ Time-Only Processing**: Flexible handling of time values without dates
- **🤖 Auto-Format Detection**: Smart sampling-based detection of date formats in your data

### 🧹 String Cleaning
- **⚡ Excel Artifact Removal**: Clean `.0` suffixes from Excel numeric exports
- **🔧 Whitespace Normalization**: Unicode-aware whitespace standardization
- **📝 Case Standardization**: Consistent case conversion across datasets
- **🏢 Source-Specific Presets**: Different cleaning rules for Excel, SAP, manual data
- **⚙️ Batch Processing**: Clean multiple columns simultaneously with parallel processing

### 🔢 Numeric Cleaning (NEW in v0.5.0)
- **💰 Currency-Aware**: Remove symbols ($, €, ₹) and codes (USD, EUR, INR)
- **📊 Format Handling**: Thousands separators, parentheses negatives, percentages
- **🎯 Null Normalization**: Converts N/A, TBD, -, NULL, #N/A → NaN
- **📝 Text Extraction**: Extract numbers from "Total: 1234.56" or "1234 units"
- **⚡ Vectorized**: 10-50x faster than .apply() with pandas optimized operations
- **✅ Type-Safe**: Always returns numeric dtype (float64 or Int64)

### 🔍 CSV Comparison (NEW in v0.5.1)
- **🎯 Simple API**: Single function call returns True/False
- **📊 Detailed Reports**: Get granular difference information
- **🧪 Test Assertions**: Built-in assertion for unit tests
- **🔢 Numeric Tolerance**: Handle floating-point comparison gracefully
- **📋 Flexible**: Ignore column order, index, or dtype differences
- **⚡ Fast Path**: Optimized for large file comparisons

### 🚀 Performance & Scale
- **⚡ Phase 2 Smart Sampling**: 7-10x faster date conversion for uniform data (default since v0.3.0)
- **📈 High Performance**: 600K+ rows/second date processing, 1M+ rows/second string/numeric cleaning
- **💾 Memory Efficient**: Chunked processing for datasets larger than RAM
- **🔄 Parallel Processing**: Multi-core utilization for batch operations
- **✅ Production Ready**: 100% tested with 26,555+ real-world records, all tests passing

## 📦 Installation

### 🔄 Updating from Previous Version

If you have a previous version of IRA installed, follow these steps to update:

```bash
# Navigate to your existing IRA directory
cd path/to/your/ira

# Pull the latest changes
git pull origin data_analytics

# Reinstall to get new features
pip install -e .

# Verify the update
python -c "import ira; print(f'Updated to IRA v{ira.__version__}!')"

# Test new string cleaning functionality
python -c "
import ira, pandas as pd
# Test the new clean_strings module
test_data = pd.Series(['12345.0', ' ABC Corp '])
clean_result = ira.clean_strings(test_data)
print('✅ New string cleaning module working!')
print(f'Original: {test_data.tolist()}')
print(f'Cleaned:  {clean_result.tolist()}')
"
```

**What's New in v0.3.0:**
- ⚡ **Phase 2 Smart Sampling NOW DEFAULT**: Your code gets 7-10x faster automatically!
- 🧠 **Intelligent format detection**: 10% sampling with automatic pandas vectorization
- 🧹 **New `clean_strings` module**: Remove .0 artifacts, normalize whitespace, standardize case
- 🚀 **Batch processing**: Clean multiple DataFrame columns simultaneously
- 🏢 **Source-specific presets**: Excel, SAP, and manual entry cleaning functions
- 📈 **Performance optimized**: 600K+ rows/second date processing, 1M+ rows/second string processing

### Option 1: Conda Environment (Recommended)

```bash
# Create a new conda environment
conda create -n ira_env python=3.10
conda activate ira_env

# Clone and install IRA
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira
pip install -e .

# Verify installation
python -c "import ira; print(f'IRA v{ira.__version__} installed successfully!')"
```

### Option 2: Python Virtual Environment (venv)

```bash
# Create a new virtual environment
python -m venv ira_env

# Activate the environment
# On Linux/Mac:
source ira_env/bin/activate
# On Windows:
# ira_env\Scripts\activate

# Install dependencies
pip install pandas>=1.3.0 pytz>=2021.1

# Clone and install IRA
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira
pip install -e .

# Verify installation (both modules)
python -c "import ira; print(f'IRA v{ira.__version__} - Date + String Cleaning modules loaded successfully!')"
```

### Option 3: Existing Virtual Environment

```bash
# Activate your existing virtual environment
# Example: source aj/bin/activate
source your_venv_name/bin/activate

# Install IRA dependencies
pip install pandas>=1.3.0 pytz>=2021.1

# Clone and install IRA
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira
pip install -e .

# Test with your existing project imports
python -c "
from backend_api_collection import get_query_data
import ira
import json

# Your existing code works with IRA
qid='9437c57a-4465-49dd-b806-a600a59d3c10'
qd=get_query_data(qid)

# Add IRA date conversion to your workflow
dates_in_data = ['07/30/2024', '2023-12-25', '45503']
converted_dates = [ira.convert_date(d) for d in dates_in_data]

print('✅ IRA integrated with existing project!')
print('Original data:', json.dumps(qd, indent=4) if qd else 'No data')
print('Converted dates:', converted_dates)
"
```

### Option 4: Any Conda Environment

```bash
# Install dependencies
pip install pandas>=1.3.0 pytz>=2021.1

# Clone and install
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira
pip install -e .
```

### Option 5: Dependencies Only

```bash
pip install pandas pytz
# Then manually copy the ira/ folder to your project
```

## 🎯 Quick Start

### 📅 Date/Time Conversion
```python
import ira

# Convert various date formats
result = ira.convert_date("07/30/2024 2:30 PM")
print(result)  # 2024-07-30 14:30:00

# Handle time-only values
time_result = ira.convert_date("11:00 AM")
print(time_result)  # 11:00:00

# Convert Excel serial dates
excel_result = ira.convert_date(45503)
print(excel_result)  # 2024-07-30 00:00:00
```

### 🧹 String Cleaning 
```python
import pandas as pd
import ira

# Clean messy string data
messy_data = pd.Series(['12345.0', ' ABC Corp ', 'XYZ\tInc'])
clean_data = ira.clean_strings(messy_data)
print(clean_data)  # ['12345', 'ABC Corp', 'XYZ Inc']

# Clean company names with case conversion
company_names = pd.Series([' abc corp ', 'xyz inc.', 'DEF\tLTD'])
clean_names = ira.clean_strings(company_names, case_mode='title')
print(clean_names)  # ['Abc Corp', 'Xyz Inc.', 'Def Ltd']

# Batch clean multiple columns
df = pd.DataFrame({
    'vendor_name': [' ABC Corp ', 'xyz inc.', 'DEF\tLTD'],
    'po_number': ['12345.0', '67890.0', '11111.0']
})
clean_df = ira.clean_strings_batch(df, ['vendor_name', 'po_number'],
                                  rules={'remove_excel_artifacts': True,
                                         'normalize_whitespace': True,
                                         'case_mode': 'title'})
print(clean_df)
```

### 🔢 Numeric Cleaning
```python
import pandas as pd
import ira

# Clean currency and formatting
amounts = pd.Series(['$1,234.56', '€2,345.67', '(100.00)', 'N/A'])
clean_amounts = ira.clean_numeric_column(amounts)
print(clean_amounts)  # [1234.56, 2345.67, -100.00, NaN]

# Clean percentages
percentages = pd.Series(['12.5%', '100%', '0.5%'])
clean_pct = ira.clean_percentage_column(percentages)  # Convert to decimal
print(clean_pct)  # [0.125, 1.0, 0.005]

# Batch clean multiple numeric columns
df = pd.DataFrame({
    'Amount': ['$1,234.56', '€2,345.67', '(100.00)'],
    'Tax': ['123.45', '234.56', 'N/A'],
    'Discount': ['10%', '5.5%', '0%']
})
df = ira.clean_numeric_batch(df, ['Amount', 'Tax'])
df = ira.clean_numeric_batch(df, ['Discount'], handle_percentages='convert')
print(df)
# Amount     Tax  Discount
# 1234.56  123.45      0.10
# 2345.67  234.56      0.055
# -100.00     NaN      0.00
```

### 🔍 CSV Comparison
```python
import ira

# Simple comparison - returns True/False
result = ira.compare_csv('file1.csv', 'file2.csv')
print(result)  # True if identical, False otherwise

# Detailed comparison with difference report
equal, report = ira.compare_csv_detailed('expected.csv', 'actual.csv')
if not equal:
    print(f"Files differ!")
    print(f"Shape match: {report['shape_match']}")
    print(f"Column match: {report['columns_match']}")
    print(f"Differences: {report['differences']}")

# Comparison with tolerance for floating-point values
result = ira.compare_csv('file1.csv', 'file2.csv', tolerance=0.001)

# Ignore column order
result = ira.compare_csv('file1.csv', 'file2.csv', ignore_column_order=True)

# Use in unit tests
def test_data_pipeline():
    process_data('input.csv', 'output.csv')
    ira.assert_csv_equal('expected.csv', 'output.csv')  # Raises AssertionError if different
```

### 🔄 Combined Workflow
```python
# Real-world CSV processing pipeline
import pandas as pd
import ira

# Load messy CSV data
df = pd.read_csv('messy_data.csv')

# Clean dates, strings, AND numerics in one workflow
df['Invoice_Date'] = ira.convert_date_column(df['Invoice_Date'])
df = ira.clean_strings_batch(df, ['Vendor_Name', 'PO_Number'],
                             rules={'case_mode': 'title'})
df = ira.clean_numeric_batch(df, ['Amount', 'Tax_Amount'])

# Save processed data
df.to_csv('processed_data.csv', index=False)

# Verify output matches expected results
ira.assert_csv_equal('expected_output.csv', 'processed_data.csv')
print("✅ Clean, analysis-ready data!")
```

---

## 📋 IRA Preprocessing Guidelines - Required Reading

**IMPORTANT**: All CSV workflow preprocessing should follow these standardized steps to ensure data quality and prevent common errors.

### ⚙️ Standard Preprocessing Workflow

Every CSV data processing workflow should apply IRA preprocessing to **all required columns** in the following order:

```python
import pandas as pd
import ira

# Step 1: Load multiple CSV files
df1 = pd.read_csv('po_report.csv', low_memory=False)
df2 = pd.read_csv('vendor_master.csv', low_memory=False)
df3 = pd.read_csv('invoice_data.csv', low_memory=False)

# Step 2: Categorize columns for EACH DataFrame (use _1, _2, _3 suffix)
# DataFrame 1: PO Report
DATE_COLS_1 = ['PO_Date', 'Expected_Delivery_Date']
SAME_COLS_1 = ['PO_Number', 'Vendor_No', 'Item_Code']
UPPER_COLS_1 = ['Status', 'Priority']
LOWER_COLS_1 = ['Department']
TITLE_COLS_1 = ['Vendor_Name']
NUMERIC_COLS_1 = ['PO_Amount', 'Quantity']

# DataFrame 2: Vendor Master
DATE_COLS_2 = ['Registration_Date', 'Last_Updated']
SAME_COLS_2 = ['Vendor_No', 'Tax_ID']
UPPER_COLS_2 = ['Country_Code', 'Category']
LOWER_COLS_2 = ['Email', 'Website']
TITLE_COLS_2 = ['Vendor_Name', 'Contact_Person']
NUMERIC_COLS_2 = ['Credit_Limit']

# DataFrame 3: Invoice Data
DATE_COLS_3 = ['Invoice_Date', 'Payment_Date']
SAME_COLS_3 = ['Invoice_No', 'PO_Number']
UPPER_COLS_3 = ['Payment_Status']
LOWER_COLS_3 = []
TITLE_COLS_3 = []
NUMERIC_COLS_3 = ['Invoice_Amount', 'Tax_Amount']

# Step 3-5: Process EACH DataFrame (dates → strings → numeric)
# Process DataFrame 1
for col in DATE_COLS_1:
    df1[col] = ira.convert_date_column(df1[col])

if SAME_COLS_1:
    df1 = ira.clean_strings_batch(df1, SAME_COLS_1, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'same'})
if UPPER_COLS_1:
    df1 = ira.clean_strings_batch(df1, UPPER_COLS_1, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'upper'})
if LOWER_COLS_1:
    df1 = ira.clean_strings_batch(df1, LOWER_COLS_1, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'lower'})
if TITLE_COLS_1:
    df1 = ira.clean_strings_batch(df1, TITLE_COLS_1, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'title'})
if NUMERIC_COLS_1:
    df1 = ira.clean_numeric_batch(df1, NUMERIC_COLS_1)

# Process DataFrame 2
for col in DATE_COLS_2:
    df2[col] = ira.convert_date_column(df2[col])

if SAME_COLS_2:
    df2 = ira.clean_strings_batch(df2, SAME_COLS_2, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'same'})
if UPPER_COLS_2:
    df2 = ira.clean_strings_batch(df2, UPPER_COLS_2, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'upper'})
if LOWER_COLS_2:
    df2 = ira.clean_strings_batch(df2, LOWER_COLS_2, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'lower'})
if TITLE_COLS_2:
    df2 = ira.clean_strings_batch(df2, TITLE_COLS_2, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'title'})
if NUMERIC_COLS_2:
    df2 = ira.clean_numeric_batch(df2, NUMERIC_COLS_2)

# Process DataFrame 3
for col in DATE_COLS_3:
    df3[col] = ira.convert_date_column(df3[col])

if SAME_COLS_3:
    df3 = ira.clean_strings_batch(df3, SAME_COLS_3, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'same'})
if UPPER_COLS_3:
    df3 = ira.clean_strings_batch(df3, UPPER_COLS_3, rules={'remove_excel_artifacts': True, 'normalize_whitespace': True, 'case_mode': 'upper'})
if NUMERIC_COLS_3:
    df3 = ira.clean_numeric_batch(df3, NUMERIC_COLS_3)

# Step 6: Business logic (merges, calculations, etc.)
merged = df1.merge(df2, on='Vendor_No')  # Works reliably - both are strings!
merged = merged.merge(df3, on='PO_Number')  # Works reliably!
total = merged['Invoice_Amount'].sum()  # Arithmetic works!
```

---

### 🎯 Key Rules

#### Rule 1: Date Columns → Use `ira.convert_date_column()`
```python
# ✅ CORRECT: Convert dates BEFORE string cleaning
df['Invoice_Date'] = ira.convert_date_column(df['Invoice_Date'])

# ❌ WRONG: Don't use clean_strings on date columns
df = ira.clean_strings_batch(df, ['Invoice_Date'])  # NO!
```

**Why?** Date columns need special parsing to handle Excel serials, timezones, and format detection.

---

#### Rule 2: All Other Columns → Use `ira.clean_strings_batch()`
```python
# ✅ CORRECT: Clean ALL non-date columns
df = ira.clean_strings_batch(df,
    ['PO_Number', 'Vendor_Name', 'Amount', 'Quantity'])
```

**What it does:**
- **Always returns object dtype (strings)** - for consistency
- **Removes Excel `.0` artifacts** - `'12345.0'` → `'12345'`
- **Normalizes whitespace** - `' ABC Corp '` → `'ABC Corp'`
- **Preserves NaN values** - `NaN` stays `NaN` (not string `'nan'`)
- **Auto-skips boolean columns** - Prevents logic bugs with warning

**What it does NOT do:**
- Does NOT convert date columns (use `ira.convert_date_column()` instead)
- Does NOT keep numeric types (returns strings)

---

#### Rule 3: Numeric Columns → Use `ira.clean_numeric_batch()`
```python
# ✅ CORRECT: Use clean_numeric for numeric columns
df = ira.clean_numeric_batch(df, ['Amount', 'Quantity', 'Tax_Amount'])
# Returns float64 directly - ready for calculations!

total = df['Amount'].sum()  # ✅ Works immediately!

# ❌ OLD WAY (deprecated): Two-step process
df = ira.clean_strings_batch(df, ['Amount', 'Quantity'])
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
```

**Why use `clean_numeric` instead of `clean_strings`?**
- **One-step cleaning**: Returns numeric dtype (float64) directly
- **Currency-aware**: Removes $, €, ₹, USD, EUR automatically
- **Format handling**: Handles (1234) → -1234, 1,234.56, percentages
- **Null normalization**: Converts N/A, TBD, -, NULL → NaN

---

#### Rule 4: Boolean Columns → DO NOT CLEAN!
```python
# ✅ CORRECT: Exclude boolean columns from cleaning
df = ira.clean_strings_batch(df,
    ['PO_Number', 'Vendor_Name'])  # No 'Is_Approved'

# ⚠️ AUTO-PROTECTED: IRA will skip boolean columns with warning
df = ira.clean_strings_batch(df,
    ['PO_Number', 'Is_Approved'])
# Warning: Skipping boolean columns: ['Is_Approved']
# Result: Is_Approved remains bool dtype (unchanged)
```

**Why?** Converting boolean `False` to string `'False'` causes silent logic bugs (string `'False'` is truthy in Python).

---

### 📊 Column Type Reference Table

| Column Type | IRA Function | Returns | Example Columns | Example Transformation |
|-------------|--------------|---------|-----------------|------------------------|
| **Date/DateTime** | `ira.convert_date_column()` | `datetime64` | Invoice_Date, PO_Date | `'01/03/2024'` → `2024-03-01` |
| **String - Type 1: SAME** | `ira.clean_strings_batch(..., case_mode='same')` | `object` (string) | PO_Number, Vendor_No, Description | `'PO-123'` → `'PO-123'` |
| **String - Type 2: UPPER** | `ira.clean_strings_batch(..., case_mode='upper')` | `object` (string) | Status, Priority, Country_Code | `'Approved'` → `'APPROVED'` |
| **String - Type 3: LOWER** | `ira.clean_strings_batch(..., case_mode='lower')` | `object` (string) | Email, Website, Department | `'SALES@EXAMPLE.COM'` → `'sales@example.com'` |
| **String - Type 4: TITLE** | `ira.clean_strings_batch(..., case_mode='title')` | `object` (string) | Vendor_Name, Customer_Name | `'abc corp'` → `'Abc Corp'` |
| **Numeric** | `ira.clean_numeric_batch()` | `float64` | Amount, Quantity, Tax | `'$1,234.56'` → `1234.56`, `'(100)'` → `-100.0` |
| **Boolean** | ⚠️ **DO NOT CLEAN** | `bool` | Is_Approved, Is_Paid | `True` → `True` (unchanged) |

---

### 🔍 Real-World Example

```python
import pandas as pd
import ira

# Load data with common issues
df = pd.DataFrame({
    'PO_Number': [1001, 1002, 1003],                    # int64 → needs cleaning
    'Vendor_No': [12345.0, 67890.0, 11111.0],           # float64 → has .0 artifacts
    'Vendor_Name': [' ABC Corp ', 'xyz inc', 'DEF Ltd'], # messy strings
    'Amount': ['$1,234.56', '€2,345.67', '(100.00)'],   # currency → needs numeric cleaning
    'Invoice_Date': ['01/03/2024', '15/07/2024', '20/12/2024'],  # dates
    'Is_Approved': [True, False, True]                  # boolean → DON'T CLEAN!
})

print("BEFORE preprocessing:")
print(df.dtypes)
# PO_Number           int64
# Vendor_No         float64
# Vendor_Name        object
# Amount             object  (has currency symbols!)
# Invoice_Date       object
# Is_Approved          bool

# STEP 1: Convert dates
df['Invoice_Date'] = ira.convert_date_column(df['Invoice_Date'])

# STEP 2: Clean strings - Type 1: SAME (IDs)
df = ira.clean_strings_batch(df,
    ['PO_Number', 'Vendor_No'],
    rules={'remove_excel_artifacts': True,
           'normalize_whitespace': True,
           'case_mode': 'same'})

# STEP 2: Clean strings - Type 4: TITLE (names)
df = ira.clean_strings_batch(df,
    ['Vendor_Name'],
    rules={'remove_excel_artifacts': True,
           'normalize_whitespace': True,
           'case_mode': 'title'})

# STEP 3: Clean numeric columns (one step!)
df = ira.clean_numeric_batch(df, ['Amount'])

print("\nAFTER preprocessing:")
print(df.dtypes)
# PO_Number            object  ← String (keep for merging)
# Vendor_No            object  ← String (keep for merging)
# Vendor_Name          object  ← String (Title Case: 'Abc Corp', 'Xyz Inc', 'Def Ltd')
# Amount              float64  ← Numeric (ready for calculations!)
# Invoice_Date     datetime64  ← DateTime (ready for date logic)
# Is_Approved            bool  ← Boolean (unchanged, correct!)

print(df['Amount'])
# 0    1234.56  ← Cleaned from '$1,234.56'
# 1    2345.67  ← Cleaned from '€2,345.67'
# 2    -100.00  ← Cleaned from '(100.00)' - negative!

# STEP 4: Business logic now works reliably
total = df['Amount'].sum()                        # ✅ Arithmetic works: 3480.23
merged = df.merge(other_df, on='PO_Number')      # ✅ Merge works (consistent dtypes)
approved = df[df['Is_Approved']]                 # ✅ Boolean filtering works
late = df[df['Invoice_Date'] > '2024-07-01']    # ✅ Date filtering works
```

---

### 🎯 Status Column Standardization Example

```python
import pandas as pd
import ira

# Data with inconsistent case in status columns
df = pd.DataFrame({
    'Order_ID': [1001, 1002, 1003, 1004],
    'Status': ['Approved', 'approved', 'APPROVED', 'pending'],     # Inconsistent!
    'Priority': ['high', 'High', 'LOW', 'Medium'],                  # Inconsistent!
})

print("BEFORE standardization:")
print(df['Status'].unique())     # ['Approved', 'approved', 'APPROVED', 'pending']
print(df['Priority'].unique())   # ['high', 'High', 'LOW', 'Medium']

# Type 2: UPPER - Standardize status columns
df = ira.clean_strings_batch(df,
    ['Status', 'Priority'],
    rules={'normalize_whitespace': True,
           'case_mode': 'upper'})

print("\nAFTER standardization:")
print(df['Status'].unique())         # ['APPROVED', 'PENDING'] ✅ Consistent!
print(df['Priority'].unique())       # ['HIGH', 'LOW', 'MEDIUM'] ✅ Consistent!

# Now filtering/grouping works reliably
approved = df[df['Status'] == 'APPROVED']  # ✅ Matches all variations!
high_priority = df[df['Priority'] == 'HIGH']  # ✅ Works correctly!
```

**Benefits:**
- **Before:** `'Approved'`, `'approved'`, `'APPROVED'` treated as 3 different values
- **After:** All become `'APPROVED'` - consistent, reliable filtering
- **Use Cases:** Status codes, priority levels, category values, country codes

---

### ⚠️ Common Mistakes to Avoid

#### Mistake 1: Not converting numeric columns back
```python
# ❌ WRONG
df = ira.clean_strings_batch(df, ['Amount'])
total = df['Amount'].sum()  # TypeError: unsupported operand type(s)

# ✅ CORRECT
df = ira.clean_strings_batch(df, ['Amount'])
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
total = df['Amount'].sum()  # Works!
```

#### Mistake 2: Cleaning date columns as strings
```python
# ❌ WRONG
df = ira.clean_strings_batch(df, ['Invoice_Date'])
# Excel serial 45503 → string '45503' (not a date!)

# ✅ CORRECT
df['Invoice_Date'] = ira.convert_date_column(df['Invoice_Date'])
# Excel serial 45503 → datetime '2024-07-30'
```

#### Mistake 3: Cleaning boolean columns
```python
# ❌ WRONG (will get warning, but still...)
df = ira.clean_strings_batch(df, ['Is_Active'])
# Warning issued, column skipped (no harm done)

# ✅ CORRECT
# Simply exclude boolean columns from cleaning list
df = ira.clean_strings_batch(df, ['PO_Number', 'Amount'])
# Is_Active not in list
```

#### Mistake 4: Forgetting to clean before merging
```python
# ❌ WRONG - dtype mismatch error
df1 = pd.read_csv('po_data.csv')  # PO_Number: int64
df2 = pd.read_csv('vhd_data.csv') # PO_Number: object
merged = df1.merge(df2, on='PO_Number')
# ValueError: You are trying to merge on int64 and object columns

# ✅ CORRECT - clean both before merging
df1 = ira.clean_strings_batch(df1, ['PO_Number'])  # → object
df2 = ira.clean_strings_batch(df2, ['PO_Number'])  # → object
merged = df1.merge(df2, on='PO_Number')  # Works!
```

---

### 📖 Summary Checklist

Before writing any CSV workflow, ensure:

- [ ] **Step 1**: All date columns processed with `ira.convert_date_column()`
- [ ] **Step 2**: All other columns (except booleans) cleaned with `ira.clean_strings_batch()`
- [ ] **Step 3**: Numeric columns explicitly converted with `pd.to_numeric()`
- [ ] **Step 4**: Boolean columns excluded from cleaning (IRA auto-protects with warning)
- [ ] **Step 5**: Data ready for business logic (merges, calculations, filtering)

Following these guidelines ensures:
- ✅ No dtype mismatch errors during merges
- ✅ No Excel `.0` artifacts in join keys
- ✅ No NaN becoming string `'nan'`
- ✅ No boolean logic bugs
- ✅ Clean, reliable, production-ready data

---

## 📚 Core Module: `convert_date`

The heart of IRA is the **`convert_date`** module, which provides intelligent date/time conversion capabilities.

### 🔧 Main Functions

#### `ira.convert_date(date_val, **options)`
**Universal date converter** - handles any date/time format automatically.

```python
# Basic usage
ira.convert_date("02/10/2023")           # → 2023-10-02 00:00:00
ira.convert_date("10 Apr 2006")          # → 2006-04-10 00:00:00
ira.convert_date("2024-07-30 15:28")     # → 2024-07-30 15:28:00
ira.convert_date(45503)                  # → 2024-07-30 00:00:00 (Excel)
ira.convert_date("11:00 AM")             # → 11:00:00 (time object)
```

**Parameters:**
- `date_val`: Any date/time value (string, number, datetime object)
- `default_day_first`: Bool - interpret DD/MM vs MM/DD (default: True)
- `handle_timezones`: Bool - process timezone info (default: True)
- `target_timezone`: String - convert to timezone (default: 'UTC')
- `time_only_mode`: String - handle time-only ('time_only', 'add_today', 'error')
- `excel_date_system`: String - Excel system ('1900', '1904')
- `verbose`: Bool - detailed output (default: False)

#### `ira.convert_date_column(series, **options)`
**Batch converter** for pandas Series/DataFrame columns with **Phase 2 Smart Sampling (default)**.

```python
import pandas as pd

# Load CSV with mixed date formats
df = pd.read_csv('data.csv')

# Default (Phase 2 enabled - 7-10x faster for uniform data!)
df['appointment_date'] = ira.convert_date_column(df['appointment_date'])
df['punch_time'] = ira.convert_date_column(df['punch_time'], verbose=True)

# With auto-detection
df['mixed_dates'] = ira.convert_date_column(df['mixed_dates'],
                                           default_day_first=True,
                                           handle_timezones=True)

# Disable Phase 2 (use Phase 1 only if needed)
df['dates'] = ira.convert_date_column(df['dates'], use_smart_sampling=False)
```

**Parameters:**
- `series`: Pandas Series to convert
- `default_day_first`: Interpret ambiguous dates as DD/MM/YYYY (default: True)
- `handle_timezones`: Convert timezone-aware dates (default: True)
- `target_timezone`: Target timezone for conversion (default: 'UTC')
- `time_only_mode`: How to handle time-only values (default: 'time_only')
- `excel_date_system`: Excel date system '1900' or '1904' (default: '1900')
- `output_format`: Output format string (default: 'DD-MM-YYYY')
- `use_smart_sampling`: Enable Phase 2 smart sampling (default: **True** since v0.3.0)
- `verbose`: Print detailed progress information (default: False)

---

### 🚀 Phase 2 Smart Sampling Algorithm (DEFAULT)

**Since v0.3.0**, `convert_date_column()` uses **Phase 2 Smart Sampling** by default for 7-10x faster processing!

#### How It Works

```
1. Column >= 100 rows?
   ↓ YES
2. Sample 10% (stratified: top/middle/bottom)
   ↓
3. Process sample with Phase 1 + format tracking
   ↓
4. Analyze format uniformity
   ↓
   ┌─────────────┴──────────────┐
   │                            │
UNIFORM (≥80% same format)   MIXED (multiple formats)
   │                            │
   ↓                            ↓
5a. Use Pandas Vectorization  5b. Use Phase 1
    (7-10x faster!)               (100% accuracy)
   │                            │
   ↓                            ↓
6. Retry failures with Phase 1
   ↓
7. Return converted dates
```

#### Performance

| Data Type | Speed | Method Used |
|-----------|-------|-------------|
| **Uniform dates** (95-100% same format) | **7-10x faster** ⚡ | Pandas vectorization |
| **Mostly uniform** (80-95% same format) | **5-7x faster** ⚡ | Pandas + Phase 1 fallback |
| **Mixed formats** (multiple formats) | Same as Phase 1 | Phase 1 fallback |
| **Small datasets** (<100 rows) | Efficient | Skips Phase 2, uses Phase 1 |

#### Example with Verbose Output

```python
import pandas as pd
import ira

dates = pd.Series(['01/03/2024', '15/07/2024', ...])  # 1000 rows

# See Phase 2 in action
result = ira.convert_date_column(dates, verbose=True)
```

**Uniform data output:**
```
Phase 2: Analyzing column format with smart sampling...
  Sampled 100 rows (10.0%)
  Format analysis:
    Success rate: 100.0%
    Uniform: True
    Detected format: %d/%m/%Y
  ✓ Uniform format detected: %d/%m/%Y
  Trying pandas with exact format: %d/%m/%Y
  ✓ Pandas successful: 100.0% conversion (1000/1000)
Phase 2: Completed using pandas vectorization
```

**Mixed data output:**
```
Phase 2: Analyzing column format with smart sampling...
  Sampled 100 rows (10.0%)
  Format analysis:
    Success rate: 100.0%
    Uniform: False
    Format distribution: {'%d/%m/%Y': 50, '%Y-%m-%d': 30, '%d %b %Y': 20}
  ✗ Mixed formats detected, using Phase 1 for entire column
Phase 2: Smart sampling recommended Phase 1, proceeding with Phase 1...
Auto-detected format: %d/%m/%Y (success rate: 50.0%)
Phase 1: Mixed formats detected
```

#### Why Phase 2 is Safe

✅ **Zero accuracy loss** - Same results as Phase 1, just faster
✅ **Automatic fallback** - Detects mixed formats and uses Phase 1
✅ **Tested thoroughly** - 67/67 tests passing on real-world data
✅ **100% backward compatible** - Existing code works without changes

---

#### `ira.convert_date_simple(date_val)`
**Quick converter** with sensible defaults.
 The function scans your DataFrame and:

  1. Finds columns containing time objects
  2. Converts them to string format (e.g., time(14, 30, 0) → "14:30:00")
  3. Leaves datetime objects unchanged (they export to CSV fine)
  4. Preserves all other data types


```python
ira.convert_date_simple("2024-01-15")    # → 2024-01-15 00:00:00
ira.convert_date_simple("3:30 PM")       # → 15:30:00
```



#### `ira.prepare_for_csv(df, date_format='%d-%m-%Y', timedelta_unit='days', verbose=False)`
**Enhanced CSV export optimizer** - intelligently converts all temporal types (datetime, timedelta, time) to clean, CSV-friendly formats with customizable output.

```python
# Basic usage (clean CSV export with sensible defaults)
df_clean = ira.prepare_for_csv(df)
df_clean.to_csv('output.csv', index=False)

# Advanced usage with custom formatting
df_clean = ira.prepare_for_csv(df,
                               date_format='%d/%m/%Y',    # Custom date format
                               timedelta_unit='days',      # Convert to numeric days
                               verbose=True)               # Show conversions
```

---

### 🎯 Why Use prepare_for_csv()?

**Problem**: DataFrames with date arithmetic and temporal columns often have messy CSV exports:
- ❌ Timestamp columns export with long formats: `2024-01-15 00:00:00`
- ❌ Timedelta columns export verbosely: `9 days 00:00:00` instead of just `9`
- ❌ Time objects export as blank cells (data loss!)
- ❌ Timezone info causes parsing errors: `2024-01-15 00:00:00+00:00`
- ❌ Extreme dates crash the function: `OverflowError`

**Solution**: `prepare_for_csv()` automatically cleans and formats all temporal data for perfect CSV export.

---

### ✨ What It Does (v0.3.0 Enhanced)

The function intelligently processes your DataFrame:

| Input Type | What It Does | Example Output |
|------------|--------------|----------------|
| **datetime64** | Converts to formatted strings | `2024-01-15 00:00:00` → `15-01-2024` (default) |
| **timedelta64** | Converts to clean numeric values | `9 days 00:00:00` → `9` |
| **time objects** | Converts to HH:MM:SS strings | `time(14, 30)` → `14:30:00` |
| **Timezone-aware** | Removes timezone suffix | `2024-01-15+00:00` → `15-01-2024` |
| **Extreme dates** | Prevents crashes gracefully | No `OverflowError` |
| **Other types** | Leaves unchanged | `int`, `float`, `str` preserved |

**Performance**: 700K+ rows/second (optimized in v0.3.0 with 10-100x speedup)

---

### 📋 Real-World Example: Invoice Date Analysis

```python
import pandas as pd
import ira

# Step 1: Load and convert dates
df = pd.DataFrame({
    'Invoice No': ['INV001', 'INV002', 'INV003'],
    'Invoice Date': ['01/01/2024', '15/02/2024', '20/03/2024'],
    'Payment Date': ['10/01/2024', '20/02/2024', '25/03/2024']
})

# Convert date strings to datetime objects
df['Invoice Date'] = ira.convert_date_column(df['Invoice Date'])
df['Payment Date'] = ira.convert_date_column(df['Payment Date'])

# Step 2: Calculate date differences (creates timedelta)
df['Days to Payment'] = (df['Payment Date'] - df['Invoice Date']).dt.days
df['Late Payment'] = df['Days to Payment'] > 30

print("Before prepare_for_csv:")
print(df.dtypes)
# Invoice No                   object
# Invoice Date         datetime64[ns]  ← Long format in CSV
# Payment Date         datetime64[ns]  ← Long format in CSV
# Days to Payment               int64  ← Good as-is
# Late Payment                   bool  ← Exports as True/False

# Step 3: Prepare for CSV export
df_clean = ira.prepare_for_csv(df,
                               date_format='%d-%m-%Y',  # DD-MM-YYYY format
                               verbose=True)

# Output shows:
# Preparing 3 rows, 5 columns for CSV export
# Conversions applied:
#   ✓ Invoice Date: datetime → string (%d-%m-%Y)
#   ✓ Payment Date: datetime → string (%d-%m-%Y)

print("\nAfter prepare_for_csv:")
print(df_clean.dtypes)
# Invoice No           object
# Invoice Date         object  ← Now clean strings: "01-01-2024"
# Payment Date         object  ← Now clean strings: "10-01-2024"
# Days to Payment       int64  ← Unchanged (already clean)
# Late Payment           bool  ← Unchanged (pandas handles it)

# Step 4: Export to CSV (clean, professional format)
df_clean.to_csv('invoice_analysis.csv', index=False)

# CSV output:
# Invoice No,Invoice Date,Payment Date,Days to Payment,Late Payment
# INV001,01-01-2024,10-01-2024,9,False
# INV002,15-02-2024,20-02-2024,5,False
# INV003,20-03-2024,25-03-2024,5,False
```

**Result**: Clean, consistent CSV with formatted dates ready for Excel or reporting tools.

---

### 🔧 Customization Options

#### 1. **Custom Date Format** (date_format parameter)

```python
# Default: DD-MM-YYYY
ira.prepare_for_csv(df)
# Dates: 15-01-2024

# DD/MM/YYYY (European format with slashes)
ira.prepare_for_csv(df, date_format='%d/%m/%Y')
# Dates: 15/01/2024

# YYYY-MM-DD (ISO standard format)
ira.prepare_for_csv(df, date_format='%Y-%m-%d')
# Dates: 2024-01-15

# Full datetime with time
ira.prepare_for_csv(df, date_format='%Y-%m-%d %H:%M:%S')
# Dates: 2024-01-15 10:30:45

# Readable format
ira.prepare_for_csv(df, date_format='%d %b %Y')
# Dates: 15 Jan 2024
```

#### 2. **Timedelta Unit** (timedelta_unit parameter)

```python
# Default: days (clean numeric)
ira.prepare_for_csv(df, timedelta_unit='days')
# 9 days → 9

# Hours (for detailed analysis)
ira.prepare_for_csv(df, timedelta_unit='hours')
# 9 days → 216.0

# Seconds (for precise calculations)
ira.prepare_for_csv(df, timedelta_unit='seconds')
# 9 days → 777600.0

# String (pandas default - verbose)
ira.prepare_for_csv(df, timedelta_unit='string')
# 9 days → "9 days"
```

#### 3. **Verbose Mode** (verbose parameter)

```python
# See what conversions are happening
df_clean = ira.prepare_for_csv(df, verbose=True)

# Output:
# Preparing 1000 rows, 5 columns for CSV export
# Conversions applied:
#   ✓ invoice_date: datetime → string (%d-%m-%Y)
#   ✓ payment_date: datetime → string (%d-%m-%Y)
#   ℹ payment_date: removed timezone information
#   ✓ days_delay: timedelta → days (numeric)
#   ✓ shift_start: time → string (HH:MM:SS)
```

---

### 💡 Common Use Cases

#### Use Case 1: Date Arithmetic Results
```python
# Calculate date differences
df['date_diff'] = (df['end_date'] - df['start_date']).dt.days

# Clean for CSV (timedelta → numeric)
df_clean = ira.prepare_for_csv(df, timedelta_unit='days')
# date_diff: 9 (clean number, not "9 days 00:00:00")
```

#### Use Case 2: Multi-Timezone Data
```python
# Data from different timezones
df['utc_time'] = pd.to_datetime(...).tz_localize('UTC')

# Remove timezone for clean CSV
df_clean = ira.prepare_for_csv(df)
# Automatically removes "+00:00" suffix
```

#### Use Case 3: Mixed Temporal Types
```python
# DataFrame with dates, times, and date differences
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-01', '2024-02-01']),
    'time': [time(10, 30), time(14, 45)],
    'duration': pd.to_timedelta([1, 2], unit='D')
})

# Single function handles everything
df_clean = ira.prepare_for_csv(df,
                               date_format='%d/%m/%Y',
                               timedelta_unit='hours',
                               verbose=True)

# Output:
# ✓ date: datetime → string (DD/MM/YYYY)
# ✓ time: time → string (HH:MM:SS)
# ✓ duration: timedelta → hours (numeric)
```

#### Use Case 4: Preventing Crashes (OverflowError Fix)
```python
# Messy data with extreme/invalid dates (e.g., 9999-12-31)
# Before v0.3.0: OverflowError: result would overflow
# After v0.3.0: Handles gracefully

df_clean = ira.prepare_for_csv(df, verbose=True)
# ⚠ Detected extreme date values, handling overflow...
# ✓ Success! No crashes.
```

---

### 🎯 When to Use prepare_for_csv()

**✅ Always use it when:**
- You have datetime columns and want consistent formatting
- You calculated date differences (timedelta columns)
- Your DataFrame contains time objects (shift times, appointment times)
- You want clean, professional CSV output
- You're exporting to Excel or reporting tools
- You have timezone-aware datetime columns
- Your data might have extreme/invalid dates

**⚠️ Optional (but still helpful):**
- DataFrames with only datetime columns (pandas exports them, but format is inconsistent)
- When you want specific date formats for downstream tools

**❌ Not needed when:**
- Exporting to databases (they handle temporal types)
- Using pandas-native formats like Parquet, HDF5
- DataFrame has no temporal columns (dates, times, timedeltas)

---

### ⚡ Performance (v0.3.0 Optimized)

**Smart sampling optimization** delivers massive speedups:

| Dataset Size | Time | Throughput | Experience |
|--------------|------|------------|------------|
| 10K rows | 0.01s | 958K rows/sec | ✅ Instant |
| 100K rows | 0.14s | 732K rows/sec | ✅ Fast |
| 1M rows | 0.5-2s | 500K-1M rows/sec | ✅ Fast |

**Before v0.3.0**: 10-20s for 1M rows (slow)
**After v0.3.0**: 0.5-2s for 1M rows (10-100x faster) ⚡

---

### 🔒 Safety Guarantees

- ✅ **No data loss**: All values preserved
- ✅ **No crashes**: Handles extreme dates gracefully (OverflowError fixed)
- ✅ **100% backward compatible**: Existing code works without changes
- ✅ **Production tested**: Real-world validation on messy data
- ✅ **Zero accuracy loss**: Same results, just faster and cleaner

### 🎨 Supported Date Formats

IRA automatically detects and converts these formats:

| Format Category | Examples | Output |
|----------------|----------|---------|
| **ISO Standards** | `2024-07-30`, `2024-07-30 14:30:00` | `2024-07-30 14:30:00` |
| **US Formats** | `07/30/2024`, `07/30/2024 2:30 PM` | `2024-07-30 14:30:00` |
| **European Formats** | `30/07/2024`, `30.07.2024` | `2024-07-30 00:00:00` |
| **Text Months** | `July 30, 2024`, `30 Jul 2024`, `01 Apr 2006` | `2024-07-30 00:00:00` |
| **Excel Serial** | `45503`, `44927` | `2024-07-30 00:00:00` |
| **Time Only** | `2:30 PM`, `14:30:00`, `11:00 AM` | `14:30:00` (time object) |
| **Timezone Aware** | `2024-07-30 14:30:00+05:30` | `2024-07-30 09:00:00+00:00` |
| **Mixed DateTime** | `13-04-2025 15:28`, `1/1/1970 8:00:00 AM` | `2025-04-13 15:28:00` |

---

## 🧹 Core Module: `clean_strings` (NEW)

The new **`clean_strings`** module provides high-performance string cleaning and standardization capabilities, addressing real-world data quality issues found in CSV workflows.

### 🔧 Main Functions

#### `ira.clean_strings(series, **options)`
**Universal string cleaner** - handles common string data issues automatically.

```python
import pandas as pd
import ira

# Basic cleaning - removes Excel artifacts and normalizes whitespace
messy_data = pd.Series(['12345.0', ' ABC Corp ', 'XYZ\tInc.', '  DEF Ltd  '])
clean_data = ira.clean_strings(messy_data)
print(clean_data)  # ['12345', 'ABC Corp', 'XYZ Inc.', 'DEF Ltd']

# Advanced cleaning with case conversion
vendor_names = pd.Series(['abc corp', 'XYZ INC.', 'def ltd'])
clean_vendors = ira.clean_strings(vendor_names,
                                 remove_excel_artifacts=True,
                                 normalize_whitespace=True,
                                 case_mode='title')
print(clean_vendors)  # ['Abc Corp', 'Xyz Inc.', 'Def Ltd']
```

**Parameters:**
- `remove_excel_artifacts`: Bool - remove .0 suffixes from Excel exports (default: True)
- `normalize_whitespace`: Bool - standardize all whitespace (default: True)
- `case_mode`: String - case conversion ('upper', 'lower', 'title', 'sentence', 'same'). Default: 'same' (preserves original case)

#### `ira.clean_strings_batch(df, columns, rules, **options)`
**Batch processor** for cleaning multiple DataFrame columns simultaneously.

```python
# Clean multiple columns with consistent rules
df = pd.DataFrame({
    'vendor_name': [' ABC Corp ', 'xyz inc.', 'DEF\tLTD'],
    'po_number': ['12345.0', '67890.0', '11111.0'],
    'description': ['  Item A  ', 'Item\tB', 'Item   C']
})

rules = {
    'remove_excel_artifacts': True,
    'normalize_whitespace': True,
    'case_mode': 'title'
}

clean_df = ira.clean_strings_batch(df, ['vendor_name', 'po_number', 'description'], rules)
print(clean_df)
#   vendor_name po_number description
# 0    Abc Corp     12345      Item A
# 1    Xyz Inc.     67890      Item B
# 2      Defltd     11111      Item C
```


### 🏢 Source-Specific Presets

#### `ira.clean_excel_export(df, columns)`
**Excel export cleaner** - handles common Excel export issues.

```python
# Clean data exported from Excel
df_excel = ira.clean_excel_export(df, ['vendor_name', 'po_number'])
# Removes .0 artifacts, normalizes whitespace, preserves case
```

#### `ira.clean_sap_export(df, columns)`
**SAP system cleaner** - standardizes SAP export formatting.

```python
# Clean data from SAP systems
df_sap = ira.clean_sap_export(df, ['vendor_name', 'item_code'])
# Uppercases text, normalizes whitespace
```

#### `ira.clean_manual_entry(df, columns)`
**Manual entry cleaner** - fixes inconsistent manual data entry.

```python
# Clean manually entered data
df_manual = ira.clean_manual_entry(df, ['vendor_name', 'description'])
# Title case, removes artifacts, normalizes whitespace
```

### 🎨 Supported String Cleaning Operations

IRA automatically detects and fixes these common issues:

| Issue Category | Examples | Fixed Output |
|----------------|----------|--------------|
| **Excel Artifacts** | `'12345.0'`, `'ABC123.0'` | `'12345'`, `'ABC123'` |
| **Whitespace Issues** | `' ABC Corp '`, `'XYZ\tInc'` | `'ABC Corp'`, `'XYZ Inc'` |
| **Case Inconsistency** | `'abc corp'`, `'XYZ INC'` | `'Abc Corp'`, `'Xyz Inc'` |

### 🚀 Performance Optimizations

The string cleaning module is optimized for large datasets:

```python
# High-performance batch processing
large_df = pd.DataFrame({
    'vendor': [f' Vendor {i}.0 ' for i in range(100000)],
    'po_num': [f'{i}.0' for i in range(100000)]
})

# Process 200K cells in under 1 second
clean_large = ira.clean_strings_batch(large_df, ['vendor', 'po_num'],
                                     rules={'remove_excel_artifacts': True,
                                            'normalize_whitespace': True},
                                     parallel=True)

# Memory-efficient chunked processing for very large datasets
cleaner = ira.LargeDatasetCleaner(chunk_size=50000)
result = cleaner.clean_large_dataset(very_large_df, columns, rules)
```

---

## 🛠 Complete Setup Guide

### Step 1: Environment Setup

#### For New Projects (Conda):
```bash
# Create dedicated environment
conda create -n my_data_project python=3.10 pandas pytz jupyter
conda activate my_data_project

# Install IRA
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira
pip install -e .
```

#### For Existing Projects:
```bash
# Activate your existing environment
conda activate my_existing_env

# Install IRA dependencies
conda install pandas pytz
# or: pip install pandas pytz

# Install IRA
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira
pip install -e .
```

### Step 2: Verify Installation

```python
# test_ira_setup.py
import ira
import pandas as pd

print(f"✅ IRA v{ira.__version__} loaded successfully!")

# Test date conversion functionality
test_dates = ["07/30/2024", "30-Jul-24", "2024-07-30 14:30", 45503]
for date in test_dates:
    result = ira.convert_date(date)
    print(f"Date: '{date}' → {result}")

# Test string cleaning functionality (NEW)
test_strings = pd.Series(['12345.0', ' ABC Corp ', 'XYZ\tInc'])
clean_result = ira.clean_strings(test_strings)
print(f"Strings: {test_strings.tolist()} → {clean_result.tolist()}")

print("🎉 Both modules working perfectly!")
```

### Step 3: Run Tests (Optional)

```bash
# Date conversion tests
python test_ira.py
python ira_testing_report.py

# String cleaning tests (NEW)
python ira/test_clean_strings.py

# Full demonstration of both modules (NEW)
python clean_strings_demo.py

# Quick validation (both modules)
python -c "
import ira, pandas as pd
# Test date conversion
result = ira.convert_date('01 Apr 2006')
assert str(result) == '2006-04-01 00:00:00'
# Test string cleaning
clean = ira.clean_strings(pd.Series(['12345.0', ' ABC Corp ']))
print('✅ Both date and string modules work perfectly!')
"
```

---

## 📖 Usage Examples

### Example 1: Complete CSV Data Cleaning Pipeline (NEW)

```python
import pandas as pd
import ira

# Load messy CSV data from multiple sources
df = pd.read_csv('vendor_payments.csv')

# Original data has multiple issues:
# - Mixed date formats: '01 Apr 2006', '30/07/2024', 45503
# - Excel artifacts: '12345.0', '67890.0'
# - Inconsistent casing: 'abc corp', 'XYZ INC.'
# - Whitespace issues: ' ABC Corp ', 'DEF\tLTD'

print("Before cleaning:")
print(df.head())

# Step 1: Clean dates with IRA
df['po_date_clean'] = ira.convert_date_column(df['po_creation_date'])
df['invoice_date_clean'] = ira.convert_date_column(df['invoice_date'])

# Step 2: Clean strings with IRA (NEW)
string_columns = ['vendor_name', 'po_number', 'description']
df_clean = ira.clean_strings_batch(df, string_columns,
                                  rules={'remove_excel_artifacts': True,
                                         'normalize_whitespace': True,
                                         'case_mode': 'title'})

print("After cleaning:")
print(df_clean.head())

# Step 3: Data is now ready for analysis
# po_number column has been cleaned (12345.0 → 12345)

# Export analysis-ready data
df_clean.to_csv('cleaned_vendor_payments.csv', index=False)
print("✅ Clean, analysis-ready data exported!")
```

### Example 2: CSV Date Cleaning Pipeline

```python
import pandas as pd
import ira

# Load messy CSV data
df = pd.read_csv('employee_data.csv')

# Original data has mixed formats:
# '01 Apr 2006', '30/07/2024', '2024-12-25', 45503, etc.

print("Before conversion:")
print(df['hire_date'].head())

# Convert with IRA
df['hire_date_clean'] = ira.convert_date_column(df['hire_date'], verbose=True)

print("After conversion:")
print(df['hire_date_clean'].head())

# Export clean data
df_export = ira.prepare_for_csv(df)
df_export.to_csv('cleaned_employee_data.csv', index=False)
```

### Example 2: Time Processing

```python
import ira

# Shift scheduling data
shift_times = ['08:00', '16:00', '00:00:00', '11:00 AM', '2:30 PM']

# Convert to time objects
time_objects = [ira.convert_date(t) for t in shift_times]
print("Time objects:", time_objects)

# Convert with today's date
datetime_objects = [ira.convert_date(t, time_only_mode='add_today') for t in shift_times]
print("With today's date:", datetime_objects)
```

### Example 3: Excel Date Processing

```python
import ira
import pandas as pd

# Excel export with serial dates
excel_data = pd.DataFrame({
    'task_id': [1, 2, 3, 4],
    'start_date': [45503, 45000, 46000, 44927],  # Excel serial dates
    'end_date': [45510, 45007, 46007, 44934]
})

# Convert Excel dates
excel_data['start_date'] = ira.convert_date_column(excel_data['start_date'])
excel_data['end_date'] = ira.convert_date_column(excel_data['end_date'])

print(excel_data)
# Output:
#    task_id start_date    end_date
# 0        1 2024-07-30  2024-08-06
# 1        2 2023-03-15  2023-03-22
# 2        3 2025-12-09  2025-12-16
# 3        4 2023-01-01  2023-01-08
```

### Example 4: Timezone Conversion

```python
import ira

# Global timestamp data
timestamps = [
    "2024-07-30 14:30:00+05:30",  # IST
    "July 30, 2024 2:30 PM EST",  # EST with text
    "30-07-2024 14:30 GMT",       # GMT
    "2024-07-30T14:30:00Z"        # ISO with Z
]

# Convert all to UTC
utc_times = [ira.convert_date(ts, target_timezone='UTC') for ts in timestamps]

for orig, utc in zip(timestamps, utc_times):
    print(f"{orig} → {utc}")
```

### Example 5: Multi-Source Data Integration (NEW)

```python
import pandas as pd
import ira

# Scenario: Merging vendor data from different systems
# Excel export with artifacts
po_data = pd.DataFrame({
    'po_number': ['12345.0', '67890.0', '11111.0'],
    'vendor_name': [' ABC Corporation ', 'xyz industries', 'DEF\tLimited'],
    'amount': ['1,000.0', '2,500.0', '750.0']
})

# SAP export with different formatting
vendor_master = pd.DataFrame({
    'vendor_name': ['ABC CORPORATION', 'XYZ INDUSTRIES', 'DEF LIMITED'],
    'vendor_code': ['V001', 'V002', 'V003'],
    'payment_terms': ['NET30', 'NET15', 'NET45']
})

print("Before standardization - merge will fail:")
print("PO Data:", po_data['vendor_name'].tolist())
print("Master:", vendor_master['vendor_name'].tolist())

# Clean both datasets for consistent merging
po_clean = ira.clean_excel_export(po_data, ['vendor_name'])
vendor_clean = ira.clean_sap_export(vendor_master, ['vendor_name'])

# Standardize case for matching
po_clean['vendor_key'] = ira.clean_strings(po_clean['vendor_name'], case_mode='upper')
vendor_clean['vendor_key'] = ira.clean_strings(vendor_clean['vendor_name'], case_mode='upper')

# Now merge will work reliably
merged = pd.merge(po_clean, vendor_clean, on='vendor_key', suffixes=('_po', '_master'))

print("After cleaning - successful merge:")
print(merged[['po_number', 'vendor_name_po', 'payment_terms']])
```

### Example 6: Simplified Data Cleaning (NEW)

```python
import ira
import pandas as pd

# Clean vendor data efficiently
vendor_data = pd.DataFrame({
    'vendor_name': [' ABC Corp.0 ', 'xyz industries.0', 'DEF\tLimited.0'],
    'contact_person': [' john doe ', 'JANE SMITH', 'bob.jones'],
    'amount': ['1,000.0', '2,500.0', '750.0']
})

print("Before cleaning:")
print(vendor_data)

# Simple, predictable cleaning
clean_vendor = ira.clean_strings_batch(vendor_data,
                                      ['vendor_name', 'contact_person'],
                                      rules={
                                          'remove_excel_artifacts': True,
                                          'normalize_whitespace': True,
                                          'case_mode': 'title'
                                      })

print("After cleaning:")
print(clean_vendor)
```

### Example 7: Large Dataset Processing (NEW)

```python
import ira
import pandas as pd

# Process large dataset efficiently
large_df = pd.read_csv('large_vendor_data.csv')  # 1M+ rows

print(f"Processing {len(large_df):,} rows...")

# High-performance batch cleaning
rules = {
    'remove_excel_artifacts': True,
    'normalize_whitespace': True,
    'case_mode': 'title'
}

# Method 1: Standard batch processing
clean_df = ira.clean_strings_batch(large_df,
                                  ['vendor_name', 'address', 'contact'],
                                  rules=rules,
                                  parallel=True)

# Method 2: Memory-efficient chunked processing for very large datasets
cleaner = ira.LargeDatasetCleaner(chunk_size=50000)
result = cleaner.clean_large_dataset(large_df,
                                    ['vendor_name', 'address', 'contact'],
                                    rules,
                                    output_path='cleaned_large_data.csv')

print("✅ Large dataset processed efficiently!")
```

---

## 🧪 Testing & Validation

IRA comes with comprehensive testing:

```bash
# Run basic tests
python test_ira.py

# Generate detailed test report
python ira_testing_report.py

# Quick performance test
python -c "
import time, ira
start = time.time()
for i in range(1000):
    ira.convert_date('07/30/2024')
print(f'Processed 1000 dates in {time.time()-start:.3f}s')
"
```

**Validation Results:**
- ✅ **9/9 CSV files** tested successfully
- ✅ **33/33 date columns** converted perfectly
- ✅ **26,555 rows** processed without errors
- ✅ **4,057 rows/second** processing speed

---

## 🔧 Advanced Configuration

### Custom Timezone Handling

```python
import ira

# Convert to specific timezone
result = ira.convert_date("2024-07-30 14:30:00+05:30",
                         target_timezone='US/Pacific')

# Disable timezone processing
result = ira.convert_date("2024-07-30 14:30:00+05:30",
                         handle_timezones=False)
```

### Excel Date Systems

```python
# Mac Excel (1904 system)
mac_date = ira.convert_date(45503, excel_date_system='1904')

# Windows Excel (1900 system - default)
win_date = ira.convert_date(45503, excel_date_system='1900')
```

### Batch Processing Settings

```python
# Date conversion - Large dataset optimization
df['dates'] = ira.convert_date_column(df['dates'],
                                     auto_detect_format=True,  # Use format detection
                                     default_day_first=True,   # DD/MM interpretation
                                     verbose=False)            # Suppress output

# String cleaning - Simplified batch processing (NEW)
rules = {
    'remove_excel_artifacts': True,
    'normalize_whitespace': True,
    'case_mode': 'title'
}

# Parallel processing for large datasets
clean_df = ira.clean_strings_batch(df, ['vendor', 'description'],
                                  rules=rules,
                                  parallel=True)

# Memory-efficient chunked processing
cleaner = ira.LargeDatasetCleaner(chunk_size='auto', low_memory=True)
result = cleaner.clean_large_dataset(df, columns, rules)
```

---

## 📋 Requirements

| Requirement | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Core runtime |
| **pandas** | ≥1.3.0 | DataFrame operations |
| **pytz** | ≥2021.1 | Timezone handling |
| **conda** | Latest | Environment management (recommended) |

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Test** your changes: `python test_ira.py`
4. **Commit** changes: `git commit -m "Add feature"`
5. **Push** to branch: `git push origin feature-name`
6. **Submit** a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/AjayMudhai07/ira/issues)
- **Documentation**: This README + inline code documentation + CLAUDE.md
- **Examples**: Check `ira_testing_report.py` and `clean_strings_demo.py` for comprehensive usage
- **Performance**: Run benchmarks with provided test scripts

---

## 📊 Performance Benchmarks

### 📅 Date Conversion Performance
| Operation | Speed | Memory | Tested Rows |
|-----------|--------|---------|-------------|
| **Single Conversion** | ~0.001s | ~1KB | N/A |
| **Batch (1000 rows)** | ~0.25s | ~100KB | 1,000 |
| **Large CSV (10K rows)** | ~2.5s | ~10MB | 10,000 |
| **Production Dataset** | 4,057 rows/sec | Variable | 26,555 |
| **Auto-detection** | +20% time | +5% memory | Variable |

### 🧹 String Cleaning Performance (NEW)
| Operation | Speed | Memory | Tested Rows |
|-----------|--------|---------|-------------|
| **Single Series** | 1M+ rows/sec | ~50KB/10K | 10,000 |
| **Batch (3 columns)** | 896K+ cells/sec | ~150KB/10K | 30,000 |
| **Excel Artifact Removal** | 0.3s/1M rows | ~100MB | 1,000,000 |
| **Whitespace Normalization** | 0.12s/1M rows (Numba) | ~80MB | 1,000,000 |
| **Parallel Processing** | 3-5x speedup | Linear scaling | Variable |
| **Chunked Processing** | Memory-limited | 75% reduction | 10M+ |

### 🔄 Combined Workflow Performance
| Workflow Type | Processing Speed | Memory Usage |
|---------------|------------------|--------------|
| **Date + String Cleaning** | 500K+ rows/sec | ~200MB/100K rows |
| **Multi-source Integration** | 300K+ rows/sec | Variable |
| **Large Dataset (1M+ rows)** | Chunked processing | <2GB RAM |

---

## 🎯 Real-World Impact

### Validation Results
- ✅ **26 production workflows** analyzed and optimized
- ✅ **26,555+ rows** of real data processed successfully
- ✅ **9/9 CSV files** tested with 100% success rate
- ✅ **33/33 date columns** converted perfectly
- ✅ **60-80% code reduction** in preprocessing workflows
- ✅ **90% reduction** in data type and merge errors

### Business Benefits
- **Development Speed**: 3-5x faster CSV workflow development
- **Data Quality**: Consistent, reliable data processing
- **Cost Savings**: Reduced manual data cleaning time
- **Scalability**: Handle enterprise-scale datasets efficiently

---

**Made with ❤️ for Data Engineers and Analysts**

*IRA - Making CSV data processing intelligent, fast, and effortless.*

## 🚀 What's Next?

Based on our analysis of 26+ production workflows, IRA is evolving into a comprehensive CSV processing platform. Future modules under consideration:

- **Smart Merging**: Fuzzy matching and intelligent join operations
- **Data Validation**: Automated quality checks and anomaly detection
- **Smart Type Conversion**: Intelligent data type detection and conversion
- **Standardized Columns**: Automatic column name mapping across sources

*Stay tuned for more powerful CSV workflow automation!*