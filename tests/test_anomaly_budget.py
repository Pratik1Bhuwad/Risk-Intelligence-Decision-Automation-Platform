"""
Unit tests for Global Combined Alert Budget Selection (Specification v2.3.2 §2).
"""

import math
import pytest

from src.anomaly.budget import AlertBudgetSelector, BudgetResult
from src.anomaly.schema import AnomalyOutputSchema, AnomalyStatus


def test_global_combined_alert_budget():
    """
    Verify K = floor(0.0100 * N_S) across combined TRANSFER and CASH_OUT population.
    Verify budget is NOT independently allocated 1% to each channel.
    """
    selector = AlertBudgetSelector(budget_rate=0.0100)

    # Create 300 TRANSFER rows and 200 CASH_OUT rows -> Total N_S = 500
    # K = floor(0.0100 * 500) = 5
    rows = []
    # Make TRANSFER have the highest anomaly scores (top 5)
    for i in range(300):
        score = 0.90 + (i * 0.001)  # High scores for TRANSFER
        rows.append(AnomalyOutputSchema.create_scored_row(i, "TRANSFER", score, False))

    for j in range(200):
        score = 0.10 + (j * 0.001)  # Low scores for CASH_OUT
        rows.append(AnomalyOutputSchema.create_scored_row(300 + j, "CASH_OUT", score, False))

    selected_rows, result = selector.select_alerts(scored_rows=rows)

    assert result.budget_denominator == 500
    assert result.budget_k == 5
    assert result.selected_alert_count == 5
    assert result.alert_rate_scored == 5 / 500  # Exactly 0.0100

    # Since all top scores were TRANSFER, all 5 alerts should be TRANSFER
    # Proves budget is global, NOT 1% independently per channel!
    alerts = [r for r in selected_rows if r.is_anomaly_flagged]
    assert len(alerts) == 5
    assert all(r.channel == "TRANSFER" for r in alerts)
    assert result.channel_breakdown["TRANSFER"]["alerts"] == 5
    assert result.channel_breakdown["CASH_OUT"]["alerts"] == 0


def test_deterministic_tie_breaking_by_row_index():
    """
    Verify deterministic tie-breaking: on equal anomaly scores,
    transactions are ranked strictly by ascending immutable row_index.
    """
    selector = AlertBudgetSelector(budget_rate=0.50)  # 50% budget to select top 1 out of 2

    # Two rows with IDENTICAL anomaly scores
    r_high_idx = AnomalyOutputSchema.create_scored_row(100, "TRANSFER", 0.85, False)
    r_low_idx = AnomalyOutputSchema.create_scored_row(5, "TRANSFER", 0.85, False)

    # Pass in shuffled order (high index first)
    selected_rows, result = selector.select_alerts(scored_rows=[r_high_idx, r_low_idx])

    assert result.budget_k == 1
    # Lower row_index (5) must win the tie-break over higher row_index (100)
    flagged = [r for r in selected_rows if r.is_anomaly_flagged]
    assert len(flagged) == 1
    assert flagged[0].row_index == 5
    assert flagged[0].alert_budget_selected is True


def test_zero_alert_budget():
    """Verify that when K = 0 (e.g. N_S < 100 at 1.00%), no alerts are selected."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    # 50 rows -> K = floor(0.0100 * 50) = 0
    rows = [AnomalyOutputSchema.create_scored_row(i, "TRANSFER", 0.5 + i * 0.01, False) for i in range(50)]
    selected_rows, result = selector.select_alerts(scored_rows=rows)

    assert result.budget_k == 0
    assert result.selected_alert_count == 0
    assert all(not r.is_anomaly_flagged for r in selected_rows)
    assert all(not r.alert_budget_selected for r in selected_rows)


def test_zero_scored_population_not_evaluable():
    """Verify that when N_S == 0, budget status is NOT_EVALUABLE and rate is null."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    degraded = [AnomalyOutputSchema.create_degraded_row(0, "TRANSFER")]

    selected_rows, result = selector.select_alerts(scored_rows=[], degraded_rows=degraded)

    assert result.budget_denominator == 0
    assert result.status == "NOT_EVALUABLE"
    assert result.alert_rate_scored is None  # Null rate, NOT fabricated 0.0!


def test_population_accounting_invariant():
    """Verify invariant: eligible_count = successfully_scored_count + unscored_count."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    scored = [AnomalyOutputSchema.create_scored_row(i, "TRANSFER", 0.5, False) for i in range(150)]
    degraded = [AnomalyOutputSchema.create_degraded_row(150 + j, "CASH_OUT") for j in range(10)]

    selected_rows, result = selector.select_alerts(
        scored_rows=scored,
        degraded_rows=degraded,
        ineligible_count=5,
    )

    assert result.input_count == 165
    assert result.eligible_count == 160  # 150 scored + 10 degraded
    assert result.ineligible_count == 5
    assert result.successfully_scored_count == 150
    assert result.unscored_eligible_count == 10  # 10 degraded eligible
    assert result.degraded_count == 10
    assert result.input_count == result.eligible_count + result.ineligible_count
    assert result.eligible_count == result.successfully_scored_count + result.unscored_eligible_count
    assert result.degraded_count <= result.unscored_eligible_count
    assert result.budget_k == 1  # floor(0.0100 * 150) = 1
    # Degraded rows must never be flagged as alerts
    degraded_out = [r for r in selected_rows if r.anomaly_status == AnomalyStatus.DEGRADED_UNSCORABLE.value]
    assert len(degraded_out) == 10
    assert all(r.is_anomaly_flagged is None for r in degraded_out)
    assert all(r.alert_budget_selected is False for r in degraded_out)


def test_population_accounting_mixed_eligible_and_ineligible():
    """Task 2: Verify accounting with mixed scored, degraded and ineligible transactions."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    scored = [AnomalyOutputSchema.create_scored_row(i, "TRANSFER", 0.5 + i * 0.001, False) for i in range(200)]
    degraded = [AnomalyOutputSchema.create_degraded_row(200 + j, "CASH_OUT") for j in range(15)]
    ineligible = 50

    _, res = selector.select_alerts(scored_rows=scored, degraded_rows=degraded, ineligible_count=ineligible)

    assert res.input_count == 265
    assert res.eligible_count == 215
    assert res.ineligible_count == 50
    assert res.successfully_scored_count == 200
    assert res.unscored_eligible_count == 15
    assert res.degraded_count == 15
    assert res.selected_alert_count == 2
    assert res.budget_k == 2  # floor(0.0100 * 200)

    # Invariants
    assert res.input_count == res.eligible_count + res.ineligible_count
    assert res.eligible_count == res.successfully_scored_count + res.unscored_eligible_count
    assert res.degraded_count <= res.unscored_eligible_count
    assert res.budget_k == math.floor(0.0100 * res.successfully_scored_count)


