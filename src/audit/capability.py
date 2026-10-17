"""
Platform capability feasibility assessment module.
"""

from typing import List
import pandas as pd
from src.config import AuditConfig


def generate_capability_assessment(
    df: pd.DataFrame, config: AuditConfig
) -> pd.DataFrame:
    """
    Generate the capability assessment matrix evaluating the feasibility of required platform
    capabilities against empirical data evidence and architectural constraints.
    """
    capabilities = [
        {
            "capability": "Transaction Risk Score",
            "evidence_required": "Transaction-level attributes (type, amount), pre-transaction origin balance, recipient type, and verified fraud outcome label.",
            "evidence_observed": "Observed: complete transaction records with type, amount, oldbalanceOrg, nameDest prefixes, and 8,213+ fraud labels.",
            "status": "FEASIBLE",
            "limitation": "Post-event balance fields (newbalanceOrig, newbalanceDest) cannot be used directly in real-time scoring without causing data leakage. Model must rely strictly on pre-auth signals.",
        },
        {
            "capability": "Customer Risk Score",
            "evidence_required": "Sufficient repeat transaction history per customer/entity over time to construct persistent customer risk profiles.",
            "evidence_observed": "Originating accounts (nameOrig) appear nearly 100% uniquely (single transaction per originator). In contrast, destination accounts (nameDest) show repeat activity.",
            "status": "SEVERELY_CONSTRAINED",
            "limitation": "Customer risk scoring cannot be built on originating accounts within PaySim due to absence of historical origin activity. Feasible only for destination entities (recipient/merchant risk profiling) or via external identity linkage.",
        },
        {
            "capability": "Behavioral Change Indicators",
            "evidence_required": "Multiple historical transactions per customer across distinct time periods to establish individual baseline spending velocity, amount distributions, and habit shifts.",
            "evidence_observed": "Single-transaction origin accounts prevent customer-level baseline derivation across time.",
            "status": "SEVERELY_CONSTRAINED",
            "limitation": "Within-customer behavioral deviation is impossible on originating accounts. Macro-level or destination-level velocity (e.g. surge in incoming transfers to a single destination account) can still be computed.",
        },
        {
            "capability": "Anomaly Indicators",
            "evidence_required": "Statistical distributions of amounts, balance-to-amount ratios, and transaction timing across cohorts.",
            "evidence_observed": "Strong empirical signals observed: extreme amount distributions, zero-balance originator drain patterns, and distinct merchant vs customer patterns.",
            "status": "FEASIBLE",
            "limitation": "Anomalies must be computed relative to population cohorts or transaction types rather than individual customer baselines.",
        },
        {
            "capability": "Explainable Risk Factors",
            "evidence_required": "Interpretable transaction features and risk drivers that can be translated into clear risk factor statements for human analysts.",
            "evidence_observed": "High interpretability of observed signals: transaction type (TRANSFER/CASH_OUT), balance liquidation (amount == oldbalanceOrg), destination entity reuse, and high-value transfers.",
            "status": "FEASIBLE",
            "limitation": "Explanations must clearly reflect the limitations of the data (e.g. noting that originator has no prior transaction history in the system).",
        },
        {
            "capability": "Decision Recommendations (Approve / Monitor / Manual Investigation)",
            "evidence_required": "Reliable risk scores, explainable risk factors, calibrated probability estimates, and business policy rules.",
            "evidence_observed": "Distinct risk separation between transaction types and balance-draining mechanisms allows multi-tier decision routing.",
            "status": "FEASIBLE",
            "limitation": "Low overall fraud prevalence (~0.13%) requires careful policy threshold tuning to prevent overwhelming fraud analysts with false positives during manual investigations.",
        },
    ]

    return pd.DataFrame(capabilities)
