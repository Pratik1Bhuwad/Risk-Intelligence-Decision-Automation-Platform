"""
Tests for synthetic artifact review module.
"""

from src.audit.synthetic import audit_synthetic_artifacts


def test_synthetic_artifacts(synthetic_df, test_config):
    synth_df = audit_synthetic_artifacts(synthetic_df, test_config)
    assert len(synth_df) >= 5

    hyp_ids = set(synth_df["hypothesis_id"])
    assert "H1_FRAUD_TRANSACTION_TYPES" in hyp_ids
    assert "H2_FRAUD_BALANCE_DRAINING" in hyp_ids
    assert "H3_MERCHANT_BALANCE_MECHANICS" in hyp_ids
    assert "H5_ORIGIN_ACCOUNT_UNIQUENESS" in hyp_ids

    # In synthetic fixture, all fraud is in TRANSFER and CASH_OUT
    h1_row = synth_df[
        synth_df["hypothesis_id"] == "H1_FRAUD_TRANSACTION_TYPES"
    ].iloc[0]
    assert h1_row["status"] == "CONFIRMED"
