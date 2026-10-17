"""
Operational Prediction Point and Field-Availability Policy module.

Enforces production-defensible boundaries between pre-authorization inputs
and post-event / outcome / unverified data.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set

PREDICTION_EVENT = "Transaction authorization request arrives at scoring/authorization boundary"
PREDICTION_POINT = "Pre-Authorization Inline Evaluation"
PREDICTION_TIME_TEMPORAL_INDEX = "step"  # Discrete simulation-time hour index
SAME_STEP_POLICY = "EXCLUDE_SAME_STEP"  # Strict prior events: historical_step < current_step


class DatasetAvailability(str, Enum):
    AVAILABLE_IN_DATASET = "AVAILABLE_IN_DATASET"
    NOT_IN_DATASET = "NOT_IN_DATASET"


class ProductionAvailability(str, Enum):
    AVAILABLE_BEFORE_TRANSACTION = "AVAILABLE_BEFORE_TRANSACTION"
    AVAILABLE_DURING_TRANSACTION = "AVAILABLE_DURING_TRANSACTION"
    AVAILABLE_ONLY_AFTER_TRANSACTION = "AVAILABLE_ONLY_AFTER_TRANSACTION"
    UNKNOWN_ARCHITECTURE_DEPENDENT = "UNKNOWN_ARCHITECTURE_DEPENDENT"


class ProjectFeaturePolicy(str, Enum):
    PERMITTED_INPUT = "PERMITTED_INPUT"
    EXCLUDED_POST_EVENT = "EXCLUDED_POST_EVENT"
    EXCLUDED_TARGET = "EXCLUDED_TARGET"
    EXCLUDED_PROXY = "EXCLUDED_PROXY"
    EXCLUDED_UNVERIFIED_SOURCE = "EXCLUDED_UNVERIFIED_SOURCE"


@dataclass(frozen=True)
class FieldPolicy:
    field_name: str
    dataset_availability: DatasetAvailability
    production_availability: ProductionAvailability
    feature_policy: ProjectFeaturePolicy
    rationale: str


FIELD_POLICIES: Dict[str, FieldPolicy] = {
    "step": FieldPolicy(
        field_name="step",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_DURING_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.PERMITTED_INPUT,
        rationale=(
            "Discrete simulation-time index representing hours from simulation start. "
            "Available upon transaction arrival. Used as the temporal index for sequencing and cyclical features."
        ),
    ),
    "type": FieldPolicy(
        field_name="type",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_DURING_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.PERMITTED_INPUT,
        rationale="Payment channel / transaction method specified by the originator upon request arrival.",
    ),
    "amount": FieldPolicy(
        field_name="amount",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_DURING_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.PERMITTED_INPUT,
        rationale="Requested transfer/payment amount specified in authorization request.",
    ),
    "nameOrig": FieldPolicy(
        field_name="nameOrig",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_BEFORE_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.PERMITTED_INPUT,
        rationale="Originating account ID, authenticated prior to authorization evaluation.",
    ),
    "oldbalanceOrg": FieldPolicy(
        field_name="oldbalanceOrg",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_BEFORE_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.PERMITTED_INPUT,
        rationale="Originating account ledger balance immediately prior to authorization, accessible in sender's ledger.",
    ),
    "newbalanceOrig": FieldPolicy(
        field_name="newbalanceOrig",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_ONLY_AFTER_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.EXCLUDED_POST_EVENT,
        rationale=(
            "Originating account balance after transaction execution/settlement. "
            "In an inline pre-authorization engine, the decision occurs before execution. "
            "If declined/blocked, this balance never occurs. Excluded to prevent post-event leakage."
        ),
    ),
    "nameDest": FieldPolicy(
        field_name="nameDest",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_DURING_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.PERMITTED_INPUT,
        rationale="Destination account / merchant ID specified as transfer recipient upon request arrival.",
    ),
    "oldbalanceDest": FieldPolicy(
        field_name="oldbalanceDest",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.UNKNOWN_ARCHITECTURE_DEPENDENT,
        feature_policy=ProjectFeaturePolicy.EXCLUDED_UNVERIFIED_SOURCE,
        rationale=(
            "Dataset Availability: AVAILABLE IN PAYSIM DATASET. "
            "Production Availability: UNKNOWN / ARCHITECTURE-DEPENDENT. "
            "Current Project Feature Policy: EXCLUDED. "
            "Reason: The assumed authorization engine should not depend on recipient-side settlement/account "
            "information unless its availability at the authorization boundary can be explicitly established. "
            "This is a project design decision, not a claim that it is impossible in all banking setups."
        ),
    ),
    "newbalanceDest": FieldPolicy(
        field_name="newbalanceDest",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_ONLY_AFTER_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.EXCLUDED_POST_EVENT,
        rationale=(
            "Destination account balance post-settlement. "
            "Generated strictly after execution. Excluded to prevent post-event leakage."
        ),
    ),
    "isFraud": FieldPolicy(
        field_name="isFraud",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.AVAILABLE_ONLY_AFTER_TRANSACTION,
        feature_policy=ProjectFeaturePolicy.EXCLUDED_TARGET,
        rationale="Ground truth fraud label established post-event via fraud investigation or chargeback. Target only.",
    ),
    "isFlaggedFraud": FieldPolicy(
        field_name="isFlaggedFraud",
        dataset_availability=DatasetAvailability.AVAILABLE_IN_DATASET,
        production_availability=ProductionAvailability.UNKNOWN_ARCHITECTURE_DEPENDENT,
        feature_policy=ProjectFeaturePolicy.EXCLUDED_PROXY,
        rationale=(
            "Legacy heuristic rule flag (>200,000 TRANSFER). Represents output of an existing rule engine. "
            "Excluded from features to avoid circular rule replication and target proxying."
        ),
    ),
}

PERMITTED_RAW_FEATURE_INPUTS: Set[str] = {
    f for f, p in FIELD_POLICIES.items() if p.feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT
}

STRICTLY_EXCLUDED_FIELDS: Set[str] = {
    f for f, p in FIELD_POLICIES.items() if p.feature_policy != ProjectFeaturePolicy.PERMITTED_INPUT
}


def is_field_permitted_for_features(field_name: str) -> bool:
    """Return True if field is permitted as an input for feature engineering."""
    policy = FIELD_POLICIES.get(field_name)
    if not policy:
        return False
    return policy.feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT


def get_field_policy(field_name: str) -> FieldPolicy:
    """Retrieve the policy record for a specific field."""
    if field_name not in FIELD_POLICIES:
        raise KeyError(f"Field '{field_name}' not defined in FIELD_POLICIES.")
    return FIELD_POLICIES[field_name]
