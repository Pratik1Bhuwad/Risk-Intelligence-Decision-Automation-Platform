"""
Tests for individual feature transformers.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.transformers import (
    TransactionChannelTransformer,
    TemporalCyclicalTransformer,
    AmountBehaviorTransformer,
    OriginBalanceLiquidationTransformer,
    CounterpartyTypeTransformer,
    PointInTimeEntityVelocityTransformer,
)


def test_transaction_channel_transformer():
    df = pd.DataFrame({"type": ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]})
    tf = TransactionChannelTransformer()
    res = tf.transform(df)

    assert res["is_transfer"].tolist() == [1, 0, 0, 0, 0]
    assert res["is_cash_out"].tolist() == [0, 1, 0, 0, 0]
    assert res["is_payment"].tolist() == [0, 0, 1, 0, 0]
    assert res["is_cash_in"].tolist() == [0, 0, 0, 1, 0]
    assert res["is_debit"].tolist() == [0, 0, 0, 0, 1]
    assert res["is_high_risk_type"].tolist() == [1, 1, 0, 0, 0]


def test_temporal_cyclical_transformer():
    df = pd.DataFrame({"step": [0, 5, 23, 24, 49]})
    tf = TemporalCyclicalTransformer()
    res = tf.transform(df)

    assert res["hour_of_day"].tolist() == [0, 5, 23, 0, 1]
    assert res["day_of_simulation"].tolist() == [0, 0, 0, 1, 2]
    assert res["day_of_week"].tolist() == [0, 0, 0, 1, 2]
    assert res["is_night_hour"].tolist() == [1, 1, 0, 1, 1]


def test_amount_behavior_transformer():
    df = pd.DataFrame({"amount": [0.0, 100.0, 1050.0, 2000.0]})
    tf = AmountBehaviorTransformer()
    res = tf.transform(df)

    assert res["is_amount_zero"].tolist() == [1, 0, 0, 0]
    assert res["is_amount_round_100"].tolist() == [0, 1, 0, 1]
    assert res["is_amount_round_1000"].tolist() == [0, 0, 0, 1]
    assert np.isclose(res["log_amount"].iloc[1], np.log1p(100.0), atol=1e-5)


def test_origin_balance_liquidation_transformer():
    df = pd.DataFrame(
        {
            "amount": [100.0, 500.0, 500.0, 0.0],
            "oldbalanceOrg": [100.0, 500.005, 0.0, 100.0],
            "type": ["TRANSFER", "TRANSFER", "TRANSFER", "PAYMENT"],
        }
    )
    tf = OriginBalanceLiquidationTransformer(drain_tolerance=0.01)
    res = tf.transform(df)

    # is_full_balance_drain: abs(amount - oldbalanceOrg) < 0.01 AND oldbalanceOrg > 0
    # Row 0: abs(100 - 100) = 0 < 0.01 and 100 > 0 -> 1
    # Row 1: abs(500 - 500.005) = 0.005 < 0.01 and 500.005 > 0 -> 1
    # Row 2: 500 vs 0 -> 0 (oldbalanceOrg is 0)
    assert res["is_full_balance_drain"].tolist() == [1, 1, 0, 0]
    assert res["is_orig_zero_balance"].tolist() == [0, 0, 1, 0]
    assert res["is_zero_balance_transfer"].tolist() == [0, 0, 1, 0]


def test_counterparty_type_transformer():
    df = pd.DataFrame({"nameDest": ["M12345", "C98765", "M99999"]})
    tf = CounterpartyTypeTransformer()
    res = tf.transform(df)

    assert res["dest_is_merchant"].tolist() == [1, 0, 1]
    assert res["dest_is_customer"].tolist() == [0, 1, 0]
