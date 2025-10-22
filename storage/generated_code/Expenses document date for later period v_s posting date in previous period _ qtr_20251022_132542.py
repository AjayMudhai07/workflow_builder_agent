# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/75e7b838-d588-4b6c-bbe8-da7d7dd20967/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_a820bd3b-fc9f-4a29-8170-da49518244f2.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date']
SAME_COLS_FBLSN = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account',
    'Document Type', 'Local Currency', 'Cost Center', 'Profit Center',
    'Text', 'Document Header Text', 'Reference',
    'Offsett.account type', 'Offsetting acct no.', 'Year/month'
]
UPPER_COLS_FBLSN = []
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBLSN
    + SAME_COLS_FBLSN
    + UPPER_COLS_FBLSN
    + LOWER_COLS_FBLSN
    + TITLE_COLS_FBLSN
    + NUMERIC_COLS_FBLSN
)
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        SAME_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"},
    )

if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        UPPER_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"},
    )

if LOWER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        LOWER_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "lower"},
    )

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        TITLE_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"},
    )

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# ---- Derive period and quarter information ---------------------------------
df_fbl3n['Document_Month_Year_Calculated'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting_Month_Year_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)

df_fbl3n['Month_Difference_Calculated'] = (
    (df_fbl3n['Document Date'].dt.year - df_fbl3n['Posting Date'].dt.year) * 12
    + (df_fbl3n['Document Date'].dt.month - df_fbl3n['Posting Date'].dt.month)
)

df_fbl3n['Document_Quarter_Calculated'] = df_fbl3n['Document Date'].dt.to_period('Q').astype(str)
df_fbl3n['Posting_Quarter_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('Q').astype(str)

df_fbl3n['Cross_Year_Indicator_Calculated'] = np.where(
    df_fbl3n['Document Date'].dt.year > df_fbl3n['Posting Date'].dt.year, 'Yes', 'No'
)

# ---- Exception flag and reason ---------------------------------------------
df_fbl3n['Exception_Flag_Calculated'] = df_fbl3n['Month_Difference_Calculated'] > 0
df_fbl3n['Exception_Reason_Calculated'] = np.where(
    df_fbl3n['Exception_Flag_Calculated'],
    'Document Month-Year later than Posting Month-Year',
    ''
)

print(f"✓ Derived calculated fields for {len(df_fbl3n):,} rows")

# ---- Prepare final output ----------------------------------------------------
# Define final column order
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account', 'Document Type',
    'Document Date', 'Posting Date', 'Amount in local currency', 'Local Currency',
    'Cost Center', 'Profit Center', 'Text', 'Document Header Text', 'Reference',
    'Offsett.account type', 'Offsetting acct no.', 'Year/month',
    'Document_Month_Year_Calculated', 'Posting_Month_Year_Calculated',
    'Month_Difference_Calculated', 'Document_Quarter_Calculated',
    'Posting_Quarter_Calculated', 'Cross_Year_Indicator_Calculated',
    'Exception_Flag_Calculated', 'Exception_Reason_Calculated'
]

# Ensure all columns exist (in case of spelling differences)
missing_out_cols = [col for col in output_columns if col not in df_fbl3n.columns]
if missing_out_cols:
    raise ValueError(f"Missing columns for output: {missing_out_cols}")

result_df = df_fbl3n[output_columns].copy()

# Validate output
if result_df.empty:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result prepared: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")