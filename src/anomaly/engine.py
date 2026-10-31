"""
Phase 05 Standalone Anomaly Detection Engine Orchestrator.

Integrates input validation, channel-conditioned robust preprocessing with
the four-tier fallback hierarchy, IsolationForest scoring, global alert-budget
enforcement, and generation of the decoupled eight-field transaction output contract.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.anomaly.config import AnomalyConfig, load_anomaly_config
from src.anomaly.schema import (
    CURRENT_SCHEMA_VERSION,
    AnomalyOutputRow,
    AnomalyOutputSchema,
    AnomalyStatus,
    EligibleChannel,
    ReasonCode,
    validate_output_row,
)
from src.anomaly.preprocessing import AnomalyPreprocessor, ELIGIBLE_CHANNELS
from src.anomaly.detector import IsolationForestDetector
from src.anomaly.budget import AlertBudgetSelector, BudgetResult


class AnomalyDetectionEngine:
    """
    End-to-end production anomaly detection engine.
    Produces independent transaction-level anomaly results without modifying Phase 04.
    """

    def __init__(
        self,
        config: Optional[AnomalyConfig] = None,
        config_path: str = "configs/anomaly_detection.yaml",
        verify_provenance: bool = True,
    ):
        if config is not None:
            self.config = config
        else:
            self.config = load_anomaly_config(config_path, verify_provenance=verify_provenance)

        self.preprocessor = AnomalyPreprocessor(
            expected_features=self.config.feature_names,
        )
        self.detectors: Dict[str, IsolationForestDetector] = {}
        self.budget_selector = AlertBudgetSelector(
            budget_rate=self.config.budget_rate,
        )
        self.is_fitted: bool = False
        self.reference_max_step: Optional[int] = None

    def fit(self, reference_df: pd.DataFrame) -> "AnomalyDetectionEngine":
        """
        Fit channel-conditioned baselines and IsolationForest detectors on reference data.

        Args:
            reference_df: Training or reference DataFrame containing 36 features and 'type'.
        """
        # Validate temporal boundaries if 'step' is present in reference data
        if "step" in reference_df.columns:
            max_ref = int(reference_df["step"].max())
            train_max_step = self.config.raw_dict.get("reproducibility", {}).get(
                "temporal_partitions", {}
            ).get("train_max_step", 400)
            if max_ref > train_max_step:
                raise ValueError(
                    f"Temporal Leakage Violation: reference data contains step {max_ref} "
                    f"exceeding train_max_step ({train_max_step})."
                )
            self.reference_max_step = max_ref

        # 1. Fit robust preprocessor on reference population
        self.preprocessor.fit(reference_df)

        # 2. Fit channel-specific IsolationForest models
        self.detectors = {}
        for channel in sorted(list(ELIGIBLE_CHANNELS)):
            ch_mask = reference_df["type"] == channel
            ch_df = reference_df.loc[ch_mask]
            active_feats = self.preprocessor.get_active_features(channel)

            if len(ch_df) == 0 or len(active_feats) == 0:
                continue

            X_robust, _, _ = self.preprocessor.transform_channel(ch_df, channel)
            detector = IsolationForestDetector.from_config(self.config.detector_hyperparameters)
            detector.fit(X_robust)
            self.detectors[channel] = detector

        self.is_fitted = True
        return self

    def score(
        self,
        df: pd.DataFrame,
        enforce_temporal_split: bool = False,
    ) -> Tuple[List[AnomalyOutputRow], pd.DataFrame, BudgetResult]:
        """
        Score a batch of transactions and apply the global alert budget.

        Args:
            df: DataFrame containing 'row_index', 'type', and the 36 canonical features.
            enforce_temporal_split: If True, asserts min(df['step']) > reference_max_step.

        Returns:
            Tuple of:
              - List[AnomalyOutputRow]
              - pd.DataFrame (the exact eight-field schema)
              - BudgetResult (run-level population summary)
        """
        if not self.is_fitted:
            raise RuntimeError("AnomalyDetectionEngine must be fitted on reference data before scoring.")

        # 1. Validate inputs and zero-leakage contract
        self.preprocessor.validate_inputs(df, require_row_index=True)
        if "type" not in df.columns:
            raise ValueError("Input scoring DataFrame must contain 'type' column.")

        # 2. Enforce strict temporal ordering if requested
        if enforce_temporal_split and "step" in df.columns and self.reference_max_step is not None:
            min_score_step = int(df["step"].min())
            if min_score_step <= self.reference_max_step:
                raise ValueError(
                    f"Temporal Ordering Violation: scoring data contains step {min_score_step} "
                    f"<= reference_max_step ({self.reference_max_step})."
                )

        # 3. Handle empty input gracefully
        if df.empty:
            final_rows, budget_summary = self.budget_selector.select_alerts(
                scored_rows=[],
                degraded_rows=[],
                ineligible_count=0,
            )
            return final_rows, AnomalyOutputSchema.to_dataframe(final_rows), budget_summary

        scored_candidates: List[AnomalyOutputRow] = []
        degraded_candidates: List[AnomalyOutputRow] = []
        ineligible_count: int = int((~df["type"].isin(ELIGIBLE_CHANNELS)).sum())

        # 4. Vectorized scoring by channel for high throughput
        for ch in sorted(list(ELIGIBLE_CHANNELS)):
            ch_mask = df["type"] == ch
            ch_df = df.loc[ch_mask]
            if ch_df.empty:
                continue

            active_feats = self.preprocessor.get_active_features(ch)
            row_indices = ch_df["row_index"].to_numpy(dtype=int)

            # All-Inactive Features Condition -> DEGRADED_UNSCORABLE
            if len(active_feats) == 0 or ch not in self.detectors:
                for r_idx in row_indices:
                    degraded_candidates.append(
                        AnomalyOutputSchema.create_degraded_row(
                            row_index=int(r_idx),
                            channel=ch,
                            reason_code=ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value,
                            schema_version=CURRENT_SCHEMA_VERSION,
                        )
                    )
                continue

            # Vectorized transform and IsolationForest scoring
            X_robust, _, _ = self.preprocessor.transform_channel(ch_df, ch)
            raw_scores = self.detectors[ch].score_samples(X_robust)

            for r_idx, score in zip(row_indices, raw_scores):
                candidate_row = AnomalyOutputRow(
                    schema_version=CURRENT_SCHEMA_VERSION,
                    row_index=int(r_idx),
                    channel=ch,
                    anomaly_score=float(score),
                    is_anomaly_flagged=False,
                    anomaly_status=AnomalyStatus.SCORED.value,
                    reason_code=None,
                    alert_budget_selected=False,
                )
                scored_candidates.append(candidate_row)

        # 5. Global Alert Budget Selection
        unscored_eligible_count = len(degraded_candidates)
        final_rows, budget_summary = self.budget_selector.select_alerts(
            scored_rows=scored_candidates,
            degraded_rows=degraded_candidates,
            ineligible_count=ineligible_count,
            unscored_eligible_count=unscored_eligible_count,
        )

        output_df = AnomalyOutputSchema.to_dataframe(final_rows)
        return final_rows, output_df, budget_summary

