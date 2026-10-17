"""
Categorical distribution and consistency audit module.
"""

from typing import List, Set
import pandas as pd
from src.config import AuditConfig

EXPECTED_PAYSIM_TYPES: Set[str] = {
    "CASH_IN",
    "CASH_OUT",
    "DEBIT",
    "PAYMENT",
    "TRANSFER",
}


def audit_categorical(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit categorical fields for observed categories, frequencies, whitespace/case anomalies,
    and unexpected values relative to documented specifications.
    Also audits entity prefixes for origin and destination accounts.
    """
    total_rows = len(df)
    records = []

    # 1. Audit configured categorical columns (e.g. 'type')
    for col in config.categorical_cols:
        if col in df.columns:
            series = df[col].dropna().astype(str)
            val_counts = series.value_counts()

            # Check for whitespace/case anomalies across unique values
            unique_raw = series.unique()
            stripped_set = set(v.strip() for v in unique_raw)
            upper_set = set(v.strip().upper() for v in unique_raw)
            has_whitespace_anomaly = len(stripped_set) < len(unique_raw)
            has_case_anomaly = len(upper_set) < len(stripped_set)

            for cat, cnt in val_counts.items():
                pct = round((cnt / total_rows * 100.0), 4) if total_rows > 0 else 0.0
                is_expected = cat in EXPECTED_PAYSIM_TYPES

                records.append(
                    {
                        "column": col,
                        "category": cat,
                        "count": int(cnt),
                        "percentage": pct,
                        "is_expected": is_expected,
                        "whitespace_anomaly": has_whitespace_anomaly,
                        "case_anomaly": has_case_anomaly,
                        "status": "CONFIRMED" if is_expected else "INVESTIGATE",
                    }
                )

    # 2. Audit entity ID prefixes (nameOrig and nameDest)
    for col in config.origin_cols + config.dest_cols:
        if col in df.columns:
            series = df[col].dropna().astype(str)
            prefixes = series.str[0].value_counts()
            for prefix, cnt in prefixes.items():
                pct = round((cnt / total_rows * 100.0), 4) if total_rows > 0 else 0.0
                records.append(
                    {
                        "column": f"{col}_PREFIX",
                        "category": f"Prefix '{prefix}'",
                        "count": int(cnt),
                        "percentage": pct,
                        "is_expected": prefix in ("C", "M"),
                        "whitespace_anomaly": False,
                        "case_anomaly": False,
                        "status": "OBSERVED",
                    }
                )

    return pd.DataFrame(records)
