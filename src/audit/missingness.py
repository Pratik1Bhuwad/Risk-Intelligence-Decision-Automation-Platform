"""
Missing-value audit module.
"""

from typing import Dict, List, Tuple
import pandas as pd
from src.config import AuditConfig


def audit_missingness(
    df: pd.DataFrame, config: AuditConfig
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform comprehensive missing-value audit.
    Measures NaN, blank strings, whitespace-only, textual markers, and zero values.
    Also evaluates missingness stratified by target and transaction type.
    """
    records = []
    total_rows = len(df)
    text_markers_set = set(m.lower() for m in config.missing_markers if m != "")

    for col in df.columns:
        series = df[col]

        # 1. NaN count
        nan_cnt = int(series.isna().sum())

        # 2. String-specific checks (blank, whitespace, textual markers)
        blank_cnt = 0
        whitespace_cnt = 0
        text_marker_cnt = 0

        if (
            pd.api.types.is_string_dtype(series)
            or pd.api.types.is_object_dtype(series)
        ):
            non_na_str = series.dropna().astype(str)
            blank_cnt = int((non_na_str == "").sum())
            whitespace_cnt = int(
                ((non_na_str.str.strip() == "") & (non_na_str != "")).sum()
            )
            lowered = non_na_str.str.lower()
            text_marker_cnt = int(lowered.isin(text_markers_set).sum())

        # 3. Zero count (separate check)
        zero_cnt = 0
        if pd.api.types.is_numeric_dtype(series):
            zero_cnt = int((series.dropna() == 0).sum())

        total_missing = nan_cnt + blank_cnt + whitespace_cnt + text_marker_cnt
        missing_pct = (
            (total_missing / total_rows * 100.0) if total_rows > 0 else 0.0
        )
        zero_pct = (zero_cnt / total_rows * 100.0) if total_rows > 0 else 0.0

        records.append(
            {
                "column": col,
                "nan_count": nan_cnt,
                "blank_count": blank_cnt,
                "whitespace_count": whitespace_cnt,
                "text_marker_count": text_marker_cnt,
                "zero_count": zero_cnt,
                "total_missing_count": total_missing,
                "missing_pct": round(missing_pct, 4),
                "zero_pct": round(zero_pct, 4),
                "status": "CONFIRMED",
            }
        )

    field_missing_df = pd.DataFrame(records)

    # Cross-comparison with target and transaction type
    stratified_records = []
    target_col = (
        config.target_cols[0]
        if config.target_cols and config.target_cols[0] in df.columns
        else None
    )
    type_col = (
        config.categorical_cols[0]
        if config.categorical_cols and config.categorical_cols[0] in df.columns
        else None
    )

    if target_col:
        for val, group in df.groupby(target_col, observed=True):
            stratified_records.append(
                {
                    "stratum_type": "TARGET",
                    "stratum_value": str(val),
                    "row_count": len(group),
                    "total_missing_cells": int(group.isna().sum().sum()),
                }
            )

    if type_col:
        for val, group in df.groupby(type_col, observed=True):
            stratified_records.append(
                {
                    "stratum_type": "TRANSACTION_TYPE",
                    "stratum_value": str(val),
                    "row_count": len(group),
                    "total_missing_cells": int(group.isna().sum().sum()),
                }
            )

    stratified_df = (
        pd.DataFrame(stratified_records)
        if stratified_records
        else pd.DataFrame(
            columns=[
                "stratum_type",
                "stratum_value",
                "row_count",
                "total_missing_cells",
            ]
        )
    )

    return field_missing_df, stratified_df
