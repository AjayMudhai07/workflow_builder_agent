# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/718312cd-2091-4949-8f33-32ef6a9116c9/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_1293ef0c-f854-4541-9e21-f164fe333f41.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'Document Type', 'G/L Account',
    'G/L Acct Long Text', 'Cost Center', 'Profit Center', 'Posting Key',
    'Reference', 'Document Header Text', 'Text', 'User Name'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document currency']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# Restrict to required columns
df_fbl3n = df_fbl3n[required_columns_fbl3n].copy()
print(f"✓ Restricted to required columns: {len(df_fbl3n.columns)} columns")

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

# Derive month-year strings (YYYY-MM)
df_fbl3n['Doc_Month_Year_Calculated'] = df_fbl3n['Document Date'].dt.strftime('%Y-%m')
df_fbl3n['Post_Month_Year_Calculated'] = df_fbl3n['Posting Date'].dt.strftime('%Y-%m')
print("✓ Derived Doc_Month_Year_Calculated and Post_Month_Year_Calculated")

# Calculate integer month difference: (Document - Posting)
doc_ym = (df_fbl3n['Document Date'].dt.year * 12) + df_fbl3n['Document Date'].dt.month
post_ym = (df_fbl3n['Posting Date'].dt.year * 12) + df_fbl3n['Posting Date'].dt.month
months_diff = doc_ym - post_ym

# Store as nullable integer
df_fbl3n['Doc_Posting_Months_Diff_Calculated'] = months_diff.astype('Int64')
print("✓ Calculated Doc_Posting_Months_Diff_Calculated")

# Exception flag: Yes when month difference > 0
is_exception = months_diff > 0
df_fbl3n['Is_Exception_Calculated'] = np.where(is_exception, 'Yes', 'No')
print(f"✓ Computed Is_Exception_Calculated: {is_exception.sum():,} exceptions")

# Cross-year indicator: Yes when Document year > Posting year
doc_year = df_fbl3n['Document Date'].dt.year
post_year = df_fbl3n['Posting Date'].dt.year
is_cross_year = doc_year > post_year
df_fbl3n['Is_Cross_Year_Calculated'] = np.where(is_cross_year, 'Yes', 'No')
print("✓ Derived Is_Cross_Year_Calculated")

# Quarter-year derivation (YYYY-Qn)
doc_quarter = df_fbl3n['Document Date'].dt.quarter
post_quarter = df_fbl3n['Posting Date'].dt.quarter

doc_qtr_year = doc_year.astype('Int64').astype(str) + '-Q' + doc_quarter.astype('Int64').astype(str)
post_qtr_year = post_year.astype('Int64').astype(str) + '-Q' + post_quarter.astype('Int64').astype(str)

df_fbl3n['Doc_Qtr_Year_Calculated'] = doc_qtr_year
df_fbl3n['Post_Qtr_Year_Calculated'] = post_qtr_year
print("✓ Derived Doc_Qtr_Year_Calculated and Post_Qtr_Year_Calculated")

# Cross-quarter indicator: Yes when Document quarter-year later than Posting quarter-year
is_cross_quarter = (doc_year > post_year) | ((doc_year == post_year) & (doc_quarter > post_quarter))
df_fbl3n['Is_Cross_Quarter_Calculated'] = np.where(is_cross_quarter, 'Yes', 'No')
print("✓ Derived Is_Cross_Quarter_Calculated")

# Final column ordering per output specification
output_columns = [
    'Company Code', 'Document Number', 'Document Type', 'Document Date', 'Posting Date',
    'G/L Account', 'G/L Acct Long Text', 'Amount in local currency', 'Local Currency',
    'Amount in doc. curr.', 'Document currency', 'Cost Center', 'Profit Center',
    'Posting Key', 'Reference', 'Document Header Text', 'Text', 'User Name', 'Entry Date',
    'Is_Exception_Calculated', 'Doc_Posting_Months_Diff_Calculated',
    'Doc_Month_Year_Calculated', 'Post_Month_Year_Calculated', 'Is_Cross_Year_Calculated',
    'Doc_Qtr_Year_Calculated', 'Post_Qtr_Year_Calculated', 'Is_Cross_Quarter_Calculated'
]

# Ensure all expected columns exist
missing_out_cols = [c for c in output_columns if c not in df_fbl3n.columns]
if missing_out_cols:
    raise ValueError(f"Missing expected output columns: {missing_out_cols}")

result_df = df_fbl3n[output_columns].copy()

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")