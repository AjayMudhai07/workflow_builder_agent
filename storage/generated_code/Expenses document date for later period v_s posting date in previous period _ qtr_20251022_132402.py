# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/75e7b838-d588-4b6c-bbe8-da7d7dd20967/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_a820bd3b-fc9f-4a29-8170-da49518244f2.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBL3N = ['Document Date', 'Posting Date']
SAME_COLS_FBL3N = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account',
    'Document Type', 'Local Currency', 'Cost Center', 'Profit Center',
    'Text', 'Document Header Text', 'Reference',
    'Offsett.account type', 'Year/month'
]
UPPER_COLS_FBL3N = []
LOWER_COLS_FBL3N = []
TITLE_COLS_FBL3N = []
NUMERIC_COLS_FBL3N = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBL3N + SAME_COLS_FBL3N + UPPER_COLS_FBL3N +
    LOWER_COLS_FBL3N + TITLE_COLS_FBL3N + NUMERIC_COLS_FBL3N
)
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBL3N:
    df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, SAME_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "same"}
    )

if UPPER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, UPPER_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "upper"}
    )

if LOWER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, LOWER_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "lower"}
    )

if TITLE_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, TITLE_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "title"}
    )

if NUMERIC_COLS_FBL3N:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBL3N)

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# -------------------------------------------------
# Derive period related fields
# -------------------------------------------------
# Document Month-Year
df_fbl3n['Document Month-Year_Calculated'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)

# Posting Month-Year
df_fbl3n['Posting Month-Year_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)

# Month Difference (Document later than Posting)
doc_year = df_fbl3n['Document Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month
post_year = df_fbl3n['Posting Date'].dt.year
post_month = df_fbl3n['Posting Date'].dt.month

month_diff = (doc_year - post_year) * 12 + (doc_month - post_month)
df_fbl3n['Month Difference_Calculated'] = month_diff

# Document Quarter
df_fbl3n['Document Quarter_Calculated'] = df_fbl3n['Document Date'].dt.quarter

# Posting Quarter
df_fbl3n['Posting Quarter_Calculated'] = df_fbl3n['Posting Date'].dt.quarter

# Cross-Year Indicator
df_fbl3n['Cross-Year Indicator_Calculated'] = np.where(
    doc_year > post_year, 'Yes', 'No'
)

# -------------------------------------------------
# Flag exceptions where Document Month-Year > Posting Month-Year
# -------------------------------------------------
df_fbl3n['Exception Flag_Calculated'] = month_diff > 0
df_fbl3n['Exception Reason_Calculated'] = np.where(
    df_fbl3n['Exception Flag_Calculated'],
    'Document Month-Year later than Posting Month-Year',
    ''
)

# Keep only flagged exceptions
result_df = df_fbl3n[df_fbl3n['Exception Flag_Calculated']].copy()
print(f"✓ Flagged {len(result_df):,} exception rows")

# -------------------------------------------------
# Select output columns in required order
# -------------------------------------------------
output_columns = [
    'Company Code', 'Document Number', 'Posting Key', 'G/L Account',
    'Document Type', 'Document Date', 'Posting Date',
    'Amount in local currency', 'Local Currency',
    'Cost Center', 'Profit Center', 'Text', 'Document Header Text',
    'Reference', 'Offsett.account type', 'Offsetting acct no.', 'Year/month',
    'Document Month-Year_Calculated', 'Posting Month-Year_Calculated',
    'Month Difference_Calculated', 'Document Quarter_Calculated',
    'Posting Quarter_Calculated', 'Cross-Year Indicator_Calculated',
    'Exception Flag_Calculated', 'Exception Reason_Calculated'
]

# Ensure all output columns exist (some may be missing if not in source)
missing_out_cols = [col for col in output_columns if col not in result_df.columns]
if missing_out_cols:
    raise ValueError(f"Missing columns for output: {missing_out_cols}")

result_df = result_df[output_columns]

# Validate non‑empty result
if result_df.empty:
    print("⚠ Warning: No exceptions found based on the defined rule.")

print(f"✓ Final result prepared: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save to CSV
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")