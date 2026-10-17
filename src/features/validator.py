"""
Feature Quality and Leakage Validation module.

Validates that engineered feature datasets satisfy data quality,
integrity, and leakage-prevention criteria.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

from src.features.policy import STRICTLY_EXCLUDED_FIELDS


class FeatureQualityValidator:
    """Validates engineered feature datasets for quality, integrity, and leakage safety."""

    def __init__(self, excluded_fields: List[str] = None):
        self.excluded_fields = (
            set(excluded_fields) if excluded_fields else STRICTLY_EXCLUDED_FIELDS
        )

    def validate(
        self,
        raw_df: pd.DataFrame,
        feature_df: pd.DataFrame,
        allow_target_in_output: bool = False,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run full validation suite on feature DataFrame.
        Returns (is_valid, report_dict).
        """
        report: Dict[str, Any] = {
            "checks_passed": True,
            "errors": [],
            "warnings": [],
            "metrics": {},
        }

        # 1. Row count preservation
        input_rows = len(raw_df)
        output_rows = len(feature_df)
        if input_rows != output_rows:
            report["checks_passed"] = False
            report["errors"].append(
                f"Row count mismatch! Raw input: {input_rows}, Feature output: {output_rows}"
            )

        # 2. Absence of strictly excluded fields
        feature_cols = set(feature_df.columns)
        forbidden_present = feature_cols.intersection(self.excluded_fields)
        if forbidden_present:
            # If target is explicitly allowed as an aligned label column, don't fail for isFraud
            if allow_target_in_output and forbidden_present == {"isFraud"}:
                report["warnings"].append(
                    "Target 'isFraud' is included as a label column in output."
                )
            else:
                report["checks_passed"] = False
                report["errors"].append(
                    f"CRITICAL LEAKAGE: Excluded fields present in feature set: {list(forbidden_present)}"
                )

        # 3. Missing values / Nulls
        null_counts = feature_df.isna().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        if not cols_with_nulls.empty:
            report["checks_passed"] = False
            report["errors"].append(
                f"Null values detected in feature columns: {cols_with_nulls.to_dict()}"
            )

        # 4. Infinite values
        numeric_cols = feature_df.select_dtypes(include=[np.number]).columns
        inf_counts = {}
        for col in numeric_cols:
            cnt = int(np.isinf(feature_df[col]).sum())
            if cnt > 0:
                inf_counts[col] = cnt

        if inf_counts:
            report["checks_passed"] = False
            report["errors"].append(
                f"Infinite values detected in feature columns: {inf_counts}"
            )

        # 5. Constant features (zero variance)
        constant_cols = []
        for col in feature_df.columns:
            if feature_df[col].nunique(dropna=False) <= 1:
                constant_cols.append(col)

        if constant_cols:
            report["warnings"].append(
                f"Constant features detected (single unique value): {constant_cols}"
            )

        # 6. Summary metrics
        report["metrics"] = {
            "input_rows": input_rows,
            "feature_rows": output_rows,
            "feature_columns_count": len(feature_df.columns),
            "columns": list(feature_df.columns),
            "null_cells_total": int(null_counts.sum()),
            "inf_cells_total": sum(inf_counts.values()),
            "constant_features_count": len(constant_cols),
        }

        return report["checks_passed"], report
