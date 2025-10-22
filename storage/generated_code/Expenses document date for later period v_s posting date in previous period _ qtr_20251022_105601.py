# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/62339d41-2fd6-43ef-8c6b-fe13b91aaf11/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_94ba8611-f972-4f03-8ffc-669d75514460.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'Document Type', 'G/L Account', 'G/L Acct Long Text',
    'Cost Center', 'Profit Center', 'Business Area', 'Posting Key', 'Offsett.account type',
    'Offsetting acct no.', 'Text', 'Document Header Text', 'Reference', 'User Name', 'Year/month'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document currency']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = [
    'Company Code', 'Document Number', 'Document Type', 'G/L Account', 'G/L Acct Long Text',
    'Cost Center', 'Profit Center', 'Business Area', 'Document Date', 'Posting Date',
    'Amount in local currency', 'Local Currency', 'Amount in doc. curr.', 'Document currency',
    'Posting Key', 'Offsett.account type', 'Offsetting acct no.', 'Text', 'Document Header Text',
    'Reference', 'Entry Date', 'User Name', 'Year/month'
]
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

# Create a working copy to append Exception_Flag without altering the original reference
result_df = df_fbl3n.copy()

# Rule 1: Exception when month-year(Document Date) > month-year(Posting Date)
if len(result_df) > 0:
    doc_dt = result_df['Document Date']
    post_dt = result_df['Posting Date']
    doc_ym = (doc_dt.dt.year * 12 + doc_dt.dt.month).astype('Int64')
    post_ym = (post_dt.dt.year * 12 + post_dt.dt.month).astype('Int64')
    exception_flag = (doc_ym > post_ym) & doc_dt.notna() & post_dt.notna()
    result_df['Exception_Flag'] = exception_flag.fillna(False).astype(bool)
else:
    result_df['Exception_Flag'] = pd.Series(dtype=bool)

# Reorder columns: keep original columns then append Exception_Flag
original_columns = [col for col in df_fbl3n.columns]
ordered_columns = original_columns + ['Exception_Flag']
result_df = result_df[ordered_columns]

exceptions_count = int(result_df['Exception_Flag'].sum()) if 'Exception_Flag' in result_df.columns else 0
print(f"✓ Added Exception_Flag column: {exceptions_count:,} exceptions flagged out of {len(result_df):,} rows")

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
output_dir = os.path.dirname(output_file_path) or "."
os.makedirs(output_dir, exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")