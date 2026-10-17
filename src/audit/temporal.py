"""
Temporal distribution and chronological ordering audit module.
"""

from typing import Dict, List
import numpy as np
import pandas as pd
from src.config import AuditConfig


def audit_temporal(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit temporal coverage, step progression, chronological monotonicity in the raw file,
    and cyclical (diurnal) distribution patterns.
    """
    temporal_col = (
        config.temporal_cols[0]
        if config.temporal_cols and config.temporal_cols[0] in df.columns
        else None
    )
    if not temporal_col:
        return pd.DataFrame()

    target_col = (
        config.target_cols[0]
        if config.target_cols and config.target_cols[0] in df.columns
        else None
    )

    series = df[temporal_col].dropna()
    total_rows = len(df)
    min_step = int(series.min())
    max_step = int(series.max())
    unique_steps = int(series.nunique())
    expected_steps = max_step - min_step + 1
    missing_steps = expected_steps - unique_steps

    # Chronological ordering check
    is_monotonic = bool(series.is_monotonic_increasing)
    # Check inversions / out-of-order rows if not monotonic
    out_of_order_count = 0
    if not is_monotonic:
        diffs = series.diff()
        out_of_order_count = int((diffs < 0).sum())

    # Observations per step
    counts_per_step = series.value_counts().sort_index()
    min_obs_step = int(counts_per_step.min())
    max_obs_step = int(counts_per_step.max())
    mean_obs_step = round(float(counts_per_step.mean()), 2)
    median_obs_step = float(counts_per_step.median())
    std_obs_step = round(float(counts_per_step.std()), 2)

    # Fraud per step if target exists
    if target_col:
        fraud_df = df[df[target_col] == 1]
        fraud_per_step = fraud_df[temporal_col].value_counts().sort_index()
        active_fraud_steps = int(fraud_per_step.nunique())
        mean_fraud_step = (
            round(float(fraud_per_step.mean()), 4) if len(fraud_per_step) > 0 else 0.0
        )
        max_fraud_step = int(fraud_per_step.max()) if len(fraud_per_step) > 0 else 0
    else:
        active_fraud_steps = 0
        mean_fraud_step = 0.0
        max_fraud_step = 0

    records = [
        {
            "metric": "TEMPORAL_RANGE",
            "value": f"[{min_step}, {max_step}]",
            "interpretation": f"Steps range from {min_step} to {max_step} ({expected_steps} total potential steps).",
            "status": "CONFIRMED",
        },
        {
            "metric": "UNIQUE_STEPS_OBSERVED",
            "value": unique_steps,
            "interpretation": (
                f"{unique_steps} discrete steps observed. Missing steps in range: {missing_steps}."
            ),
            "status": "CONFIRMED",
        },
        {
            "metric": "CHRONOLOGICAL_ORDERING_RAW_FILE",
            "value": "MONOTONIC_INCREASING" if is_monotonic else "NOT_SORTED",
            "interpretation": (
                "File is strictly sorted chronologically by step."
                if is_monotonic
                else f"File is NOT sorted chronologically ({out_of_order_count} negative step inversions)."
            ),
            "status": "CONFIRMED",
        },
        {
            "metric": "TRANSACTIONS_PER_STEP_STATS",
            "value": f"min={min_obs_step}, median={median_obs_step}, mean={mean_obs_step}, max={max_obs_step}, std={std_obs_step}",
            "interpretation": "Distribution of transaction volume across simulated time steps.",
            "status": "OBSERVED",
        },
        {
            "metric": "FRAUD_TEMPORAL_COVERAGE",
            "value": f"steps_with_fraud={active_fraud_steps}, mean_fraud_per_active_step={mean_fraud_step}, max_fraud_in_single_step={max_fraud_step}",
            "interpretation": "Fraud events distribution across simulated time steps.",
            "status": "OBSERVED",
        },
    ]

    # Diurnal / 24-hour cycle analysis: step % 24
    diurnal_series = series % 24
    diurnal_counts = diurnal_series.value_counts().sort_index()
    low_activity_hours = [
        int(hr)
        for hr, cnt in diurnal_counts.items()
        if cnt < (mean_obs_step * 24 * 0.1)
    ]
    records.append(
        {
            "metric": "DIURNAL_CYCLE_SIMULATION",
            "value": f"low_volume_hours={low_activity_hours}",
            "interpretation": (
                f"Transactions follow cyclical 24-hour simulation patterns with identifiable low-activity hours: {low_activity_hours}."
            ),
            "status": "OBSERVED",
        }
    )

    return pd.DataFrame(records)
