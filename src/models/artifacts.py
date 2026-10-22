"""
Model Artifact Serialization and Metadata Management.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import joblib


class ModelArtifactManager:
    """
    Handles saving, versioning, and loading of production model bundles.
    """

    BUNDLE_FILENAME = "model_bundle.joblib"
    METADATA_FILENAME = "model_metadata.json"

    @classmethod
    def save_bundle(
        cls,
        artifact_dir: str,
        model: Any,
        preprocessor: Any,
        calibrator: Any,
        threshold_optimizer: Any,
        metadata: Dict[str, Any],
    ) -> Dict[str, str]:
        """Save fitted model bundle and metadata JSON into artifact directory."""
        os.makedirs(artifact_dir, exist_ok=True)

        bundle = {
            "model": model,
            "preprocessor": preprocessor,
            "calibrator": calibrator,
            "threshold_optimizer": threshold_optimizer,
            "model_class": model.__class__.__name__,
            "saved_at": datetime.now().isoformat(),
        }

        bundle_path = os.path.join(artifact_dir, cls.BUNDLE_FILENAME)
        joblib.dump(bundle, bundle_path)

        metadata_path = os.path.join(artifact_dir, cls.METADATA_FILENAME)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return {
            "bundle_path": bundle_path,
            "metadata_path": metadata_path,
        }

    @classmethod
    def load_bundle(cls, artifact_dir: str) -> Dict[str, Any]:
        """Load fitted model bundle and verify presence of metadata."""
        bundle_path = os.path.join(artifact_dir, cls.BUNDLE_FILENAME)
        metadata_path = os.path.join(artifact_dir, cls.METADATA_FILENAME)

        if not os.path.exists(bundle_path):
            raise FileNotFoundError(f"Model bundle not found at '{bundle_path}'")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Model metadata not found at '{metadata_path}'")

        bundle = joblib.load(bundle_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        bundle["metadata"] = metadata
        return bundle
