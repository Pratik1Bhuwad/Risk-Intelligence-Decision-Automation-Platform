"""
Numerical distribution and data-quality audit module.
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from src.config import AuditConfig


def audit_numerical(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit numerical fields for distribution parameters, quantiles, and data-quality checks.
    Uses rigorous terminology (data-quality flags, potential outliers, distribution checks)
    rather than modeling-stage anomaly detection.
    """
    numerical_cols = [c for c in config.numerical_cols if c in df.columns]
    # Also include temporal step if numeric
    for col in config.temporal_cols:
        if col in df.columns and col not in numerical_cols:
            numerical_cols.append(col)

    records = []
    quantiles_to_calc = config.quantiles

    for col in numerical_cols:
        series = df[col]
        non_null_series = series.dropna()

        cnt = int(len(non_null_series))
        missing_cnt = int(series.isna().sum())

        if cnt > 0:
            min_val = float(non_null_series.min())
            max_val = float(non_null_series.max())
            mean_val = round(float(non_null_series.mean()), 4)
            median_val = float(non_null_series.median())
            std_val = round(float(non_null_series.std()), 4)

            # Quantiles
            q_values = np.percentile(
                non_null_series, [q * 100 for q in quantiles_to_calc]
            )
            q_map = {
                f"p{int(q*100):02d}": round(float(val), 4)
                for q, val in zip(quantiles_to_calc, q_values)
            }

            # Invalid / suspicious counts
            neg_cnt = int((non_null_series < 0).sum())
            zero_cnt = int((non_null_series == 0).sum())
            inf_cnt = int(np.isinf(non_null_series).sum())

            # Data-quality checks / flags
            dq_flags = []
            if neg_cnt > 0:
                dq_flags.append(f"NEGATIVE_VALUES_DETECTED({neg_cnt})")
            if inf_cnt > 0:
                dq_flags.append(f"INFINITE_VALUES_DETECTED({inf_cnt})")
            if zero_cnt > 0:
                zero_pct = round(zero_cnt / cnt * 100.0, 2)
                if zero_pct > 50.0:
                    dq_flags.append(f"HIGH_ZERO_CONCENTRATION({zero_pct}%)")

            flag_summary = "; ".join(dq_flags) if dq_flags else "NORMAL"
        else:
            min_val = max_val = mean_val = median_val = std_val = 0.0
            q_map = {f"p{int(q*100):02d}": 0.0 for q in quantiles_to_calc}
            neg_cnt = zero_cnt = inf_cnt = 0
            flag_summary = "ALL_MISSING"

        row_dict = {
            "column": col,
            "count": cnt,
            "missing_count": missing_cnt,
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "median": median_val,
            "std": std_val,
            **q_map,
            "negative_count": neg_cnt,
            "zero_count": zero_cnt,
            "infinite_count": inf_cnt,
            "data_quality_flags": flag_summary,
            "status": "OBSERVED",
        }
        records.append(row_dict)

    return pd.DataFrame(records)
