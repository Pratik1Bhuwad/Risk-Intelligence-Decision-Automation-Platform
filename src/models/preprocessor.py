"""
Feature Preprocessing and Validation Pipeline for ML Models.
"""

from typing import List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

from src.features.policy import STRICTLY_EXCLUDED_FIELDS
from src.features.metadata import FEATURE_CATALOG


class ModelFeaturePreprocessor(BaseEstimator, TransformerMixin):
    """
    Validates and standardizes input feature matrices for modeling and inference.
    Guarantees strict schema adherence and rejects prohibited leakage fields.
    """

    def __init__(
        self,
        scale_numeric: bool = False,
        expected_features: Optional[List[str]] = None,
    ):
        self.scale_numeric = scale_numeric
        self.expected_features = expected_features or list(FEATURE_CATALOG.keys())
        self.scaler: Optional[StandardScaler] = None
        self.is_fitted: bool = False

    def validate_columns(self, df: pd.DataFrame) -> None:
        """Verify presence of required features and absence of prohibited leakage fields."""
        cols = set(df.columns)

        # 1. Reject prohibited post-event and leakage fields
        leakage = cols.intersection(STRICTLY_EXCLUDED_FIELDS)
        if leakage:
            raise ValueError(
                f"Security/Leakage Violation: Prohibited columns detected in model input: {sorted(list(leakage))}"
            )

        # 2. Check for missing required features
        missing = [f for f in self.expected_features if f not in cols]
        if missing:
            raise ValueError(
                f"Missing required model input features ({len(missing)} missing): {missing}"
            )

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "ModelFeaturePreprocessor":
        """Fit preprocessor strictly on training data."""
        self.validate_columns(X)

        # Reorder columns to guaranteed canonical order
        X_ordered = X[self.expected_features]

        if self.scale_numeric:
            self.scaler = StandardScaler()
            self.scaler.fit(X_ordered)

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform input features using fitted parameters."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before transforming data.")

        self.validate_columns(X)
        X_ordered = X[self.expected_features].copy()

        # Check for nulls or infinities
        if X_ordered.isnull().any().any():
            raise ValueError("Input features contain NaN/null values.")

        # Check for infinite values
        numeric_cols = X_ordered.select_dtypes(include=[np.number]).columns
        if np.isneginf(X_ordered[numeric_cols]).any().any() or np.isposinf(X_ordered[numeric_cols]).any().any():
            raise ValueError("Input features contain infinite values (+inf / -inf).")

        if self.scale_numeric and self.scaler is not None:
            scaled_vals = self.scaler.transform(X_ordered)
            return pd.DataFrame(scaled_vals, columns=self.expected_features, index=X_ordered.index)

        return X_ordered
