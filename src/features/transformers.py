"""
Feature Transformers module for Risk Intelligence & Decision Automation Platform.

Implements modular, deterministic, leakage-safe feature transformations.
Historical features enforce the strict temporal boundary: historical_step < current_step.
Transactions occurring at the same step do NOT contaminate each other.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.features.policy import (
    PREDICTION_TIME_TEMPORAL_INDEX,
    SAME_STEP_POLICY,
    is_field_permitted_for_features,
)


class BaseTransformer:
    """Base class for feature transformers."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class TransactionChannelTransformer(BaseTransformer):
    """
    Computes transaction channel and method features based strictly on raw 'type'.
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if "type" not in df.columns:
            raise KeyError("Missing required input column 'type'.")

        tx_type = df["type"].astype(str)

        features = pd.DataFrame(index=df.index)
        features["is_transfer"] = (tx_type == "TRANSFER").astype(np.int8)
        features["is_cash_out"] = (tx_type == "CASH_OUT").astype(np.int8)
        features["is_payment"] = (tx_type == "PAYMENT").astype(np.int8)
        features["is_cash_in"] = (tx_type == "CASH_IN").astype(np.int8)
        features["is_debit"] = (tx_type == "DEBIT").astype(np.int8)
        features["is_high_risk_type"] = (
            tx_type.isin(["TRANSFER", "CASH_OUT"])
        ).astype(np.int8)

        return features


class TemporalCyclicalTransformer(BaseTransformer):
    """
    Computes temporal and cyclical features from the discrete simulation index 'step'.
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if "step" not in df.columns:
            raise KeyError("Missing required input column 'step'.")

        step = df["step"].values

        features = pd.DataFrame(index=df.index)
        hour = (step % 24).astype(np.int8)
        day_sim = (step // 24).astype(np.int16)
        day_wk = ((step // 24) % 7).astype(np.int8)

        features["hour_of_day"] = hour
        features["day_of_simulation"] = day_sim
        features["day_of_week"] = day_wk
        features["is_night_hour"] = np.isin(hour, [0, 1, 2, 3, 4, 5, 6]).astype(np.int8)

        return features


class AmountBehaviorTransformer(BaseTransformer):
    """
    Computes amount behavioral features from the requested transaction amount.
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if "amount" not in df.columns:
            raise KeyError("Missing required input column 'amount'.")

        amount = df["amount"].values.astype(np.float64)
        non_neg_amount = np.maximum(0.0, amount)

        features = pd.DataFrame(index=df.index)
        features["amount"] = amount
        features["log_amount"] = np.log1p(non_neg_amount).astype(np.float32)
        features["is_amount_zero"] = (amount == 0.0).astype(np.int8)
        features["is_amount_round_100"] = (
            (amount > 0.0) & (np.fmod(amount, 100.0) == 0.0)
        ).astype(np.int8)
        features["is_amount_round_1000"] = (
            (amount > 0.0) & (np.fmod(amount, 1000.0) == 0.0)
        ).astype(np.int8)

        return features


class OriginBalanceLiquidationTransformer(BaseTransformer):
    """
    Computes origin balance and behavioral liquidation features.
    Inputs are strictly pre-authorization: 'amount', 'oldbalanceOrg', 'type'.
    """

    def __init__(self, drain_tolerance: float = 0.01):
        self.drain_tolerance = drain_tolerance

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["amount", "oldbalanceOrg", "type"]:
            if col not in df.columns:
                raise KeyError(f"Missing required input column '{col}'.")

        amount = df["amount"].values.astype(np.float64)
        old_bal = df["oldbalanceOrg"].values.astype(np.float64)
        tx_type = df["type"].astype(str).values

        non_neg_bal = np.maximum(0.0, old_bal)

        features = pd.DataFrame(index=df.index)
        features["oldbalanceOrg"] = old_bal
        features["log_oldbalanceOrg"] = np.log1p(non_neg_bal).astype(np.float32)
        features["is_orig_zero_balance"] = (old_bal == 0.0).astype(np.int8)
        features["amount_to_orig_balance_ratio"] = (
            amount / (non_neg_bal + 1.0)
        ).astype(np.float32)
        features["orig_balance_to_amount_ratio"] = (
            non_neg_bal / (np.maximum(0.0, amount) + 1.0)
        ).astype(np.float32)
        features["is_amount_exceeds_orig_balance"] = (amount > old_bal).astype(np.int8)

        # Definition: abs(amount - oldbalanceOrg) < tolerance AND oldbalanceOrg > 0
        features["is_full_balance_drain"] = (
            (np.abs(amount - old_bal) < self.drain_tolerance) & (old_bal > 0.0)
        ).astype(np.int8)

        features["is_zero_balance_transfer"] = (
            (old_bal == 0.0) & (tx_type == "TRANSFER")
        ).astype(np.int8)

        return features


class CounterpartyTypeTransformer(BaseTransformer):
    """
    Computes destination entity counterparty classification (Merchant vs Customer).
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if "nameDest" not in df.columns:
            raise KeyError("Missing required input column 'nameDest'.")

        name_dest = df["nameDest"].astype(str)

        features = pd.DataFrame(index=df.index)
        features["dest_is_merchant"] = name_dest.str.startswith("M").astype(np.int8)
        features["dest_is_customer"] = name_dest.str.startswith("C").astype(np.int8)

        return features


class PointInTimeEntityVelocityTransformer(BaseTransformer):
    """
    Computes strictly prior-event point-in-time velocity features for destination and origin entities.

    Guarantees:
    1. Strict temporal boundary: Only records with historical_step < current_step are considered.
    2. Same-step exclusion: Records sharing the same step index do NOT see each other.
    3. Self-invariance: The current transaction cannot contaminate its own history.
    4. Deterministic and $O(N)$ execution time.
    """

    def __init__(self, window_steps: int = 24):
        self.window_steps = window_steps

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["step", "amount", "nameDest", "nameOrig"]:
            if col not in df.columns:
                raise KeyError(f"Missing required input column '{col}'.")

        n = len(df)
        if n == 0:
            return pd.DataFrame(
                columns=[
                    "dest_prior_tx_count",
                    "dest_prior_total_amount",
                    "dest_prior_avg_amount",
                    "dest_time_since_last_tx",
                    "dest_is_first_time_seen",
                    "dest_tx_count_prior_24h",
                    "dest_amount_sum_prior_24h",
                    "orig_prior_tx_count",
                    "orig_prior_total_amount",
                    "orig_time_since_last_tx",
                    "orig_is_first_time_seen",
                ]
            )

        # Check if already sorted by step (PaySim raw data is strictly sorted)
        # If not, sort by step stable-fashion and re-index at end
        original_index = df.index
        is_sorted = df["step"].is_monotonic_increasing

        if is_sorted:
            work_df = df
            sort_order = None
        else:
            sort_order = np.argsort(df["step"].values, kind="stable")
            work_df = df.iloc[sort_order]

        steps = work_df["step"].values
        amounts = work_df["amount"].values.astype(np.float64)
        dests = work_df["nameDest"].astype(str).values
        origs = work_df["nameOrig"].astype(str).values

        # Output arrays
        dest_prior_cnt = np.empty(n, dtype=np.int32)
        dest_prior_amt = np.empty(n, dtype=np.float64)
        dest_prior_avg = np.empty(n, dtype=np.float32)
        dest_time_since = np.empty(n, dtype=np.float32)
        dest_first_seen = np.empty(n, dtype=np.int8)
        dest_cnt_24h = np.empty(n, dtype=np.int32)
        dest_amt_24h = np.empty(n, dtype=np.float64)

        orig_prior_cnt = np.empty(n, dtype=np.int32)
        orig_prior_amt = np.empty(n, dtype=np.float64)
        orig_time_since = np.empty(n, dtype=np.float32)
        orig_first_seen = np.empty(n, dtype=np.int8)

        # Committed historical states (strictly historical_step < current_step)
        dest_committed = {}  # dest -> (count, total_amount, last_step)
        dest_window = {}     # dest -> [deque of (step, amount), running_sum]
        orig_committed = {}  # orig -> (count, total_amount, last_step)

        # Step buffer: stores records seen during current_step
        # Format: list of (dest, orig, amount, step)
        step_buffer: List[Tuple[str, str, float, int]] = []
        current_step = steps[0]

        for i in range(n):
            st = steps[i]
            d = dests[i]
            o = origs[i]
            am = amounts[i]

            # When step advances, commit buffered transactions from prior steps
            if st > current_step:
                for b_d, b_o, b_am, b_st in step_buffer:
                    # Commit destination all-time
                    if b_d in dest_committed:
                        c, s, _ = dest_committed[b_d]
                        dest_committed[b_d] = (c + 1, s + b_am, b_st)
                    else:
                        dest_committed[b_d] = (1, b_am, b_st)

                    # Commit destination window
                    if b_d not in dest_window:
                        dest_window[b_d] = [deque(), 0.0]
                    dest_window[b_d][0].append((b_st, b_am))
                    dest_window[b_d][1] += b_am

                    # Commit originator all-time
                    if b_o in orig_committed:
                        c, s, _ = orig_committed[b_o]
                        orig_committed[b_o] = (c + 1, s + b_am, b_st)
                    else:
                        orig_committed[b_o] = (1, b_am, b_st)

                step_buffer.clear()
                current_step = st

            # -------------------------------------------------------------
            # Read strictly from committed states (historical_step < current_step)
            # -------------------------------------------------------------

            # Destination All-Time Prior
            if d in dest_committed:
                c, s, last_st = dest_committed[d]
                dest_prior_cnt[i] = c
                dest_prior_amt[i] = s
                dest_prior_avg[i] = float(s / c) if c > 0 else 0.0
                dest_time_since[i] = float(st - last_st)
                dest_first_seen[i] = 0
            else:
                dest_prior_cnt[i] = 0
                dest_prior_amt[i] = 0.0
                dest_prior_avg[i] = 0.0
                dest_time_since[i] = -1.0
                dest_first_seen[i] = 1

            # Destination 24-Step Sliding Window Prior (lazy window eviction strictly in [st - window_steps, st))
            if d in dest_window:
                q, rsum = dest_window[d]
                cutoff = st - self.window_steps
                while q and q[0][0] < cutoff:
                    _, ev_am = q.popleft()
                    rsum -= ev_am
                dest_window[d][1] = rsum
                dest_cnt_24h[i] = len(q)
                dest_amt_24h[i] = max(0.0, rsum)
            else:
                dest_cnt_24h[i] = 0
                dest_amt_24h[i] = 0.0

            # Originator All-Time Prior
            if o in orig_committed:
                c, s, last_st = orig_committed[o]
                orig_prior_cnt[i] = c
                orig_prior_amt[i] = s
                orig_time_since[i] = float(st - last_st)
                orig_first_seen[i] = 0
            else:
                orig_prior_cnt[i] = 0
                orig_prior_amt[i] = 0.0
                orig_time_since[i] = -1.0
                orig_first_seen[i] = 1

            # Buffer current transaction for subsequent step commitment
            step_buffer.append((d, o, am, st))

        features = pd.DataFrame(
            {
                "dest_prior_tx_count": dest_prior_cnt,
                "dest_prior_total_amount": dest_prior_amt,
                "dest_prior_avg_amount": dest_prior_avg,
                "dest_time_since_last_tx": dest_time_since,
                "dest_is_first_time_seen": dest_first_seen,
                "dest_tx_count_prior_24h": dest_cnt_24h,
                "dest_amount_sum_prior_24h": dest_amt_24h,
                "orig_prior_tx_count": orig_prior_cnt,
                "orig_prior_total_amount": orig_prior_amt,
                "orig_time_since_last_tx": orig_time_since,
                "orig_is_first_time_seen": orig_first_seen,
            },
            index=work_df.index,
        )

        # If data was re-ordered for sorting, restore original index alignment
        if not is_sorted:
            features = features.reindex(original_index)

        return features
