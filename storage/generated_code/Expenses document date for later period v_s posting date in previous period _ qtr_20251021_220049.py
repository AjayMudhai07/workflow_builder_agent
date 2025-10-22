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
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'Posting Key', 'Account', 'G/L Account',
    'Cost Center', 'Profit Center', 'Document Type', 'Text', 'Document Header Text',
    'Reference', 'Offsetting acct no.', 'User Name', 'Year/month'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document currency', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify base required columns from Business Logic Plan
REQUIRED_BASE_COLS = [
    "Company Code", "Document Number", "Posting Key", "Account", "G/L Account",
    "Document Date", "Posting Date", "Amount in local currency", "Local Currency",
    "Amount in doc. curr.", "Document currency", "Cost Center", "Profit Center",
    "Document Type", "Text", "Document Header Text", "Reference", "Offsett.account type",
    "Offsetting acct no.", "Entry Date", "User Name", "Year/month"
]
missing_base_cols = [col for col in REQUIRED_BASE_COLS if col not in df_fbl3n.columns]
if missing_base_cols:
    raise ValueError(f"Missing columns in FBL3N required by plan: {missing_base_cols}")

# Verify required columns for preprocessing (union of category lists)
required_columns_fbl3n = list(set(DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN))
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N for preprocessing: {missing_columns}")

# IRA preprocessing for FBL3N
# Dates
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

# Strings (preserve case)
same_cols_to_clean = [c for c in SAME_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
if same_cols_to_clean:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, same_cols_to_clean, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

# Uppercase strings
upper_cols_to_clean = [c for c in UPPER_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
if upper_cols_to_clean:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, upper_cols_to_clean, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

# Title case strings (none in this workflow but kept for structure)
title_cols_to_clean = [c for c in TITLE_COLS_FBLSN if c in df_fbl3n.columns and df_fbl3n[c].dtype == 'object']
if title_cols_to_clean:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, title_cols_to_clean, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

# Numeric amounts
if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Rule: Flag line where Document Date month-year > Posting Date month-year
post_year = df_fbl3n['Posting Date'].dt.year
post_month = df_fbl3n['Posting Date'].dt.month
doc_year = df_fbl3n['Document Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month

post_ym = post_year * 12 + post_month
doc_ym = doc_year * 12 + doc_month

exception_flag = (doc_ym > post_ym)

# Month difference: number of months Document Date is ahead of Posting Date
month_diff = np.where(
    exception_flag,
    (doc_ym - post_ym),
    np.where((doc_ym.isna()) | (post_ym.isna()), np.nan, 0)
)
month_diff = pd.Series(month_diff, index=df_fbl3n.index).astype('Int64')

# Year boundary flag: Document year later than Posting year
year_boundary_flag = (doc_year > post_year) & exception_flag

# Quarter context as "YYYY-Q#"
posting_quarter_num = post_month.apply(lambda m: ((m - 1) // 3) + 1 if pd.notna(m) else np.nan)
document_quarter_num = doc_month.apply(lambda m: ((m - 1) // 3) + 1 if pd.notna(m) else np.nan)

posting_quarter = np.where(
    df_fbl3n['Posting Date'].notna(),
    post_year.astype('Int64').astype(str) + '-Q' + posting_quarter_num.astype('Int64').astype(str),
    None
)
document_quarter = np.where(
    df_fbl3n['Document Date'].notna(),
    doc_year.astype('Int64').astype(str) + '-Q' + document_quarter_num.astype('Int64').astype(str),
    None
)

# Exception reason
exception_reason = np.where(
    exception_flag,
    'Document month-year later than Posting month-year by ' + month_diff.astype(str) + ' months',
    ''
)

# Create calculated columns
df_fbl3n['Exception Flag_Calculated'] = exception_flag
df_fbl3n['Month Difference_Calculated'] = month_diff
df_fbl3n['Posting Quarter_Calculated'] = posting_quarter
df_fbl3n['Document Quarter_Calculated'] = document_quarter
df_fbl3n['Year Boundary Flag_Calculated'] = year_boundary_flag
df_fbl3n['Exception Reason_Calculated'] = exception_reason

# Final output columns in required order
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'Account', 'G/L Account',
    'Document Date', 'Posting Date', 'Amount in local currency', 'Local Currency',
    'Amount in doc. curr.', 'Document currency', 'Cost Center', 'Profit Center',
    'Document Type', 'Text', 'Document Header Text', 'Reference', 'Offsett.account type',
    'Offsetting acct no.', 'Entry Date', 'User Name', 'Year/month',
    'Exception Flag_Calculated', 'Month Difference_Calculated', 'Posting Quarter_Calculated',
    'Document Quarter_Calculated', 'Year Boundary Flag_Calculated', 'Exception Reason_Calculated'
]

# Validate output columns presence
missing_output_cols = [col for col in output_columns if col not in df_fbl3n.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns in FBL3N after processing: {missing_output_cols}")

# Assemble result
result_df = df_fbl3n[output_columns].copy()

total_rows = len(result_df)
flagged_rows = int(result_df['Exception Flag_Calculated'].sum())
print(f"✓ Applied exception rules: {flagged_rows:,} exceptions out of {total_rows:,} rows")
print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")