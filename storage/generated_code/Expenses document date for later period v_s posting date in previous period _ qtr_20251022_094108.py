# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/233dd7f6-e058-4884-bb7e-31835f2988e9/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_4e6ae026-3bcc-4d08-9094-393bcb65f138.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'G/L Account', 'Cost Center', 'Profit Center',
    'Reference', 'Offsetting acct no.', 'User Name', 'Year/month'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document currency', 'Document Type', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = [
    'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Text', 'Document Header Text',
    'Long Text', 'Long Text.1'
]
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")
if len(df_fbl3n) == 0:
    print("⚠ Warning: FBL3N dataframe is empty. Proceeding with structure-only output.")

# Verify required columns
required_columns_fbl3n = DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
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

# Create a working copy including all rows
result_df = df_fbl3n.copy()

# Calculate derived month-year fields from dates
result_df['Document_Month_Year_Calculated'] = result_df['Document Date'].dt.strftime('%Y-%m')
result_df['Posting_Month_Year_Calculated'] = result_df['Posting Date'].dt.strftime('%Y-%m')
print("✓ Derived Document_Month_Year_Calculated and Posting_Month_Year_Calculated")

# Compute month difference: (Document period - Posting period)
doc_ym = result_df['Document Date'].dt.year * 12 + result_df['Document Date'].dt.month
post_ym = result_df['Posting Date'].dt.year * 12 + result_df['Posting Date'].dt.month
result_df['Month_Diff_Calculated'] = (doc_ym - post_ym).astype('float')
print("✓ Calculated Month_Diff_Calculated")

# Core exception rule: flag when doc month-year > posting month-year
result_df['Exception Flag'] = (result_df['Month_Diff_Calculated'] > 0)
print(f"✓ Applied exception rule: {result_df['Exception Flag'].sum():,} exceptions flagged")

# Exception reason only when flagged
reason_text = "Document month-year later than Posting month-year"
result_df['Exception Reason_Calculated'] = np.where(result_df['Exception Flag'], reason_text, "")
print("✓ Added Exception Reason_Calculated")

# Reorder and select output columns as specified
output_columns = [
    'Company Code', 'Document Number', 'Document Date', 'Posting Date', 'G/L Account',
    'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Amount in local currency', 'Local Currency',
    'Amount in doc. curr.', 'Document currency', 'Document Type', 'Cost Center', 'Profit Center',
    'Text', 'Document Header Text', 'Reference', 'Offsett.account type', 'Offsetting acct no.',
    'Entry Date', 'User Name', 'Year/month', 'Long Text', 'Long Text.1',
    'Document_Month_Year_Calculated', 'Posting_Month_Year_Calculated', 'Month_Diff_Calculated',
    'Exception Reason_Calculated', 'Exception Flag'
]

# Ensure all output columns exist (safety check)
missing_out_cols = [c for c in output_columns if c not in result_df.columns]
if missing_out_cols:
    raise ValueError(f"Missing expected output columns: {missing_out_cols}")

result_df = result_df[output_columns].copy()
print(f"✓ Final result prepared: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")