"""
Model Training and Comparison Orchestrator.
"""

import time
from typing import Any, Dict, List, Optional
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from src.models.preprocessor import ModelFeaturePreprocessor


class ModelTrainer:
    """
    Coordinates training of baseline, candidate, and champion risk models.
    Enforces strict reproducibility and zero leakage.
    """

    def __init__(
        self,
        random_state: int = 42,
        models_config: Optional[Dict[str, Any]] = None,
    ):
        self.random_state = random_state
        self.models_config = models_config or {}
        self.trained_models: Dict[str, Any] = {}
        self.training_times: Dict[str, float] = {}
        self.preprocessors: Dict[str, ModelFeaturePreprocessor] = {}

    def train_dummy_baseline(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> DummyClassifier:
        """Train naive reference baseline model (predicts prior class distribution)."""
        t0 = time.time()
        prep = ModelFeaturePreprocessor(scale_numeric=False)
        prep.fit(X_train)
        self.preprocessors["dummy_baseline"] = prep

        model = DummyClassifier(strategy="prior", random_state=self.random_state)
        model.fit(prep.transform(X_train), y_train)
        self.training_times["dummy_baseline"] = round(time.time() - t0, 3)
        self.trained_models["dummy_baseline"] = model
        return model

    def train_logistic_baseline(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        max_iter: int = 500,
        class_weight: str = "balanced",
        C: float = 1.0,
    ) -> LogisticRegression:
        """Train interpretable linear baseline with StandardScaler."""
        t0 = time.time()
        prep = ModelFeaturePreprocessor(scale_numeric=True)
        prep.fit(X_train)
        self.preprocessors["logistic_regression"] = prep

        X_tr = prep.transform(X_train)
        model = LogisticRegression(
            max_iter=max_iter,
            class_weight=class_weight,
            C=C,
            solver="lbfgs",
            random_state=self.random_state,
        )
        model.fit(X_tr, y_train)
        self.training_times["logistic_regression"] = round(time.time() - t0, 3)
        self.trained_models["logistic_regression"] = model
        return model

    def train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_estimators: int = 50,
        max_depth: int = 10,
    ) -> RandomForestClassifier:
        """Train Random Forest ensemble bagging baseline."""
        t0 = time.time()
        prep = ModelFeaturePreprocessor(scale_numeric=False)
        prep.fit(X_train)
        self.preprocessors["random_forest"] = prep

        X_tr = prep.transform(X_train)
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight="balanced",
            n_jobs=-1,
            random_state=self.random_state,
        )
        model.fit(X_tr, y_train)
        self.training_times["random_forest"] = round(time.time() - t0, 3)
        self.trained_models["random_forest"] = model
        return model

    def train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        num_leaves: int = 31,
        scale_pos_weight: float = 1.0,
    ) -> lgb.LGBMClassifier:
        """Train primary LightGBM gradient boosted decision tree model."""
        t0 = time.time()
        prep = ModelFeaturePreprocessor(scale_numeric=False)
        prep.fit(X_train)
        self.preprocessors["lightgbm"] = prep

        X_tr = prep.transform(X_train)
        model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            num_leaves=num_leaves,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_state,
            verbose=-1,
            n_jobs=-1,
        )
        model.fit(X_tr, y_train)
        self.training_times["lightgbm"] = round(time.time() - t0, 3)
        self.trained_models["lightgbm"] = model
        return model

    def train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        scale_pos_weight: float = 1.0,
    ) -> XGBClassifier:
        """Train challenger XGBoost model."""
        t0 = time.time()
        prep = ModelFeaturePreprocessor(scale_numeric=False)
        prep.fit(X_train)
        self.preprocessors["xgboost"] = prep

        X_tr = prep.transform(X_train)
        model = XGBClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=self.random_state,
            n_jobs=-1,
        )
        model.fit(X_tr, y_train)
        self.training_times["xgboost"] = round(time.time() - t0, 3)
        self.trained_models["xgboost"] = model
        return model

    def predict_proba(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        """Generate prediction probabilities using specified model and its fitted preprocessor."""
        if model_name not in self.trained_models:
            raise KeyError(f"Model '{model_name}' has not been trained yet.")
        prep = self.preprocessors[model_name]
        model = self.trained_models[model_name]
        X_tf = prep.transform(X)
        return model.predict_proba(X_tf)[:, 1]
