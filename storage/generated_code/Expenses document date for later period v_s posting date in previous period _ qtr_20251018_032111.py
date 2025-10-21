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
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account',
    'Text', 'Document Header Text', 'G/L Acct Long Text', 'G/L Acct Long Text.1',
    'Cost Center', 'Profit Center', 'Reference', 'User Name',
    'Offsett.account type', 'Offsetting acct no.'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document Type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = sorted(set(DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN))
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

# Clean only object dtype columns for string cleaning to avoid altering numeric codes
same_object_cols = [c for c in SAME_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
if same_object_cols:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, same_object_cols, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

upper_object_cols = [c for c in UPPER_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
if upper_object_cols:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, upper_object_cols, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

if TITLE_COLS_FBLSN:
    title_object_cols = [c for c in TITLE_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
    if title_object_cols:
        df_fbl3n = ira.clean_strings_batch(df_fbl3n, title_object_cols, rules={
            "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Derive month-year strings for Document and Posting dates
df_fbl3n['Doc_MonthYear'] = df_fbl3n['Document Date'].dt.strftime('%Y-%m')
df_fbl3n['Post_MonthYear'] = df_fbl3n['Posting Date'].dt.strftime('%Y-%m')

# Compute Month_Diff = (DocYear-PostYear)*12 + (DocMonth-PostMonth)
doc_year = df_fbl3n['Document Date'].dt.year
post_year = df_fbl3n['Posting Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month
post_month = df_fbl3n['Posting Date'].dt.month
# Result will be float if NaT present; that's fine for comparison and output
df_fbl3n['Month_Diff'] = (doc_year - post_year) * 12 + (doc_month - post_month)

# Derive quarters in format Qn-YYYY
doc_q = df_fbl3n['Document Date'].dt.quarter
post_q = df_fbl3n['Posting Date'].dt.quarter
df_fbl3n['Doc_Quarter'] = 'Q' + doc_q.astype('Int64').astype(str) + '-' + df_fbl3n['Document Date'].dt.year.astype('Int64').astype(str)
df_fbl3n['Post_Quarter'] = 'Q' + post_q.astype('Int64').astype(str) + '-' + df_fbl3n['Posting Date'].dt.year.astype('Int64').astype(str)

# Rule 1: Keep items where Document Month-Year is later than Posting Month-Year
result_df = df_fbl3n[df_fbl3n['Month_Diff'] > 0].copy()
print(f"✓ Applied Rule 1 (Doc later than Post): {len(result_df):,} rows")

# Rule 2: Exclude entries containing 'PROVISION' in G/L Acct Long Text
if 'G/L Acct Long Text' in result_df.columns:
    before = len(result_df)
    mask_prov = result_df['G/L Acct Long Text'].str.contains('PROVISION', case=False, na=False)
    result_df = result_df[~mask_prov].copy()
    print(f"✓ Applied Rule 2 (exclude PROVISION): removed {before - len(result_df):,} rows")

# Rule 3: Exclude entries containing 'Clearing' in G/L Acct Long Text
if 'G/L Acct Long Text' in result_df.columns:
    before = len(result_df)
    mask_clear = result_df['G/L Acct Long Text'].str.contains('Clearing', case=False, na=False)
    result_df = result_df[~mask_clear].copy()
    print(f"✓ Applied Rule 3 (exclude Clearing): removed {before - len(result_df):,} rows")

# Exception reason column
result_df['Exception_Reason'] = "Document Date later than Posting Date (month-year)"

# Prepare final output columns in required order
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account',
    'Document Date', 'Posting Date', 'Amount in local currency', 'Local Currency',
    'Document Type', 'Text', 'Document Header Text', 'G/L Acct Long Text',
    'G/L Acct Long Text.1', 'Cost Center', 'Profit Center', 'Reference',
    'Entry Date', 'User Name', 'Offsett.account type', 'Offsetting acct no.',
    'Doc_MonthYear', 'Post_MonthYear', 'Month_Diff', 'Doc_Quarter', 'Post_Quarter',
    'Exception_Reason'
]

missing_output_cols = [c for c in output_columns if c not in result_df.columns]
if missing_output_cols:
    # Create any missing derived columns as empty to preserve schema
    for col in missing_output_cols:
        result_df[col] = np.nan
    missing_output_cols = [c for c in output_columns if c not in result_df.columns]
    if missing_output_cols:
        raise ValueError(f"Missing expected output columns: {missing_output_cols}")

result_df = result_df[output_columns].copy()

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")