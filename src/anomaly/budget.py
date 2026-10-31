"""
Phase 05 Global Alert Budget Selection and Deterministic Ranking.

Implements the combined 1.00% alert budget over successfully scored transactions
under Specification v2.3.2 Section 2:
  K = floor(0.0100 * N_S) where N_S = |S_T| + |S_C|
Deterministic tie-breaking on immutable row_index ascending.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.anomaly.schema import AnomalyOutputRow, AnomalyStatus, EligibleChannel


@dataclass(frozen=True)
class BudgetResult:
    """Run-level summary of alert budget application."""
    budget_rate: float
    input_count: int
    eligible_count: int
    ineligible_count: int
    successfully_scored_count: int
    unscored_eligible_count: int
    degraded_count: int
    selected_alert_count: int
    budget_denominator: int  # N_S
    budget_k: int
    status: str  # 'EVALUATED' or 'NOT_EVALUABLE'
    alert_rate_scored: Optional[float]
    alert_rate_all_eligible: Optional[float]
    channel_breakdown: Dict[str, Dict[str, Any]]
    unscored_count: int  # Alias for unscored_eligible_count
    degraded_unscorable_count: int  # Alias for degraded_count


class AlertBudgetSelector:
    """
    Applies global combined alert budget across eligible channels.
    Ranks scored rows by descending anomaly_score, breaking equal-score ties
    strictly by ascending immutable row_index.
    """

    def __init__(self, budget_rate: float = 0.0100):
        if budget_rate <= 0.0 or budget_rate > 1.0:
            raise ValueError(f"Invalid alert budget rate {budget_rate}: must be in (0, 1]")
        self.budget_rate = budget_rate

    def select_alerts(
        self,
        scored_rows: List[AnomalyOutputRow],
        degraded_rows: Optional[List[AnomalyOutputRow]] = None,
        ineligible_count: int = 0,
        unscored_eligible_count: Optional[int] = None,
    ) -> Tuple[List[AnomalyOutputRow], BudgetResult]:
        """
        Rank scored rows and select top K alerts under the global budget.

        Args:
            scored_rows: List of AnomalyOutputRows in SCORED state (from TRANSFER and CASH_OUT).
            degraded_rows: Optional list of AnomalyOutputRows in DEGRADED_UNSCORABLE state.
            ineligible_count: Count of transactions from ineligible channels (PAYMENT, CASH_IN, DEBIT).
            unscored_eligible_count: Optional explicit count of unscored eligible transactions.

        Returns:
            Tuple of (final_updated_rows, BudgetResult)
        """
        degraded_rows = degraded_rows or []
        n_scored = len(scored_rows)
        n_degraded = len(degraded_rows)
        n_unscored_eligible = unscored_eligible_count if unscored_eligible_count is not None else n_degraded
        n_eligible = n_scored + n_unscored_eligible
        n_ineligible = int(ineligible_count)
        n_input = n_eligible + n_ineligible

        # Zero-scored-population check
        if n_scored == 0:
            result = BudgetResult(
                budget_rate=self.budget_rate,
                input_count=n_input,
                eligible_count=n_eligible,
                ineligible_count=n_ineligible,
                successfully_scored_count=0,
                unscored_eligible_count=n_unscored_eligible,
                degraded_count=n_degraded,
                selected_alert_count=0,
                budget_denominator=0,
                budget_k=0,
                status="NOT_EVALUABLE",
                alert_rate_scored=None,
                alert_rate_all_eligible=0.0 if n_eligible > 0 else None,
                channel_breakdown={
                    EligibleChannel.TRANSFER.value: {"eligible": 0, "scored": 0, "unscored": 0, "degraded": 0, "alerts": 0},
                    EligibleChannel.CASH_OUT.value: {"eligible": 0, "scored": 0, "unscored": 0, "degraded": 0, "alerts": 0},
                },
                unscored_count=n_unscored_eligible,
                degraded_unscorable_count=n_degraded,
            )
            return list(degraded_rows), result

        # Compute K = floor(budget_rate * N_S)
        k = int(math.floor(self.budget_rate * n_scored))

        # Deterministic sorting:
        # Primary key: anomaly_score DESCENDING (-x.anomaly_score)
        # Secondary key: row_index ASCENDING (x.row_index)
        sorted_scored = sorted(
            scored_rows,
            key=lambda r: (-float(r.anomaly_score if r.anomaly_score is not None else 0.0), int(r.row_index)),
        )

        selected_indices = set()
        if k > 0:
            for r in sorted_scored[:k]:
                selected_indices.add(r.row_index)

        # Build updated output rows with authoritative budget flags
        updated_scored_rows: List[AnomalyOutputRow] = []
        channel_counts = {
            EligibleChannel.TRANSFER.value: {"eligible": 0, "scored": 0, "unscored": 0, "degraded": 0, "alerts": 0},
            EligibleChannel.CASH_OUT.value: {"eligible": 0, "scored": 0, "unscored": 0, "degraded": 0, "alerts": 0},
        }

        for r in sorted_scored:
            ch = r.channel
            is_selected = r.row_index in selected_indices
            updated_row = AnomalyOutputRow(
                schema_version=r.schema_version,
                row_index=r.row_index,
                channel=r.channel,
                anomaly_score=r.anomaly_score,
                is_anomaly_flagged=is_selected,
                anomaly_status=r.anomaly_status,
                reason_code=None,
                alert_budget_selected=is_selected,
            )
            updated_scored_rows.append(updated_row)

            if ch in channel_counts:
                channel_counts[ch]["scored"] += 1
                if is_selected:
                    channel_counts[ch]["alerts"] += 1

        # Channel breakdowns
        for d in degraded_rows:
            if d.channel in channel_counts:
                channel_counts[d.channel]["degraded"] += 1
                channel_counts[d.channel]["unscored"] += 1

        for ch in channel_counts:
            channel_counts[ch]["eligible"] = channel_counts[ch]["scored"] + channel_counts[ch]["unscored"]

        alert_rate_scored = float(len(selected_indices) / n_scored) if n_scored > 0 else None
        alert_rate_eligible = float(len(selected_indices) / n_eligible) if n_eligible > 0 else None

        budget_summary = BudgetResult(
            budget_rate=self.budget_rate,
            input_count=n_input,
            eligible_count=n_eligible,
            ineligible_count=n_ineligible,
            successfully_scored_count=n_scored,
            unscored_eligible_count=n_unscored_eligible,
            degraded_count=n_degraded,
            selected_alert_count=len(selected_indices),
            budget_denominator=n_scored,
            budget_k=k,
            status="EVALUATED",
            alert_rate_scored=alert_rate_scored,
            alert_rate_all_eligible=alert_rate_eligible,
            channel_breakdown=channel_counts,
            unscored_count=n_unscored_eligible,
            degraded_unscorable_count=n_degraded,
        )

        # Combine updated scored rows and degraded rows, sorted by row_index for clean output
        all_rows = sorted(updated_scored_rows + degraded_rows, key=lambda r: r.row_index)
        return all_rows, budget_summary

