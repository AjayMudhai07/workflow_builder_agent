# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/7169d4e8-b3e0-420a-a633-a6fd5eb681d5/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_602b2a8e-29f0-4e22-8115-b7556cf80b40.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBL3N = ['Document Date', 'Posting Date', 'Year/month']
SAME_COLS_FBL3N = []
UPPER_COLS_FBL3N = []
LOWER_COLS_FBL3N = []
TITLE_COLS_FBL3N = []
NUMERIC_COLS_FBL3N = ['Amount in local currency', 'Amount in doc. curr.']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = [
    "Company Code", "Document Number", "Posting Key", "G/L Account", "Account",
    "Document Date", "Posting Date", "Year/month", "Document Type",
    "Amount in local currency", "Local Currency", "Amount in doc. curr.",
    "Document currency", "Cost Center", "Profit Center", "G/L Acct Long Text",
    "G/L Acct Long Text.1", "Text", "Document Header Text", "Reference",
    "Offsett.account type", "Offsetting acct no.", "Entry Date", "User Name"
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
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

if UPPER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, UPPER_COLS_FBL3N, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

if LOWER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, LOWER_COLS_FBL3N, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "lower"})

if TITLE_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBL3N, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBL3N:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBL3N)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# --------------------------------------------------------------------
# Create month‑year derived columns (ignoring day component)
# --------------------------------------------------------------------
df_fbl3n['Doc_MonthYear_Calculated'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting_MonthYear_Calculated'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)
df_fbl3n['YearMonth_Calculated'] = df_fbl3n['Year/month'].dt.to_period('M').astype(str)

print("✓ Calculated month‑year fields")

# --------------------------------------------------------------------
# Flag exceptions: Document month‑year must be later than BOTH
# Posting month‑year AND SAP Year/month period
# --------------------------------------------------------------------
condition = (
    (df_fbl3n['Doc_MonthYear_Calculated'] > df_fbl3n['Posting_MonthYear_Calculated']) &
    (df_fbl3n['Doc_MonthYear_Calculated'] > df_fbl3n['YearMonth_Calculated'])
)

df_exceptions = df_fbl3n[condition].copy()
df_exceptions['Exception_Flag_Calculated'] = 1

print(f"✓ Applied exception flag: {len(df_exceptions):,} rows flagged")

# --------------------------------------------------------------------
# Prepare final output with required columns + calculated fields
# --------------------------------------------------------------------
output_columns = required_columns_fbl3n + [
    'Doc_MonthYear_Calculated',
    'Posting_MonthYear_Calculated',
    'Exception_Flag_Calculated'
]

result_df = df_exceptions[output_columns].reset_index(drop=True)

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# --------------------------------------------------------------------
# Save result
# --------------------------------------------------------------------
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")