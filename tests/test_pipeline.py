"""
Tests for end-to-end audit pipeline execution.
"""

import json
import os
from src.audit.pipeline import run_audit

EXPECTED_OUTPUT_FILES = [
    "audit_summary.json",
    "run_metadata.json",
    "schema.csv",
    "missing_values.csv",
    "duplicates.csv",
    "cardinality.csv",
    "numerical_summary.csv",
    "categorical_summary.csv",
    "target_analysis.csv",
    "temporal_analysis.csv",
    "entity_analysis.csv",
    "prediction_time_matrix.csv",
    "leakage_matrix.csv",
    "synthetic_artifact_review.csv",
    "data_dictionary.csv",
    "capability_assessment.csv",
    "audit_report.html",
    "audit.log",
]


def test_end_to_end_pipeline(test_config):
    summary = run_audit(test_config)
    assert summary is not None

    output_dir = test_config.output_dir

    # Verify all 18 output artifacts exist and have non-zero size
    for fname in EXPECTED_OUTPUT_FILES:
        fpath = os.path.join(output_dir, fname)
        assert os.path.exists(fpath), f"Expected output file missing: {fname}"
        assert os.path.getsize(fpath) > 0, f"Output file is empty: {fname}"

    # Verify run_metadata.json content
    metadata_path = os.path.join(output_dir, "run_metadata.json")
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["audit_version"] == "0.1.0"
    assert meta["audit_mode"] == "FULL"
    assert meta["row_count"] == 10
    assert meta["column_count"] == 11
    assert meta["read_only_verified"] is True
