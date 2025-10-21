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

# Flag rows where Document Date falls in a later accounting month-year than Posting Date
if len(df_fbl3n) == 0:
    print("⚠ Warning: FBL3N dataframe is empty! Saving empty output with headers.")

# Initialize period columns with nullable integer dtype
n_rows = len(df_fbl3n)
df_fbl3n['Doc_Period_YYYYMM'] = pd.Series([pd.NA] * n_rows, dtype='Int64')
df_fbl3n['Post_Period_YYYYMM'] = pd.Series([pd.NA] * n_rows, dtype='Int64')

# Masks for valid dates
mask_doc = df_fbl3n['Document Date'].notna()
mask_post = df_fbl3n['Posting Date'].notna()
mask_both = mask_doc & mask_post

# Compute YYYYMM for document and posting dates where available
doc_y = df_fbl3n.loc[mask_doc, 'Document Date'].dt.year
doc_m = df_fbl3n.loc[mask_doc, 'Document Date'].dt.month
post_y = df_fbl3n.loc[mask_post, 'Posting Date'].dt.year
post_m = df_fbl3n.loc[mask_post, 'Posting Date'].dt.month

if mask_doc.any():
    df_fbl3n.loc[mask_doc, 'Doc_Period_YYYYMM'] = (doc_y * 100 + doc_m).astype('Int64').values
if mask_post.any():
    df_fbl3n.loc[mask_post, 'Post_Period_YYYYMM'] = (post_y * 100 + post_m).astype('Int64').values

# Month difference where both dates are present
df_fbl3n['Doc_vs_Post_Months_Diff'] = np.nan
if mask_both.any():
    doc_y_b = df_fbl3n.loc[mask_both, 'Document Date'].dt.year
    doc_m_b = df_fbl3n.loc[mask_both, 'Document Date'].dt.month
    post_y_b = df_fbl3n.loc[mask_both, 'Posting Date'].dt.year
    post_m_b = df_fbl3n.loc[mask_both, 'Posting Date'].dt.month
    diff_vals = (doc_y_b - post_y_b) * 12 + (doc_m_b - post_m_b)
    df_fbl3n.loc[mask_both, 'Doc_vs_Post_Months_Diff'] = diff_vals.astype('float64').values

# Flag later document period strictly greater than posting period
df_fbl3n['DocDate_Later_Period_Flag'] = df_fbl3n['Doc_vs_Post_Months_Diff'] > 0

flagged_count = int(df_fbl3n['DocDate_Later_Period_Flag'].sum())
print(f"✓ Computed timing flag. Flagged rows: {flagged_count:,} of {len(df_fbl3n):,}")

# Include ALL rows of raw data with the computed fields
result_df = df_fbl3n.copy()
print(f"✓ Prepared final dataset with all rows: {len(result_df):,}")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")