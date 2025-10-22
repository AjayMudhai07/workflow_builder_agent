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
    'Cost Center', 'Profit Center', 'Reference', 'User Name', 'Year/month',
    'Text', 'Document Header Text', 'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Long Text', 'Long Text.1'
]
UPPER_COLS_FBLSN = ['Local Currency', 'Document currency', 'Document Type', 'Offsett.account type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns (Business Logic Plan required + categorized columns)
REQUIRED_COLS_FBLSN = [
    "Company Code", "Document Number", "Document Date", "Posting Date", "G/L Account",
    "G/L Acct Long Text", "G/L Acct Long Text.1", "Amount in local currency", "Local Currency",
    "Amount in doc. curr.", "Document currency", "Document Type", "Cost Center", "Profit Center",
    "Text", "Document Header Text", "Reference", "Offsett.account type", "Offsetting acct no.",
    "Entry Date", "User Name", "Year/month", "Long Text", "Long Text.1"
]
required_columns_fbl3n = list(set(
    REQUIRED_COLS_FBLSN + DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
))
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing required columns in FBL3N: {missing_columns}")
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

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Derive month-year for Document Date and Posting Date
df_fbl3n['Document_Month_Year_Calculated'] = df_fbl3n['Document Date'].dt.strftime('%Y-%m')
df_fbl3n['Posting_Month_Year_Calculated'] = df_fbl3n['Posting Date'].dt.strftime('%Y-%m')
print("✓ Derived month-year strings for Document and Posting dates")

# Calculate month difference: (DocYear - PostYear) * 12 + (DocMonth - PostMonth)
doc_year = df_fbl3n['Document Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month
post_year = df_fbl3n['Posting Date'].dt.year
post_month = df_fbl3n['Posting Date'].dt.month

month_diff = (doc_year - post_year) * 12 + (doc_month - post_month)
month_diff = month_diff.where(~(doc_year.isna() | post_year.isna()))
df_fbl3n['Month_Diff_Calculated'] = month_diff
print("✓ Calculated Month_Diff_Calculated")

# Cross-year indicator (Yes if the periods cross calendar years)
df_fbl3n['Cross_Year_Calculated'] = np.where((doc_year > post_year) & month_diff.notna(), 'Yes', 'No')
print("✓ Derived Cross_Year_Calculated")

# Apply exception rule: Flag rows where Document month-year is later than Posting month-year
flag_mask = df_fbl3n['Month_Diff_Calculated'] > 0
flagged_df = df_fbl3n[flag_mask].copy()
print(f"✓ Applied exception rule: {len(flagged_df):,} rows flagged")

# Add fixed exception reason
flagged_df['Exception Reason_Calculated'] = "Document month-year later than Posting month-year"

# Final output columns in specified order
output_columns = [
    "Company Code", "Document Number", "Document Date", "Posting Date", "G/L Account",
    "G/L Acct Long Text", "G/L Acct Long Text.1", "Amount in local currency", "Local Currency",
    "Amount in doc. curr.", "Document currency", "Document Type", "Cost Center", "Profit Center",
    "Text", "Document Header Text", "Reference", "Offsett.account type", "Offsetting acct no.",
    "Entry Date", "User Name", "Year/month", "Long Text", "Long Text.1",
    "Document_Month_Year_Calculated", "Posting_Month_Year_Calculated", "Month_Diff_Calculated",
    "Cross_Year_Calculated", "Exception Reason_Calculated"
]

# Validate output columns exist
missing_output_cols = [col for col in output_columns if col not in flagged_df.columns]
if missing_output_cols:
    raise ValueError(f"Missing expected output columns before saving: {missing_output_cols}")

result_df = flagged_df[output_columns].copy()

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty! No exceptions found based on the rule.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")