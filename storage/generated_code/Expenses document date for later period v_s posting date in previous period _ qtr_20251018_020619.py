# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/17df12b8-fce6-45fa-b58f-0c874417b7db/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_9d9b26d0-4a18-4982-84b3-a0c49ee4d0c1.csv"

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
    'Company Code', 'Document Number', 'G/L Account',
    'Posting Key', 'Cost Center', 'Profit Center',
    'Offsetting acct no.', 'Reference', 'Reference Key 1',
    'Reference Key 2', 'Reference Key 3', 'User Name',
    'Year/month'
]
UPPER_COLS_FBLSN = [
    'Local Currency', 'Document currency', 'Document Type', 'Offsett.account type'
]
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = [
    'G/L Acct Long Text', 'Document Header Text', 'Text'
]
NUMERIC_COLS_FBLSN = [
    'Amount in local currency', 'Amount in doc. curr.'
]

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = list(set(
    DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
))
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

# Clean only object dtype columns for string operations
same_obj_cols = [c for c in SAME_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
upper_obj_cols = [c for c in UPPER_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
title_obj_cols = [c for c in TITLE_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']

if same_obj_cols:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, same_obj_cols, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

if upper_obj_cols:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, upper_obj_cols, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

if title_obj_cols:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, title_obj_cols, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Derive month-year strings for Document Date and Posting Date
df_fbl3n['Document Month-Year_Calculated'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting Month-Year_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)

# Calculate month difference: (Document - Posting)
doc_year = df_fbl3n['Document Date'].dt.year
post_year = df_fbl3n['Posting Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month
post_month = df_fbl3n['Posting Date'].dt.month

month_diff = (doc_year - post_year) * 12 + (doc_month - post_month)
# Ensure NaN when either date missing
month_diff = month_diff.where(~(doc_year.isna() | post_year.isna()))
# Store as nullable integer where possible
try:
    df_fbl3n['Month Difference (Document minus Posting)_Calculated'] = month_diff.astype('Int64')
except Exception:
    df_fbl3n['Month Difference (Document minus Posting)_Calculated'] = month_diff

# Cross-year flag
cross_year_bool = (doc_year != post_year) & (~doc_year.isna()) & (~post_year.isna())
df_fbl3n['Cross-Year Flag_Calculated'] = np.where(cross_year_bool, 'Yes', 'No')

# Exception flag and reason
exception_bool = df_fbl3n['Month Difference (Document minus Posting)_Calculated'] > 0
exception_bool = exception_bool.fillna(False)  # treat NA as non-exception

df_fbl3n['Exception Flag_Calculated'] = np.where(exception_bool, 'Yes', 'No')
df_fbl3n['Exception Reason_Calculated'] = np.where(
    exception_bool,
    'Document month-year later than Posting month-year',
    ''
)

print("✓ Calculated period fields, month difference, cross-year, and exception flags")

# Filter to exceptions only
result_df = df_fbl3n[exception_bool].copy()
print(f"✓ Flagged exceptions: {len(result_df):,} of {len(df_fbl3n):,} rows")

# Select and order output columns as per business plan
output_columns = [
    'Company Code', 'Document Number', 'G/L Account', 'G/L Acct Long Text',
    'Document Date', 'Posting Date', 'Amount in local currency', 'Local Currency',
    'Amount in doc. curr.', 'Document currency', 'Posting Key', 'Document Type',
    'Document Header Text', 'Text', 'Cost Center', 'Profit Center',
    'Offsett.account type', 'Offsetting acct no.', 'Reference', 'Reference Key 1',
    'Reference Key 2', 'Reference Key 3', 'Entry Date', 'User Name', 'Year/month',
    'Document Month-Year_Calculated', 'Posting Month-Year_Calculated',
    'Month Difference (Document minus Posting)_Calculated', 'Cross-Year Flag_Calculated',
    'Exception Flag_Calculated', 'Exception Reason_Calculated'
]

# Validate output columns exist
missing_output_cols = [c for c in output_columns if c not in result_df.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns: {missing_output_cols}")

result_df = result_df[output_columns]

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty! No exceptions found.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")