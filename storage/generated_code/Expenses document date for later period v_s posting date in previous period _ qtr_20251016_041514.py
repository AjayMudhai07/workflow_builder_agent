# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = csv_files[0]
output_file_path = output_path

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = [
    'Text', 'Document Header Text', 'Reference', 'Assignment', 'User Name',
    'G/L Acct Long Text', 'Cost Center', 'Profit Center'
]
UPPER_COLS_FBLSN = ['Account Type', 'Local Currency', 'Document Type', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = [
    'Amount in local currency', 'G/L Account', 'Company Code',
    'Document Number', 'Posting Key', 'Offsetting acct no.'
]

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = list(set(DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN))
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

# 1) Filter population: Account Type = 'S'
df_s = df_fbl3n[df_fbl3n['Account Type'] == 'S'].copy()
print(f"✓ Applied filter Account Type='S': {len(df_s):,} rows")

# 1b) Include only debits based on Posting Key (for G/L Account 'S', debit posting key is 40)
df_s = df_s[df_s['Posting Key'] == 40].copy()
print(f"✓ Applied debit filter by Posting Key (40): {len(df_s):,} rows")

# 2) Derive period components and calculated fields
# Extract year and month from Document Date and Posting Date
doc_year = df_s['Document Date'].dt.year
post_year = df_s['Posting Date'].dt.year
doc_month = df_s['Document Date'].dt.month
post_month = df_s['Posting Date'].dt.month

# Period strings YYYY-MM
df_s['Doc_Period'] = df_s['Document Date'].dt.strftime('%Y-%m')
df_s['Post_Period'] = df_s['Posting Date'].dt.strftime('%Y-%m')

# Month_Diff calculation
month_diff = (doc_year - post_year) * 12 + (doc_month - post_month)
df_s['Month_Diff'] = month_diff

# Quarter_Mismatch and Flag
df_s['Quarter_Mismatch'] = (df_s['Month_Diff'] >= 3)
df_s['Flag'] = (df_s['Month_Diff'] > 0)
print("✓ Derived Doc_Period, Post_Period, Month_Diff, Quarter_Mismatch, Flag")

# 3) Keep one row per line item (Document Number + Posting Key)
pre_dedup_rows = len(df_s)
df_s = df_s.drop_duplicates(subset=['Document Number', 'Posting Key'], keep='first').copy()
print(f"✓ Deduplicated by Document Number + Posting Key: {pre_dedup_rows:,} -> {len(df_s):,} rows")

# 4) Optional sort for review
sort_cols = ['Flag', 'Month_Diff', 'Posting Date', 'Company Code', 'Document Number', 'Posting Key']
sort_ascending = [False, False, True, True, True, True]
for c in sort_cols:
    if c not in df_s.columns:
        raise KeyError(f"Required sort column missing: {c}")
df_s = df_s.sort_values(by=sort_cols, ascending=sort_ascending)
print("✓ Applied sorting for review")

# 5) Select and order output columns
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'Account Type', 'G/L Account', 'G/L Acct Long Text',
    'Cost Center', 'Profit Center', 'Document Date', 'Posting Date', 'Amount in local currency', 'Local Currency',
    'Document Type', 'Text', 'Document Header Text', 'Offsetting acct no.', 'Offsett.account type', 'Reference',
    'Assignment', 'Entry Date', 'User Name', 'Doc_Period', 'Post_Period', 'Month_Diff', 'Quarter_Mismatch', 'Flag'
]
missing_out_cols = [c for c in output_columns if c not in df_s.columns]
if missing_out_cols:
    raise ValueError(f"Missing required output columns in FBL3N after processing: {missing_out_cols}")

result_df = df_s[output_columns].copy()
print(f"✓ Final result prepared: {len(result_df):,} rows, {len(result_df.columns)} columns")

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")