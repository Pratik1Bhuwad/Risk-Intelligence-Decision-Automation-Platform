"""
Customer and account entity history audit module.
"""

from typing import List
import numpy as np
import pandas as pd
from src.config import AuditConfig


def audit_entity(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit customer/account history depth, repeat transaction rates, active duration,
    and fraud concentration for originating and destination entities.
    """
    records = []
    total_rows = len(df)
    target_col = (
        config.target_cols[0]
        if config.target_cols and config.target_cols[0] in df.columns
        else None
    )
    temporal_col = (
        config.temporal_cols[0]
        if config.temporal_cols and config.temporal_cols[0] in df.columns
        else None
    )

    # 1. Originating Accounts (nameOrig)
    for orig_col in config.origin_cols:
        if orig_col in df.columns:
            orig_series = df[orig_col].dropna()
            total_orig_records = len(orig_series)
            unique_orig = int(orig_series.nunique())

            # Frequency distribution
            counts = orig_series.value_counts()
            single_tx_cnt = int((counts == 1).sum())
            single_tx_pct = (
                round(single_tx_cnt / unique_orig * 100.0, 4)
                if unique_orig > 0
                else 0.0
            )
            multi_tx_cnt = unique_orig - single_tx_cnt
            multi_tx_pct = (
                round(multi_tx_cnt / unique_orig * 100.0, 4)
                if unique_orig > 0
                else 0.0
            )

            min_tx = int(counts.min())
            median_tx = float(counts.median())
            mean_tx = round(float(counts.mean()), 4)
            p95_tx = round(float(np.percentile(counts, 95)), 4)
            p99_tx = round(float(np.percentile(counts, 99)), 4)
            max_tx = int(counts.max())

            records.append(
                {
                    "entity_role": "ORIGINATING_ACCOUNT",
                    "column": orig_col,
                    "metric": "TOTAL_UNIQUE_ENTITIES",
                    "value": unique_orig,
                    "percentage": round(unique_orig / total_orig_records * 100.0, 4),
                    "interpretation": f"{unique_orig} unique originating accounts observed.",
                    "status": "CONFIRMED",
                }
            )
            records.append(
                {
                    "entity_role": "ORIGINATING_ACCOUNT",
                    "column": orig_col,
                    "metric": "SINGLE_TRANSACTION_ENTITIES",
                    "value": single_tx_cnt,
                    "percentage": single_tx_pct,
                    "interpretation": (
                        f"{single_tx_pct}% of originating accounts appear exactly once. "
                        "Critical architectural constraint: Zero historical customer profile for single-tx originators."
                    ),
                    "status": "CONFIRMED",
                }
            )
            records.append(
                {
                    "entity_role": "ORIGINATING_ACCOUNT",
                    "column": orig_col,
                    "metric": "REPEAT_TRANSACTION_ENTITIES",
                    "value": multi_tx_cnt,
                    "percentage": multi_tx_pct,
                    "interpretation": (
                        f"{multi_tx_cnt} originating accounts ({multi_tx_pct}%) have 2 or more transactions."
                    ),
                    "status": "CONFIRMED",
                }
            )
            records.append(
                {
                    "entity_role": "ORIGINATING_ACCOUNT",
                    "column": orig_col,
                    "metric": "HISTORY_DEPTH_PERCENTILES",
                    "value": f"min={min_tx}, median={median_tx}, mean={mean_tx}, p95={p95_tx}, p99={p99_tx}, max={max_tx}",
                    "percentage": 0.0,
                    "interpretation": "Percentile distribution of transaction counts per originating account.",
                    "status": "OBSERVED",
                }
            )

            # Fraud concentration across originators
            if target_col:
                fraud_origs = df[df[target_col] == 1][orig_col].unique()
                fraud_orig_cnt = len(fraud_origs)
                fraud_orig_pct = (
                    round(fraud_orig_cnt / unique_orig * 100.0, 5)
                    if unique_orig > 0
                    else 0.0
                )
                records.append(
                    {
                        "entity_role": "ORIGINATING_ACCOUNT",
                        "column": orig_col,
                        "metric": "FRAUD_INVOLVED_ENTITIES",
                        "value": fraud_orig_cnt,
                        "percentage": fraud_orig_pct,
                        "interpretation": f"{fraud_orig_cnt} originating entities ({fraud_orig_pct}%) engaged in fraud.",
                        "status": "OBSERVED",
                    }
                )

    # 2. Destination Accounts (nameDest)
    for dest_col in config.dest_cols:
        if dest_col in df.columns:
            dest_series = df[dest_col].dropna()
            total_dest_records = len(dest_series)
            unique_dest = int(dest_series.nunique())

            counts = dest_series.value_counts()
            single_tx_cnt = int((counts == 1).sum())
            single_tx_pct = (
                round(single_tx_cnt / unique_dest * 100.0, 4)
                if unique_dest > 0
                else 0.0
            )
            multi_tx_cnt = unique_dest - single_tx_cnt
            multi_tx_pct = (
                round(multi_tx_cnt / unique_dest * 100.0, 4)
                if unique_dest > 0
                else 0.0
            )

            min_tx = int(counts.min())
            median_tx = float(counts.median())
            mean_tx = round(float(counts.mean()), 4)
            p95_tx = round(float(np.percentile(counts, 95)), 4)
            p99_tx = round(float(np.percentile(counts, 99)), 4)
            max_tx = int(counts.max())

            # Destination entity type: Customer (C*) vs Merchant (M*)
            m_cnt = int(dest_series.str.startswith("M").sum())
            c_cnt = int(dest_series.str.startswith("C").sum())
            m_pct = (
                round(m_cnt / total_dest_records * 100.0, 4)
                if total_dest_records > 0
                else 0.0
            )
            c_pct = (
                round(c_cnt / total_dest_records * 100.0, 4)
                if total_dest_records > 0
                else 0.0
            )

            records.append(
                {
                    "entity_role": "DESTINATION_ACCOUNT",
                    "column": dest_col,
                    "metric": "TOTAL_UNIQUE_ENTITIES",
                    "value": unique_dest,
                    "percentage": round(unique_dest / total_dest_records * 100.0, 4),
                    "interpretation": f"{unique_dest} unique destination accounts observed.",
                    "status": "CONFIRMED",
                }
            )
            records.append(
                {
                    "entity_role": "DESTINATION_ACCOUNT",
                    "column": dest_col,
                    "metric": "REPEAT_DESTINATION_RATE",
                    "value": multi_tx_cnt,
                    "percentage": multi_tx_pct,
                    "interpretation": f"{multi_tx_cnt} destination accounts ({multi_tx_pct}%) receive multiple transactions.",
                    "status": "CONFIRMED",
                }
            )
            records.append(
                {
                    "entity_role": "DESTINATION_ACCOUNT",
                    "column": dest_col,
                    "metric": "DESTINATION_TYPE_SPLIT",
                    "value": f"Merchants(M)={m_cnt}, Customers(C)={c_cnt}",
                    "percentage": m_pct,
                    "interpretation": f"Destination split: {m_pct}% Merchants (M*), {c_pct}% Customers (C*).",
                    "status": "CONFIRMED",
                }
            )
            records.append(
                {
                    "entity_role": "DESTINATION_ACCOUNT",
                    "column": dest_col,
                    "metric": "HISTORY_DEPTH_PERCENTILES",
                    "value": f"min={min_tx}, median={median_tx}, mean={mean_tx}, p95={p95_tx}, p99={p99_tx}, max={max_tx}",
                    "percentage": 0.0,
                    "interpretation": "Percentile distribution of transaction counts per destination account.",
                    "status": "OBSERVED",
                }
            )

            if target_col:
                fraud_dests = df[df[target_col] == 1][dest_col].unique()
                fraud_dest_cnt = len(fraud_dests)
                fraud_dest_pct = (
                    round(fraud_dest_cnt / unique_dest * 100.0, 5)
                    if unique_dest > 0
                    else 0.0
                )
                records.append(
                    {
                        "entity_role": "DESTINATION_ACCOUNT",
                        "column": dest_col,
                        "metric": "FRAUD_INVOLVED_ENTITIES",
                        "value": fraud_dest_cnt,
                        "percentage": fraud_dest_pct,
                        "interpretation": f"{fraud_dest_cnt} destination entities ({fraud_dest_pct}%) received fraud funds.",
                        "status": "OBSERVED",
                    }
                )

    return pd.DataFrame(records)
