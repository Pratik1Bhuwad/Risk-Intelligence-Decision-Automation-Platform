"""
Data dictionary generation module.
"""

from typing import List
import pandas as pd
from src.config import AuditConfig


def generate_data_dictionary(
    df: pd.DataFrame, config: AuditConfig
) -> pd.DataFrame:
    """
    Generate the formal data dictionary based on observed schema, documented specifications,
    and audit status.
    """
    dict_definitions = {
        "step": {
            "semantic_role": "TEMPORAL_STEP",
            "documented_meaning": "Maps a unit of time in the real world. In this simulation 1 step is 1 hour of time.",
            "observed_meaning": "Integer hours ranging across simulation duration (total steps observed).",
            "entity_level": "TRANSACTION",
            "temporal_role": "EVENT_TIMESTAMP",
            "target_relation": "INDEPENDENT_FEATURE",
            "prediction_time_status": "AVAILABLE",
            "leakage_status": "SAFE_WITH_TIME_SPLIT",
            "confidence_status": "CONFIRMED",
        },
        "type": {
            "semantic_role": "CATEGORICAL_TRANSACTION_TYPE",
            "documented_meaning": "Transaction type: CASH-IN, CASH-OUT, DEBIT, PAYMENT, and TRANSFER.",
            "observed_meaning": "String category (CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER).",
            "entity_level": "TRANSACTION",
            "temporal_role": "STATIC_AT_EVENT",
            "target_relation": "INDEPENDENT_FEATURE",
            "prediction_time_status": "AVAILABLE",
            "leakage_status": "SAFE",
            "confidence_status": "CONFIRMED",
        },
        "amount": {
            "semantic_role": "NUMERICAL_AMOUNT",
            "documented_meaning": "Amount of the transaction in local currency.",
            "observed_meaning": "Float transaction volume, non-negative values.",
            "entity_level": "TRANSACTION",
            "temporal_role": "STATIC_AT_EVENT",
            "target_relation": "INDEPENDENT_FEATURE",
            "prediction_time_status": "AVAILABLE",
            "leakage_status": "SAFE",
            "confidence_status": "CONFIRMED",
        },
        "nameOrig": {
            "semantic_role": "ENTITY_ID_ORIGIN",
            "documented_meaning": "Customer who started the transaction.",
            "observed_meaning": "Alphanumeric customer ID prefixed with 'C'.",
            "entity_level": "ORIGINATING_ENTITY",
            "temporal_role": "STATIC_AT_EVENT",
            "target_relation": "ENTITY_IDENTIFIER",
            "prediction_time_status": "AVAILABLE",
            "leakage_status": "SAFE_IF_POINT_IN_TIME",
            "confidence_status": "CONFIRMED",
        },
        "oldbalanceOrg": {
            "semantic_role": "NUMERICAL_BALANCE",
            "documented_meaning": "Initial balance before the transaction.",
            "observed_meaning": "Float ledger balance of originating customer prior to transaction.",
            "entity_level": "ORIGINATING_ENTITY",
            "temporal_role": "STATE_BEFORE_EVENT",
            "target_relation": "INDEPENDENT_FEATURE",
            "prediction_time_status": "AVAILABLE",
            "leakage_status": "SAFE",
            "confidence_status": "CONFIRMED",
        },
        "newbalanceOrig": {
            "semantic_role": "NUMERICAL_BALANCE",
            "documented_meaning": "New balance after the transaction.",
            "observed_meaning": "Float ledger balance of originating customer after transaction.",
            "entity_level": "ORIGINATING_ENTITY",
            "temporal_role": "STATE_AFTER_EVENT",
            "target_relation": "POST_EVENT_OUTCOME",
            "prediction_time_status": "UNAVAILABLE_PRE_AUTH",
            "leakage_status": "POST_EVENT_LEAKAGE_RISK",
            "confidence_status": "INVESTIGATE",
        },
        "nameDest": {
            "semantic_role": "ENTITY_ID_DEST",
            "documented_meaning": "Customer who is the recipient of the transaction.",
            "observed_meaning": "Alphanumeric recipient ID prefixed with 'C' (customer) or 'M' (merchant).",
            "entity_level": "DESTINATION_ENTITY",
            "temporal_role": "STATIC_AT_EVENT",
            "target_relation": "ENTITY_IDENTIFIER",
            "prediction_time_status": "AVAILABLE",
            "leakage_status": "SAFE_IF_POINT_IN_TIME",
            "confidence_status": "CONFIRMED",
        },
        "oldbalanceDest": {
            "semantic_role": "NUMERICAL_BALANCE",
            "documented_meaning": "Initial balance recipient before the transaction. Note that there is not information for customers that start with M (Merchants).",
            "observed_meaning": "Float recipient balance prior to transaction. 0.0 for merchants.",
            "entity_level": "DESTINATION_ENTITY",
            "temporal_role": "STATE_BEFORE_EVENT",
            "target_relation": "INDEPENDENT_FEATURE",
            "prediction_time_status": "CONDITIONAL_AVAILABILITY",
            "leakage_status": "EXTERNAL_INFO_RISK",
            "confidence_status": "INVESTIGATE",
        },
        "newbalanceDest": {
            "semantic_role": "NUMERICAL_BALANCE",
            "documented_meaning": "New balance recipient after the transaction. Note that there is not information for customers that start with M (Merchants).",
            "observed_meaning": "Float recipient balance after transaction settlement. 0.0 for merchants.",
            "entity_level": "DESTINATION_ENTITY",
            "temporal_role": "STATE_AFTER_EVENT",
            "target_relation": "POST_EVENT_OUTCOME",
            "prediction_time_status": "UNAVAILABLE_PRE_AUTH",
            "leakage_status": "POST_EVENT_LEAKAGE_RISK",
            "confidence_status": "INVESTIGATE",
        },
        "isFraud": {
            "semantic_role": "TARGET_BINARY",
            "documented_meaning": "This is the transactions made by the fraudulent agents inside the simulation.",
            "observed_meaning": "Binary indicator (1 = fraudulent, 0 = non-fraudulent).",
            "entity_level": "TRANSACTION",
            "temporal_role": "OUTCOME_LABEL",
            "target_relation": "GROUND_TRUTH_TARGET",
            "prediction_time_status": "NEVER_AVAILABLE",
            "leakage_status": "DIRECT_TARGET",
            "confidence_status": "CONFIRMED",
        },
        "isFlaggedFraud": {
            "semantic_role": "FLAG_BINARY",
            "documented_meaning": "The business model aims to control massive transfers from one account to another and flags illegal attempts. An illegal attempt in this dataset is an attempt to transfer more than 200,000 in a single transaction.",
            "observed_meaning": "Binary indicator flagging large unauthorized transfer attempts.",
            "entity_level": "TRANSACTION",
            "temporal_role": "DECISION_FLAG",
            "target_relation": "RULE_OUTPUT_OR_PROXY",
            "prediction_time_status": "LEGACY_RULE_OUTPUT",
            "leakage_status": "RULE_OUTPUT_LEAKAGE_RISK",
            "confidence_status": "INVESTIGATE",
        },
    }

    records = []
    for col in df.columns:
        info = dict_definitions.get(
            col,
            {
                "semantic_role": "UNKNOWN",
                "documented_meaning": "UNDOCUMENTED",
                "observed_meaning": "UNVERIFIED",
                "entity_level": "UNKNOWN",
                "temporal_role": "UNKNOWN",
                "target_relation": "UNKNOWN",
                "prediction_time_status": "UNKNOWN",
                "leakage_status": "UNKNOWN",
                "confidence_status": "UNKNOWN",
            },
        )
        observed_dtype = str(df[col].dtype)
        records.append(
            {
                "column": col,
                "observed_dtype": observed_dtype,
                **info,
            }
        )

    return pd.DataFrame(records)
