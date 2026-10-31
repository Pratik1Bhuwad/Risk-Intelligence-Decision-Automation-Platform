"""
Phase 05 Standalone Transaction-Level Output Contract & Schema Definitions.

Implements the eight-field decoupled output contract under Specification v2.3.2 Section 4.
Preserves strict state semantics across States A, B, and C without modifying Phase 04 interfaces.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Optional
import pandas as pd

CURRENT_SCHEMA_VERSION = "1.0.0"


class AnomalyStatus(str, Enum):
    SCORED = "SCORED"
    DEGRADED_UNSCORABLE = "DEGRADED_UNSCORABLE"


class EligibleChannel(str, Enum):
    TRANSFER = "TRANSFER"
    CASH_OUT = "CASH_OUT"


class ReasonCode(str, Enum):
    ALL_ANOMALY_FEATURES_INACTIVE = "ALL_ANOMALY_FEATURES_INACTIVE"
    UNSUPPORTED_CHANNEL = "UNSUPPORTED_CHANNEL"
    INVALID_ROW_INDEX = "INVALID_ROW_INDEX"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


@dataclass(frozen=True)
class AnomalyOutputRow:
    """
    Standalone transaction-level anomaly output record.
    Preserves exact eight fields specified in v2.3.2 Section 4.1.
    """
    schema_version: str
    row_index: int
    channel: str
    anomaly_score: Optional[float]
    is_anomaly_flagged: Optional[bool]
    anomaly_status: str
    reason_code: Optional[str]
    alert_budget_selected: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard Python dictionary."""
        return {
            "schema_version": self.schema_version,
            "row_index": int(self.row_index),
            "channel": str(self.channel),
            "anomaly_score": float(self.anomaly_score) if self.anomaly_score is not None else None,
            "is_anomaly_flagged": bool(self.is_anomaly_flagged) if self.is_anomaly_flagged is not None else None,
            "anomaly_status": str(self.anomaly_status),
            "reason_code": str(self.reason_code) if self.reason_code is not None else None,
            "alert_budget_selected": bool(self.alert_budget_selected),
        }

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to strict JSON-compatible dictionary (no NaNs, no strings for booleans)."""
        d = self.to_dict()
        if d["anomaly_score"] is not None and not math.isfinite(d["anomaly_score"]):
            raise ValueError(f"Non-finite anomaly score detected for row_index {self.row_index}: {d['anomaly_score']}")
        return d


def validate_output_row(row: AnomalyOutputRow) -> None:
    """
    Validate output row semantics against Specification v2.3.2 Section 4.4.

    Raises:
        ValueError: If row violates contract invariants.
    """
    # 1. row_index validation
    if not isinstance(row.row_index, int) or row.row_index < 0:
        raise ValueError(f"Invalid row_index: must be non-negative integer, got {row.row_index}")

    # 2. channel validation
    if row.channel not in [EligibleChannel.TRANSFER.value, EligibleChannel.CASH_OUT.value]:
        raise ValueError(f"Invalid channel '{row.channel}': must be TRANSFER or CASH_OUT")

    # 3. Status discriminator validation
    if row.anomaly_status == AnomalyStatus.SCORED.value:
        # State A or State B
        if row.anomaly_score is None:
            raise ValueError(f"Scored row (row_index={row.row_index}) must have non-null anomaly_score")
        if not math.isfinite(row.anomaly_score):
            raise ValueError(f"Scored row (row_index={row.row_index}) must have finite anomaly_score, got {row.anomaly_score}")
        if row.is_anomaly_flagged is None:
            raise ValueError(f"Scored row (row_index={row.row_index}) must have non-null is_anomaly_flagged")
        if row.reason_code is not None:
            raise ValueError(f"Scored row (row_index={row.row_index}) must have null reason_code, got '{row.reason_code}'")
        # Parity check
        if row.is_anomaly_flagged != row.alert_budget_selected:
            raise ValueError(
                f"Contradictory selection flags for row_index {row.row_index}: "
                f"is_anomaly_flagged={row.is_anomaly_flagged} != alert_budget_selected={row.alert_budget_selected}"
            )

    elif row.anomaly_status == AnomalyStatus.DEGRADED_UNSCORABLE.value:
        # State C
        if row.anomaly_score is not None:
            raise ValueError(f"Degraded row (row_index={row.row_index}) must have null anomaly_score, got {row.anomaly_score}")
        if row.is_anomaly_flagged is not None:
            raise ValueError(f"Degraded row (row_index={row.row_index}) must have null is_anomaly_flagged, got {row.is_anomaly_flagged}")
        if not row.reason_code:
            raise ValueError(f"Degraded row (row_index={row.row_index}) must have non-null machine-readable reason_code")
        if row.alert_budget_selected:
            raise ValueError(f"Degraded row (row_index={row.row_index}) cannot have alert_budget_selected=True")

    else:
        raise ValueError(f"Unknown anomaly_status: '{row.anomaly_status}'")


class AnomalyOutputSchema:
    """Helper class for DataFrame-level schema validation and conversion."""

    COLUMN_NAMES: List[str] = [
        "schema_version",
        "row_index",
        "channel",
        "anomaly_score",
        "is_anomaly_flagged",
        "anomaly_status",
        "reason_code",
        "alert_budget_selected",
    ]

    @classmethod
    def create_scored_row(
        cls,
        row_index: int,
        channel: str,
        score: float,
        is_flagged: bool,
        schema_version: str = CURRENT_SCHEMA_VERSION,
    ) -> AnomalyOutputRow:
        """Create State A or State B scored row."""
        row = AnomalyOutputRow(
            schema_version=schema_version,
            row_index=int(row_index),
            channel=str(channel),
            anomaly_score=float(score),
            is_anomaly_flagged=bool(is_flagged),
            anomaly_status=AnomalyStatus.SCORED.value,
            reason_code=None,
            alert_budget_selected=bool(is_flagged),
        )
        validate_output_row(row)
        return row

    @classmethod
    def create_degraded_row(
        cls,
        row_index: int,
        channel: str,
        reason_code: str = ReasonCode.ALL_ANOMALY_FEATURES_INACTIVE.value,
        schema_version: str = CURRENT_SCHEMA_VERSION,
    ) -> AnomalyOutputRow:
        """Create State C degraded unscorable row."""
        row = AnomalyOutputRow(
            schema_version=schema_version,
            row_index=int(row_index),
            channel=str(channel),
            anomaly_score=None,
            is_anomaly_flagged=None,
            anomaly_status=AnomalyStatus.DEGRADED_UNSCORABLE.value,
            reason_code=str(reason_code),
            alert_budget_selected=False,
        )
        validate_output_row(row)
        return row

    @classmethod
    def to_dataframe(cls, rows: List[AnomalyOutputRow]) -> pd.DataFrame:
        """Convert list of AnomalyOutputRows to structured pandas DataFrame."""
        for r in rows:
            validate_output_row(r)
        data = [r.to_dict() for r in rows]
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=cls.COLUMN_NAMES)
        return df[cls.COLUMN_NAMES]

