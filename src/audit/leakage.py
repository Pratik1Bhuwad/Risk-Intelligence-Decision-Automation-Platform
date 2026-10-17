"""
Data leakage methodology and risk assessment module.
"""

from typing import List
import pandas as pd
from src.config import AuditConfig


def audit_leakage(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit potential data leakage across fields.
    Does NOT automatically classify fields as confirmed leakage without empirical evidence
    and defined operational decision points.
    Distinguishes target leakage, post-event leakage, temporal leakage, entity leakage,
    rule-output leakage, and future information.
    """
    records = []

    # 1. isFraud (Direct Target)
    records.append(
        {
            "field": "isFraud",
            "suspected_leakage_type": "DIRECT_TARGET",
            "evidence": "By definition, the ground truth binary outcome label.",
            "severity": "CRITICAL",
            "prediction_time_interpretation": "Generated post-event via fraud detection/investigation/chargebacks.",
            "recommended_handling": "Exclude from model feature set; use strictly as training target and evaluation ground truth.",
            "status": "CONFIRMED",
        }
    )

    # 2. isFlaggedFraud (Rule-Output / Proxy Investigation)
    flag_col = config.flag_cols[0] if config.flag_cols else "isFlaggedFraud"
    if flag_col in df.columns:
        flagged_series = df[flag_col]
        flagged_count = int((flagged_series == 1).sum())
        records.append(
            {
                "field": flag_col,
                "suspected_leakage_type": "RULE_OUTPUT_LEAKAGE",
                "evidence": f"Flag is set in {flagged_count} records. Historically configured as an internal business rule (>200,000 threshold).",
                "severity": "HIGH",
                "prediction_time_interpretation": "If this flag represents the output of an existing rule engine, including it in a predictive model risks learning to mimic the rule rather than detecting fraud patterns.",
                "recommended_handling": "INVESTIGATE operational origin. If confirmed as a legacy rule output, exclude from features or evaluate as a baseline benchmark rule only.",
                "status": "INVESTIGATE",
            }
        )

    # 3. newbalanceOrig (Post-Event Balance Investigation)
    if "newbalanceOrig" in df.columns:
        records.append(
            {
                "field": "newbalanceOrig",
                "suspected_leakage_type": "POST_EVENT_LEAKAGE",
                "evidence": "Represents originating account balance after transaction execution.",
                "severity": "HIGH",
                "prediction_time_interpretation": "In an inline, real-time risk decision engine, the decision to approve/block occurs before ledger settlement. If a transaction is blocked, newbalanceOrig never occurs.",
                "recommended_handling": "INVESTIGATE whether model operates inline (pre-auth) or offline (post-auth). If inline, exclude newbalanceOrig or replace with synthetic pre-computed feature: `oldbalanceOrg - amount`.",
                "status": "INVESTIGATE",
            }
        )

    # 4. oldbalanceOrg (Pre-Transaction Origin Balance)
    if "oldbalanceOrg" in df.columns:
        records.append(
            {
                "field": "oldbalanceOrg",
                "suspected_leakage_type": "NONE",
                "evidence": "Reflects account balance before transaction execution.",
                "severity": "NONE",
                "prediction_time_interpretation": "Available from internal ledger at transaction arrival time.",
                "recommended_handling": "Safe for feature engineering in conjunction with transaction amount (e.g. balance-to-amount ratio).",
                "status": "OBSERVED",
            }
        )

    # 5. oldbalanceDest (Destination Pre-Transaction Balance Investigation)
    if "oldbalanceDest" in df.columns:
        records.append(
            {
                "field": "oldbalanceDest",
                "suspected_leakage_type": "FUTURE_OR_EXTERNAL_INFORMATION",
                "evidence": "Contains recipient balance prior to transaction.",
                "severity": "MEDIUM",
                "prediction_time_interpretation": "In closed-loop systems (single mobile wallet provider), this balance may be internally readable. In inter-bank/external transfers, recipient balance is NOT available to sender.",
                "recommended_handling": "INVESTIGATE whether target deployment is closed-loop or open-loop. If open-loop, exclude to prevent unrealistic performance estimation.",
                "status": "INVESTIGATE",
            }
        )

    # 6. newbalanceDest (Destination Post-Transaction Balance Investigation)
    if "newbalanceDest" in df.columns:
        records.append(
            {
                "field": "newbalanceDest",
                "suspected_leakage_type": "POST_EVENT_LEAKAGE",
                "evidence": "Represents destination balance post-transaction execution.",
                "severity": "HIGH",
                "prediction_time_interpretation": "Updated strictly post-settlement. Never available prior to authorization.",
                "recommended_handling": "Exclude from real-time decision feature set unless evaluating post-clearing batch monitoring.",
                "status": "INVESTIGATE",
            }
        )

    # 7. step (Temporal Ordering & Leakage)
    if "step" in df.columns:
        records.append(
            {
                "field": "step",
                "suspected_leakage_type": "TEMPORAL_LEAKAGE",
                "evidence": "Monotonically increasing simulation hour.",
                "severity": "LOW",
                "prediction_time_interpretation": "Timestamp is known at transaction time, but random train/test splits that shuffle step leak future information.",
                "recommended_handling": "Enforce strict chronological train/validation/test splits (time-based cutoff) rather than random K-fold splits.",
                "status": "OBSERVED",
            }
        )

    # 8. nameOrig / nameDest (Entity History Leakage)
    records.append(
        {
            "field": "nameOrig, nameDest",
            "suspected_leakage_type": "ENTITY_HISTORY_LEAKAGE",
            "evidence": "Entity identifiers used across multiple transactions.",
            "severity": "MEDIUM",
            "prediction_time_interpretation": "Using global entity statistics computed across the entire dataset leaks future entity behavior into past transactions.",
            "recommended_handling": "Compute historical entity aggregations strictly on expanding temporal windows (point-in-time features without lookahead).",
            "status": "OBSERVED",
        }
    )

    return pd.DataFrame(records)
