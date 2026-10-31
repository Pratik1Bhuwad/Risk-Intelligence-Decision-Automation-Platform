"""
Phase 05 IsolationForest Anomaly Detector.

Wraps scikit-learn IsolationForest under Specification v2.3.2 and frozen configuration.
Enforces deterministic score convention: s_raw(x) = -score_samples(x).
"""

from typing import Any, Dict, Optional, Union
import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    """
    Deterministic IsolationForest outlier detector.
    Computes negated decision scores where higher scores indicate greater anomaly severity.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_samples: Union[str, int, float] = "auto",
        contamination: Union[str, float] = "auto",
        max_features: float = 1.0,
        bootstrap: bool = False,
        random_state: int = 42,
        n_jobs: int = 1,
        verbose: int = 0,
    ):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.verbose = verbose

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=self.contamination,
            max_features=self.max_features,
            bootstrap=self.bootstrap,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            verbose=self.verbose,
        )
        self.is_fitted: bool = False
        self.n_features_in_: int = 0

    @classmethod
    def from_config(cls, hyperparameters: Dict[str, Any]) -> "IsolationForestDetector":
        """Instantiate detector from configuration dictionary."""
        return cls(
            n_estimators=int(hyperparameters.get("n_estimators", 100)),
            max_samples=hyperparameters.get("max_samples", "auto"),
            contamination=hyperparameters.get("contamination", "auto"),
            max_features=float(hyperparameters.get("max_features", 1.0)),
            bootstrap=bool(hyperparameters.get("bootstrap", False)),
            random_state=int(hyperparameters.get("random_state", 42)),
            n_jobs=int(hyperparameters.get("n_jobs", 1)),
            verbose=int(hyperparameters.get("verbose", 0)),
        )

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        """
        Fit IsolationForest model on standardized reference feature matrix.

        Args:
            X: 2D array of shape (n_samples, n_features). Must be non-empty.
        """
        if X.ndim != 2:
            raise ValueError(f"Input feature matrix must be 2-dimensional, got ndim={X.ndim}")
        n_samples, n_features = X.shape
        if n_samples == 0:
            raise ValueError("Cannot fit IsolationForest on empty sample matrix (0 samples).")
        if n_features == 0:
            raise ValueError("Cannot fit IsolationForest with 0 active features.")

        # Check for NaN / infinite values
        if not np.all(np.isfinite(X)):
            raise ValueError("Feature matrix contains non-finite values (NaN/Inf).")

        self.model.fit(X)
        self.is_fitted = True
        self.n_features_in_ = n_features
        return self

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Compute authoritative raw anomaly scores:
          s_raw(x) = -score_samples(x)

        Higher scores indicate greater anomaly severity.
        """
        if not self.is_fitted:
            raise RuntimeError("IsolationForestDetector must be fitted before scoring.")
        if X.ndim != 2:
            raise ValueError(f"Input feature matrix must be 2-dimensional, got ndim={X.ndim}")
        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"Feature dimension mismatch: detector fitted with {self.n_features_in_} features, "
                f"received {X.shape[1]}"
            )

        n_samples = X.shape[0]
        if n_samples == 0:
            return np.empty(0, dtype=float)

        if not np.all(np.isfinite(X)):
            raise ValueError("Feature matrix contains non-finite values (NaN/Inf).")

        # Negate scikit-learn score_samples so higher means more anomalous
        raw_scores = -self.model.score_samples(X)
        return raw_scores

