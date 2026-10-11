import pandas as pd
import numpy as np

def winsorise(s: pd.Series, lo=0.005, hi=0.995) -> pd.Series:
    """Winsorise to cap extreme outliers without dropping them."""
    return s.clip(lower=s.quantile(lo), upper=s.quantile(hi))

def check_pii(df: pd.DataFrame, source_id: str):
    """
    Very basic check for obvious PII traces if security/pii.py isn't ready.
    Flags '@' symbol or runs of 10+ digits.
    """
    for col in df.select_dtypes(include=['object', 'string']):
        s = df[col].astype(str)
        if s.str.contains(r'@').any() or s.str.contains(r'\d{10,}').any():
            raise ValueError(f"[{source_id}] Potential PII detected in column {col}")

def drop_report(before: int, after: int, name: str, limit=0.05):
    """Report drop rate and fail if exceeding limit."""
    rate = 1 - (after / before)
    print(f"{name}: dropped {rate:.1%}")
    if rate > limit:
        raise RuntimeError(f"{name}: >{limit:.1%} dropped, investigate immediately")

def sanitize_df(df: pd.DataFrame, source_id: str) -> pd.DataFrame:
    """
    Apply generic sanitisation routines to a dataframe.
    """
    before = len(df)
    
    # 1. Strip whitespace from string columns
    for col in df.select_dtypes(include=['object', 'string']):
        df[col] = df[col].str.strip()
        
    # 2. Drop full duplicates
    df = df.drop_duplicates()
    
    # 3. Scan for basic PII before saving
    check_pii(df, source_id)
    
    after = len(df)
    drop_report(before, after, source_id)
    
    return df
