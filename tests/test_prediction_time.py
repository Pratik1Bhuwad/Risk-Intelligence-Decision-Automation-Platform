"""
Tests for prediction-time availability matrix.
"""

from src.audit.prediction_time import generate_prediction_time_matrix


def test_prediction_time_matrix(synthetic_df, test_config):
    pred_df = generate_prediction_time_matrix(synthetic_df, test_config)
    assert len(pred_df) == 11
    assert "field" in pred_df.columns
    assert "leakage_risk" in pred_df.columns

    # Verify isFraud is DIRECT_TARGET
    fraud_row = pred_df[pred_df["field"] == "isFraud"].iloc[0]
    assert bool(fraud_row["available_at_transaction_time"]) is False
    assert bool(fraud_row["generated_after_transaction"]) is True
    assert fraud_row["leakage_risk"] == "DIRECT_TARGET"

    # Verify isFlaggedFraud is INVESTIGATE
    flag_row = pred_df[pred_df["field"] == "isFlaggedFraud"].iloc[0]
    assert flag_row["status"] == "INVESTIGATE"

    # Verify newbalanceOrig is INVESTIGATE
    newbal_row = pred_df[pred_df["field"] == "newbalanceOrig"].iloc[0]
    assert newbal_row["status"] == "INVESTIGATE"
