"""
Cardinality and entity frequency audit module.
"""

from typing import List
import numpy as np
import pandas as pd
from src.config import AuditConfig


def audit_cardinality(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Compute cardinality and frequency distribution statistics for entity and categorical columns.
    Calculates uniqueness ratio, min, median, mean, p95, p99, and max entity frequencies.
    """
    target_cols = (
        config.origin_cols
        + config.dest_cols
        + config.categorical_cols
        + config.target_cols
        + config.flag_cols
    )
    # Deduplicate while preserving order
    cols_to_check = [c for c in dict.fromkeys(target_cols) if c in df.columns]

    total_rows = len(df)
    records = []

    for col in cols_to_check:
        series = df[col].dropna()
        unique_cnt = int(series.nunique())
        uniqueness_ratio = (
            round(unique_cnt / total_rows, 6) if total_rows > 0 else 0.0
        )

        val_counts = series.value_counts()
        if len(val_counts) > 0:
            min_f = int(val_counts.min())
            median_f = float(val_counts.median())
            mean_f = round(float(val_counts.mean()), 4)
            p95_f = round(float(np.percentile(val_counts, 95)), 4)
            p99_f = round(float(np.percentile(val_counts, 99)), 4)
            max_f = int(val_counts.max())
        else:
            min_f = median_f = mean_f = p95_f = p99_f = max_f = 0

        records.append(
            {
                "column": col,
                "total_count": total_rows,
                "unique_count": unique_cnt,
                "uniqueness_ratio": uniqueness_ratio,
                "min_freq": min_f,
                "median_freq": median_f,
                "mean_freq": mean_f,
                "p95_freq": p95_f,
                "p99_freq": p99_f,
                "max_freq": max_f,
                "status": "CONFIRMED",
            }
        )

    return pd.DataFrame(records)
