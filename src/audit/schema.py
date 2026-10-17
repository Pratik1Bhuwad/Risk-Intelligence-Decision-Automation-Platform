"""
Schema audit module.
"""

from typing import List
import pandas as pd
from src.config import AuditConfig


def infer_semantic_category(col: str, config: AuditConfig) -> str:
    """Infer semantic category using configuration-driven role mappings."""
    if col in config.temporal_cols:
        return "TEMPORAL_STEP"
    if col in config.categorical_cols:
        return "CATEGORICAL_TRANSACTION_TYPE"
    if col in config.origin_cols:
        return "ENTITY_ID_ORIGIN"
    if col in config.dest_cols:
        return "ENTITY_ID_DEST"
    if col in config.target_cols:
        return "TARGET_BINARY"
    if col in config.flag_cols:
        return "FLAG_BINARY"
    if col in config.numerical_cols:
        if "balance" in col.lower():
            return "NUMERICAL_BALANCE"
        if "amount" in col.lower():
            return "NUMERICAL_AMOUNT"
        return "NUMERICAL"
    return "UNKNOWN"


def audit_schema(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Perform schema audit across all columns.
    Returns DataFrame matching schema.csv specification.
    """
    records = []
    total_rows = len(df)

    for col in df.columns:
        series = df[col]
        non_null = int(series.notna().sum())
        null_cnt = int(series.isna().sum())
        null_pct = (null_cnt / total_rows * 100.0) if total_rows > 0 else 0.0

        unique_cnt = int(series.nunique(dropna=False))

        # Representative values (first 3-5 distinct non-null values)
        sample_vals = series.dropna().unique()[:4]
        rep_vals = "; ".join([str(v) for v in sample_vals])

        # Min and Max where applicable
        min_val = None
        max_val = None
        if pd.api.types.is_numeric_dtype(series):
            valid_nums = series.dropna()
            if not valid_nums.empty:
                min_val = float(valid_nums.min())
                max_val = float(valid_nums.max())
        else:
            try:
                valid_vals = series.dropna()
                if not valid_vals.empty:
                    min_val = str(valid_vals.min())
                    max_val = str(valid_vals.max())
            except Exception:
                min_val = "N/A"
                max_val = "N/A"

        records.append(
            {
                "column_name": col,
                "pandas_dtype": str(series.dtype),
                "inferred_semantic_category": infer_semantic_category(
                    col, config
                ),
                "non_null_count": non_null,
                "null_count": null_cnt,
                "null_percentage": round(null_pct, 4),
                "unique_count": unique_cnt,
                "representative_values": rep_vals,
                "min_value": min_val,
                "max_value": max_val,
                "status": "CONFIRMED",
            }
        )

    return pd.DataFrame(records)
