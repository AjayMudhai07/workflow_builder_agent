# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/b9bedc8a-db2e-4b10-b59e-e25be9b3fd7a/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_119c65ac-c477-445e-b62a-fabec098ae93.csv"


# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N
DATE_COLS_FBL3N = ['Posting Date', 'Document Date']
SAME_COLS_FBL3N = ['Document Number', 'Company Code', 'G/L Account']
UPPER_COLS_FBL3N = []
LOWER_COLS_FBL3N = []
TITLE_COLS_FBL3N = []
NUMERIC_COLS_FBL3N = []

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBL3N
    + SAME_COLS_FBL3N
    + UPPER_COLS_FBL3N
    + LOWER_COLS_FBL3N
    + TITLE_COLS_FBL3N
    + NUMERIC_COLS_FBL3N
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

# Create month‑year periods for comparison
df_fbl3n['Posting_Month_Year'] = df_fbl3n['Posting Date'].dt.to_period('M')
df_fbl3n['Document_Month_Year'] = df_fbl3n['Document Date'].dt.to_period('M')

# Flag records where Document month‑year is later than Posting month‑year
flag_condition = df_fbl3n['Document_Month_Year'] > df_fbl3n['Posting_Month_Year']
flagged_df = df_fbl3n[flag_condition].copy()
print(f"✓ Flagged {len(flagged_df):,} records where Document Date > Posting Date (month‑year)")

# Add derived column formatted as YYYY‑MM
flagged_df['Document_Date_Month_Year'] = flagged_df['Document Date'].dt.strftime('%Y-%m')

# Select final output columns
output_columns = [
    'Document Number',
    'Company Code',
    'G/L Account',
    'Posting Date',
    'Document Date',
    'Document_Date_Month_Year',
]
result_df = flagged_df[output_columns].reset_index(drop=True)

# Validate output
if result_df.empty:
    print("⚠ Warning: No records met the flagging criteria; output will be empty.")
else:
    print(f"✓ Final result prepared: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save to CSV
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")