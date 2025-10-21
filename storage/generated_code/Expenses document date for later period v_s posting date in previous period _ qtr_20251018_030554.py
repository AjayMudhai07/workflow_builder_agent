# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = csv_files[0]
output_file_path = output_path

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Dynamically categorize columns present in the file
all_cols = set(df_fbl3n.columns)

# Candidate columns by category (intersect with actual columns)
DATE_CANDIDATES_FBLSN = [
    'Posting_Date', 'Document_Date', 'Clearing_Date', 'Baseline_Payment_Date',
    'Due_Date', 'Net_Due_Date', 'Value_Date'
]
SAME_CANDIDATES_FBLSN = [
    'Document_No', 'Vendor_No', 'Customer_No', 'GL_Account', 'Reference',
    'Invoice_No', 'Company_Code', 'Fiscal_Year', 'Document_Type', 'Assignment',
    'Item', 'Profit_Center', 'Cost_Center'
]
UPPER_CANDIDATES_FBLSN = [
    'Status', 'Currency', 'Posting_Key', 'DC'
]
LOWER_CANDIDATES_FBLSN = [
    'Email', 'Vendor_Email', 'Website', 'URL'
]
TITLE_CANDIDATES_FBLSN = [
    'Vendor_Name', 'Customer_Name', 'Name'
]
NUMERIC_CANDIDATES_FBLSN = [
    'Amount', 'Open_Amount', 'Tax_Amount', 'Quantity', 'Debit', 'Credit',
    'Balance', 'Clearing_Amount', 'Discount', 'Payment_Terms_Days'
]

# Final category lists based on actual columns
DATE_COLS_FBLSN = [c for c in DATE_CANDIDATES_FBLSN if c in all_cols]
SAME_COLS_FBLSN = [c for c in SAME_CANDIDATES_FBLSN if c in all_cols]
UPPER_COLS_FBLSN = [c for c in UPPER_CANDIDATES_FBLSN if c in all_cols]
LOWER_COLS_FBLSN = [c for c in LOWER_CANDIDATES_FBLSN if c in all_cols]
TITLE_COLS_FBLSN = [c for c in TITLE_CANDIDATES_FBLSN if c in all_cols]
NUMERIC_COLS_FBLSN = [c for c in NUMERIC_CANDIDATES_FBLSN if c in all_cols]

# Verify required columns (for preprocessing categories we will apply)
required_columns_fbl3n = (
    DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN +
    LOWER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
)
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, SAME_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"
    })

if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, UPPER_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"
    })

if LOWER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, LOWER_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "lower"
    })

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"
    })

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================

# Preserve ALL original rows, including those with Crosses_Year = True
result_df = df_fbl3n.copy()
print(f"✓ Preserved all rows without filtering: {len(result_df):,} rows")

# Optional: Report counts for Crosses_Year if present to confirm inclusion
if 'Crosses_Year' in result_df.columns:
    counts = result_df['Crosses_Year'].value_counts(dropna=False)
    true_count = int(counts.get(True, 0))
    false_count = int(counts.get(False, 0))
    na_count = int(result_df['Crosses_Year'].isna().sum())
    print(f"✓ Crosses_Year breakdown -> True: {true_count:,}, False: {false_count:,}, NaN: {na_count:,}")

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
out_dir = os.path.dirname(output_file_path)
if out_dir:
    os.makedirs(out_dir, exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")