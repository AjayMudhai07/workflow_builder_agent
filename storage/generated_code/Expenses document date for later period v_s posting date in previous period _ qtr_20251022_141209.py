# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/6a26da2d-84df-4970-af43-9a0ee70035e9/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_1b9f31d3-1243-40a3-95e6-4e3b8ed9c7cf.csv"


# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBL3N = ['Document Date', 'Posting Date', 'Entry Date']
SAME_COLS_FBL3N = []          # No same‑case string columns needed for this workflow
UPPER_COLS_FBL3N = []         # No upper‑case string columns needed
LOWER_COLS_FBL3N = []         # No lower‑case string columns needed
TITLE_COLS_FBL3N = []         # No title‑case string columns needed
NUMERIC_COLS_FBL3N = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required source columns
required_columns_fbl3n = [
    "Company Code", "Document Number", "Posting Key", "G/L Account",
    "G/L Acct Long Text", "G/L Acct Long Text.1", "Cost Center", "Profit Center",
    "Document Date", "Posting Date", "Amount in local currency", "Document currency",
    "Document Type", "Text", "Document Header Text", "Reference", "Assignment",
    "Offsett.account type", "Offsetting acct no.", "Supplier", "Purchasing Document",
    "Entry Date", "User Name"
]
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBL3N:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, SAME_COLS_FBL3N, rules={
        "remove_excel_artifacts": True,
        "normalize_whitespace": True,
        "case_mode": "same"
    })

if UPPER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, UPPER_COLS_FBL3N, rules={
        "remove_excel_artifacts": True,
        "normalize_whitespace": True,
        "case_mode": "upper"
    })

if LOWER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, LOWER_COLS_FBL3N, rules={
        "remove_excel_artifacts": True,
        "normalize_whitespace": True,
        "case_mode": "lower"
    })

if TITLE_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBL3N, rules={
        "remove_excel_artifacts": True,
        "normalize_whitespace": True,
        "case_mode": "title"
    })

if NUMERIC_COLS_FBL3N:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBL3N)

print(f"✓ IRA preprocessing complete for FBL3N")


# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# -------------------------------------------------
# Step 1: Derive month‑year strings for Document and Posting dates
# -------------------------------------------------
df_fbl3n['Document Month-Year_Calculated'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting Month-Year_Calculated']   = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)

# -------------------------------------------------
# Step 2: Calculate whole‑month difference (Document – Posting)
# -------------------------------------------------
df_fbl3n['Month Difference_Calculated'] = (
    (df_fbl3n['Document Date'].dt.year - df_fbl3n['Posting Date'].dt.year) * 12 +
    (df_fbl3n['Document Date'].dt.month - df_fbl3n['Posting Date'].dt.month)
)

# -------------------------------------------------
# Step 3: Flags for crossing quarter / year boundaries
# -------------------------------------------------
df_fbl3n['Cross Quarter Flag_Calculated'] = np.where(
    df_fbl3n['Document Date'].dt.quarter != df_fbl3n['Posting Date'].dt.quarter,
    'Y', 'N'
)

df_fbl3n['Cross Year Flag_Calculated'] = np.where(
    df_fbl3n['Document Date'].dt.year != df_fbl3n['Posting Date'].dt.year,
    'Y', 'N'
)

print("✓ Calculated month‑year fields, month difference, and crossing flags")

# -------------------------------------------------
# Step 4: Filter for exceptions (Document month later than Posting month by ≥ 1)
# -------------------------------------------------
exception_df = df_fbl3n[df_fbl3n['Month Difference_Calculated'] >= 1].copy()
print(f"✓ Applied exception filter: {len(exception_df):,} flagged rows")

# -------------------------------------------------
# Step 5: Select and order final output columns
# -------------------------------------------------
output_columns = [
    "Company Code", "Document Number", "Posting Key", "G/L Account",
    "G/L Acct Long Text", "G/L Acct Long Text.1", "Cost Center", "Profit Center",
    "Document Date", "Posting Date", "Amount in local currency", "Document currency",
    "Document Type", "Text", "Document Header Text", "Reference", "Assignment",
    "Offsett.account type", "Offsetting acct no.", "Supplier", "Purchasing Document",
    "Entry Date", "User Name", "Document Month-Year_Calculated",
    "Posting Month-Year_Calculated", "Month Difference_Calculated",
    "Cross Quarter Flag_Calculated", "Cross Year Flag_Calculated"
]

# Ensure all required output columns exist (calculated ones have just been added)
missing_output = [col for col in output_columns if col not in exception_df.columns]
if missing_output:
    raise ValueError(f"Missing columns in final output: {missing_output}")

result_df = exception_df[output_columns].reset_index(drop=True)

# -------------------------------------------------
# Validation
# -------------------------------------------------
if result_df.empty:
    print("⚠ Warning: No exceptions detected – result dataframe is empty.")
else:
    print(f"✓ Final result prepared: {len(result_df):,} rows, {len(result_df.columns)} columns")

# -------------------------------------------------
# Save to CSV
# -------------------------------------------------
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")