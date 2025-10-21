# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/7bf47c19-92fc-410c-bc60-72fc01311953/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/result.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = ['Text', 'Document Header Text', 'Cost Center', 'Profit Center', 'Reference', 'User Name']
UPPER_COLS_FBLSN = ['Local Currency', 'Document Type', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = ['G/L Acct Long Text', 'G/L Acct Long Text.1']
NUMERIC_COLS_FBLSN = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns as per Business Logic Plan
required_columns_plan = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account', 'Document Date',
    'Posting Date', 'Amount in local currency', 'Local Currency', 'Document Type', 'Text',
    'Document Header Text', 'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Cost Center',
    'Profit Center', 'Reference', 'Entry Date', 'User Name', 'Offsett.account type',
    'Offsetting acct no.'
]
# Include all category columns too
required_columns_fbl3n = sorted(list(set(required_columns_plan + DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN)))
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

# Derive month-year and quarter fields
df_fbl3n['Doc_MonthYear'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Post_MonthYear'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)
df_fbl3n['Doc_Quarter'] = df_fbl3n['Document Date'].dt.to_period('Q').astype(str)
df_fbl3n['Post_Quarter'] = df_fbl3n['Posting Date'].dt.to_period('Q').astype(str)
print("✓ Derived month-year and quarter fields")

# Calculate Month_Diff: number of months Document Date is later than Posting Date
month_diff = (
    (df_fbl3n['Document Date'].dt.year - df_fbl3n['Posting Date'].dt.year) * 12 +
    (df_fbl3n['Document Date'].dt.month - df_fbl3n['Posting Date'].dt.month)
)
df_fbl3n['Month_Diff'] = month_diff.astype('float')
print("✓ Calculated Month_Diff")

# Apply exclusions per rules: remove PROVISION and Clearing in G/L Acct Long Text
provision_mask = df_fbl3n['G/L Acct Long Text'].str.contains('PROVISION', case=False, na=False)
clearing_mask = df_fbl3n['G/L Acct Long Text'].str.contains('Clearing', case=False, na=False)
exclusion_mask = ~(provision_mask | clearing_mask)
excluded_count = (~exclusion_mask).sum()
print(f"✓ Applied exclusions (PROVISION/Clearing): excluded {excluded_count:,} rows")

# Flag exceptions: Document month-year later than Posting month-year (Month_Diff > 0)
exception_mask = (df_fbl3n['Month_Diff'] > 0) & exclusion_mask
result_df = df_fbl3n.loc[exception_mask].copy()
print(f"✓ Flagged exceptions: {len(result_df):,} rows")

# Add Exception_Reason
result_df['Exception_Reason'] = "Document Date later than Posting Date (month-year)"

# Reorder and select output columns
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account', 'Document Date', 'Posting Date',
    'Amount in local currency', 'Local Currency', 'Document Type', 'Text', 'Document Header Text',
    'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Cost Center', 'Profit Center', 'Reference',
    'Entry Date', 'User Name', 'Offsett.account type', 'Offsetting acct no.',
    'Doc_MonthYear', 'Post_MonthYear', 'Month_Diff', 'Doc_Quarter', 'Post_Quarter', 'Exception_Reason'
]

# Validate output columns exist before final selection
missing_output_cols = [col for col in output_columns if col not in result_df.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns: {missing_output_cols}")

result_df = result_df[output_columns]

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")