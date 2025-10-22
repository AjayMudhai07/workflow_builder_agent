# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/b44a50cb-072c-477c-96cd-5f73bbc12380/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_dc0ec4da-aaa5-4fdb-bbd2-1064e75396dd.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# --------------------------------------------------------------------
# 1. Load the source file
# --------------------------------------------------------------------
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# --------------------------------------------------------------------
# 2. Verify that the two date columns required for the rule exist
# --------------------------------------------------------------------
required_date_cols = ['Document Date', 'Posting Date']
missing_dates = [c for c in required_date_cols if c not in df_fbl3n.columns]
if missing_dates:
    raise ValueError(f"Missing essential date columns in FBL3N: {missing_dates}")

# --------------------------------------------------------------------
# 3. Align column names to the names expected by the Business Logic Plan
#    (rename where a source column maps to a required name)
# --------------------------------------------------------------------
rename_map = {
    'Amount in local currency': 'Amount (Local Currency)',
    'Supplier': 'Supplier (Vendor)',
    'Sub-number': 'Document Item (Sub-number)',
    'Local Currency': 'Currency',
    'Reference': 'Reference Document'
    # Columns that truly do not exist (Batch, Tax Code) will be added later as NaN
}
df_fbl3n = df_fbl3n.rename(columns=rename_map)

# --------------------------------------------------------------------
# 4. Ensure all columns that will appear in the final output exist.
#    Missing ones are created with NaN values.
# --------------------------------------------------------------------
expected_output_cols = [
    "Company Code", "Document Number", "Document Item (Sub-number)",
    "Document Date", "Posting Date", "Document Type", "Posting Key",
    "Amount (Local Currency)", "G/L Account", "Cost Center", "Profit Center",
    "Supplier (Vendor)", "Material", "Text", "Fiscal Year", "Fiscal Period",
    "Currency", "Reference Document", "Batch", "Tax Code", "Business Area",
    "Date_Mismatch_Flag"
]

for col in expected_output_cols:
    if col not in df_fbl3n.columns:
        df_fbl3n[col] = np.nan

# --------------------------------------------------------------------
# 5. Define IRA column categories (using the *post‑rename* column names)
# --------------------------------------------------------------------
DATE_COLS_FBL3N = ['Document Date', 'Posting Date']
SAME_COLS_FBL3N = []                                   # none required
UPPER_COLS_FBL3N = ['Document Type']                  # make upper case
LOWER_COLS_FBL3N = []
TITLE_COLS_FBL3N = []
# Numeric columns that actually exist after renaming
NUMERIC_COLS_FBL3N = [
    'Company Code', 'Document Number', 'Posting Key',
    'Amount (Local Currency)', 'G/L Account', 'Cost Center',
    'Profit Center', 'Fiscal Year', 'Fiscal Period',
    'Batch', 'Tax Code', 'Business Area'
]

# --------------------------------------------------------------------
# 6. IRA preprocessing
# --------------------------------------------------------------------
# Dates
for col in DATE_COLS_FBL3N:
    df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

# Upper‑case strings
if UPPER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, UPPER_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "upper"}
    )

# Numeric columns (clean only those present)
existing_numeric = [c for c in NUMERIC_COLS_FBL3N if c in df_fbl3n.columns]
if existing_numeric:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, existing_numeric)

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# -------------------------------------------------
# Rule 1 – flag rows where Document Date month‑year > Posting Date month‑year
# -------------------------------------------------
doc_period = df_fbl3n['Document Date'].dt.to_period('M')
post_period = df_fbl3n['Posting Date'].dt.to_period('M')
df_fbl3n['Date_Mismatch_Flag'] = np.where(doc_period > post_period, 1, np.nan)

# -------------------------------------------------
# Keep only flagged rows
# -------------------------------------------------
flagged_df = df_fbl3n[df_fbl3n['Date_Mismatch_Flag'] == 1].copy()
print(f"✓ Flagged {len(flagged_df):,} records where Document Date > Posting Date (month‑year)")

# -------------------------------------------------
# Select columns in the exact order required by the plan
# -------------------------------------------------
result_df = flagged_df[expected_output_cols]

# -------------------------------------------------
# Validation message
# -------------------------------------------------
if result_df.empty:
    print("⚠ Warning: No mismatches found – result dataframe is empty.")
else:
    print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# -------------------------------------------------
# Save output
# -------------------------------------------------
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")