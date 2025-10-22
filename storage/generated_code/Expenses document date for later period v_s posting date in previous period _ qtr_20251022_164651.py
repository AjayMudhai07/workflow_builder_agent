# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/80b634d3-7cac-4433-92d6-a1c2f6bc4d53/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_87b8dd1f-15ff-45b8-86ef-090240e97b21.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Column categories for FBL3N (after renaming to the Business Logic names)
DATE_COLS_FBL3N   = ['DocumentDate', 'PostingDate']
SAME_COLS_FBL3N   = ['DocumentNumber', 'CompanyCode', 'PostingKey']
UPPER_COLS_FBL3N  = ['DocumentType']
LOWER_COLS_FBL3N  = []
TITLE_COLS_FBL3N  = []
NUMERIC_COLS_FBL3N = ['AmountLC']

# Load raw data
df_fbl3n_raw = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n_raw):,} rows from FBL3N")

# ----------------------------------------------------------------------
# Rename columns to match the Business Logic Plan
# ----------------------------------------------------------------------
rename_map = {
    'Document Number': 'DocumentNumber',
    'Company Code': 'CompanyCode',
    'Document Date': 'DocumentDate',
    'Posting Date': 'PostingDate',
    'Document Type': 'DocumentType',
    'Posting Key': 'PostingKey',
    'Amount in local currency': 'AmountLC',
    'Cost Center': 'CostCenter',
    'Profit Center': 'ProfitCenter',
    'G/L Account': 'GLAccount',
    'G/L Acct Long Text': 'GLAccountLongText',
    'Text': 'Text',
    'Document Header Text': 'DocumentHeaderText'
}
df_fbl3n = df_fbl3n_raw.rename(columns=rename_map)

# Verify required columns
required_columns_fbl3n = (
    DATE_COLS_FBL3N + SAME_COLS_FBL3N + UPPER_COLS_FBL3N +
    TITLE_COLS_FBL3N + NUMERIC_COLS_FBL3N +
    ['CostCenter', 'ProfitCenter', 'GLAccount', 'GLAccountLongText',
     'DocumentHeaderText']
)
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing – dates
for col in DATE_COLS_FBL3N:
    df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

# IRA preprocessing – SAME case strings
if SAME_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, SAME_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "same"}
    )

# IRA preprocessing – UPPER case strings
if UPPER_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, UPPER_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "upper"}
    )

# IRA preprocessing – TITLE case strings (none needed here)
if TITLE_COLS_FBL3N:
    df_fbl3n = ira.clean_strings_batch(
        df_fbl3n, TITLE_COLS_FBL3N,
        rules={"remove_excel_artifacts": True,
               "normalize_whitespace": True,
               "case_mode": "title"}
    )

# IRA preprocessing – numeric columns
if NUMERIC_COLS_FBL3N:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBL3N)

print("✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# --- Rule 1 & 3: Compute month‑year difference (ignore day) ---
doc_ym = df_fbl3n['DocumentDate'].dt.year * 12 + df_fbl3n['DocumentDate'].dt.month
post_ym = df_fbl3n['PostingDate'].dt.year * 12 + df_fbl3n['PostingDate'].dt.month

df_fbl3n['MonthYearDifference'] = doc_ym - post_ym

# --- Rule 5: Flag if DocumentDate month‑year is later than PostingDate month‑year ---
df_fbl3n['Flag'] = np.where(df_fbl3n['MonthYearDifference'] > 0, 'Yes', 'No')

print(f"✓ Applied month‑year comparison and flagging: {df_fbl3n['Flag'].value_counts().to_dict()}")

# --- Select and order output columns ---
output_columns = [
    'DocumentNumber', 'CompanyCode', 'DocumentDate', 'PostingDate',
    'MonthYearDifference', 'Flag', 'DocumentType', 'PostingKey',
    'AmountLC', 'CostCenter', 'ProfitCenter', 'GLAccount',
    'GLAccountLongText', 'Text', 'DocumentHeaderText'
]

result_df = df_fbl3n[output_columns].copy()
print(f"✓ Prepared final result dataframe with {len(result_df):,} rows and {len(result_df.columns)} columns")

# Validate non‑empty result
if result_df.empty:
    print("⚠ Warning: Result dataframe is empty!")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save to CSV
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")