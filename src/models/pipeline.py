"""
ML Risk Modeling Pipeline Orchestrator.

Coordinates data loading, temporal splitting, baseline and candidate training,
probability calibration, threshold optimization, error analysis, and artifact serialization.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
import yaml

from src.features.metadata import FEATURE_CATALOG
from src.models.artifacts import ModelArtifactManager
from src.models.calibration import RiskCalibrator
from src.models.evaluation import ModelEvaluator
from src.models.inference import RiskPredictor
from src.models.preprocessor import ModelFeaturePreprocessor
from src.models.split import TemporalSplitter
from src.models.threshold import ThresholdOptimizer
from src.models.trainer import ModelTrainer


def get_logger(name: str = "MLPipeline") -> logging.Logger:
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


class MLRiskPipeline:
    """
    End-to-end training, validation, and benchmarking pipeline for fraud risk models.
    """

    def __init__(self, config_path: str = "configs/modeling.yaml"):
        self.config_path = config_path
        self.logger = get_logger()
        self.config: Dict[str, Any] = {}

        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    self.config = loaded

        split_cfg = self.config.get("splitting", {})
        self.train_max_step = split_cfg.get("train_max_step", 400)
        self.val_max_step = split_cfg.get("val_max_step", 550)
        self.test_max_step = split_cfg.get("test_max_step", 743)
        self.random_seed = self.config.get("random_seed", 42)

        data_cfg = self.config.get("data", {})
        self.default_data_path = data_cfg.get("features_parquet", "data/processed/paysim_features_full.parquet")
        self.artifacts_dir = data_cfg.get("artifacts_dir", "models/risk_model_v1")
        self.reports_dir = data_cfg.get("reports_dir", "reports")

    def run(
        self,
        data_path: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
        models_to_train: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Execute full training, evaluation, calibration, and artifact generation run.
        """
        start_time = time.time()
        data_path = data_path or self.default_data_path
        artifacts_dir = artifacts_dir or self.artifacts_dir
        reports_dir = reports_dir or self.reports_dir
        models_to_train = models_to_train or ["dummy_baseline", "logistic_regression", "lightgbm", "xgboost"]

        os.makedirs(artifacts_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        self.logger.info(f"Loading feature dataset from '{data_path}'...")
        if data_path.endswith(".parquet"):
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)

        self.logger.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns.")

        # 1. Temporal Splitting
        self.logger.info(
            f"Partitioning data chronologically: Train (<= {self.train_max_step}), "
            f"Val ({self.train_max_step + 1}–{self.val_max_step}), "
            f"Test ({self.val_max_step + 1}–{self.test_max_step})..."
        )
        splitter = TemporalSplitter(
            train_max_step=self.train_max_step,
            val_max_step=self.val_max_step,
            test_max_step=self.test_max_step,
        )
        (X_train, y_train), (X_val, y_val), (X_test, y_test), split_summaries = splitter.split(df)

        for name, summary in split_summaries.items():
            self.logger.info(
                f"Split '{name}': {summary.total_count:,} rows, {summary.fraud_count:,} frauds ({summary.fraud_rate_pct:.3f}%) | steps {summary.min_step}–{summary.max_step}"
            )

        # 2. Training Models
        trainer = ModelTrainer(random_state=self.random_seed)
        model_results = {}

        if "dummy_baseline" in models_to_train:
            self.logger.info("Training Dummy Prior Reference Baseline...")
            trainer.train_dummy_baseline(X_train, y_train)

        if "logistic_regression" in models_to_train:
            self.logger.info("Training Logistic Regression (StandardScaler + Balanced)...")
            lr_cfg = self.config.get("models", {}).get("baseline_logistic", {})
            trainer.train_logistic_baseline(
                X_train,
                y_train,
                max_iter=lr_cfg.get("max_iter", 500),
                class_weight=lr_cfg.get("class_weight", "balanced"),
                C=lr_cfg.get("C", 1.0),
            )

        if "lightgbm" in models_to_train:
            self.logger.info("Training LightGBM Champion Model...")
            lgb_cfg = self.config.get("models", {}).get("champion_lightgbm", {})
            trainer.train_lightgbm(
                X_train,
                y_train,
                n_estimators=lgb_cfg.get("n_estimators", 100),
                learning_rate=lgb_cfg.get("learning_rate", 0.05),
                max_depth=lgb_cfg.get("max_depth", 6),
                num_leaves=lgb_cfg.get("num_leaves", 31),
                scale_pos_weight=lgb_cfg.get("scale_pos_weight", 1.0),
            )

        if "xgboost" in models_to_train:
            self.logger.info("Training XGBoost Challenger Model...")
            xgb_cfg = self.config.get("models", {}).get("challenger_xgboost", {})
            trainer.train_xgboost(
                X_train,
                y_train,
                n_estimators=xgb_cfg.get("n_estimators", 100),
                learning_rate=xgb_cfg.get("learning_rate", 0.05),
                max_depth=xgb_cfg.get("max_depth", 6),
                scale_pos_weight=xgb_cfg.get("scale_pos_weight", 1.0),
            )

        # 3. Model Comparison & Evaluation
        self.logger.info("Evaluating all models across Train, Validation, and Test splits...")
        evaluator = ModelEvaluator()

        for m_name in trainer.trained_models.keys():
            t_train_prob = trainer.predict_proba(m_name, X_train)
            t_val_prob = trainer.predict_proba(m_name, X_val)
            t_test_prob = trainer.predict_proba(m_name, X_test)

            eval_train = evaluator.evaluate_predictions(y_train, t_train_prob, threshold=0.5)
            eval_val = evaluator.evaluate_predictions(y_val, t_val_prob, threshold=0.5)
            eval_test = evaluator.evaluate_predictions(y_test, t_test_prob, threshold=0.5)

            model_results[m_name] = {
                "training_time_seconds": trainer.training_times.get(m_name, 0.0),
                "train_metrics": eval_train,
                "val_metrics": eval_val,
                "test_metrics": eval_test,
            }
            self.logger.info(
                f"Model [{m_name}] -> Val PR-AUC: {eval_val['pr_auc']:.5f}, Val ROC-AUC: {eval_val['roc_auc']:.5f} | "
                f"Test PR-AUC: {eval_test['pr_auc']:.5f}, Test ROC-AUC: {eval_test['roc_auc']:.5f}"
            )

        # 4. Champion Selection, Calibration, and Threshold Optimization
        champion_name = "lightgbm" if "lightgbm" in trainer.trained_models else list(trainer.trained_models.keys())[-1]
        self.logger.info(f"Selecting Champion Model: '{champion_name}'")

        champion_model = trainer.trained_models[champion_name]
        champion_prep = trainer.preprocessors[champion_name]

        # Raw probabilities for champion
        val_probs = trainer.predict_proba(champion_name, X_val)
        test_probs = trainer.predict_proba(champion_name, X_test)

        # Fit probability calibrator on validation fold
        self.logger.info("Fitting RiskCalibrator on Validation fold...")
        calibrator = RiskCalibrator(method="sigmoid")
        calibrator.fit(y_val, val_probs)
        self.logger.info(
            f"Calibrator diagnostics: Brier score {calibrator.diagnostics['raw_brier_score']:.6f} -> "
            f"{calibrator.diagnostics['calibrated_brier_score']:.6f} (improvement: {calibrator.diagnostics['brier_improvement']:.6f})"
        )

        cal_val_probs = calibrator.predict_proba(val_probs)
        cal_test_probs = calibrator.predict_proba(test_probs)

        # Fit threshold optimizer strictly on validation fold
        self.logger.info("Optimizing decision thresholds on Validation fold...")
        threshold_optimizer = ThresholdOptimizer(target_metric="f1")
        threshold_optimizer.fit(y_val, cal_val_probs)
        opt_thresh = threshold_optimizer.optimal_threshold
        self.logger.info(
            f"Optimal validation threshold selected: {opt_thresh:.4f} "
            f"(Val F1: {threshold_optimizer.optimization_summary['max_f1_candidate']['f1_score']:.5f})"
        )

        # Evaluate Champion with optimal threshold and calibrated probabilities on Test Set
        champion_test_eval = evaluator.evaluate_predictions(y_test, cal_test_probs, threshold=opt_thresh)
        self.logger.info(
            f"Champion Final Test Evaluation (at threshold {opt_thresh:.4f}): "
            f"Precision: {champion_test_eval['precision']:.5f}, Recall: {champion_test_eval['recall']:.5f}, "
            f"F1: {champion_test_eval['f1_score']:.5f}, PR-AUC: {champion_test_eval['pr_auc']:.5f}, "
            f"ROC-AUC: {champion_test_eval['roc_auc']:.5f}"
        )

        # Error Analysis on Test Set
        self.logger.info("Performing Error Analysis on Test set...")
        error_analysis = evaluator.perform_error_analysis(X_test, y_test, cal_test_probs, threshold=opt_thresh)

        # 5. Save Artifact Bundle
        metadata = {
            "model_version": self.config.get("version", "1.0.0"),
            "dataset_version": "paysim_v0.1.0",
            "champion_model": champion_name,
            "created_at": datetime.now().isoformat(),
            "random_seed": self.random_seed,
            "feature_names": list(FEATURE_CATALOG.keys()),
            "feature_count": len(FEATURE_CATALOG),
            "temporal_split": {k: v.__dict__ for k, v in split_summaries.items()},
            "threshold_policy": threshold_optimizer.optimization_summary,
            "calibration_diagnostics": calibrator.diagnostics,
            "champion_test_metrics": champion_test_eval,
            "error_analysis_summary": {
                "false_positives": error_analysis["false_positive_count"],
                "false_negatives": error_analysis["false_negative_count"],
                "channel_error_breakdown": error_analysis["channel_error_breakdown"],
            },
        }

        self.logger.info(f"Saving Champion model bundle to '{artifacts_dir}'...")
        saved_paths = ModelArtifactManager.save_bundle(
            artifact_dir=artifacts_dir,
            model=champion_model,
            preprocessor=champion_prep,
            calibrator=calibrator,
            threshold_optimizer=threshold_optimizer,
            metadata=metadata,
        )

        # Save machine-readable evaluation report
        report_data = {
            "execution_timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "dataset_path": data_path,
            "split_summaries": {k: v.__dict__ for k, v in split_summaries.items()},
            "model_comparison": model_results,
            "champion_evaluation": {
                "model_name": champion_name,
                "threshold": opt_thresh,
                "test_metrics": champion_test_eval,
                "calibration": calibrator.diagnostics,
                "error_analysis": error_analysis,
            },
            "saved_artifacts": saved_paths,
        }

        report_path = os.path.join(reports_dir, "ml_risk_modeling_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"Evaluation report saved to '{report_path}'. Pipeline completed in {report_data['elapsed_seconds']}s.")

        return report_data
