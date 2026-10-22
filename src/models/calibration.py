"""
Probability Calibration and Diagnostics module.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss


class RiskCalibrator:
    """
    Fits and applies post-hoc probability calibration strictly on validation data.
    Provides diagnostic reliability curves and Brier score evaluation.
    """

    def __init__(self, method: str = "sigmoid"):
        if method not in ("sigmoid", "isotonic"):
            raise ValueError(f"Unsupported calibration method: {method}. Use 'sigmoid' or 'isotonic'.")
        self.method = method
        self.calibrator: Optional[Any] = None
        self.is_fitted: bool = False
        self.diagnostics: Dict[str, Any] = {}

    def fit(self, y_val: pd.Series, y_val_prob: np.ndarray) -> "RiskCalibrator":
        """Fit calibrator mapping raw model probabilities to calibrated probabilities."""
        y_val = np.asarray(y_val).astype(int)
        y_val_prob = np.asarray(y_val_prob).astype(float)

        raw_brier = float(brier_score_loss(y_val, y_val_prob))

        if self.method == "sigmoid":
            # Platt scaling: Logistic regression on logit or probability
            self.calibrator = LogisticRegression(C=1.0, solver="lbfgs")
            self.calibrator.fit(y_val_prob.reshape(-1, 1), y_val)
        else:
            # Isotonic non-parametric calibration
            self.calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self.calibrator.fit(y_val_prob, y_val)

        calibrated_probs = self.predict_proba(y_val_prob)
        calibrated_brier = float(brier_score_loss(y_val, calibrated_probs))

        # Calibration curve points (5 bins for extreme imbalance)
        prob_true, prob_pred = calibration_curve(y_val, calibrated_probs, n_bins=5, strategy="uniform")

        self.diagnostics = {
            "method": self.method,
            "raw_brier_score": round(raw_brier, 6),
            "calibrated_brier_score": round(calibrated_brier, 6),
            "brier_improvement": round(raw_brier - calibrated_brier, 6),
            "calibration_curve": {
                "prob_true": [round(float(v), 4) for v in prob_true],
                "prob_pred": [round(float(v), 4) for v in prob_pred],
            },
        }

        self.is_fitted = True
        return self

    def predict_proba(self, probs: np.ndarray) -> np.ndarray:
        """Calibrate an array or scalar of raw probabilities."""
        probs = np.asarray(probs).astype(float)
        if not self.is_fitted or self.calibrator is None:
            return probs

        if self.method == "sigmoid":
            return self.calibrator.predict_proba(probs.reshape(-1, 1))[:, 1]
        else:
            return self.calibrator.predict(probs)
