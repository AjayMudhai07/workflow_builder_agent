# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/718312cd-2091-4949-8f33-32ef6a9116c9/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_1293ef0c-f854-4541-9e21-f164fe333f41.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Strict required columns from Business Logic Plan
REQUIRED_COLUMNS_FBLSN = [
    "Company Code", "Document Number", "Document Type", "Document Date", "Posting Date",
    "G/L Account", "G/L Acct Long Text", "Amount in local currency", "Local Currency",
    "Amount in doc. curr.", "Document currency", "Cost Center", "Profit Center",
    "Posting Key", "Reference", "Document Header Text", "Text", "User Name", "Entry Date"
]

# Column categories for IRA preprocessing
DATE_COLS_FBLSN = ["Document Date", "Posting Date", "Entry Date"]
SAME_COLS_FBLSN = ["Reference", "Document Header Text", "Text", "User Name", "Cost Center", "Profit Center", "G/L Acct Long Text"]
UPPER_COLS_FBLSN = ["Local Currency", "Document currency", "Document Type"]
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ["Amount in local currency", "Amount in doc. curr."]

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns exist
missing_columns = [col for col in REQUIRED_COLUMNS_FBLSN if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
# Dates
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

# Strings - SAME case
if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, SAME_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"}
    )

# Strings - UPPER case
if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, UPPER_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"}
    )

# Strings - TITLE case (not used here, but kept for completeness)
if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, TITLE_COLS_FBLSN,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"}
    )

# Numerics
if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Rule: Derive month-year and months difference fields for Document vs Posting dates
doc_dates = df_fbl3n["Document Date"]
post_dates = df_fbl3n["Posting Date"]

df_fbl3n["Doc_Month_Year_Calculated"] = doc_dates.dt.strftime("%Y-%m")
df_fbl3n["Post_Month_Year_Calculated"] = post_dates.dt.strftime("%Y-%m")

months_diff = (doc_dates.dt.year - post_dates.dt.year) * 12 + (doc_dates.dt.month - post_dates.dt.month)
df_fbl3n["Doc_Posting_Months_Diff_Calculated"] = pd.Series(months_diff, index=df_fbl3n.index).astype("Int64")

cross_year = (doc_dates.dt.year > post_dates.dt.year)
df_fbl3n["Is_Cross_Year_Calculated"] = cross_year.map({True: "Yes", False: "No"})
print("✓ Derived month-year and months-difference indicators")

# Apply primary exception rule: Document month-year strictly later than Posting month-year (months_diff > 0)
exceptions_df = df_fbl3n[df_fbl3n["Doc_Posting_Months_Diff_Calculated"] > 0].copy()
print(f"✓ Applied exception rule: {len(exceptions_df):,} rows flagged where Document month-year is later than Posting month-year")

# Select and order output columns exactly as specified
output_columns = [
    "Company Code", "Document Number", "Document Type", "Document Date", "Posting Date",
    "G/L Account", "G/L Acct Long Text", "Amount in local currency", "Local Currency",
    "Amount in doc. curr.", "Document currency", "Cost Center", "Profit Center", "Posting Key",
    "Reference", "Document Header Text", "Text", "User Name", "Entry Date",
    "Doc_Posting_Months_Diff_Calculated", "Doc_Month_Year_Calculated", "Post_Month_Year_Calculated",
    "Is_Cross_Year_Calculated"
]

missing_out_cols = [c for c in output_columns if c not in exceptions_df.columns]
if missing_out_cols:
    raise ValueError(f"Missing expected output columns: {missing_out_cols}")

result_df = exceptions_df[output_columns].copy()

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty based on the applied rule.")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")