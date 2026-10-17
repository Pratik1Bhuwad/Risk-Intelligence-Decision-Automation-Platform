"""
Tests for Operational Prediction Point and Field-Availability Policy.
"""

import pytest
from src.features.policy import (
    FIELD_POLICIES,
    PERMITTED_RAW_FEATURE_INPUTS,
    STRICTLY_EXCLUDED_FIELDS,
    DatasetAvailability,
    ProductionAvailability,
    ProjectFeaturePolicy,
    is_field_permitted_for_features,
    get_field_policy,
)


def test_field_policy_classifications():
    # Permitted inputs
    assert get_field_policy("step").feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT
    assert get_field_policy("type").feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT
    assert get_field_policy("amount").feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT
    assert get_field_policy("nameOrig").feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT
    assert get_field_policy("nameDest").feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT
    assert get_field_policy("oldbalanceOrg").feature_policy == ProjectFeaturePolicy.PERMITTED_INPUT

    # Excluded post-event fields
    assert get_field_policy("newbalanceOrig").feature_policy == ProjectFeaturePolicy.EXCLUDED_POST_EVENT
    assert get_field_policy("newbalanceDest").feature_policy == ProjectFeaturePolicy.EXCLUDED_POST_EVENT

    # Excluded target
    assert get_field_policy("isFraud").feature_policy == ProjectFeaturePolicy.EXCLUDED_TARGET

    # Excluded proxy
    assert get_field_policy("isFlaggedFraud").feature_policy == ProjectFeaturePolicy.EXCLUDED_PROXY


def test_oldbalance_dest_policy():
    """Verify Correction 2: oldbalanceDest 3-way distinction."""
    policy = get_field_policy("oldbalanceDest")
    assert policy.dataset_availability == DatasetAvailability.AVAILABLE_IN_DATASET
    assert policy.production_availability == ProductionAvailability.UNKNOWN_ARCHITECTURE_DEPENDENT
    assert policy.feature_policy == ProjectFeaturePolicy.EXCLUDED_UNVERIFIED_SOURCE
    assert is_field_permitted_for_features("oldbalanceDest") is False


def test_permission_helper():
    assert is_field_permitted_for_features("step") is True
    assert is_field_permitted_for_features("amount") is True
    assert is_field_permitted_for_features("newbalanceOrig") is False
    assert is_field_permitted_for_features("newbalanceDest") is False
    assert is_field_permitted_for_features("isFraud") is False
    assert is_field_permitted_for_features("isFlaggedFraud") is False
    assert is_field_permitted_for_features("random_unknown_col") is False


def test_sets_partition_all_fields():
    all_fields = set(FIELD_POLICIES.keys())
    assert PERMITTED_RAW_FEATURE_INPUTS.union(STRICTLY_EXCLUDED_FIELDS) == all_fields
    assert PERMITTED_RAW_FEATURE_INPUTS.intersection(STRICTLY_EXCLUDED_FIELDS) == set()
