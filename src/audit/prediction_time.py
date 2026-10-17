"""
Prediction-time availability matrix module.
"""

from typing import List
import pandas as pd
from src.config import AuditConfig


def generate_prediction_time_matrix(
    df: pd.DataFrame, config: AuditConfig
) -> pd.DataFrame:
    """
    Generate Prediction-Time Availability Matrix.
    Evaluates each column against candidate lifecycle stages:
    1. Before transaction
    2. Transaction arrives
    3. Risk decision
    4. Transaction outcome
    Maintains rigorous status classification (CONFIRMED, OBSERVED, HYPOTHESIS, UNKNOWN, INVESTIGATE).
    """
    matrix_definitions = {
        "step": {
            "semantic_meaning": "Discrete hourly time step of the simulation/transaction event.",
            "known_before_transaction": False,
            "available_at_transaction_time": True,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "SAFE (TEMPORAL)",
            "rationale": "Transaction timestamp is generated when the transaction arrives.",
            "status": "CONFIRMED",
        },
        "type": {
            "semantic_meaning": "Transaction method/channel (e.g. PAYMENT, TRANSFER, CASH_OUT).",
            "known_before_transaction": False,
            "available_at_transaction_time": True,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "SAFE (CATEGORICAL)",
            "rationale": "Defined at initiation by the user/system.",
            "status": "CONFIRMED",
        },
        "amount": {
            "semantic_meaning": "Nominal currency amount requested for the transaction.",
            "known_before_transaction": False,
            "available_at_transaction_time": True,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "SAFE (NUMERICAL)",
            "rationale": "Transaction amount is specified at request time.",
            "status": "CONFIRMED",
        },
        "nameOrig": {
            "semantic_meaning": "Originating customer account identifier.",
            "known_before_transaction": True,
            "available_at_transaction_time": True,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "SAFE (ENTITY_ORIGIN)",
            "rationale": "Originating account must exist and be authenticated before transacting.",
            "status": "CONFIRMED",
        },
        "oldbalanceOrg": {
            "semantic_meaning": "Pre-transaction ledger balance of the originating account.",
            "known_before_transaction": True,
            "available_at_transaction_time": True,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "SAFE / INVESTIGATE",
            "rationale": "Origin balance before transaction is known internally by the account ledger.",
            "status": "OBSERVED",
        },
        "newbalanceOrig": {
            "semantic_meaning": "Post-transaction ledger balance of originating account.",
            "known_before_transaction": False,
            "available_at_transaction_time": False,
            "generated_after_transaction": True,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "POST_EVENT_LEAKAGE_RISK",
            "rationale": "Computed and posted after transaction execution. If a transaction is blocked/declined at decision time, this balance is never realized. Requires investigation before feature use.",
            "status": "INVESTIGATE",
        },
        "nameDest": {
            "semantic_meaning": "Destination customer or merchant account identifier.",
            "known_before_transaction": False,
            "available_at_transaction_time": True,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "SAFE (ENTITY_DEST)",
            "rationale": "Provided by user or routing instructions at transaction arrival.",
            "status": "CONFIRMED",
        },
        "oldbalanceDest": {
            "semantic_meaning": "Pre-transaction balance of destination recipient account.",
            "known_before_transaction": False,
            "available_at_transaction_time": False,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "EXTERNAL_DATA_AVAILABILITY_RISK",
            "rationale": "In closed-loop wallets, destination balance may be readable. In open banking/inter-bank rails, recipient balance is NOT available to the sender institution at transaction time. Status unknown until operational architecture confirmed.",
            "status": "INVESTIGATE",
        },
        "newbalanceDest": {
            "semantic_meaning": "Post-transaction balance of destination recipient account.",
            "known_before_transaction": False,
            "available_at_transaction_time": False,
            "generated_after_transaction": True,
            "derived_from_outcome": False,
            "potentially_target_proxy": False,
            "leakage_risk": "POST_EVENT_LEAKAGE_RISK",
            "rationale": "Updated post-settlement. In open-loop transfers, completely unavailable to sender. In closed-loop systems, generated strictly post-event.",
            "status": "INVESTIGATE",
        },
        "isFraud": {
            "semantic_meaning": "Ground truth indicator of fraudulent transaction.",
            "known_before_transaction": False,
            "available_at_transaction_time": False,
            "generated_after_transaction": True,
            "derived_from_outcome": True,
            "potentially_target_proxy": False,
            "leakage_risk": "DIRECT_TARGET",
            "rationale": "Ground truth outcome label. Established post-event via investigation or dispute. NEVER available at prediction time.",
            "status": "CONFIRMED",
        },
        "isFlaggedFraud": {
            "semantic_meaning": "Pre-existing heuristic rule flag in the legacy/source system.",
            "known_before_transaction": False,
            "available_at_transaction_time": False,
            "generated_after_transaction": False,
            "derived_from_outcome": False,
            "potentially_target_proxy": True,
            "leakage_risk": "RULE_OUTPUT_LEAKAGE_RISK",
            "rationale": "Represents an existing threshold rule (e.g. transfer > 200,000). Must be investigated to determine whether it reflects prior rule output rather than an independent predictive feature.",
            "status": "INVESTIGATE",
        },
    }

    records = []
    for col in df.columns:
        info = matrix_definitions.get(
            col,
            {
                "semantic_meaning": "Unconfigured column",
                "known_before_transaction": False,
                "available_at_transaction_time": False,
                "generated_after_transaction": False,
                "derived_from_outcome": False,
                "potentially_target_proxy": False,
                "leakage_risk": "UNKNOWN",
                "rationale": "Column not in standard specification.",
                "status": "UNKNOWN",
            },
        )
        records.append({"field": col, **info})

    return pd.DataFrame(records)