def test_population_accounting_all_ineligible():
    """Task 2: Verify accounting when entire batch consists of ineligible channels."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    _, res = selector.select_alerts(scored_rows=[], degraded_rows=[], ineligible_count=100)

    assert res.input_count == 100
    assert res.eligible_count == 0
    assert res.ineligible_count == 100
    assert res.successfully_scored_count == 0
    assert res.unscored_eligible_count == 0
    assert res.degraded_count == 0
    assert res.selected_alert_count == 0
    assert res.budget_k == 0
    assert res.status == "NOT_EVALUABLE"
    assert res.alert_rate_scored is None
    assert res.alert_rate_all_eligible is None

    # Invariants
    assert res.input_count == res.eligible_count + res.ineligible_count
    assert res.eligible_count == res.successfully_scored_count + res.unscored_eligible_count
    assert res.degraded_count <= res.unscored_eligible_count


def test_population_accounting_eligible_but_degraded():
    """Task 2: Verify accounting when all eligible transactions are degraded/unscorable."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    degraded = [AnomalyOutputSchema.create_degraded_row(i, "TRANSFER") for i in range(25)]
    _, res = selector.select_alerts(scored_rows=[], degraded_rows=degraded, ineligible_count=0)

    assert res.input_count == 25
    assert res.eligible_count == 25
    assert res.ineligible_count == 0
    assert res.successfully_scored_count == 0
    assert res.unscored_eligible_count == 25
    assert res.degraded_count == 25
    assert res.selected_alert_count == 0
    assert res.budget_k == 0
    assert res.status == "NOT_EVALUABLE"
    assert res.alert_rate_scored is None
    assert res.alert_rate_all_eligible == 0.0

    # Invariants
    assert res.input_count == res.eligible_count + res.ineligible_count
    assert res.eligible_count == res.successfully_scored_count + res.unscored_eligible_count
    assert res.degraded_count <= res.unscored_eligible_count


def test_population_accounting_partially_scored_eligible():
    """Task 2: Verify rates when part of eligible population is degraded."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    scored = [AnomalyOutputSchema.create_scored_row(i, "TRANSFER", 0.6, False) for i in range(100)]
    degraded = [AnomalyOutputSchema.create_degraded_row(100 + j, "CASH_OUT") for j in range(50)]

    _, res = selector.select_alerts(scored_rows=scored, degraded_rows=degraded, ineligible_count=10)

    assert res.input_count == 160
    assert res.eligible_count == 150
    assert res.ineligible_count == 10
    assert res.successfully_scored_count == 100
    assert res.unscored_eligible_count == 50
    assert res.degraded_count == 50
    assert res.budget_k == 1
    assert res.selected_alert_count == 1
    assert math.isclose(res.alert_rate_scored, 1 / 100, rel_tol=1e-6)
    assert math.isclose(res.alert_rate_all_eligible, 1 / 150, rel_tol=1e-6)

    # Invariants
    assert res.input_count == res.eligible_count + res.ineligible_count
    assert res.eligible_count == res.successfully_scored_count + res.unscored_eligible_count
    assert res.degraded_count <= res.unscored_eligible_count


def test_population_accounting_empty_input():
    """Task 2: Verify accounting on completely empty input."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    rows, res = selector.select_alerts(scored_rows=[], degraded_rows=[], ineligible_count=0)

    assert len(rows) == 0
    assert res.input_count == 0
    assert res.eligible_count == 0
    assert res.ineligible_count == 0
    assert res.successfully_scored_count == 0
    assert res.unscored_eligible_count == 0
    assert res.degraded_count == 0
    assert res.budget_k == 0
    assert res.status == "NOT_EVALUABLE"
    assert res.alert_rate_scored is None
    assert res.alert_rate_all_eligible is None

    # Invariants
    assert res.input_count == res.eligible_count + res.ineligible_count
    assert res.eligible_count == res.successfully_scored_count + res.unscored_eligible_count


def test_population_accounting_zero_eligible_population():
    """Task 2: Verify accounting when eligible population is zero but ineligible exists."""
    selector = AlertBudgetSelector(budget_rate=0.0100)
    _, res = selector.select_alerts(scored_rows=[], degraded_rows=[], ineligible_count=75)

    assert res.input_count == 75
    assert res.eligible_count == 0
    assert res.ineligible_count == 75
    assert res.status == "NOT_EVALUABLE"
    assert res.budget_k == 0
    assert res.alert_rate_scored is None
    assert res.alert_rate_all_eligible is None
    assert res.input_count == res.eligible_count + res.ineligible_count


