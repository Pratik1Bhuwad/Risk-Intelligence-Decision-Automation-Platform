"""
Duplicate records and transaction identifier audit module.
"""

from typing import List
import pandas as pd
from src.config import AuditConfig


def audit_duplicates(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit exact duplicate rows, potential transaction identifiers, entity repeats,
    and repeated combinations of key fields.
    """
    total_rows = len(df)
    records = []

    # 1. Exact duplicate rows
    exact_dups = int(df.duplicated().sum())
    exact_pct = (exact_dups / total_rows * 100.0) if total_rows > 0 else 0.0
    records.append(
        {
            "check_type": "EXACT_DUPLICATE_ROWS",
            "target_columns": "ALL_COLUMNS",
            "total_records": total_rows,
            "duplicate_records": exact_dups,
            "duplicate_percentage": round(exact_pct, 4),
            "is_explicit_id": False,
            "interpretation": (
                "Identical transaction records occurring multiple times in dataset."
                if exact_dups > 0
                else "Zero exact duplicate rows observed."
            ),
            "status": "CONFIRMED",
        }
    )

    # 2. Check candidate entity / identifier columns
    candidate_id_cols = config.origin_cols + config.dest_cols
    for col in candidate_id_cols:
        if col in df.columns:
            unique_cnt = int(df[col].nunique())
            dups_cnt = total_rows - unique_cnt
            dup_pct = (dups_cnt / total_rows * 100.0) if total_rows > 0 else 0.0
            is_unique = dups_cnt == 0

            records.append(
                {
                    "check_type": "ENTITY_IDENTIFIER_REPEAT",
                    "target_columns": col,
                    "total_records": total_rows,
                    "duplicate_records": dups_cnt,
                    "duplicate_percentage": round(dup_pct, 4),
                    "is_explicit_id": False,  # We do NOT assume it's an explicit tx ID
                    "interpretation": (
                        f"Field '{col}' has {unique_cnt} unique values across {total_rows} rows. "
                        + (
                            "All values are unique."
                            if is_unique
                            else "Repeated entity values observed."
                        )
                    ),
                    "status": "CONFIRMED",
                }
            )

    # 3. Composite key checks
    composite_keys = [
        ["step", "nameOrig", "amount"],
        ["step", "nameOrig", "nameDest", "amount"],
        ["nameOrig", "step"],
    ]

    for key_cols in composite_keys:
        existing_cols = [c for c in key_cols if c in df.columns]
        if len(existing_cols) == len(key_cols):
            dup_count = int(df.duplicated(subset=existing_cols).sum())
            dup_pct = (dup_count / total_rows * 100.0) if total_rows > 0 else 0.0
            records.append(
                {
                    "check_type": "COMPOSITE_KEY_DUPLICATE",
                    "target_columns": "+".join(existing_cols),
                    "total_records": total_rows,
                    "duplicate_records": dup_count,
                    "duplicate_percentage": round(dup_pct, 4),
                    "is_explicit_id": False,
                    "interpretation": (
                        f"{dup_count} records share identical ({'+'.join(existing_cols)}) values."
                    ),
                    "status": "CONFIRMED",
                }
            )

    return pd.DataFrame(records)
