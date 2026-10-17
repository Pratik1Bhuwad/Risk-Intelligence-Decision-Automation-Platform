"""
Feature Engineering Pipeline orchestrator.

Executes all feature group transformers, validates feature quality,
and saves production-defensible feature sets and metadata manifests.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import yaml

from src.features.policy import (
    PREDICTION_EVENT,
    PREDICTION_POINT,
    PREDICTION_TIME_TEMPORAL_INDEX,
    SAME_STEP_POLICY,
    STRICTLY_EXCLUDED_FIELDS,
)
from src.features.metadata import FEATURE_CATALOG, get_feature_catalog_df
from src.features.transformers import (
    TransactionChannelTransformer,
    TemporalCyclicalTransformer,
    AmountBehaviorTransformer,
    OriginBalanceLiquidationTransformer,
    CounterpartyTypeTransformer,
    PointInTimeEntityVelocityTransformer,
)
from src.features.validator import FeatureQualityValidator


def get_logger(name: str = "FeaturePipeline") -> logging.Logger:
    """Configure console logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(handler)
    return logger


class FeaturePipeline:
    """
    Coordinates end-to-end feature engineering with strict leakage prevention.
    """

    def __init__(
        self,
        config_path: Optional[str] = "configs/feature_engineering.yaml",
        drain_tolerance: float = 0.01,
        velocity_window_steps: int = 24,
    ):
        self.config_path = config_path
        self.drain_tolerance = drain_tolerance
        self.velocity_window_steps = velocity_window_steps
        self.logger = get_logger()

        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if isinstance(cfg, dict):
                    tol = cfg.get("tolerance", {}).get("balance_drain_tolerance")
                    if tol is not None:
                        self.drain_tolerance = float(tol)
                    win = cfg.get("lookback_windows", {}).get("short_window_steps")
                    if win is not None:
                        self.velocity_window_steps = int(win)

        self.tx_channel_tf = TransactionChannelTransformer()
        self.temporal_tf = TemporalCyclicalTransformer()
        self.amount_tf = AmountBehaviorTransformer()
        self.balance_tf = OriginBalanceLiquidationTransformer(drain_tolerance=self.drain_tolerance)
        self.counterparty_tf = CounterpartyTypeTransformer()
        self.velocity_tf = PointInTimeEntityVelocityTransformer(window_steps=self.velocity_window_steps)
        self.validator = FeatureQualityValidator()

    def transform(
        self,
        df: pd.DataFrame,
        include_target_label: bool = False,
    ) -> pd.DataFrame:
        """
        Transform raw transaction DataFrame into leakage-safe feature DataFrame.
        """
        self.logger.info("Extracting Transaction Channel features...")
        f_tx = self.tx_channel_tf.transform(df)

        self.logger.info("Extracting Temporal & Cyclical features...")
        f_temp = self.temporal_tf.transform(df)

        self.logger.info("Extracting Amount Behavior features...")
        f_amt = self.amount_tf.transform(df)

        self.logger.info("Extracting Origin Balance & Liquidation features...")
        f_bal = self.balance_tf.transform(df)

        self.logger.info("Extracting Counterparty Type features...")
        f_cp = self.counterparty_tf.transform(df)

        self.logger.info(
            f"Extracting Point-in-Time Entity Velocity features (window={self.velocity_window_steps} steps, strict step < current_step)..."
        )
        f_vel = self.velocity_tf.transform(df)

        # Concatenate horizontally
        feature_df = pd.concat([f_tx, f_temp, f_amt, f_bal, f_cp, f_vel], axis=1)

        if include_target_label and "isFraud" in df.columns:
            feature_df["isFraud"] = df["isFraud"].values

        return feature_df

    def run(
        self,
        raw_csv_path: str,
        output_dir: str = "data/processed",
        nrows: Optional[int] = None,
        save_csv: bool = True,
        save_parquet: bool = True,
        include_target_label: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute full pipeline against dataset file, validate, and write outputs.
        """
        start_time = time.time()
        os.makedirs(output_dir, exist_ok=True)

        self.logger.info(f"Loading raw dataset from '{raw_csv_path}' (nrows={nrows})...")
        raw_df = pd.read_csv(raw_csv_path, nrows=nrows)
        self.logger.info(f"Loaded {len(raw_df):,} rows, {len(raw_df.columns)} columns.")

        # Transform
        feature_df = self.transform(raw_df, include_target_label=include_target_label)

        # Validate
        self.logger.info("Validating feature dataset quality and leakage constraints...")
        is_valid, report = self.validator.validate(
            raw_df=raw_df,
            feature_df=feature_df,
            allow_target_in_output=include_target_label,
        )

        if not is_valid:
            self.logger.error(f"Feature validation failed with errors: {report['errors']}")
            raise ValueError(f"Feature validation failed! Errors: {report['errors']}")

        self.logger.info("Feature validation PASSED successfully.")

        # Save outputs
        base_name = f"paysim_features_{len(raw_df)}" if nrows else "paysim_features_full"
        output_files = {}

        if save_parquet:
            pq_path = os.path.join(output_dir, f"{base_name}.parquet")
            self.logger.info(f"Saving Parquet to '{pq_path}'...")
            try:
                feature_df.to_parquet(pq_path, index=False)
                output_files["parquet"] = pq_path
            except Exception as e:
                self.logger.warning(f"Could not save parquet (missing pyarrow/fastparquet?): {e}")

        if save_csv:
            csv_path = os.path.join(output_dir, f"{base_name}.csv")
            self.logger.info(f"Saving CSV to '{csv_path}'...")
            feature_df.to_csv(csv_path, index=False)
            output_files["csv"] = csv_path

        # Save feature catalog documentation
        catalog_path = os.path.join(output_dir, "feature_catalog.csv")
        get_feature_catalog_df().to_csv(catalog_path, index=False)
        output_files["catalog_csv"] = catalog_path

        elapsed_sec = round(time.time() - start_time, 2)

        # Manifest
        manifest = {
            "execution_timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed_sec,
            "prediction_event": PREDICTION_EVENT,
            "prediction_point": PREDICTION_POINT,
            "prediction_time_temporal_index": PREDICTION_TIME_TEMPORAL_INDEX,
            "same_step_policy": SAME_STEP_POLICY,
            "input_file": raw_csv_path,
            "row_count": len(feature_df),
            "feature_count": len([c for c in feature_df.columns if c != "isFraud"]),
            "has_target_label": "isFraud" in feature_df.columns,
            "feature_columns": [c for c in feature_df.columns if c != "isFraud"],
            "validation_report": report,
            "output_files": output_files,
        }

        manifest_path = os.path.join(output_dir, "feature_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        self.logger.info(
            f"Feature engineering pipeline completed successfully in {elapsed_sec}s. Manifest saved to '{manifest_path}'."
        )

        return manifest
