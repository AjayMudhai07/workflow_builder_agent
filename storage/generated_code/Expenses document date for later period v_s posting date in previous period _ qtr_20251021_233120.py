# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/989f7e5c-5989-4683-a007-f1b8e2190ef5/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_2adb78e2-7b18-40c5-91ca-4dc73f71af5c.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = [
    'Document Date',
    'Posting Date',
    'Entry Date'
]
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'Posting Key', 'Account', 'G/L Account',
    'Cost Center', 'Profit Center', 'Text', 'Document Header Text', 'Reference',
    'Offsetting acct no.', 'User Name', 'Year/month'
]
UPPER_COLS_FBLSN = [
    'Local Currency', 'Document currency', 'Document Type', 'Offsett.account type'
]
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = [
    'Amount in local currency', 'Amount in doc. curr.'
]

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

# Compute month difference between Document Date and Posting Date
if len(df_fbl3n) == 0:
    print("⚠ Warning: FBL3N dataframe is empty! Proceeding with empty result.")

doc_year = df_fbl3n['Document Date'].dt.year.astype('Int64')
post_year = df_fbl3n['Posting Date'].dt.year.astype('Int64')
doc_month = df_fbl3n['Document Date'].dt.month.astype('Int64')
post_month = df_fbl3n['Posting Date'].dt.month.astype('Int64')

month_diff = (doc_year - post_year) * 12 + (doc_month - post_month)
df_fbl3n['Month Difference_Calculated'] = month_diff

# Exception flag: True when month difference > 0
exception_flag = (df_fbl3n['Month Difference_Calculated'] > 0).fillna(False)
df_fbl3n['Exception Flag_Calculated'] = exception_flag
print(f"✓ Calculated exceptions: {exception_flag.sum():,} rows flagged")

# Quarters derived from Posting Date and Document Date
post_quarter = df_fbl3n['Posting Date'].dt.quarter.astype('Int64')
post_year_q = df_fbl3n['Posting Date'].dt.year.astype('Int64')
doc_quarter = df_fbl3n['Document Date'].dt.quarter.astype('Int64')
doc_year_q = df_fbl3n['Document Date'].dt.year.astype('Int64')

df_fbl3n['Posting Quarter_Calculated'] = np.where(
    df_fbl3n['Posting Date'].notna(),
    'Q' + post_quarter.astype(str) + ' ' + post_year_q.astype(str),
    np.nan
)

df_fbl3n['Document Quarter_Calculated'] = np.where(
    df_fbl3n['Document Date'].notna(),
    'Q' + doc_quarter.astype(str) + ' ' + doc_year_q.astype(str),
    np.nan
)
print("✓ Derived quarter fields from Posting Date and Document Date")

# Exception reason text
df_fbl3n['Exception Reason_Calculated'] = np.where(
    df_fbl3n['Exception Flag_Calculated'],
    'Document month-year later than Posting month-year by ' + df_fbl3n['Month Difference_Calculated'].astype('Int64').astype(str) + ' months',
    ''
)
print("✓ Composed exception reason text")

# Filter: keep only exceptions per refinement
result_df = df_fbl3n[df_fbl3n['Exception Flag_Calculated']].copy()
print(f"✓ Applied filter to keep exceptions only: {len(result_df):,} rows")

# Select and order output columns as specified
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'Account', 'G/L Account',
    'Document Date', 'Posting Date',
    'Amount in local currency', 'Local Currency', 'Amount in doc. curr.', 'Document currency',
    'Cost Center', 'Profit Center', 'Document Type', 'Text', 'Document Header Text', 'Reference',
    'Offsett.account type', 'Offsetting acct no.', 'Entry Date', 'User Name', 'Year/month',
    'Exception Flag_Calculated', 'Month Difference_Calculated',
    'Posting Quarter_Calculated', 'Document Quarter_Calculated', 'Exception Reason_Calculated'
]

# Validate output columns presence before final selection
missing_out_cols = [c for c in output_columns if c not in result_df.columns]
if missing_out_cols:
    raise ValueError(f"Missing expected output columns: {missing_out_cols}")

result_df = result_df[output_columns]

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty after applying exception filter!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")