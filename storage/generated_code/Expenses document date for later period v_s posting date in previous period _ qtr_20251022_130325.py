# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/fdb96e3a-bc25-488f-a0dd-e4e3e499fc26/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_ba4ecb5f-30a5-4c8c-bbd1-b7ae0ff1811c.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================
# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns
required_columns_fbl3n = ["Document Date", "Posting Date", "Document Number", "Amount in local currency", "Account Type"]
missing_columns = [col for col in required_columns_fbl3n if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# Column categories for FBL3N
DATE_COLS_FBLSN = ['Document Date', 'Posting Date']
SAME_COLS_FBLSN = ['Document Number']
UPPER_COLS_FBLSN = []
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ['Amount in local currency']

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
# Create a new column, Exception Flag, and set it to True for line items that meet the flagging criteria and False otherwise
df_fbl3n['Exception Flag'] = False

# Compare the Document Date and Posting Date based on the defined boundary
df_fbl3n.loc[((df_fbl3n['Document Date'].dt.year > df_fbl3n['Posting Date'].dt.year) | 
               ((df_fbl3n['Document Date'].dt.year == df_fbl3n['Posting Date'].dt.year) & 
                (df_fbl3n['Document Date'].dt.month > df_fbl3n['Posting Date'].dt.month))), 'Exception Flag'] = True

print(f"✓ Applied business logic: {len(df_fbl3n):,} rows")

# Validate output
if len(df_fbl3n) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(df_fbl3n):,} rows, {len(df_fbl3n.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
df_fbl3n.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")