# ============================================================================
# PART 1: IMPORT LIBRARIES & FILE PATH VARIABLES
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import ira

fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/62339d41-2fd6-43ef-8c6b-fe13b91aaf11/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/Expenses_document_date_for_later_period_v/s_posting_date_in_previous_period_/_qtr/output_94ba8611-f972-4f03-8ffc-669d75514460.csv"

# ============================================================================
# PART 2: LOAD DATAFRAMES & IRA PREPROCESSING
# ============================================================================

# Required columns from Business Logic Plan
REQUIRED_COLS_FBLSN = [
    "Company Code", "Document Number", "Document Type", "G/L Account", "G/L Acct Long Text",
    "Cost Center", "Profit Center", "Business Area", "Document Date", "Posting Date",
    "Amount in local currency", "Local Currency", "Amount in doc. curr.", "Document currency",
    "Posting Key", "Offsett.account type", "Offsetting acct no.", "Text", "Document Header Text",
    "Reference", "Entry Date", "User Name", "Year/month"
]

# Column categories for FBL3N (for IRA preprocessing)
DATE_COLS_FBLSN = ["Document Date", "Posting Date", "Entry Date"]
SAME_COLS_FBLSN = [
    # Include textual identifier/context columns only to avoid altering numeric/code dtypes
    "G/L Acct Long Text", "Text", "Document Header Text", "Reference",
    "User Name", "Year/month", "Offsett.account type", "Offsetting acct no."
]
UPPER_COLS_FBLSN = ["Document Type", "Local Currency", "Document currency"]
LOWER_COLS_FBLSN = []
TITLE_COLS_FBLSN = []
NUMERIC_COLS_FBLSN = ["Amount in local currency", "Amount in doc. curr."]

# Load FBL3N data
df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
print(f"✓ Loaded {len(df_fbl3n):,} rows from FBL3N")

# Verify required columns exist
missing_columns = [col for col in REQUIRED_COLS_FBLSN if col not in df_fbl3n.columns]
if missing_columns:
    raise ValueError(f"Missing columns in FBL3N: {missing_columns}")

# IRA preprocessing for FBL3N
for col in DATE_COLS_FBLSN:
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

# Step 2: Derive period fields (month-year and months difference)
doc_year = df_fbl3n["Document Date"].dt.year
doc_month = df_fbl3n["Document Date"].dt.month
post_year = df_fbl3n["Posting Date"].dt.year
post_month = df_fbl3n["Posting Date"].dt.month

# Doc_MonthYear and Post_MonthYear as YYYY-MM (safe construction with masks)
doc_my = pd.Series(pd.NA, index=df_fbl3n.index, dtype=object)
post_my = pd.Series(pd.NA, index=df_fbl3n.index, dtype=object)

mask_doc_my = doc_year.notna() & doc_month.notna()
mask_post_my = post_year.notna() & post_month.notna()

doc_my.loc[mask_doc_my] = (
    doc_year.loc[mask_doc_my].astype(int).astype(str) + "-" + doc_month.loc[mask_doc_my].astype(int).astype(str).str.zfill(2)
)
post_my.loc[mask_post_my] = (
    post_year.loc[mask_post_my].astype(int).astype(str) + "-" + post_month.loc[mask_post_my].astype(int).astype(str).str.zfill(2)
)

df_fbl3n["Doc_MonthYear"] = doc_my
df_fbl3n["Post_MonthYear"] = post_my

# Months_Diff = (doc_year - post_year) * 12 + (doc_month - post_month), nullable Int64
both_months_available = doc_year.notna() & post_year.notna() & doc_month.notna() & post_month.notna()
months_diff = ((doc_year - post_year) * 12 + (doc_month - post_month)).where(both_months_available, np.nan)
df_fbl3n["Months_Diff"] = pd.Series(months_diff).astype("Int64")

# Cross_Year indicator: Yes if year(Document Date) > year(Posting Date)
cross_year_bool = doc_year.gt(post_year).fillna(False)
df_fbl3n["Cross_Year"] = cross_year_bool.map({True: "Yes", False: "No"})

