"""
Production Risk Scoring Inference Engine and Prediction Interface.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.features.policy import STRICTLY_EXCLUDED_FIELDS
from src.features.metadata import FEATURE_CATALOG
from src.models.artifacts import ModelArtifactManager


class RiskPredictor:
    """
    Production inference interface for real-time transaction scoring.
    Loads trained artifact bundles, validates input schema, enforces zero-leakage,
    and returns risk scores, levels, and decision recommendations.
    """

    def __init__(
        self,
        model: Any,
        preprocessor: Any,
        calibrator: Optional[Any] = None,
        threshold_optimizer: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.calibrator = calibrator
        self.threshold_optimizer = threshold_optimizer
        self.metadata = metadata or {}
        self.expected_features = list(FEATURE_CATALOG.keys())

    @classmethod
    def load(cls, artifact_dir: str) -> "RiskPredictor":
        """Load fitted model bundle and instantiate RiskPredictor."""
        bundle = ModelArtifactManager.load_bundle(artifact_dir)
        return cls(
            model=bundle["model"],
            preprocessor=bundle["preprocessor"],
            calibrator=bundle.get("calibrator"),
            threshold_optimizer=bundle.get("threshold_optimizer"),
            metadata=bundle.get("metadata", {}),
        )

    def _prepare_dataframe(self, data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame]) -> Tuple[pd.DataFrame, bool]:
        """Convert input data to DataFrame and record whether single-record input was provided."""
        is_single = False
        if isinstance(data, dict):
            df = pd.DataFrame([data])
            is_single = True
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise TypeError(f"Unsupported data type for scoring: {type(data)}. Expected dict, list of dicts, or DataFrame.")

        # 1. Enforce strict leakage boundary
        cols = set(df.columns)
        leakage = cols.intersection(STRICTLY_EXCLUDED_FIELDS)
        if leakage:
            raise ValueError(
                f"Prediction Security Violation: Input contains prohibited fields: {sorted(list(leakage))}"
            )

        # 2. Check for missing required features
        missing = [f for f in self.expected_features if f not in cols]
        if missing:
            raise ValueError(
                f"Missing required model input features ({len(missing)} missing): {missing}"
            )

        return df[self.expected_features], is_single

    def predict_proba(self, data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame]) -> Union[float, np.ndarray]:
        """Generate calibrated probability of fraud."""
        df_clean, is_single = self._prepare_dataframe(data)
        X_tf = self.preprocessor.transform(df_clean)

        raw_probs = self.model.predict_proba(X_tf)[:, 1]

        if self.calibrator is not None and getattr(self.calibrator, "is_fitted", False):
            probs = self.calibrator.predict_proba(raw_probs)
        else:
            probs = raw_probs

        if is_single:
            return float(probs[0])
        return probs

    def predict_score(self, data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame]) -> Union[int, np.ndarray]:
        """Generate 0–100 integer risk score."""
        probs = self.predict_proba(data)
        if isinstance(probs, (float, np.floating)):
            return int(np.clip(round(probs * 100), 0, 100))
        return np.clip(np.round(probs * 100), 0, 100).astype(int)

    def predict_decision(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Generate full risk decision recommendations:
          - risk_score: calibrated probability [0.0, 1.0]
          - risk_score_100: integer score [0, 100]
          - risk_level: LOW / MEDIUM / HIGH
          - decision: APPROVE / MONITOR / MANUAL_INVESTIGATION
          - is_fraud_flagged: 1 if >= optimal threshold else 0
        """
        df_clean, is_single = self._prepare_dataframe(data)
        probs = self.predict_proba(df_clean)

        if self.threshold_optimizer is not None:
            results_df = self.threshold_optimizer.classify_batch(probs)
        else:
            # Default thresholds if optimizer absent
            policy = self.metadata.get("threshold_policy", {})
            thresh = policy.get("selected_operating_threshold", self.metadata.get("threshold", 0.5))
            high_thresh = policy.get("high_risk_threshold", 0.70)
            low_thresh = policy.get("low_risk_threshold", 0.30)
            scores_100 = np.clip(np.round(probs * 100), 0, 100).astype(int)
            decisions = np.where(probs >= high_thresh, "MANUAL_INVESTIGATION", np.where(probs >= low_thresh, "MONITOR", "APPROVE"))
            levels = np.where(probs >= high_thresh, "HIGH", np.where(probs >= low_thresh, "MEDIUM", "LOW"))
            flags = (probs >= thresh).astype(int)
            results_df = pd.DataFrame({
                "risk_score": probs,
                "risk_score_100": scores_100,
                "risk_level": levels,
                "decision": decisions,
                "is_fraud_flagged": flags,
            })

        if is_single:
            row = results_df.iloc[0]
            return {
                "risk_score": round(float(row["risk_score"]), 6),
                "risk_score_100": int(row["risk_score_100"]),
                "risk_level": str(row["risk_level"]),
                "decision": str(row["decision"]),
                "is_fraud_flagged": int(row["is_fraud_flagged"]),
            }
        return results_df

    def get_feature_names(self) -> List[str]:
        """Return the canonical list of 36 expected input features."""
        return list(self.expected_features)

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata associated with the loaded model."""
        return dict(self.metadata)
