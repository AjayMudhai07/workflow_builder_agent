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
DATE_COLS_FBLSN = [
    "Document Date",
    "Posting Date",
    "Entry Date",
]
SAME_COLS_FBLSN = [
    "Cost Center",
    "Profit Center",
    "Text",
    "Document Header Text",
    "Reference",
    "User Name",
    "Year/month",
]
UPPER_COLS_FBLSN = [
    "Local Currency",
    "Document currency",
    "Document Type",
    "Offsett.account type",
]
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = [
    "G/L Acct Long Text",
]
NUMERIC_COLS_FBLSN = [
    "Amount in local currency",
    "Amount in doc. curr.",
    "Company Code",
    "Document Number",
    "G/L Account",
    "Business Area",
    "Posting Key",
    "Offsetting acct no.",
]

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBLSN
    + SAME_COLS_FBLSN
    + UPPER_COLS_FBLSN
    + TITLE_COLS_FBLSN
    + NUMERIC_COLS_FBLSN
)
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        SAME_COLS_FBLSN,
        rules={
            "remove_excel_artifacts": True,
            "normalize_whitespace": True,
            "case_mode": "same",
        },
    )

if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        UPPER_COLS_FBLSN,
        rules={
            "remove_excel_artifacts": True,
            "normalize_whitespace": True,
            "case_mode": "upper",
        },
    )

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        TITLE_COLS_FBLSN,
        rules={
            "remove_excel_artifacts": True,
            "normalize_whitespace": True,
            "case_mode": "title",
        },
    )

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Derive month-year strings for Document Date and Posting Date
df_fbl3n['Doc_MonthYear'] = df_fbl3n['Document Date'].dt.strftime('%Y-%m')
df_fbl3n['Post_MonthYear'] = df_fbl3n['Posting Date'].dt.strftime('%Y-%m')
print("✓ Derived Doc_MonthYear and Post_MonthYear")

# Compute months difference (Document Date minus Posting Date)
doc_year = df_fbl3n['Document Date'].dt.year
post_year = df_fbl3n['Posting Date'].dt.year
doc_month = df_fbl3n['Document Date'].dt.month
post_month = df_fbl3n['Posting Date'].dt.month
months_diff = (doc_year - post_year) * 12 + (doc_month - post_month)

# Keep NaN where either date is missing
invalid_mask = df_fbl3n['Document Date'].isna() | df_fbl3n['Posting Date'].isna()
months_diff = months_diff.mask(invalid_mask)
df_fbl3n['Months_Diff'] = months_diff.astype('Int64')
print("✓ Calculated Months_Diff")

# Compute Cross_Year flag with object dtype to avoid dtype promotion errors
cross_year_series = pd.Series('No', index=df_fbl3n.index, dtype='object')
cross_year_series.loc[(~invalid_mask) & (doc_year > post_year)] = 'Yes'
cross_year_series.loc[invalid_mask] = np.nan
df_fbl3n['Cross_Year'] = cross_year_series
print("✓ Computed Cross_Year flag")

# Rule: Flag where Document Date month-year is later than Posting Date month-year (Months_Diff > 0)
flag_mask = df_fbl3n['Months_Diff'] > 0
result_df = df_fbl3n[flag_mask].copy()
print(f"✓ Flagged exceptions where Document Date is later than Posting Date: {len(result_df):,} rows")

# Select and order output columns as specified
output_columns = [
    "Company Code",
    "Document Number",
    "Document Type",
    "G/L Account",
    "G/L Acct Long Text",
    "Cost Center",
    "Profit Center",
    "Business Area",
    "Document Date",
    "Posting Date",
    "Amount in local currency",
    "Local Currency",
    "Amount in doc. curr.",
    "Document currency",
    "Posting Key",
    "Offsett.account type",
    "Offsetting acct no.",
    "Text",
    "Document Header Text",
    "Reference",
    "Entry Date",
    "User Name",
    "Year/month",
    "Doc_MonthYear",
    "Post_MonthYear",
    "Months_Diff",
    "Cross_Year",
]

# Validate presence of all output columns
missing_out_cols = [col for col in output_columns if col not in result_df.columns]
if missing_out_cols:
    raise ValueError(f"Missing expected output columns: {missing_out_cols}")

result_df = result_df[output_columns].reset_index(drop=True)

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty! No exceptions found based on the defined rule.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
output_dir = os.path.dirname(output_file_path)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")