# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/7df9d8bb-86e3-413e-9028-520e56ce6a43/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_9df3a4d3-5961-422b-abe3-dc1445c0881f.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBL3N = ['Document Date', 'Posting Date']
SAME_COLS_FBL3N = ['Document Number']
UPPER_COLS_FBL3N = ['Document Type']
LOWER_COLS_FBL3N = []
TITLE_COLS_FBL3N = []
NUMERIC_COLS_FBL3N = [
    'Amount in local currency',
    'Company Code',
    'Posting Key',
    'Supplier'
]

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBL3N
    + SAME_COLS_FBL3N
    + UPPER_COLS_FBL3N
    + TITLE_COLS_FBL3N
    + NUMERIC_COLS_FBL3N
    + ['Company Code', 'Text', 'Cost Center', 'Profit Center', 'Supplier']
)
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
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

# Calculate date difference (Document Date - Posting Date) in days
df_fbl3n['Date Difference (days)'] = (
    df_fbl3n['Document Date'] - df_fbl3n['Posting Date']
).dt.days

# Flag where Document Date is later than Posting Date
df_fbl3n['Flag'] = df_fbl3n['Date Difference (days)'] > 0

# Derive month‑year strings
df_fbl3n['Document Month-Year'] = df_fbl3n['Document Date'].dt.to_period('M').astype(str)
df_fbl3n['Posting Month-Year'] = df_fbl3n['Posting Date'].dt.to_period('M').astype(str)

# Select and order output columns
output_columns = [
    'Company Code',
    'Document Number',
    'Document Date',
    'Posting Date',
    'Date Difference (days)',
    'Flag',
    'Document Type',
    'Amount in local currency',
    'Text',
    'Cost Center',
    'Profit Center',
    'Supplier',
    'Document Month-Year',
    'Posting Month-Year',
]

result_df = df_fbl3n[output_columns].copy()
print(f"✓ Result dataframe prepared with {len(result_df):,} rows and {len(result_df.columns)} columns")

# Validate non‑empty result
if result_df.empty:
    print("⚠ Warning: Result dataframe is empty!")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save to CSV
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")