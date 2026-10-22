"""
Decision Threshold Optimization and Multi-Tier Risk Policy.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve


class ThresholdOptimizer:
    """
    Selects operational decision thresholds strictly on validation data.
    Provides multi-tier decision mapping:
      - APPROVE (Low Risk)
      - MONITOR (Medium Risk / Anomaly)
      - MANUAL_INVESTIGATION (High Risk / Fraud Suspect)
    """

    def __init__(
        self,
        target_metric: str = "f1",
        min_recall_constraint: float = 0.95,
        max_fpr_constraint: float = 0.001,
    ):
        self.target_metric = target_metric
        self.min_recall_constraint = min_recall_constraint
        self.max_fpr_constraint = max_fpr_constraint
        self.optimal_threshold: float = 0.5
        self.low_threshold: float = 0.30
        self.high_threshold: float = 0.70
        self.optimization_summary: Dict[str, Any] = {}

    def fit(self, y_val: pd.Series, y_val_prob: np.ndarray) -> "ThresholdOptimizer":
        """
        Optimize threshold strictly using validation probabilities.
        Never touches test data.
        """
        y_val = np.asarray(y_val).astype(int)
        y_val_prob = np.asarray(y_val_prob).astype(float)

        precisions, recalls, thresholds = precision_recall_curve(y_val, y_val_prob)
        # Avoid division by zero
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-12)

        # 1. Optimal F1 threshold
        best_f1_idx = int(np.argmax(f1_scores[:-1])) if len(thresholds) > 0 else 0
        opt_thresh_f1 = float(thresholds[best_f1_idx]) if len(thresholds) > 0 else 0.5
        best_f1 = float(f1_scores[best_f1_idx]) if len(thresholds) > 0 else 0.0

        # 2. Constrained Recall Threshold (Recall >= min_recall_constraint)
        valid_rec_indices = np.where(recalls[:-1] >= self.min_recall_constraint)[0]
        if len(valid_rec_indices) > 0:
            # Pick highest threshold that maintains target recall
            rec_constrained_idx = valid_rec_indices[-1]
            rec_thresh = float(thresholds[rec_constrained_idx])
            rec_prec = float(precisions[rec_constrained_idx])
            rec_val = float(recalls[rec_constrained_idx])
        else:
            rec_thresh = 0.5
            rec_prec = 0.0
            rec_val = 0.0

        # 3. Constrained FPR Threshold (FPR <= max_fpr_constraint)
        fpr, tpr, roc_thresholds = roc_curve(y_val, y_val_prob)
        valid_fpr_indices = np.where(fpr <= self.max_fpr_constraint)[0]
        if len(valid_fpr_indices) > 0:
            # Pick the lowest threshold within permitted FPR
            fpr_constrained_idx = valid_fpr_indices[-1]
            fpr_thresh = float(roc_thresholds[fpr_constrained_idx])
            fpr_tpr = float(tpr[fpr_constrained_idx])
            actual_fpr = float(fpr[fpr_constrained_idx])
        else:
            fpr_thresh = 0.5
            fpr_tpr = 0.0
            actual_fpr = 0.0

        if self.target_metric == "f1":
            self.optimal_threshold = opt_thresh_f1
        elif self.target_metric == "recall":
            self.optimal_threshold = rec_thresh
        elif self.target_metric == "fpr":
            self.optimal_threshold = fpr_thresh
        else:
            self.optimal_threshold = opt_thresh_f1

        # Multi-tier risk boundaries
        self.high_threshold = max(0.50, self.optimal_threshold)
        self.low_threshold = min(0.30, self.high_threshold * 0.5)

        self.optimization_summary = {
            "selected_operating_threshold": round(self.optimal_threshold, 4),
            "low_risk_threshold": round(self.low_threshold, 4),
            "high_risk_threshold": round(self.high_threshold, 4),
            "max_f1_candidate": {
                "threshold": round(opt_thresh_f1, 4),
                "f1_score": round(best_f1, 5),
                "precision": round(float(precisions[best_f1_idx]), 5),
                "recall": round(float(recalls[best_f1_idx]), 5),
            },
            "recall_constrained_candidate": {
                "min_recall_target": self.min_recall_constraint,
                "threshold": round(rec_thresh, 4),
                "actual_recall": round(rec_val, 5),
                "precision": round(rec_prec, 5),
            },
            "fpr_constrained_candidate": {
                "max_fpr_target": self.max_fpr_constraint,
                "threshold": round(fpr_thresh, 4),
                "actual_fpr": round(actual_fpr, 6),
                "recall": round(fpr_tpr, 5),
            },
        }

        return self

    def classify_probability(
        self,
        prob: float,
    ) -> Tuple[str, str, int]:
        """
        Map a single probability to (decision, risk_level, binary_flag).
        """
        if prob >= self.high_threshold:
            return "MANUAL_INVESTIGATION", "HIGH", 1
        elif prob >= self.low_threshold:
            return "MONITOR", "MEDIUM", 0
        else:
            return "APPROVE", "LOW", 0

    def classify_batch(
        self,
        probs: np.ndarray,
    ) -> pd.DataFrame:
        """
        Map array of probabilities to structured decision DataFrame.
        """
        probs = np.asarray(probs).astype(float)
        risk_scores_100 = np.clip(np.round(probs * 100), 0, 100).astype(int)

        decisions = np.where(
            probs >= self.high_threshold,
            "MANUAL_INVESTIGATION",
            np.where(probs >= self.low_threshold, "MONITOR", "APPROVE"),
        )
        risk_levels = np.where(
            probs >= self.high_threshold,
            "HIGH",
            np.where(probs >= self.low_threshold, "MEDIUM", "LOW"),
        )
        flags = (probs >= self.optimal_threshold).astype(int)

        return pd.DataFrame(
            {
                "risk_score": probs,
                "risk_score_100": risk_scores_100,
                "risk_level": risk_levels,
                "decision": decisions,
                "is_fraud_flagged": flags,
            }
        )
