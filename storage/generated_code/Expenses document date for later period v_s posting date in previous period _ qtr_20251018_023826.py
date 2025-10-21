# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/6cf2045d-73ce-4683-8c5e-41dd2ee4cb10/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_d8cfb7a9-3e3f-4426-9ca2-1f4153e7a139.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date']
SAME_COLS_FBLSN = ['Cost Center', 'Profit Center', 'Text', 'Document Header Text', 'Reference']
UPPER_COLS_FBLSN = ['Account Type', 'Local Currency', 'Document Type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = ['G/L Acct Long Text', 'G/L Acct Long Text.1']
NUMERIC_COLS_FBLSN = ['Amount in local currency', 'Document Number', 'Posting Key', 'G/L Account', 'Company Code']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = list(set(DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN))
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

if LOWER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, LOWER_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "lower"})

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Apply scope: include only G/L line items where Account Type == 'S'
scope_df = df_fbl3n[df_fbl3n['Account Type'] == 'S'].copy()
print(f"✓ Applied scope (Account Type = 'S'): {len(scope_df):,} rows")

# Ensure both dates are present for evaluation
scope_df = scope_df[scope_df['Document Date'].notna() & scope_df['Posting Date'].notna()].copy()
print(f"✓ Retained rows with both dates present: {len(scope_df):,} rows")

# Derive period integers for month-year comparison (ignore day)
scope_df['Doc_Period_Int'] = scope_df['Document Date'].dt.year * 12 + scope_df['Document Date'].dt.month
scope_df['Post_Period_Int'] = scope_df['Posting Date'].dt.year * 12 + scope_df['Posting Date'].dt.month

# Calculate month difference (positive when Document Date is later than Posting Date)
scope_df['Month_Difference'] = scope_df['Doc_Period_Int'] - scope_df['Post_Period_Int']

# Flag exceptions where Document Month-Year is later than Posting Month-Year
exceptions_df = scope_df[scope_df['Month_Difference'] > 0].copy()
print(f"✓ Identified exceptions (Doc later than Post by month-year): {len(exceptions_df):,} rows")

if len(exceptions_df) > 0:
    # Derived display fields
    exceptions_df['Document_Month_Year'] = exceptions_df['Document Date'].dt.to_period('M').astype(str)
    exceptions_df['Posting_Month_Year'] = exceptions_df['Posting Date'].dt.to_period('M').astype(str)
    exceptions_df['Crosses_Year'] = exceptions_df['Document Date'].dt.year > exceptions_df['Posting Date'].dt.year

    # Select and order output columns
    output_columns = [
        'Company Code',
        'Document Number',
        'G/L Account',
        'Posting Key',
        'Document Type',
        'Cost Center',
        'Profit Center',
        'Document Date',
        'Posting Date',
        'Amount in local currency',
        'Local Currency',
        'G/L Acct Long Text',
        'G/L Acct Long Text.1',
        'Text',
        'Document Header Text',
        'Reference',
        'Document_Month_Year',
        'Posting_Month_Year',
        'Month_Difference',
        'Crosses_Year'
    ]

    # Ensure all columns exist before final selection
    missing_out_cols = [c for c in output_columns if c not in exceptions_df.columns]
    if missing_out_cols:
        raise ValueError(f"Missing expected output columns before final selection: {missing_out_cols}")

    result_df = exceptions_df[output_columns].copy()
else:
    # Create empty dataframe with the correct schema
    result_df = pd.DataFrame(columns=[
        'Company Code', 'Document Number', 'G/L Account', 'Posting Key', 'Document Type',
        'Cost Center', 'Profit Center', 'Document Date', 'Posting Date', 'Amount in local currency',
        'Local Currency', 'G/L Acct Long Text', 'G/L Acct Long Text.1', 'Text', 'Document Header Text',
        'Reference', 'Document_Month_Year', 'Posting_Month_Year', 'Month_Difference', 'Crosses_Year'
    ])
    print("⚠ Warning: No exceptions found; output will be an empty dataframe with headers.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")