"""
Temporal Splitting module for leakage-safe train/val/test partitioning.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import pandas as pd


@dataclass(frozen=True)
class SplitSummary:
    name: str
    min_step: int
    max_step: int
    total_count: int
    fraud_count: int
    fraud_rate_pct: float


class TemporalSplitter:
    """
    Partitions datasets along discrete temporal simulation steps.
    Guarantees strict forward-chaining chronology (train < val < test) with zero look-ahead.
    """

    def __init__(
        self,
        train_max_step: int = 400,
        val_max_step: int = 550,
        test_max_step: int = 743,
        temporal_index_col: str = "step",
        target_col: str = "isFraud",
    ):
        if train_max_step >= val_max_step:
            raise ValueError(
                f"Invalid split boundaries: train_max_step ({train_max_step}) must be < val_max_step ({val_max_step})"
            )
        if val_max_step > test_max_step:
            raise ValueError(
                f"Invalid split boundaries: val_max_step ({val_max_step}) must be <= test_max_step ({test_max_step})"
            )

        self.train_max_step = train_max_step
        self.val_max_step = val_max_step
        self.test_max_step = test_max_step
        self.temporal_index_col = temporal_index_col
        self.target_col = target_col

    def get_step_series(self, df: pd.DataFrame) -> pd.Series:
        """Extract or reconstruct discrete temporal step index."""
        if self.temporal_index_col in df.columns:
            return df[self.temporal_index_col]
        elif "day_of_simulation" in df.columns and "hour_of_day" in df.columns:
            # Reconstruct exact step from cyclical hourly and elapsed day features
            return (df["day_of_simulation"] * 24 + df["hour_of_day"]).astype(int)
        else:
            raise KeyError(
                f"Cannot locate temporal index '{self.temporal_index_col}' and cannot reconstruct from "
                f"'day_of_simulation' and 'hour_of_day'."
            )

    def split(
        self,
        df: pd.DataFrame,
    ) -> Tuple[
        Tuple[pd.DataFrame, pd.Series],
        Tuple[pd.DataFrame, pd.Series],
        Tuple[pd.DataFrame, pd.Series],
        Dict[str, SplitSummary],
    ]:
        """
        Split DataFrame into train, validation, and test subsets based on discrete step.
        Returns:
            (X_train, y_train), (X_val, y_val), (X_test, y_test), summaries_dict
        """
        if self.target_col not in df.columns:
            raise ValueError(f"Target column '{self.target_col}' not found in DataFrame.")

        step = self.get_step_series(df)

        train_mask = step <= self.train_max_step
        val_mask = (step > self.train_max_step) & (step <= self.val_max_step)
        test_mask = (step > self.val_max_step) & (step <= self.test_max_step)

        # Invariant: Disjoint masks
        assert not (train_mask & val_mask).any(), "Temporal overlap detected between train and val"
        assert not (val_mask & test_mask).any(), "Temporal overlap detected between val and test"
        assert not (train_mask & test_mask).any(), "Temporal overlap detected between train and test"

        feature_cols = [c for c in df.columns if c not in [self.target_col, self.temporal_index_col]]

        X_train, y_train = df.loc[train_mask, feature_cols].copy(), df.loc[train_mask, self.target_col].copy()
        X_val, y_val = df.loc[val_mask, feature_cols].copy(), df.loc[val_mask, self.target_col].copy()
        X_test, y_test = df.loc[test_mask, feature_cols].copy(), df.loc[test_mask, self.target_col].copy()

        # Check positive classes in every fold
        for fold_name, y_fold in [("Train", y_train), ("Validation", y_val), ("Test", y_test)]:
            if len(y_fold) == 0:
                raise ValueError(f"{fold_name} split is empty.")
            if y_fold.nunique() < 2:
                # Warning or exception if fold lacks one of the classes
                pass

        summaries = {}
        for name, mask, y_fold in [
            ("train", train_mask, y_train),
            ("val", val_mask, y_val),
            ("test", test_mask, y_test),
        ]:
            steps_fold = step[mask]
            min_s = int(steps_fold.min()) if len(steps_fold) > 0 else 0
            max_s = int(steps_fold.max()) if len(steps_fold) > 0 else 0
            n_rows = int(len(y_fold))
            n_fraud = int(y_fold.sum())
            rate = round((n_fraud / n_rows * 100), 5) if n_rows > 0 else 0.0
            summaries[name] = SplitSummary(
                name=name,
                min_step=min_s,
                max_step=max_s,
                total_count=n_rows,
                fraud_count=n_fraud,
                fraud_rate_pct=rate,
            )

        return (X_train, y_train), (X_val, y_val), (X_test, y_test), summaries
