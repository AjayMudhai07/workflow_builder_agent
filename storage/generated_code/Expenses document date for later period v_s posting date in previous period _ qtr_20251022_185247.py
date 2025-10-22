# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/f4457ecb-e2f7-4dcd-9fd8-3b3d9d875722/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_8d182eba-d1de-4c2e-94bf-d546598d7fe5.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# --------------------------------------------------------------------
# Load raw data
# --------------------------------------------------------------------
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# --------------------------------------------------------------------
# Align column names with Business Logic expectations
# --------------------------------------------------------------------
rename_map = {
    "Amount in doc. curr.": "Amount in document currency",
    "Document currency": "Document Currency",
}
df_fbl3n.rename(columns=rename_map, inplace=True)

# --------------------------------------------------------------------
# Column categories for IRA preprocessing
# --------------------------------------------------------------------
DATE_COLS_FBL3N = ["Document Date", "Posting Date"]
SAME_COLS_FBL3N = ["Document Number", "Company Code"]
UPPER_COLS_FBL3N = ["Document Type", "Local Currency", "Document Currency"]
LOWER_COLS_FBL3N = []                     # none required
TITLE_COLS_FBL3N = ["Text"]
NUMERIC_COLS_FBL3N = ["Amount in local currency", "Amount in document currency"]

# Columns needed for final output but not part of cleaning
EXTRA_REQUIRED_FBL3N = ["Posting Key", "Cost Center", "Profit Center", "Supplier"]

# --------------------------------------------------------------------
# Verify required columns exist
# --------------------------------------------------------------------
required_columns_fbl3n = (
    DATE_COLS_FBL3N
    + SAME_COLS_FBL3N
    + UPPER_COLS_FBL3N
    + TITLE_COLS_FBL3N
    + NUMERIC_COLS_FBL3N
    + EXTRA_REQUIRED_FBL3N
)

missing_columns = [c for c in required_columns_fbl3n if c not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# --------------------------------------------------------------------
# IRA preprocessing (dates → strings → numerics)
# --------------------------------------------------------------------
for col in DATE_COLS_FBL3N:
    df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        SAME_COLS_FBL3N,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"},
    )

if UPPER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        UPPER_COLS_FBL3N,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"},
    )

if LOWER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        LOWER_COLS_FBL3N,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "lower"},
    )

if TITLE_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n,
        TITLE_COLS_FBL3N,
        rules={"remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"},
    )

if NUMERIC_COLS_FBL3N:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBL3N)

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# --------------------------------------------------------------------
# Rule 1 – Flag rows where Document Date is later than Posting Date (full date)
# --------------------------------------------------------------------
df_fbl3n["Date Mismatch Flag"] = df_fbl3n["Document Date"] > df_fbl3n["Posting Date"]
print(f"✓ Applied Date Mismatch Flag (true rows: {df_fbl3n['Date Mismatch Flag'].sum():,})")

# --------------------------------------------------------------------
# Rule 6 – Days Difference between Document Date and Posting Date
# --------------------------------------------------------------------
df_fbl3n["Days Difference"] = (df_fbl3n["Document Date"] - df_fbl3n["Posting Date"]).dt.days

# --------------------------------------------------------------------
# Rule 7 – Derive Year‑Month fields (YYYY‑MM)
# --------------------------------------------------------------------
df_fbl3n["Year-Month Document"] = df_fbl3n["Document Date"].dt.strftime("%Y-%m")
df_fbl3n["Year-Month Posting"] = df_fbl3n["Posting Date"].dt.strftime("%Y-%m")

# --------------------------------------------------------------------
# Keep only mismatched records (Rule 4 – flag all mismatches)
# --------------------------------------------------------------------
result_df = df_fbl3n[df_fbl3n["Date Mismatch Flag"]].copy()
print(f"✓ Filtered mismatched records: {len(result_df):,}")

# --------------------------------------------------------------------
# Select and order final output columns
# --------------------------------------------------------------------
output_columns = [
    "Company Code",
    "Document Number",
    "Document Date",
    "Posting Date",
    "Posting Key",
    "Document Type",
    "Amount in local currency",
    "Local Currency",
    "Amount in document currency",
    "Document Currency",
    "Text",
    "Cost Center",
    "Profit Center",
    "Supplier",
    "Date Mismatch Flag",
    "Days Difference",
    "Year-Month Document",
    "Year-Month Posting",
]

result_df = result_df[output_columns]

# --------------------------------------------------------------------
# Final validation
# --------------------------------------------------------------------
if result_df.empty:
    print("⚠ Warning: No mismatched records found.")
else:
    print(f"✓ Final result ready: {len(result_df):,} rows, {len(result_df.columns)} columns")

# --------------------------------------------------------------------
# Save the result
# --------------------------------------------------------------------
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")