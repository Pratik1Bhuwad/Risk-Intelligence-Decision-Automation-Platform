"""
Configuration module for the PaySim Data Audit.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

AUDIT_VERSION = "0.1.0"


@dataclass
class AuditConfig:
    dataset: str = "paysim"
    audit_version: str = AUDIT_VERSION
    data_path: str = "data/raw/paysim/PaySimData.csv"
    output_dir: str = "audit_output"
    mode: str = "full"  # 'full' or 'sample'
    sample_size: Optional[int] = None
    chunk_size: int = 100000

    # Column roles (configuration-driven)
    temporal_cols: List[str] = field(default_factory=lambda: ["step"])
    categorical_cols: List[str] = field(default_factory=lambda: ["type"])
    origin_cols: List[str] = field(default_factory=lambda: ["nameOrig"])
    dest_cols: List[str] = field(default_factory=lambda: ["nameDest"])
    numerical_cols: List[str] = field(
        default_factory=lambda: [
            "amount",
            "oldbalanceOrg",
            "newbalanceOrig",
            "oldbalanceDest",
            "newbalanceDest",
        ]
    )
    target_cols: List[str] = field(default_factory=lambda: ["isFraud"])
    flag_cols: List[str] = field(default_factory=lambda: ["isFlaggedFraud"])

    # Audit settings
    missing_markers: List[str] = field(
        default_factory=lambda: [
            "null",
            "nan",
            "none",
            "na",
            "?",
            "missing",
            "n/a",
            "",
        ]
    )
    quantiles: List[float] = field(
        default_factory=lambda: [
            0.01,
            0.05,
            0.10,
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99,
        ]
    )

    @classmethod
    def from_yaml(
        cls,
        yaml_path: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "AuditConfig":
        """Load configuration from YAML file with optional CLI overrides."""
        path = Path(yaml_path)
        data: Dict[str, Any] = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded

        columns = data.get("columns", {})
        entities = columns.get("entities", {})
        settings = data.get("audit_settings", {})

        config = cls(
            dataset=data.get("dataset", "paysim"),
            audit_version=data.get("audit_version", AUDIT_VERSION),
            data_path=data.get("data_path", "data/raw/paysim/PaySimData.csv"),
            output_dir=data.get("output_dir", "audit_output"),
            temporal_cols=columns.get("temporal", ["step"]),
            categorical_cols=columns.get("categorical", ["type"]),
            origin_cols=entities.get("origin", ["nameOrig"]),
            dest_cols=entities.get("destination", ["nameDest"]),
            numerical_cols=columns.get(
                "numerical",
                [
                    "amount",
                    "oldbalanceOrg",
                    "newbalanceOrig",
                    "oldbalanceDest",
                    "newbalanceDest",
                ],
            ),
            target_cols=columns.get("target", ["isFraud"]),
            flag_cols=columns.get("flags", ["isFlaggedFraud"]),
            missing_markers=settings.get(
                "missing_markers",
                ["null", "nan", "none", "na", "?", "missing", "n/a", ""],
            ),
            quantiles=settings.get(
                "quantiles",
                [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99],
            ),
            chunk_size=settings.get("chunk_size", 100000),
        )

        if overrides:
            for key, val in overrides.items():
                if val is not None and hasattr(config, key):
                    setattr(config, key, val)

        return config
