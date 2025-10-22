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
    'Company Code', 'Document Number', 'G/L Account', 'G/L Acct Long Text',
    'G/L Acct Long Text.1', 'Document Type', 'Cost Center', 'Profit Center',
    'Text', 'Document Header Text', 'Reference', 'Offsett.account type',
    'Offsetting acct no.', 'User Name', 'Year/month', 'Long Text', 'Long Text.1'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document currency']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
)
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

# Calculate month-year components
doc_year = df_fbl3n['Document Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month
post_year = df_fbl3n['Posting Date'].dt.year
post_month = df_fbl3n['Posting Date'].dt.month

# String month-year representations
df_fbl3n['Document_Month_Year_Calculated'] = pd.PeriodIndex(df_fbl3n['Document Date'], freq='M').astype(str)
df_fbl3n['Posting_Month_Year_Calculated'] = pd.PeriodIndex(df_fbl3n['Posting Date'], freq='M').astype(str)

# Month number index (year*12 + month)
doc_ym = doc_year * 12 + doc_month
post_ym = post_year * 12 + post_month

# Month difference: positive when document period is later than posting period
df_fbl3n['Month_Diff_Calculated'] = doc_ym - post_ym

# Cross year flag
df_fbl3n['Cross_Year_Calculated'] = np.where(
    (doc_year.notna()) & (post_year.notna()) & (doc_year > post_year), 'Yes', 'No'
)

# Quarter calculations
doc_quarter = df_fbl3n['Document Date'].dt.quarter
post_quarter = df_fbl3n['Posting Date'].dt.quarter

# Quarter-Year strings
df_fbl3n['Document_Quarter_Year_Calculated'] = df_fbl3n['Document Date'].dt.to_period('Q').astype(str).replace('NaT', '')
df_fbl3n['Posting_Quarter_Year_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('Q').astype(str).replace('NaT', '')

# Quarter difference
df_fbl3n['Quarter_Diff_Calculated'] = (doc_year * 4 + doc_quarter) - (post_year * 4 + post_quarter)

# Quarter exception flag
df_fbl3n['Quarter_Exception_Flag_Calculated'] = np.where(df_fbl3n['Quarter_Diff_Calculated'] > 0, 'Yes', 'No')

print("✓ Calculated month-year and quarter-based fields")

# Core exception flag (Rule 1): month-year(Document Date) > month-year(Posting Date)
exception_mask = df_fbl3n['Month_Diff_Calculated'] > 0
flagged_count = int(exception_mask.sum())
print(f"✓ Applied core exception rule: {flagged_count:,} records flagged")

# Filter to flagged records only
result_df = df_fbl3n.loc[exception_mask].copy()

# Add fixed exception reason
result_df['Exception Reason_Calculated'] = 'Document month-year later than Posting month-year'

# Final output columns in the specified order
output_columns = [
    'Company Code', 'Document Number', 'Document Date', 'Posting Date', 'G/L Account',
    'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Amount in local currency', 'Local Currency',
    'Amount in doc. curr.', 'Document currency', 'Document Type', 'Cost Center', 'Profit Center',
    'Text', 'Document Header Text', 'Reference', 'Offsett.account type', 'Offsetting acct no.',
    'Entry Date', 'User Name', 'Year/month', 'Long Text', 'Long Text.1',
    'Document_Month_Year_Calculated', 'Posting_Month_Year_Calculated', 'Month_Diff_Calculated',
    'Cross_Year_Calculated', 'Exception Reason_Calculated',
    'Document_Quarter_Year_Calculated', 'Posting_Quarter_Year_Calculated',
    'Quarter_Diff_Calculated', 'Quarter_Exception_Flag_Calculated'
]

# Ensure all output columns exist before selection
missing_output_cols = [c for c in output_columns if c not in result_df.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns: {missing_output_cols}")

result_df = result_df[output_columns]

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")