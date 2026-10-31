"""
Configuration loader and integrity verifier for Phase 05 Anomaly Detection.

Validates the 16 specification-required sections and verifies cryptographic
provenance against the frozen baseline under Specification v2.3.2.
"""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

FROZEN_CONFIG_RAW_SHA256 = "53cf7a64597965b38d5df32c7818002370c4e4e6a2da8837788f7019fd882ae2"
FROZEN_CONFIG_SEMANTIC_SHA256 = "d9acda394310cdf0f373b28de85a354571c9b37d6fbd2d8b92211ce3f0df98c0"

REQUIRED_SECTIONS: List[str] = [
    "specification",
    "detector",
    "eligibility",
    "features",
    "historical_reference_windows",
    "channel_conditioning",
    "preprocessing",
    "fallback_hierarchy",
    "active_inactive_feature_behavior",
    "score_definition",
    "alert_budget",
    "tie_breaking",
    "unscored_and_degraded_behavior",
    "metric_definitions",
    "reproducibility",
    "software_versions",
]


@dataclass(frozen=True)
class AnomalyConfig:
    raw_dict: Dict[str, Any]
    spec_version: str
    detector_algorithm: str
    detector_hyperparameters: Dict[str, Any]
    eligible_channels: List[str]
    feature_names: List[str]
    short_window_steps: int
    long_window_steps: int
    same_step_policy: str
    channel_conditioning_enabled: bool
    budget_rate: float
    budget_scope: str
    random_seed: int
    raw_sha256: str
    semantic_sha256: str

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        raw_sha256: str = "",
        semantic_sha256: str = "",
    ) -> "AnomalyConfig":
        """Construct validated AnomalyConfig from dictionary."""
        missing = [sec for sec in REQUIRED_SECTIONS if sec not in data]
        if missing:
            raise ValueError(f"Configuration validation failure: missing required sections: {missing}")

        spec = data["specification"]
        detector = data["detector"]
        eligibility = data["eligibility"]
        features = data["features"]
        windows = data["historical_reference_windows"]
        conditioning = data["channel_conditioning"]
        budget = data["alert_budget"]
        reproducibility = data["reproducibility"]

        # Validate feature list count and names
        feat_list = features.get("feature_names", [])
        if len(feat_list) != 36:
            raise ValueError(f"Configuration must define exactly 36 features, found {len(feat_list)}")

        # Validate budget rate
        rate = float(budget.get("rate", 0.0))
        if rate <= 0.0 or rate > 1.0:
            raise ValueError(f"Alert budget rate must be in (0, 1], found {rate}")

        # Compute semantic hash if not provided
        if not semantic_sha256:
            canonical_json = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
            semantic_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return cls(
            raw_dict=data,
            spec_version=str(spec.get("version", "")),
            detector_algorithm=str(detector.get("algorithm", "")),
            detector_hyperparameters=dict(detector.get("hyperparameters", {})),
            eligible_channels=list(eligibility.get("channels", [])),
            feature_names=list(feat_list),
            short_window_steps=int(windows.get("lookback_windows", {}).get("short_window_steps", 24)),
            long_window_steps=int(windows.get("lookback_windows", {}).get("long_window_steps", 168)),
            same_step_policy=str(windows.get("same_step_policy", "EXCLUDE_SAME_STEP")),
            channel_conditioning_enabled=bool(conditioning.get("enabled", True)),
            budget_rate=rate,
            budget_scope=str(budget.get("scope", "global")),
            random_seed=int(reproducibility.get("random_seed", 42)),
            raw_sha256=raw_sha256,
            semantic_sha256=semantic_sha256,
        )


def compute_config_digests(yaml_path: str | Path) -> tuple[str, str]:
    """Compute raw byte SHA-256 (LF normalized) and semantic AST JSON SHA-256."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    raw_bytes = path.read_bytes()
    lf_bytes = raw_bytes.replace(b"\r\n", b"\n")
    raw_sha = hashlib.sha256(lf_bytes).hexdigest()

    parsed = yaml.safe_load(lf_bytes.decode("utf-8"))
    canonical_json = json.dumps(parsed, sort_keys=True, indent=2, ensure_ascii=False)
    semantic_sha = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    return raw_sha, semantic_sha


def load_anomaly_config(
    yaml_path: str | Path = "configs/anomaly_detection.yaml",
    verify_provenance: bool = True,
) -> AnomalyConfig:
    """
    Load, validate, and verify Phase 05 anomaly detection configuration.

    Args:
        yaml_path: Path to YAML configuration file.
        verify_provenance: If True, asserts exact match against frozen SHA-256 baseline.

    Returns:
        Validated AnomalyConfig instance.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    raw_sha, semantic_sha = compute_config_digests(path)

    if verify_provenance:
        if raw_sha != FROZEN_CONFIG_RAW_SHA256:
            raise ValueError(
                f"Configuration integrity failure: raw SHA-256 {raw_sha} does not match "
                f"frozen baseline {FROZEN_CONFIG_RAW_SHA256}"
            )
        if semantic_sha != FROZEN_CONFIG_SEMANTIC_SHA256:
            raise ValueError(
                f"Configuration integrity failure: semantic AST SHA-256 {semantic_sha} does not match "
                f"frozen baseline {FROZEN_CONFIG_SEMANTIC_SHA256}"
            )

    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise TypeError(f"Invalid YAML content in {path}: expected dictionary mapping")

    return AnomalyConfig.from_dict(data, raw_sha256=raw_sha, semantic_sha256=semantic_sha)

