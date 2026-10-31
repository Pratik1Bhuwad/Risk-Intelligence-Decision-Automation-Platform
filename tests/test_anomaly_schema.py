"""
Unit tests for Phase 05 Standalone Transaction Output Contract (Specification v2.3.2 §4).
"""

import math
import pytest

from src.anomaly.schema import (
    AnomalyOutputRow,
    AnomalyOutputSchema,
    AnomalyStatus,
    EligibleChannel,
    ReasonCode,
    validate_output_row,
)


def test_valid_state_a_scored_not_flagged():
    """Verify State A semantics: Scored, finite score, not flagged, budget_selected False."""
    row = AnomalyOutputSchema.create_scored_row(
        row_index=10,
        channel="TRANSFER",
        score=0.45,
        is_flagged=False,
    )
    assert row.row_index == 10
    assert row.channel == "TRANSFER"
    assert row.anomaly_score == 0.45
    assert row.is_anomaly_flagged is False
    assert row.anomaly_status == AnomalyStatus.SCORED.value
    assert row.reason_code is None
    assert row.alert_budget_selected is False
    validate_output_row(row)


def test_valid_state_b_scored_selected():
    """Verify State B semantics: Scored, finite score, flagged True, budget_selected True."""
    row = AnomalyOutputSchema.create_scored_row(
        row_index=20,
        channel="CASH_OUT",
        score=0.92,
        is_flagged=True,
    )
    assert row.row_index == 20
    assert row.channel == "CASH_OUT"
    assert row.anomaly_score == 0.92
    assert row.is_anomaly_flagged is True
    assert row.anomaly_status == AnomalyStatus.SCORED.value
    assert row.reason_code is None
    assert row.alert_budget_selected is True
    validate_output_row(row)


def test_valid_state_c_degraded_unscorable():
    """Verify State C semantics: Degraded, null score, null flag, alert_budget_selected False."""
    row = AnomalyOutputSchema.create_degraded_row(
        row_index=30,
        channel="TRANSFER",
        reason_code=ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value,
    )
    assert row.row_index == 30
    assert row.channel == "TRANSFER"
    assert row.anomaly_score is None
    assert row.is_anomaly_flagged is None
    assert row.anomaly_status == AnomalyStatus.DEGRADED_UNSCORABLE.value
    assert row.reason_code == ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value
    assert row.alert_budget_selected is False
    validate_output_row(row)


def test_reject_contradictory_flags():
    """Scored row must have is_anomaly_flagged == alert_budget_selected."""
    bad_row = AnomalyOutputRow(
        schema_version="1.0.0",
        row_index=1,
        channel="TRANSFER",
        anomaly_score=0.5,
        is_anomaly_flagged=True,
        anomaly_status="SCORED",
        reason_code=None,
        alert_budget_selected=False,  # Contradicts is_anomaly_flagged
    )
    with pytest.raises(ValueError, match="Contradictory selection flags"):
        validate_output_row(bad_row)


def test_reject_non_finite_score_in_scored_state():
    """Scored row cannot have NaN or Inf score."""
    bad_row = AnomalyOutputRow(
        schema_version="1.0.0",
        row_index=1,
        channel="TRANSFER",
        anomaly_score=float("nan"),
        is_anomaly_flagged=False,
        anomaly_status="SCORED",
        reason_code=None,
        alert_budget_selected=False,
    )
    with pytest.raises(ValueError, match="finite anomaly_score"):
        validate_output_row(bad_row)


def test_reject_degraded_with_score_or_flag():
    """Degraded row must have null score and null flag."""
    bad_row = AnomalyOutputRow(
        schema_version="1.0.0",
        row_index=1,
        channel="TRANSFER",
        anomaly_score=0.0,  # Prohibited in degraded state
        is_anomaly_flagged=None,
        anomaly_status="DEGRADED_UNSCORABLE",
        reason_code="ALL_ANOMALY_FEATURES_INACTIVE",
        alert_budget_selected=False,
    )
    with pytest.raises(ValueError, match="must have null anomaly_score"):
        validate_output_row(bad_row)


def test_reject_negative_or_non_integer_row_index():
    """row_index must be non-negative integer."""
    bad_row = AnomalyOutputRow(
        schema_version="1.0.0",
        row_index=-5,
        channel="TRANSFER",
        anomaly_score=0.5,
        is_anomaly_flagged=False,
        anomaly_status="SCORED",
        reason_code=None,
        alert_budget_selected=False,
    )
    with pytest.raises(ValueError, match="must be non-negative integer"):
        validate_output_row(bad_row)


def test_dataframe_conversion():
    """Verify DataFrame conversion and column completeness."""
    r1 = AnomalyOutputSchema.create_scored_row(0, "TRANSFER", 0.1, False)
    r2 = AnomalyOutputSchema.create_scored_row(1, "CASH_OUT", 0.9, True)
    r3 = AnomalyOutputSchema.create_degraded_row(2, "TRANSFER")

    df = AnomalyOutputSchema.to_dataframe([r1, r2, r3])
    assert len(df) == 3
    assert list(df.columns) == AnomalyOutputSchema.COLUMN_NAMES
    assert df.loc[2, "anomaly_score"] is None or math.isnan(df.loc[2, "anomaly_score"])
    assert df.loc[2, "anomaly_status"] == AnomalyStatus.DEGRADED_UNSCORABLE.value


def test_schema_version_decoupled_from_specification_version():
    """
    Task 1: Authoritative schema version reconciliation.
    Specification v2.3.2 Section 4.1 specifies: schema_version is output contract version, initially '1.0.0'.
    Specification document version is '2.3.2'.
    Verify that transaction-level schema_version is '1.0.0' and decoupled from config spec_version.
    """
    from src.anomaly.schema import CURRENT_SCHEMA_VERSION
    from src.anomaly.config import load_anomaly_config

    config = load_anomaly_config("configs/anomaly_detection.yaml", verify_provenance=True)
    assert config.spec_version == "2.3.2"
    assert CURRENT_SCHEMA_VERSION == "1.0.0"
    assert config.spec_version != CURRENT_SCHEMA_VERSION

    scored_row = AnomalyOutputSchema.create_scored_row(1, "TRANSFER", 0.5, False)
    assert scored_row.schema_version == "1.0.0"

    degraded_row = AnomalyOutputSchema.create_degraded_row(2, "CASH_OUT")
    assert degraded_row.schema_version == "1.0.0"


