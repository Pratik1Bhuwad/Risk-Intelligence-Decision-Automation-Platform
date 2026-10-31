"""
Temporal Window Verification Tests for Phase 05 (Implementation Command 08, Task 3).

Verifies the mathematical and implementation properties of temporal windows:
  - 24-step sliding window (short_window_steps: 24) exact lower boundary and eviction.
  - 168-step sliding window (long_window_steps: 168) exact lower boundary and eviction.
  - Strict historical condition: historical_step < current_step.
  - Same-step observation exclusion (SAME_STEP_POLICY = "EXCLUDE_SAME_STEP").
  - Future-step lookahead exclusion.
  - Empty history and insufficient history handling.
  - Step advancement and buffer commitment.
  - Repeated observations within the same step.
  - Feature catalog audit confirming 168-step window status in the 36 canonical features.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.transformers import PointInTimeEntityVelocityTransformer
from src.features.metadata import FEATURE_CATALOG
from src.anomaly.config import load_anomaly_config


def _build_test_stream(records):
    """
    Build DataFrame for PointInTimeEntityVelocityTransformer.
    records: list of tuples (step, dest, orig, amount)
    """
    df = pd.DataFrame(records, columns=["step", "nameDest", "nameOrig", "amount"])
    df["type"] = "TRANSFER"
    df["row_index"] = np.arange(len(df), dtype=int)
    return df


def test_24_step_window_exact_boundaries():
    """
    Verify exact 24-step sliding window lower boundary inclusion and eviction:
      Window interval for transaction at step `st`: [st - 24, st).
      Record at `st - 25`: EVICTED (< st - 24).
      Record at `st - 24`: INCLUDED (>= st - 24).
      Record at `st - 1`: INCLUDED.
      Record at `st`: EXCLUDED (same step buffer).
    """
    transformer = PointInTimeEntityVelocityTransformer(window_steps=24)

    # Sequence of transactions to same destination 'D1':
    # Step 5: tx amount 100
    # Step 6: tx amount 200
    # Step 15: tx amount 300
    # Step 30: evaluate here! cutoff = 30 - 24 = 6.
    #   Step 5 is evicted (5 < 6).
    #   Step 6 is kept (6 >= 6).
    #   Step 15 is kept (15 >= 6).
    #   Expected 24h count at step 30 = 2 (step 6 and 15), sum = 200 + 300 = 500.
    records = [
        (5, "D1", "O1", 100.0),
        (6, "D1", "O2", 200.0),
        (15, "D1", "O3", 300.0),
        (30, "D1", "O4", 400.0),
    ]
    df = _build_test_stream(records)
    out = transformer.transform(df)

    # Step 5 (index 0): first seen, count = 0, sum = 0.0
    assert out.loc[0, "dest_tx_count_prior_24h"] == 0
    assert out.loc[0, "dest_amount_sum_prior_24h"] == 0.0

    # Step 6 (index 1): sees step 5 (6 - 24 = -18 <= 5), count = 1, sum = 100.0
    assert out.loc[1, "dest_tx_count_prior_24h"] == 1
    assert out.loc[1, "dest_amount_sum_prior_24h"] == 100.0

    # Step 15 (index 2): sees step 5 and step 6 (15 - 24 = -9 <= 5), count = 2, sum = 300.0
    assert out.loc[2, "dest_tx_count_prior_24h"] == 2
    assert out.loc[2, "dest_amount_sum_prior_24h"] == 300.0

    # Step 30 (index 3): cutoff = 30 - 24 = 6.
    # Step 5 evicted (5 < 6); step 6 and 15 retained.
    assert out.loc[3, "dest_tx_count_prior_24h"] == 2
    assert out.loc[3, "dest_amount_sum_prior_24h"] == 500.0

    # Step 31: cutoff = 31 - 24 = 7.
    # Now step 6 is also evicted (6 < 7).
    # Kept: step 15 (300) and step 30 (400).
    df_step31 = pd.concat([df, _build_test_stream([(31, "D1", "O5", 50.0)])], ignore_index=True)
    out31 = transformer.transform(df_step31)
    assert out31.loc[4, "dest_tx_count_prior_24h"] == 2
    assert out31.loc[4, "dest_amount_sum_prior_24h"] == 700.0  # 300 + 400


def test_24_step_window_eviction_boundary_transition():
    """Verify single-step transition across the 24-step eviction boundary."""
    transformer = PointInTimeEntityVelocityTransformer(window_steps=24)

    # Transaction at step 10.
    # At step 34: 34 - 24 = 10. Boundary inclusive -> step 10 retained!
    # At step 35: 35 - 24 = 11. Boundary passed -> step 10 evicted!
    records = [
        (10, "DEST_BOUNDARY", "O1", 1000.0),
        (34, "DEST_BOUNDARY", "O2", 50.0),
        (35, "DEST_BOUNDARY", "O3", 50.0),
    ]
    df = _build_test_stream(records)
    out = transformer.transform(df)

    # Step 10: initial
    assert out.loc[0, "dest_tx_count_prior_24h"] == 0

    # Step 34: 34 - 24 = 10 -> step 10 is >= cutoff -> retained!
    assert out.loc[1, "dest_tx_count_prior_24h"] == 1
    assert out.loc[1, "dest_amount_sum_prior_24h"] == 1000.0

    # Step 35: 35 - 24 = 11 -> step 10 (< 11) is evicted!
    # Kept: only step 34 (amount 50.0)
    assert out.loc[2, "dest_tx_count_prior_24h"] == 1
    assert out.loc[2, "dest_amount_sum_prior_24h"] == 50.0


def test_168_step_window_exact_boundaries():
    """
    Verify exact 168-step sliding window lower boundary inclusion and eviction:
      Window interval for transaction at step `st`: [st - 168, st).
      Record at `st - 169`: EVICTED (< st - 168).
      Record at `st - 168`: INCLUDED (>= st - 168).
    """
    transformer_168 = PointInTimeEntityVelocityTransformer(window_steps=168)

    # Transaction at step 32 (amount 1,500)
    # At step 200: cutoff = 200 - 168 = 32 -> step 32 retained!
    # At step 201: cutoff = 201 - 168 = 33 -> step 32 evicted!
    records = [
        (32, "DEST_168", "O1", 1500.0),
        (200, "DEST_168", "O2", 100.0),
        (201, "DEST_168", "O3", 100.0),
    ]
    df = _build_test_stream(records)
    out = transformer_168.transform(df)

    # Step 32: initial
    assert out.loc[0, "dest_tx_count_prior_24h"] == 0

    # Step 200: 200 - 168 = 32 -> step 32 is >= cutoff -> retained!
    assert out.loc[1, "dest_tx_count_prior_24h"] == 1
    assert out.loc[1, "dest_amount_sum_prior_24h"] == 1500.0

    # Step 201: 201 - 168 = 33 -> step 32 (< 33) is evicted!
    # Kept: only step 200 (amount 100.0)
    assert out.loc[2, "dest_tx_count_prior_24h"] == 1
    assert out.loc[2, "dest_amount_sum_prior_24h"] == 100.0


def test_strict_same_step_and_future_exclusion():
    """
    Verify SAME_STEP_POLICY = "EXCLUDE_SAME_STEP":
      Transactions occurring in the same step must NEVER observe each other.
    """
    transformer = PointInTimeEntityVelocityTransformer(window_steps=24)

    # 4 transactions occurring in the exact same step (step 10) to same destination
    records = [
        (10, "DEST_SAME", "O1", 100.0),
        (10, "DEST_SAME", "O2", 200.0),
        (10, "DEST_SAME", "O3", 300.0),
        (10, "DEST_SAME", "O4", 400.0),
        # Next step
        (11, "DEST_SAME", "O5", 50.0),
    ]
    df = _build_test_stream(records)
    out = transformer.transform(df)

    # All transactions in step 10 must see 0 prior transactions
    for idx in range(4):
        assert out.loc[idx, "dest_tx_count_prior_24h"] == 0
        assert out.loc[idx, "dest_amount_sum_prior_24h"] == 0.0
        assert out.loc[idx, "dest_prior_tx_count"] == 0
        assert out.loc[idx, "dest_prior_total_amount"] == 0.0

    # Transaction in step 11 must commit all 4 prior transactions together
    assert out.loc[4, "dest_tx_count_prior_24h"] == 4
    assert out.loc[4, "dest_amount_sum_prior_24h"] == 1000.0
    assert out.loc[4, "dest_prior_tx_count"] == 4
    assert out.loc[4, "dest_prior_total_amount"] == 1000.0
    assert out.loc[4, "dest_time_since_last_tx"] == 1.0  # 11 - 10


def test_empty_and_insufficient_history():
    """Verify first-time-seen entity indicators and empty history defaults."""
    transformer = PointInTimeEntityVelocityTransformer(window_steps=24)

    records = [
        (1, "DEST_NEW", "ORIG_NEW", 500.0),
    ]
    df = _build_test_stream(records)
    out = transformer.transform(df)

    assert out.loc[0, "dest_is_first_time_seen"] == 1
    assert out.loc[0, "dest_prior_tx_count"] == 0
    assert out.loc[0, "dest_prior_total_amount"] == 0.0
    assert out.loc[0, "dest_time_since_last_tx"] == -1.0
    assert out.loc[0, "dest_tx_count_prior_24h"] == 0
    assert out.loc[0, "dest_amount_sum_prior_24h"] == 0.0

    assert out.loc[0, "orig_is_first_time_seen"] == 1
    assert out.loc[0, "orig_prior_tx_count"] == 0
    assert out.loc[0, "orig_prior_total_amount"] == 0.0
    assert out.loc[0, "orig_time_since_last_tx"] == -1.0


def test_catalog_window_audit_and_configuration_role():
    """
    Task 3: Independent audit of the 36 canonical features and the 168-step configuration.
    Confirms:
      1. Exactly 36 canonical features exist in FEATURE_CATALOG.
      2. Exactly two 24-step features exist: dest_tx_count_prior_24h, dest_amount_sum_prior_24h.
      3. Zero 168-step features exist in the 36 approved features.
      4. configs/anomaly_detection.yaml retains long_window_steps: 168 as an architectural parameter.
    """
    catalog = FEATURE_CATALOG
    assert len(catalog) == 36

    # 24-step window features
    window_24_features = [f for f, meta in catalog.items() if meta.time_window == "WINDOW_24_STEPS_STRICT_PRIOR"]
    assert window_24_features == ["dest_tx_count_prior_24h", "dest_amount_sum_prior_24h"]

    # 168-step window features
    window_168_features = [f for f, meta in catalog.items() if "168" in meta.time_window or "168" in f]
    assert len(window_168_features) == 0, (
        "Expected zero 168-step features in the 36 canonical feature catalog."
    )

    # Configuration verification
    config = load_anomaly_config("configs/anomaly_detection.yaml", verify_provenance=True)
    assert config.short_window_steps == 24
    assert config.long_window_steps == 168

