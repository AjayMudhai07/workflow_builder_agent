# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/e0ac6727-704b-4f5a-b242-3a3ee7d973fa/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_160b6e1a-00c7-4998-9fcf-77be4d29c10a.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'G/L Account', 'Posting Key', 'Cost Center', 'Profit Center',
    'Reference', 'Offsetting acct no.', 'User Name', 'Reference Key 1', 'Reference Key 2', 'Reference Key 3',
    'Year/month', 'Document Header Text', 'Text', 'Long Text', 'Long Text.1'
]
UPPER_COLS_FBLSN = ['Account Type', 'Local Currency', 'Document currency', 'Document Type', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns based on categories
required_columns_fbl3n = list(dict.fromkeys(
    DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
))
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

# Create normalized period labels
df_fbl3n['Document Month-Year'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting Month-Year'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)
print("✓ Created Document Month-Year and Posting Month-Year labels")

# Calculate month indices and months difference
doc_month_index = (df_fbl3n['Document Date'].dt.year * 12 + df_fbl3n['Document Date'].dt.month)
post_month_index = (df_fbl3n['Posting Date'].dt.year * 12 + df_fbl3n['Posting Date'].dt.month)
months_diff = doc_month_index - post_month_index

# Exception flag: Document month-year later than Posting month-year
df_fbl3n['Exception Flag'] = months_diff > 0

# Months Difference
df_fbl3n['Months Difference'] = months_diff.where(months_diff.notna(), np.nan)

# Quarter Difference: compute via quarter indices for accuracy across boundaries
doc_q_index = (df_fbl3n['Document Date'].dt.year * 4 + df_fbl3n['Document Date'].dt.quarter)
post_q_index = (df_fbl3n['Posting Date'].dt.year * 4 + df_fbl3n['Posting Date'].dt.quarter)
quarter_diff = doc_q_index - post_q_index
df_fbl3n['Quarter Difference'] = quarter_diff.where(quarter_diff.notna(), np.nan)

# Cross-Year Indicator
df_fbl3n['Cross-Year Indicator'] = (df_fbl3n['Document Date'].dt.year > df_fbl3n['Posting Date'].dt.year).fillna(False)
print("✓ Calculated Exception Flag, Months Difference, Quarter Difference, and Cross-Year Indicator")

# Keep only exceptions as per Rule 7
result_df = df_fbl3n[df_fbl3n['Exception Flag']].copy()
print(f"✓ Filtered exceptions: {len(result_df):,} rows")

# Select and order output columns as specified
output_columns = [
    'Company Code', 'Document Number', 'G/L Account', 'Posting Key', 'Account Type', 'Document Date',
    'Posting Date', 'Entry Date', 'Amount in local currency', 'Local Currency', 'Amount in doc. curr.',
    'Document currency', 'Document Type', 'Document Header Text', 'Text', 'Cost Center', 'Profit Center',
    'Reference', 'Offsett.account type', 'Offsetting acct no.', 'User Name', 'Reference Key 1',
    'Reference Key 2', 'Reference Key 3', 'Year/month', 'Long Text', 'Long Text.1',
    'Exception Flag', 'Months Difference', 'Quarter Difference', 'Cross-Year Indicator',
    'Document Month-Year', 'Posting Month-Year'
]

# Ensure all output columns exist before finalizing
missing_output_cols = [col for col in output_columns if col not in result_df.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns: {missing_output_cols}")

result_df = result_df[output_columns]

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty! No exceptions found based on the defined rule.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
dir_name = os.path.dirname(output_file_path)
if dir_name:
    os.makedirs(dir_name, exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")