# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

# Define file path variables
fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/fdb96e3a-bc25-488f-a0dd-e4e3e499fc26/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_ba4ecb5f-30a5-4c8c-bbd1-b7ae0ff1811c.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================
# Define column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date']
SAME_COLS_FBLSN = ['Document Number']
UPPER_COLS_FBLSN = ['Account Type']
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency']

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = DATE_COLS_FBLSN + SAME_COLS_FBLSN + UPPER_COLS_FBLSN + TITLE_COLS_FBLSN + NUMERIC_COLS_FBLSN
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
    if col in df_fbl3n.columns:
        df_fbl3n[col] = ira.convert_date_column(df_fbl3n[col])

if SAME_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, SAME_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "same"})

if UPPER_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, UPPER_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "upper"})

if TITLE_COLS_FBLSN:
    df_fbl3n = ira.clean_strings_batch(df_fbl3n, TITLE_COLS_FBLSN, rules={
        "remove_excel_artifacts": True, "normalize_whitespace": True, "case_mode": "title"})

if NUMERIC_COLS_FBLSN:
    df_fbl3n = ira.clean_numeric_batch(df_fbl3n, NUMERIC_COLS_FBLSN)

print(f"✓ IRA preprocessing complete for FBL3N")

# ============================================================================
# PART 3: BUSINESS LOGIC
# ============================================================================
# Flag line items where the Document Date year is greater than the Posting Date year,
# or if the years are equal and the Document Date month is greater than the Posting Date month
result_df = df_fbl3n[
    ((df_fbl3n['Document Date'].dt.year > df_fbl3n['Posting Date'].dt.year) |
     ((df_fbl3n['Document Date'].dt.year == df_fbl3n['Posting Date'].dt.year) &
      (df_fbl3n['Document Date'].dt.month > df_fbl3n['Posting Date'].dt.month)))
].copy()

print(f"✓ Flagged {len(result_df):,} records with Document Date in later period")

# Validate output
if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

# Select required columns
required_columns = ['Document Number', 'Document Date', 'Posting Date', 'Amount in local currency', 'Account Type']
result_df = result_df[required_columns]

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")