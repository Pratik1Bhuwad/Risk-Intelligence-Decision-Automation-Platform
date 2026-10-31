"""
Phase 05 Robust Preprocessing and Four-Tier Fallback Hierarchy.

Implements channel-conditioned robust median centering and scaling under
Specification v2.3.2 Section 5:
  1. MAD scaled by 1.4826
  2. IQR scaled by 1/1.349
  3. Positive-subset dispersion (min 10 observations)
  4. Feature exclusion (no arbitrary epsilon)
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

from src.features.policy import STRICTLY_EXCLUDED_FIELDS
from src.features.metadata import FEATURE_CATALOG

MAD_SCALE_FACTOR: float = 1.4826
IQR_DIVISOR: float = 1.349
MIN_POSITIVE_SUBSET_OBSERVATIONS: int = 10
ELIGIBLE_CHANNELS: Set[str] = {"TRANSFER", "CASH_OUT"}


@dataclass(frozen=True)
class FeatureFallbackResult:
    feature_name: str
    channel: str
    median: float
    scale: Optional[float]
    method: str  # 'MAD', 'IQR', 'positive_subset_dispersion', 'EXCLUDED'
    is_active: bool
    exclusion_reason: Optional[str] = None


class AnomalyPreprocessor:
    """
    Channel-conditioned robust preprocessor enforcing zero-leakage,
    strict fallback hierarchy without arbitrary epsilon, and active-feature determination.
    """

    def __init__(
        self,
        expected_features: Optional[List[str]] = None,
        min_pos_obs: int = MIN_POSITIVE_SUBSET_OBSERVATIONS,
    ):
        self.expected_features = expected_features or list(FEATURE_CATALOG.keys())
        self.min_pos_obs = min_pos_obs
        # Baselines keyed by channel -> feature_name -> FeatureFallbackResult
        self.channel_baselines: Dict[str, Dict[str, FeatureFallbackResult]] = {}
        self.is_fitted: bool = False

    def validate_inputs(
        self,
        df: pd.DataFrame,
        require_row_index: bool = True,
    ) -> None:
        """Validate absence of leakage fields, presence of features, and row_index uniqueness."""
        cols = set(df.columns)

        # 1. Prohibit post-event and leakage fields
        leakage = cols.intersection(STRICTLY_EXCLUDED_FIELDS)
        if leakage:
            raise ValueError(
                f"Prediction Security Violation: Input contains prohibited fields: {sorted(list(leakage))}"
            )

        # 2. Check row_index contract if required
        if require_row_index:
            if "row_index" not in cols:
                raise ValueError("Missing required immutable 'row_index' column in input data.")
            if len(df) > 0:
                if df["row_index"].isnull().any():
                    raise ValueError("Input data contains null values in immutable 'row_index'.")
                if not pd.api.types.is_integer_dtype(df["row_index"]):
                    raise TypeError("Input 'row_index' column must be integer dtype.")
                if df["row_index"].duplicated().any():
                    dup_count = int(df["row_index"].duplicated().sum())
                    raise ValueError(f"Input data contains {dup_count} duplicate 'row_index' values.")

        # 3. Check for required feature columns
        missing_features = [f for f in self.expected_features if f not in cols]
        if missing_features:
            raise ValueError(
                f"Missing required anomaly feature columns ({len(missing_features)} missing): {missing_features}"
            )

        # 4. Check for NaN/null or infinite values in feature columns
        if len(df) > 0:
            feat_df = df[self.expected_features]
            if feat_df.isnull().any().any():
                null_cols = [c for c in self.expected_features if feat_df[c].isnull().any()]
                raise ValueError(f"Input features contain NaN/null values in columns: {null_cols}")

            numeric_cols = feat_df.select_dtypes(include=[np.number]).columns
            if np.isneginf(feat_df[numeric_cols]).any().any() or np.isposinf(feat_df[numeric_cols]).any().any():
                inf_cols = [c for c in numeric_cols if np.isneginf(feat_df[c]).any() or np.isposinf(feat_df[c]).any()]
                raise ValueError(f"Input features contain infinite values (+inf / -inf) in columns: {inf_cols}")

    @classmethod
    def compute_feature_dispersion(
        cls,
        values: np.ndarray,
        feature_name: str,
        channel: str,
        min_pos_obs: int = MIN_POSITIVE_SUBSET_OBSERVATIONS,
    ) -> FeatureFallbackResult:
        """
        Compute robust scale according to the exact four-tier hierarchy.
        Strictly prohibits manufactured scale, silent zeros, or arbitrary epsilon.
        """
        clean_vals = values[np.isfinite(values)]
        if len(clean_vals) == 0:
            return FeatureFallbackResult(
                feature_name=feature_name,
                channel=channel,
                median=0.0,
                scale=None,
                method="EXCLUDED",
                is_active=False,
                exclusion_reason="NO_FINITE_OBSERVATIONS",
            )

        med = float(np.median(clean_vals))

        # -------------------------------------------------------------
        # Tier 1: MAD
        # -------------------------------------------------------------
        mad = float(np.median(np.abs(clean_vals - med)))
        mad_scale = MAD_SCALE_FACTOR * mad
        if np.isfinite(mad_scale) and mad_scale > 0.0:
            return FeatureFallbackResult(
                feature_name=feature_name,
                channel=channel,
                median=med,
                scale=mad_scale,
                method="MAD",
                is_active=True,
            )

        # -------------------------------------------------------------
        # Tier 2: IQR
        # -------------------------------------------------------------
        q75, q25 = np.percentile(clean_vals, [75, 25])
        iqr = float(q75 - q25)
        iqr_scale = iqr / IQR_DIVISOR
        if np.isfinite(iqr_scale) and iqr_scale > 0.0:
            return FeatureFallbackResult(
                feature_name=feature_name,
                channel=channel,
                median=med,
                scale=iqr_scale,
                method="IQR",
                is_active=True,
            )

        # -------------------------------------------------------------
        # Tier 3: Positive-Subset Sample Standard Deviation
        # -------------------------------------------------------------
        pos_subset = clean_vals[clean_vals > 0.0]
        if len(pos_subset) >= min_pos_obs:
            pos_std = float(np.std(pos_subset, ddof=1))
            if np.isfinite(pos_std) and pos_std > 0.0:
                return FeatureFallbackResult(
                    feature_name=feature_name,
                    channel=channel,
                    median=med,
                    scale=pos_std,
                    method="positive_subset_dispersion",
                    is_active=True,
                )

        # -------------------------------------------------------------
        # Tier 4: Feature Exclusion (No arbitrary epsilon)
        # -------------------------------------------------------------
        reason = "ZERO_OR_INVALID_DISPERSION_ACROSS_ALL_FALLBACK_TIERS"
        if len(pos_subset) < min_pos_obs and (mad_scale == 0.0 or iqr_scale == 0.0):
            reason = f"ZERO_DISPERSION_AND_INSUFFICIENT_POSITIVE_OBSERVATIONS_{len(pos_subset)}_LT_{min_pos_obs}"

        return FeatureFallbackResult(
            feature_name=feature_name,
            channel=channel,
            median=med,
            scale=None,
            method="EXCLUDED",
            is_active=False,
            exclusion_reason=reason,
        )

    def fit(self, reference_df: pd.DataFrame) -> "AnomalyPreprocessor":
        """
        Fit robust channel-conditioned baselines on reference data.
        Enforces separate parameters for TRANSFER and CASH_OUT.
        """
        self.validate_inputs(reference_df, require_row_index=False)
        if "type" not in reference_df.columns:
            raise ValueError("Reference DataFrame must contain 'type' column for channel conditioning.")

        self.channel_baselines = {}
        for channel in sorted(list(ELIGIBLE_CHANNELS)):
            ch_mask = reference_df["type"] == channel
            ch_df = reference_df.loc[ch_mask]
            baselines: Dict[str, FeatureFallbackResult] = {}

            if len(ch_df) == 0:
                # Channel empty in reference fold
                for feat in self.expected_features:
                    baselines[feat] = FeatureFallbackResult(
                        feature_name=feat,
                        channel=channel,
                        median=0.0,
                        scale=None,
                        method="EXCLUDED",
                        is_active=False,
                        exclusion_reason="EMPTY_CHANNEL_REFERENCE_FOLD",
                    )
            else:
                for feat in self.expected_features:
                    vals = ch_df[feat].to_numpy(dtype=float)
                    baselines[feat] = self.compute_feature_dispersion(
                        vals,
                        feature_name=feat,
                        channel=channel,
                        min_pos_obs=self.min_pos_obs,
                    )

            self.channel_baselines[channel] = baselines

        self.is_fitted = True
        return self

    def get_active_features(self, channel: str) -> List[str]:
        """Return list of active feature names for the given channel."""
        if not self.is_fitted:
            raise RuntimeError("AnomalyPreprocessor must be fitted before querying active features.")
        if channel not in self.channel_baselines:
            return []
        return [
            feat for feat, res in self.channel_baselines[channel].items()
            if res.is_active and res.scale is not None and res.scale > 0.0
        ]

    def transform_channel(
        self,
        df: pd.DataFrame,
        channel: str,
    ) -> Tuple[np.ndarray, List[str], np.ndarray]:
        """
        Robustly standardize active features for a single channel slice.

        Returns:
            X_robust: Array of shape (n_samples, n_active_features) with z_j(x) = (x_j - median_j) / scale_j
            active_feature_names: List of active feature names
            composite_z_scores: Mean robust deviation across active features (1/|A|) * sum |z_j|
        """
        if not self.is_fitted:
            raise RuntimeError("AnomalyPreprocessor must be fitted before transforming.")

        active_feats = self.get_active_features(channel)
        n_samples = len(df)

        if not active_feats or n_samples == 0:
            return np.empty((n_samples, 0)), [], np.zeros(n_samples)

        baselines = self.channel_baselines[channel]
        robust_cols = []
        abs_z_cols = []

        for feat in active_feats:
            res = baselines[feat]
            raw_vals = df[feat].to_numpy(dtype=float)
            # z = (x - median) / scale
            z = (raw_vals - res.median) / res.scale
            robust_cols.append(z)
            abs_z_cols.append(np.abs(z))

        X_robust = np.column_stack(robust_cols)
        # Composite score: mean across active features
        composite_z = np.mean(np.column_stack(abs_z_cols), axis=1)

        return X_robust, active_feats, composite_z

