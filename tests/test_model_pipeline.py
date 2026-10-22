"""
Tests for MLRiskPipeline end-to-end execution.
"""

import json
import os
import numpy as np
import pandas as pd
import pytest

from src.features.metadata import FEATURE_CATALOG
from src.models.inference import RiskPredictor
from src.models.pipeline import MLRiskPipeline


@pytest.fixture
def synthetic_feature_csv(tmp_path) -> str:
    """Create synthetic dataset matching the 36 feature catalog schema across multiple steps."""
    features = list(FEATURE_CATALOG.keys())
    np.random.seed(42)

    n_rows = 60
    data = {}
    for f in features:
        if f.startswith("is_") or f.endswith("_is_merchant") or f.endswith("_is_customer"):
            data[f] = np.random.randint(0, 2, n_rows).astype(np.int8)
        elif "count" in f:
            data[f] = np.random.randint(0, 10, n_rows).astype(np.int32)
        else:
            data[f] = np.random.uniform(0, 1000, n_rows).astype(np.float64)

    # 3 distinct step ranges for splitting
    # steps 1-5 for train (30 rows), 6-8 for val (15 rows), 9-10 for test (15 rows)
    steps = [1, 2, 3, 4, 5] * 6 + [6, 7, 8] * 5 + [9, 10] * 7 + [10]
    data["day_of_simulation"] = [s // 24 for s in steps[:n_rows]]
    data["hour_of_day"] = [s % 24 for s in steps[:n_rows]]
    data["step"] = steps[:n_rows]

    # Target label with both 0 and 1 in each fold
    y = [0, 1, 0, 0, 1] * 6 + [0, 1, 0] * 5 + [0, 1] * 7 + [0]
    data["isFraud"] = y[:n_rows]

    df = pd.DataFrame(data)
    csv_path = str(tmp_path / "synthetic_features.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


def test_ml_risk_pipeline_run_end_to_end(synthetic_feature_csv, tmp_path):
    artifacts_dir = str(tmp_path / "test_artifacts")
    reports_dir = str(tmp_path / "test_reports")

    pipeline = MLRiskPipeline()
    pipeline.train_max_step = 5
    pipeline.val_max_step = 8
    pipeline.test_max_step = 10

    report = pipeline.run(
        data_path=synthetic_feature_csv,
        artifacts_dir=artifacts_dir,
        reports_dir=reports_dir,
        models_to_train=["dummy_baseline", "logistic_regression", "lightgbm"],
    )

    assert "split_summaries" in report
    assert "model_comparison" in report
    assert "champion_evaluation" in report
    assert "saved_artifacts" in report

    # Verify report JSON was created
    report_file = os.path.join(reports_dir, "ml_risk_modeling_report.json")
    assert os.path.exists(report_file)

    # Verify artifact loading and inference works
    predictor = RiskPredictor.load(artifacts_dir)
    features = list(FEATURE_CATALOG.keys())
    single_record = {f: 1.0 for f in features}
    decision = predictor.predict_decision(single_record)

    assert decision["decision"] in ("APPROVE", "MONITOR", "MANUAL_INVESTIGATION")
    assert 0 <= decision["risk_score_100"] <= 100
