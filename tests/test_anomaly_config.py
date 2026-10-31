"""
Unit tests for Phase 05 Configuration loading and provenance verification.
"""

from pathlib import Path
import pytest
import yaml

from src.anomaly.config import (
    AnomalyConfig,
    FROZEN_CONFIG_RAW_SHA256,
    FROZEN_CONFIG_SEMANTIC_SHA256,
    compute_config_digests,
    load_anomaly_config,
)


def test_load_frozen_anomaly_config():
    """Verify loading and provenance verification of the frozen configuration file."""
    config = load_anomaly_config("configs/anomaly_detection.yaml", verify_provenance=True)
    assert config.spec_version == "2.3.2"
    assert config.detector_algorithm == "IsolationForest"
    assert config.budget_rate == 0.0100
    assert config.budget_scope == "global"
    assert config.random_seed == 42
    assert config.eligible_channels == ["TRANSFER", "CASH_OUT"]
    assert len(config.feature_names) == 36
    assert config.raw_sha256 == FROZEN_CONFIG_RAW_SHA256
    assert config.semantic_sha256 == FROZEN_CONFIG_SEMANTIC_SHA256


def test_config_digests_computation(tmp_path):
    """Test cryptographic digest computation on arbitrary YAML content."""
    dummy_yaml = tmp_path / "dummy.yaml"
    dummy_yaml.write_text("a: 1\nb: 2\n", encoding="utf-8")
    raw_sha, sem_sha = compute_config_digests(dummy_yaml)
    assert isinstance(raw_sha, str) and len(raw_sha) == 64
    assert isinstance(sem_sha, str) and len(sem_sha) == 64


def test_reject_tampered_config(tmp_path):
    """Verify that tampering with any attribute causes provenance verification to fail."""
    real_text = Path("configs/anomaly_detection.yaml").read_text(encoding="utf-8")
    tampered_text = real_text.replace("rate: 0.0100", "rate: 0.0200")
    tampered_file = tmp_path / "tampered.yaml"
    tampered_file.write_text(tampered_text, encoding="utf-8")

    with pytest.raises(ValueError, match="Configuration integrity failure"):
        load_anomaly_config(tampered_file, verify_provenance=True)


def test_reject_missing_required_sections():
    """Verify that omitting any of the 16 required sections raises a ValueError."""
    incomplete_dict = {
        "specification": {"version": "2.3.2"},
        "detector": {"algorithm": "IsolationForest"},
    }
    with pytest.raises(ValueError, match="missing required sections"):
        AnomalyConfig.from_dict(incomplete_dict)


def test_reject_invalid_budget_rate():
    """Verify that non-positive or >1.0 budget rates are rejected."""
    config = load_anomaly_config("configs/anomaly_detection.yaml", verify_provenance=False)
    bad_dict = dict(config.raw_dict)
    bad_dict["alert_budget"] = {"rate": -0.05, "scope": "global"}
    with pytest.raises(ValueError, match="Alert budget rate must be in"):
        AnomalyConfig.from_dict(bad_dict)

