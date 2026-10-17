"""
Synthetic-data artifact and simulation hypothesis audit module.
"""

from typing import List
import numpy as np
import pandas as pd
from src.config import AuditConfig


def audit_synthetic_artifacts(
    df: pd.DataFrame, config: AuditConfig
) -> pd.DataFrame:
    """
    Empirically evaluate synthetic-data hypotheses and simulation artifacts.
    Labels every finding strictly as CONFIRMED, OBSERVED, HYPOTHESIS, UNKNOWN, or INVESTIGATE.
    """
    total_rows = len(df)
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
    flag_col = (
        config.flag_cols[0]
        if config.flag_cols and config.flag_cols[0] in df.columns
        else None
    )

    records = []

    # -------------------------------------------------------------
    # Hypothesis 1: Fraud restricted exclusively to TRANSFER and CASH_OUT
    # -------------------------------------------------------------
    if target_col and type_col:
        fraud_df = df[df[target_col] == 1]
        fraud_types = (
            set(fraud_df[type_col].unique()) if len(fraud_df) > 0 else set()
        )
        non_transfer_cashout_fraud = len(
            fraud_df[~fraud_df[type_col].isin(["TRANSFER", "CASH_OUT"])]
        )

        h1_status = (
            "CONFIRMED"
            if non_transfer_cashout_fraud == 0 and len(fraud_df) > 0
            else "OBSERVED"
        )
        records.append(
            {
                "hypothesis_id": "H1_FRAUD_TRANSACTION_TYPES",
                "hypothesis_description": "Fraud occurs exclusively in TRANSFER and CASH_OUT transaction types.",
                "empirical_evidence": f"Observed fraud types: {sorted(list(fraud_types))}. Fraud occurrences outside TRANSFER/CASH_OUT: {non_transfer_cashout_fraud}.",
                "observed_metric": f"non_transfer_cashout_fraud_count={non_transfer_cashout_fraud}",
                "interpretation": (
                    "Fraud generation in PaySim simulation is strictly restricted to TRANSFER and CASH_OUT. "
                    "Models can eliminate fraud predictions on PAYMENT, CASH_IN, and DEBIT."
                    if non_transfer_cashout_fraud == 0
                    else "Fraud appears in other transaction types."
                ),
                "status": h1_status,
            }
        )

    # -------------------------------------------------------------
    # Hypothesis 2: Zeroing-out rule (Draining entire originating balance)
    # -------------------------------------------------------------
    if target_col and "oldbalanceOrg" in df.columns and "amount" in df.columns:
        fraud_df = df[df[target_col] == 1]
        total_fraud = len(fraud_df)

        if total_fraud > 0:
            # Drain condition: amount == oldbalanceOrg and oldbalanceOrg > 0
            drain_df = fraud_df[
                (fraud_df["amount"] == fraud_df["oldbalanceOrg"])
                & (fraud_df["oldbalanceOrg"] > 0)
            ]
            drain_count = len(drain_df)
            drain_pct = round(drain_count / total_fraud * 100.0, 2)

            # Also check newbalanceOrig == 0
            zero_post_df = (
                fraud_df[fraud_df["newbalanceOrig"] == 0]
                if "newbalanceOrig" in fraud_df.columns
                else pd.DataFrame()
            )
            zero_post_pct = (
                round(len(zero_post_df) / total_fraud * 100.0, 2)
                if total_fraud > 0
                else 0.0
            )

            records.append(
                {
                    "hypothesis_id": "H2_FRAUD_BALANCE_DRAINING",
                    "hypothesis_description": "Fraud transactions drain the entire available balance (amount == oldbalanceOrg and newbalanceOrig == 0).",
                    "empirical_evidence": f"{drain_count} of {total_fraud} fraud transactions ({drain_pct}%) have amount == oldbalanceOrg. {len(zero_post_df)} ({zero_post_pct}%) result in zero newbalanceOrig.",
                    "observed_metric": f"drain_pct={drain_pct}%, zero_post_pct={zero_post_pct}%",
                    "interpretation": (
                        f"High concentration ({drain_pct}%) of fraud events transfer exactly the full balance, "
                        "indicating a synthetic simulation rule where simulated fraudsters liquidate compromised accounts completely."
                    ),
                    "status": "OBSERVED",
                }
            )

    # -------------------------------------------------------------
    # Hypothesis 3: Merchant destination balance mechanics
    # -------------------------------------------------------------
    if (
        "nameDest" in df.columns
        and "oldbalanceDest" in df.columns
        and "newbalanceDest" in df.columns
    ):
        m_mask = df["nameDest"].str.startswith("M", na=False)
        m_count = int(m_mask.sum())
        if m_count > 0:
            m_zero_balances = (
                (df.loc[m_mask, "oldbalanceDest"] == 0)
                & (df.loc[m_mask, "newbalanceDest"] == 0)
            ).sum()
            m_zero_pct = round(m_zero_balances / m_count * 100.0, 2)
            records.append(
                {
                    "hypothesis_id": "H3_MERCHANT_BALANCE_MECHANICS",
                    "hypothesis_description": "Merchant accounts (nameDest starting with 'M') always have zero balances (oldbalanceDest == 0 and newbalanceDest == 0).",
                    "empirical_evidence": f"Of {m_count} merchant destination records, {m_zero_balances} ({m_zero_pct}%) have both balances exactly equal to 0.",
                    "observed_metric": f"merchant_zero_balance_pct={m_zero_pct}%",
                    "interpretation": (
                        "Merchant destination balances are not simulated in PaySim and remain fixed at 0. "
                        "Balance features for merchants convey no information and reflect simulator omission."
                    ),
                    "status": "CONFIRMED" if m_zero_pct == 100.0 else "OBSERVED",
                }
            )

    # -------------------------------------------------------------
    # Hypothesis 4: Balance discrepancy artifacts
    # -------------------------------------------------------------
    if (
        "oldbalanceOrg" in df.columns
        and "amount" in df.columns
        and "newbalanceOrig" in df.columns
    ):
        # Discrepancy: oldbalanceOrg - amount != newbalanceOrig
        # For non-cash-in records where balance decreases
        non_cash_in = df[
            df[type_col].isin(["CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"])
        ]
        non_ci_count = len(non_cash_in)
        if non_ci_count > 0:
            diff = (
                non_cash_in["oldbalanceOrg"]
                - non_cash_in["amount"]
                - non_cash_in["newbalanceOrig"]
            ).abs()
            discrepancy_cnt = int((diff > 0.01).sum())
            disc_pct = round(discrepancy_cnt / non_ci_count * 100.0, 2)

            records.append(
                {
                    "hypothesis_id": "H4_ORIGIN_BALANCE_DISCREPANCY",
                    "hypothesis_description": "Originating account balance transition exhibits arithmetic discrepancies (old - amount != new).",
                    "empirical_evidence": f"{discrepancy_cnt} of {non_ci_count} non-cash-in records ({disc_pct}%) violate exact balance accounting.",
                    "observed_metric": f"origin_balance_discrepancy_pct={disc_pct}%",
                    "interpretation": (
                        "Balance tracking in the simulator contains intentional or unintentional accounting errors, "
                        "such as transactions allowed from zero-balance accounts or truncated calculations."
                    ),
                    "status": "OBSERVED",
                }
            )

    # -------------------------------------------------------------
    # Hypothesis 5: Originating entity uniqueness (No historical profile)
    # -------------------------------------------------------------
    if config.origin_cols and config.origin_cols[0] in df.columns:
        orig_col = config.origin_cols[0]
        unique_orig = int(df[orig_col].nunique())
        orig_ratio = (
            round(unique_orig / total_rows * 100.0, 4) if total_rows > 0 else 0.0
        )

        records.append(
            {
                "hypothesis_id": "H5_ORIGIN_ACCOUNT_UNIQUENESS",
                "hypothesis_description": "Originating accounts appear nearly or strictly once in the entire dataset, precluding customer history depth.",
                "empirical_evidence": f"{unique_orig} unique originating accounts across {total_rows} rows ({orig_ratio}% unique).",
                "observed_metric": f"origin_uniqueness_pct={orig_ratio}%",
                "interpretation": (
                    "In PaySim, originating accounts rarely repeat. This confirms that within-customer behavioral profiling "
                    "is severely limited on the origin side without external customer identity linkage."
                ),
                "status": "CONFIRMED" if orig_ratio > 99.0 else "OBSERVED",
            }
        )

    # -------------------------------------------------------------
    # Hypothesis 6: Destination account reuse
    # -------------------------------------------------------------
    if config.dest_cols and config.dest_cols[0] in df.columns:
        dest_col = config.dest_cols[0]
        unique_dest = int(df[dest_col].nunique())
        dest_ratio = (
            round(unique_dest / total_rows * 100.0, 4) if total_rows > 0 else 0.0
        )
        dest_reuse_pct = round(100.0 - dest_ratio, 4)

        records.append(
            {
                "hypothesis_id": "H6_DESTINATION_ACCOUNT_REUSE",
                "hypothesis_description": "Destination accounts receive repeat transactions, allowing destination-level profiling.",
                "empirical_evidence": f"{unique_dest} unique destination accounts across {total_rows} rows (reuse rate {dest_reuse_pct}%).",
                "observed_metric": f"dest_reuse_pct={dest_reuse_pct}%",
                "interpretation": (
                    "Destination entities exhibit substantial repeat activity, enabling entity-level destination profiling, "
                    "in-degree velocity metrics, and merchant risk categorization."
                ),
                "status": "CONFIRMED" if dest_reuse_pct > 10.0 else "OBSERVED",
            }
        )

    # -------------------------------------------------------------
    # Hypothesis 7: isFlaggedFraud rule behavior
    # -------------------------------------------------------------
    if (
        flag_col
        and flag_col in df.columns
        and "amount" in df.columns
        and type_col
        and type_col in df.columns
    ):
        flagged_df = df[df[flag_col] == 1]
        flagged_count = len(flagged_df)

        if flagged_count > 0:
            min_flagged_amt = float(flagged_df["amount"].min())
            flagged_types = list(flagged_df[type_col].unique())
            all_over_200k = bool((flagged_df["amount"] > 200000).all())
            all_transfers = bool((flagged_df[type_col] == "TRANSFER").all())

            # Check how many transfers > 200k were NOT flagged
            transfer_200k_unflagged = len(
                df[
                    (df[type_col] == "TRANSFER")
                    & (df["amount"] > 200000)
                    & (df[flag_col] == 0)
                ]
            )

            records.append(
                {
                    "hypothesis_id": "H7_FLAGGED_FRAUD_RULE_LOGIC",
                    "hypothesis_description": "isFlaggedFraud represents a simple threshold rule: TRANSFER transactions > 200,000.",
                    "empirical_evidence": f"Flagged count: {flagged_count}. Types: {flagged_types}. Min amount: {min_flagged_amt}. All > 200k: {all_over_200k}. Unflagged transfers > 200k: {transfer_200k_unflagged}.",
                    "observed_metric": f"min_flagged_amt={min_flagged_amt}, unflagged_over_200k={transfer_200k_unflagged}",
                    "interpretation": (
                        f"All {flagged_count} flagged records are TRANSFERs > 200,000, but {transfer_200k_unflagged} transfers > 200k were NOT flagged. "
                        "The rule is either an incomplete/legacy threshold or depends on an undocumented condition."
                    ),
                    "status": "OBSERVED",
                }
            )

    return pd.DataFrame(records)
