# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/tests/fixtures/sample_csvs/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Simple_Test_Workflow/orchestrator_test_result.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = ['Document Number', 'Account', 'Offsetting acct no.', 
                   'Supplier', 'Purchasing Document', 'Name 1', 
                   'Invoice reference', 'Clearing Document', 'Year/month']
UPPER_COLS_FBLSN = ['Document Type', 'Local Currency', 'Document currency', 
                    'Account Type', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = ['User Name', 'Document Header Text', 'Material', 
                    'G/L Acct Long Text', 'G/L Acct Long Text.1', 
                    'Long Text', 'Long Text.1', 'Cost Center', 'Profit Center', 
                    'Reference Key 1', 'Reference Key 2', 'Reference Key 3', 
                    'Asset', 'Sub-number', 'Plant']
NUMERIC_COLS_FBLSN = ['Business Area', 'Posting Key', 'Amount in local currency', 
                      'Amount in doc. curr.', 'Quantity', 'Clearing date']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, SAME_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, UPPER_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# As per the business logic, retain all records and columns
# No additional filtering or calculations are required

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
df_fbl3n.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")