# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/fd00bc81-5de1-44be-b03f-229308356465/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_b2d7c4d8-4e28-42bc-a767-859432041214.csv"

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
    'Company Code', 'Document Number', 'Document Type', 'Posting Key',
    'G/L Account', 'G/L Acct Long Text', 'Text', 'Document Header Text',
    'Offsett.account type', 'Offsetting acct no.', 'Cost Center', 'Profit Center',
    'Reference', 'User Name'
]
UPPER_COLS_FBLSN = ['Local Currency']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
)
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

# Rule: Flag when Document Date month-year > Posting Date month-year (cross-year allowed)
# Build comparable month keys (YYYY*12 + MM)
doc_month_key = (df_fbl3n['Document Date'].dt.year * 12 + df_fbl3n['Document Date'].dt.month)
post_month_key = (df_fbl3n['Posting Date'].dt.year * 12 + df_fbl3n['Posting Date'].dt.month)
exception_flag = doc_month_key > post_month_key

# Filter to only exceptions at line level
result_df = df_fbl3n[exception_flag].copy()
print(f"✓ Applied month-year exception filter: {len(result_df):,} rows flagged")

# Add Exception_Flag and Reason (all rows in result are exceptions)
result_df['Exception_Flag'] = True
result_df['Exception_Reason'] = "Document month-year > Posting month-year"

# Compute Quarterly Exception Flag: Document quarter-year > Posting quarter-year
# Quarter key (YYYY*4 + Q)
doc_quarter_key = (result_df['Document Date'].dt.year * 4 + result_df['Document Date'].dt.quarter)
post_quarter_key = (result_df['Posting Date'].dt.year * 4 + result_df['Posting Date'].dt.quarter)
result_df['Quarterly_Exception_Flag'] = doc_quarter_key > post_quarter_key

# Quarterly reason only when quarterly flag is True
quarter_reason = "Document quarter-year > Posting quarter-year"
result_df['Quarterly_Exception_Reason'] = ""
result_df.loc[result_df['Quarterly_Exception_Flag'] == True, 'Quarterly_Exception_Reason'] = quarter_reason
print("✓ Computed quarterly exception indicators")

# Select and order output columns as specified
output_columns = [
    'Company Code', 'Document Number', 'Document Type', 'Posting Key',
    'G/L Account', 'G/L Acct Long Text', 'Document Date', 'Posting Date',
    'Amount in local currency', 'Local Currency', 'Text', 'Document Header Text',
    'Offsett.account type', 'Offsetting acct no.', 'Cost Center', 'Profit Center',
    'Reference', 'Entry Date', 'User Name',
    'Exception_Flag', 'Exception_Reason', 'Quarterly_Exception_Flag', 'Quarterly_Exception_Reason'
]

# Ensure all output columns exist before finalizing
missing_output_cols = [c for c in output_columns if c not in result_df.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns: {missing_output_cols}")

result_df = result_df[output_columns]

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty! No exceptions found based on the rule.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")