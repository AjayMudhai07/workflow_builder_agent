# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/042d387b-1c6c-4a33-b48b-4050ed43a162/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_3e540862-9a65-481d-8759-3f9dfd1a7194.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBLSN = ['Document Type', 'Cost Center', 'Profit Center', 'Text', 'Document Header Text', 'Reference', 'User Name']
UPPER_COLS_FBLSN = ['Local Currency', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = ['G/L Acct Long Text.1']
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Company Code', 'Document Number', 'Posting Key', 'G/L Account', 'Offsetting acct no.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = list(dict.fromkeys(
    DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
))
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")
print("✓ Verified required columns for FBL3N")

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

# Derive month-year strings for Document Date and Posting Date
df_fbl3n['Document_MonthYear_Calculated'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting_MonthYear_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)
print("✓ Derived Document_MonthYear_Calculated and Posting_MonthYear_Calculated")

# Compute month difference (Document month - Posting month); positive only when Document is later
valid_dates = df_fbl3n['Document Date'].notna() & df_fbl3n['Posting Date'].notna()
months_doc = (df_fbl3n['Document Date'].dt.year * 12 + df_fbl3n['Document Date'].dt.month)
months_post = (df_fbl3n['Posting Date'].dt.year * 12 + df_fbl3n['Posting Date'].dt.month)
month_diff_series = (months_doc - months_post).where(valid_dates)
df_fbl3n['Month_Difference_Calculated'] = month_diff_series.astype('Int64')
print("✓ Computed Month_Difference_Calculated")

# Flag exceptions where Document month-year is later than Posting month-year
flag_mask = df_fbl3n['Month_Difference_Calculated'] > 0
result_df = df_fbl3n.loc[flag_mask].copy()
print(f"✓ Applied exception flag: {flag_mask.sum():,} records flagged")

# Add standardized flag reason
result_df['Flag_Reason'] = "Document month-year later than Posting month-year"

# Select and order output columns as specified
final_columns = [
    'Company Code', 'Document Number', 'Document Type', 'Posting Key', 'G/L Account', 'G/L Acct Long Text.1',
    'Cost Center', 'Profit Center', 'Document Date', 'Posting Date', 'Amount in local currency', 'Local Currency',
    'Text', 'Document Header Text', 'Reference', 'Offsett.account type', 'Offsetting acct no.', 'Entry Date',
    'User Name', 'Document_MonthYear_Calculated', 'Posting_MonthYear_Calculated', 'Month_Difference_Calculated',
    'Flag_Reason'
]

# Validate that all final columns exist
missing_final_cols = [c for c in final_columns if c not in result_df.columns]
if missing_final_cols:
    raise ValueError(f"Missing expected output columns: {missing_final_cols}")

result_df = result_df[final_columns]

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty! No exceptions found based on month-year comparison.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")