print("✓ Derived month-year fields and Cross_Year indicator")

# Step 3: Derive quarter fields and indicators
doc_quarter = df_fbl3n["Document Date"].dt.quarter
post_quarter = df_fbl3n["Posting Date"].dt.quarter

# Quarter labels like YYYY-Qn
doc_q_label = pd.Series(np.nan, index=df_fbl3n.index, dtype=object)
post_q_label = pd.Series(np.nan, index=df_fbl3n.index, dtype=object)
mask_doc_q = doc_year.notna() & doc_quarter.notna()
mask_post_q = post_year.notna() & post_quarter.notna()

doc_q_label.loc[mask_doc_q] = (
    doc_year.loc[mask_doc_q].astype(int).astype(str) + "-Q" + doc_quarter.loc[mask_doc_q].astype(int).astype(str)
)
post_q_label.loc[mask_post_q] = (
    post_year.loc[mask_post_q].astype(int).astype(str) + "-Q" + post_quarter.loc[mask_post_q].astype(int).astype(str)
)

df_fbl3n["Doc_Quarter"] = doc_q_label
df_fbl3n["Post_Quarter"] = post_q_label

# Quarter indices: (Year * 4 + Quarter), nullable Int64
_doc_q_index = pd.Series(pd.NA, index=df_fbl3n.index, dtype="Int64")
_post_q_index = pd.Series(pd.NA, index=df_fbl3n.index, dtype="Int64")

_doc_mask = doc_year.notna() & doc_quarter.notna()
_post_mask = post_year.notna() & post_quarter.notna()

_doc_q_index.loc[_doc_mask] = (doc_year.loc[_doc_mask].astype("Int64") * 4 + doc_quarter.loc[_doc_mask].astype("Int64"))
_post_q_index.loc[_post_mask] = (post_year.loc[_post_mask].astype("Int64") * 4 + post_quarter.loc[_post_mask].astype("Int64"))

# Quarter_Diff and Cross_Quarter
quarter_diff = (_doc_q_index - _post_q_index).astype("Int64")
df_fbl3n["Quarter_Diff"] = quarter_diff
cross_quarter_bool = quarter_diff.gt(0).fillna(False)
df_fbl3n["Cross_Quarter"] = cross_quarter_bool.map({True: "Yes", False: "No"})

print("✓ Derived quarter fields and Cross_Quarter indicator")

# Step 4: Exception flagging (Months_Diff > 0)
exception_mask = df_fbl3n["Months_Diff"].gt(0).fillna(False)
result_df = df_fbl3n.loc[exception_mask].copy()
print(f"✓ Applied exception filter (Months_Diff > 0): {len(result_df):,} rows flagged")

# Step 5: Prepare final output
output_columns = [
    "Company Code", "Document Number", "Document Type", "G/L Account", "G/L Acct Long Text",
    "Cost Center", "Profit Center", "Business Area", "Document Date", "Posting Date",
    "Amount in local currency", "Local Currency", "Amount in doc. curr.", "Document currency",
    "Posting Key", "Offsett.account type", "Offsetting acct no.", "Text", "Document Header Text",
    "Reference", "Entry Date", "User Name", "Year/month",
    "Doc_MonthYear", "Post_MonthYear", "Months_Diff", "Cross_Year",
    "Doc_Quarter", "Post_Quarter", "Quarter_Diff", "Cross_Quarter"
]

missing_out_cols = [c for c in output_columns if c not in result_df.columns]
if missing_out_cols:
    raise ValueError(f"Missing expected output columns: {missing_out_cols}")

result_df = result_df[output_columns]

if len(result_df) == 0:
    print("⚠ Warning: Result dataframe is empty!")

print(f"✓ Final result: {len(result_df):,} rows, {len(result_df.columns)} columns")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Save output
result_df.to_csv(output_file_path, index=False)
print(f"✓ SUCCESS: Saved results to {output_file_path}")