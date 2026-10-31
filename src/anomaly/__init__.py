"""
Phase 05 — Anomaly Detection & Behavioral Outlier Profiling Engine.

Independent, leakage-safe anomaly detection module operating under
Specification v2.3.2 and frozen configuration baseline.
"""

from src.anomaly.config import AnomalyConfig, load_anomaly_config
from src.anomaly.schema import (
    AnomalyOutputRow,
    AnomalyOutputSchema,
    AnomalyStatus,
    EligibleChannel,
    ReasonCode,
    validate_output_row,
)
from src.anomaly.preprocessing import AnomalyPreprocessor, FeatureFallbackResult
from src.anomaly.detector import IsolationForestDetector
from src.anomaly.budget import AlertBudgetSelector, BudgetResult
from src.anomaly.engine import AnomalyDetectionEngine

__all__ = [
    "AnomalyConfig",
    "load_anomaly_config",
    "AnomalyOutputRow",
    "AnomalyOutputSchema",
    "AnomalyStatus",
    "EligibleChannel",
    "ReasonCode",
    "validate_output_row",
    "AnomalyPreprocessor",
    "FeatureFallbackResult",
    "IsolationForestDetector",
    "AlertBudgetSelector",
    "BudgetResult",
    "AnomalyDetectionEngine",
]

