"""
Tests for configuration loading and validation.
"""

from src.config import AuditConfig, AUDIT_VERSION


def test_default_config():
    config = AuditConfig()
    assert config.dataset == "paysim"
    assert config.audit_version == AUDIT_VERSION
    assert "step" in config.temporal_cols
    assert "type" in config.categorical_cols
    assert "nameOrig" in config.origin_cols
    assert "nameDest" in config.dest_cols
    assert "isFraud" in config.target_cols
    assert "isFlaggedFraud" in config.flag_cols
    assert config.mode == "full"


def test_config_from_yaml(tmp_path):
    yaml_content = """
dataset: custom_test
audit_version: "0.2.0"
columns:
  temporal:
    - tx_time
  categorical:
    - tx_type
  entities:
    origin:
      - sender_id
    destination:
      - receiver_id
  numerical:
    - tx_amount
  target:
    - fraud_label
  flags:
    - rule_flag
"""
    yaml_file = tmp_path / "custom.yaml"
    yaml_file.write_text(yaml_content, encoding="utf-8")

    cfg = AuditConfig.from_yaml(str(yaml_file))
    assert cfg.dataset == "custom_test"
    assert cfg.audit_version == "0.2.0"
    assert cfg.temporal_cols == ["tx_time"]
    assert cfg.categorical_cols == ["tx_type"]
    assert cfg.origin_cols == ["sender_id"]
    assert cfg.dest_cols == ["receiver_id"]
    assert cfg.numerical_cols == ["tx_amount"]
    assert cfg.target_cols == ["fraud_label"]
    assert cfg.flag_cols == ["rule_flag"]


def test_config_overrides(tmp_path):
    cfg = AuditConfig.from_yaml(
        "non_existent.yaml",
        overrides={"mode": "sample", "sample_size": 1000, "dataset": "override_test"},
    )
    assert cfg.mode == "sample"
    assert cfg.sample_size == 1000
    assert cfg.dataset == "override_test"
