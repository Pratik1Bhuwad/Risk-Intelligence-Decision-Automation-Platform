"""
Phase 06 Evaluation & Validation Module for Anomaly Detection.

Implements pure mathematical calculations, data-contract validation,
population-slicing logic, dual-framework metric calculations, and report formatting
under Protocol v1.2.7-DRAFT and Specification v2.3.2.

RESTRICTION NOTICE:
This module contains pure evaluation logic only. In accordance with Phase 06
governance, it intentionally contains NO execution orchestrator, NO CLI entry point,
and NO automated invocation of Phase 05 detector fitting or scoring on real data.
All fitting and scoring execution remains subject to separate, explicit Project-Owner
authorization.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import numpy as np
import pandas as pd

from src.features.policy import STRICTLY_EXCLUDED_FIELDS
from src.features.metadata import FEATURE_CATALOG
from src.anomaly.schema import (
    CURRENT_SCHEMA_VERSION,
    AnomalyOutputRow,
    AnomalyStatus,
    EligibleChannel,
    ReasonCode,
)

# ==============================================================================
# PROTOCOL CONSTANTS & GOVERNANCE BASELINE
# ==============================================================================

PROTOCOL_VERSION: str = "v1.2.7-DRAFT"

# Gate 4: Ratified Retrospective Alert-Budget Sensitivity Scenarios
APPROVED_ALERT_BUDGET_SCENARIOS: Tuple[float, ...] = (0.0010, 0.0050, 0.0100, 0.0200)

# Gate 6.2: Ratified PSI Smoothing Floor added ONLY to zero-valued cells
DEFAULT_PSI_EPSILON: float = 1e-4
DEFAULT_PSI_BINS: int = 10

# Status Codes
STATUS_COMPLETED: str = "COMPLETED"
STATUS_NOT_EVALUABLE: str = "NOT_EVALUABLE"
STATUS_EVALUATED: str = "EVALUATED"

# Gate 1 & Gate 3: Partition Boundary Steps
STEP_RANGE_REFERENCE: Tuple[int, int] = (1, 400)
STEP_RANGE_PRELIMINARY_VALIDATION: Tuple[int, int] = (401, 550)
STEP_RANGE_QUALIFIED_HOLDOUT: Tuple[int, int] = (551, 743)
STEP_RANGE_CONTINUOUS_EVALUATION: Tuple[int, int] = (401, 743)

# Physical Verified Eligible Row Denominators (TRANSFER + CASH_OUT)
ELIGIBLE_DENOMINATOR_REFERENCE: int = 2_529_536
ELIGIBLE_DENOMINATOR_PRELIMINARY_VALIDATION: int = 158_652
ELIGIBLE_DENOMINATOR_QUALIFIED_HOLDOUT: int = 82_221
ELIGIBLE_DENOMINATOR_CONTINUOUS_EVALUATION: int = 240_873

# Eligible Channels
ELIGIBLE_CHANNELS: Set[str] = {"TRANSFER", "CASH_OUT"}


# ==============================================================================
# DATA CONTRACT VALIDATION & POPULATION SLICING
# ==============================================================================

def validate_evaluation_data_contract(
    df: pd.DataFrame,
    require_target: bool = True,
    expected_features: Optional[List[str]] = None,
) -> None:
    """
    Validate that an input evaluation DataFrame conforms to contract invariants.

    Args:
        df: Input DataFrame to validate.
        require_target: If True, asserts presence of 'isFraud'.
        expected_features: List of 36 expected canonical feature names.

    Raises:
        ValueError: If mandatory columns are missing, nulls occur in row_index,
                    duplicate row_indices exist, or feature dimensions mismatch.
        TypeError: If row_index is not integer dtype.
    """
    if expected_features is None:
        expected_features = list(FEATURE_CATALOG.keys())

    cols = set(df.columns)

    # 1. Row index validation if present
    if "row_index" in cols:
        if df["row_index"].isnull().any():
            raise ValueError("Evaluation data contract violation: 'row_index' contains null values.")
        if not pd.api.types.is_integer_dtype(df["row_index"]):
            raise TypeError("Evaluation data contract violation: 'row_index' must be integer dtype.")
        if df["row_index"].duplicated().any():
            dup_count = int(df["row_index"].duplicated().sum())
            raise ValueError(f"Evaluation data contract violation: 'row_index' contains {dup_count} duplicates.")

    # 2. Temporal & Channel fields presence check (raw or one-hot)
    has_step = "step" in cols
    has_cyclical = "day_of_simulation" in cols and "hour_of_day" in cols
    if not (has_step or has_cyclical):
        raise ValueError(
            "Evaluation data contract violation: missing temporal fields. "
            "Must provide either 'step' or both 'day_of_simulation' and 'hour_of_day'."
        )

    has_raw_type = "type" in cols
    has_one_hot = "is_transfer" in cols and "is_cash_out" in cols
    if not (has_raw_type or has_one_hot):
        raise ValueError(
            "Evaluation data contract violation: missing channel fields. "
            "Must provide either 'type' or one-hot flags ('is_transfer', 'is_cash_out')."
        )

    # 3. Target label presence check if required
    if require_target and "isFraud" not in cols:
        raise ValueError("Evaluation data contract violation: required target column 'isFraud' is missing.")

    # 4. Canonical features presence check
    missing_feats = [f for f in expected_features if f not in cols]
    if missing_feats:
        raise ValueError(
            f"Evaluation data contract violation: missing {len(missing_feats)} canonical features: {missing_feats}"
        )


def reconstruct_step_and_channel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reconstruct discrete simulation 'step' and string channel 'type' from one-hot features.

    Exact identities:
      step = day_of_simulation * 24 + hour_of_day
      type = 'TRANSFER' if is_transfer==1 else 'CASH_OUT' if is_cash_out==1 ...

    Args:
        df: DataFrame containing temporal and one-hot channel features.

    Returns:
        DataFrame with 'step' and 'type' populated.
    """
    out_df = df.copy()

    # Reconstruct step if missing
    if "step" not in out_df.columns:
        if "day_of_simulation" not in out_df.columns or "hour_of_day" not in out_df.columns:
            raise KeyError("Cannot reconstruct 'step': 'day_of_simulation' and 'hour_of_day' must be present.")
        out_df["step"] = (
            out_df["day_of_simulation"].astype(int) * 24 + out_df["hour_of_day"].astype(int)
        ).astype(int)

    # Reconstruct type if missing
    if "type" not in out_df.columns:
        type_series = pd.Series("OTHER", index=out_df.index, dtype=object)
        if "is_transfer" in out_df.columns:
            type_series = type_series.mask(out_df["is_transfer"] == 1, "TRANSFER")
        if "is_cash_out" in out_df.columns:
            type_series = type_series.mask(out_df["is_cash_out"] == 1, "CASH_OUT")
        if "is_payment" in out_df.columns:
            type_series = type_series.mask(out_df["is_payment"] == 1, "PAYMENT")
        if "is_cash_in" in out_df.columns:
            type_series = type_series.mask(out_df["is_cash_in"] == 1, "CASH_IN")
        if "is_debit" in out_df.columns:
            type_series = type_series.mask(out_df["is_debit"] == 1, "DEBIT")
        out_df["type"] = type_series

    return out_df


def extract_clean_features_and_target(
    df: pd.DataFrame,
    expected_features: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Decouple ground-truth target 'isFraud' and strip prohibited leakage fields.

    Produces a clean DataFrame strictly suitable for input to Phase 05 preprocessor/engine.

    Args:
        df: Full feature DataFrame.
        expected_features: 36 canonical anomaly features.

    Returns:
        Tuple of (clean_df, y_true).
    """
    if expected_features is None:
        expected_features = list(FEATURE_CATALOG.keys())

    y_true: Optional[pd.Series] = None
    if "isFraud" in df.columns:
        y_true = df["isFraud"].copy()

    # Base columns to retain
    retained_cols: List[str] = []
    if "row_index" in df.columns:
        retained_cols.append("row_index")
    if "type" in df.columns:
        retained_cols.append("type")
    if "step" in df.columns:
        retained_cols.append("step")

    for f in expected_features:
        if f in df.columns and f not in retained_cols:
            retained_cols.append(f)

    clean_df = df[retained_cols].copy()

    # Assert zero prohibited field leakage
    leakage = set(clean_df.columns).intersection(STRICTLY_EXCLUDED_FIELDS)
    if leakage:
        raise ValueError(f"Prohibited field leakage detected in clean DataFrame: {sorted(list(leakage))}")

    return clean_df, y_true


def slice_evaluation_population(
    df: pd.DataFrame,
    step_range: Tuple[int, int],
) -> pd.DataFrame:
    """
    Slice evaluation DataFrame to a forward-chained temporal step partition.

    Args:
        df: Input DataFrame with 'step' column.
        step_range: Tuple of (min_step, max_step) inclusive.

    Returns:
        Filtered DataFrame partition.
    """
    if "step" not in df.columns:
        raise KeyError("Cannot slice evaluation population: missing 'step' column.")

    min_s, max_s = step_range
    mask = (df["step"] >= min_s) & (df["step"] <= max_s)
    return df.loc[mask].copy()


# ==============================================================================
# PURE MATHEMATICAL PSI CALCULATOR (SELECTIVE SMOOTHING)
# ==============================================================================

def compute_psi(
    reference_scores: Union[np.ndarray, pd.Series, Sequence[float]],
    evaluation_scores: Union[np.ndarray, pd.Series, Sequence[float]],
    num_bins: int = DEFAULT_PSI_BINS,
    epsilon: float = DEFAULT_PSI_EPSILON,
) -> Dict[str, Any]:
    """
    Compute channel Population Stability Index (PSI) using linear decile cut-points,
    empty-population short-circuiting, and selective zero-cell smoothing.

    Execution Sequence (Protocol v1.2.7-DRAFT Section 7.1):
      1. Filter finite numeric scores (-inf < s < +inf). Zero (s=0.0) is finite and included.
      2. If |S_ref| == 0 or |S_eval| == 0 -> TERMINATE IMMEDIATELY with NOT_EVALUABLE.
      3. Compute internal decile cut points q_1..q_9 via Series.quantile(interpolation='linear').
      4. Collapse duplicate cut points; exclude min and max.
      5. If zero internal cut points remain (m == 0) -> TERMINATE with NOT_EVALUABLE.
      6. Form M = m + 1 mutually exclusive, collectively exhaustive bins.
      7. Calculate raw bin proportions Q_b and P_b.
      8. Selective smoothing: add epsilon ONLY if proportion == 0. Nonzero cells unchanged.
      9. Independently renormalize P* and Q* to sum to 1.0.
      10. Sum: PSI = sum (P*_b - Q*_b) * ln(P*_b / Q*_b).

    Args:
        reference_scores: In-sample baseline scores (e.g. steps 1-400).
        evaluation_scores: Out-of-sample evaluation scores.
        num_bins: Number of target quantile bins (default 10 for deciles).
        epsilon: Smoothing floor added only to zero-count bins (default 1e-4).

    Returns:
        Dictionary with calculation details and PSI value.
    """
    # 1. Filter finite numeric scores
    ref_arr = np.asarray(reference_scores, dtype=float)
    eval_arr = np.asarray(evaluation_scores, dtype=float)

    ref_finite = ref_arr[np.isfinite(ref_arr)]
    eval_finite = eval_arr[np.isfinite(eval_arr)]

    n_ref_finite = int(len(ref_finite))
    n_eval_finite = int(len(eval_finite))
    n_ref_nonfinite = int(len(ref_arr) - n_ref_finite)
    n_eval_nonfinite = int(len(eval_arr) - n_eval_finite)

    # 2. Immediate Empty-Population Short-Circuit
    if n_ref_finite == 0 or n_eval_finite == 0:
        return {
            "psi": None,
            "status": STATUS_NOT_EVALUABLE,
            "reason": "EMPTY_FINITE_POPULATION",
            "n_ref_finite": n_ref_finite,
            "n_eval_finite": n_eval_finite,
            "n_ref_nonfinite": n_ref_nonfinite,
            "n_eval_nonfinite": n_eval_nonfinite,
            "num_bins": 0,
            "cut_points": [],
            "q_proportions": [],
            "p_proportions": [],
        }

    # 3. Quantile cut-point calculation using pandas interpolation="linear"
    ref_series = pd.Series(ref_finite)
    quantiles = np.linspace(0.0, 1.0, num_bins + 1)[1:-1]  # deciles 0.1, 0.2, ..., 0.9
    raw_cuts = ref_series.quantile(quantiles, interpolation="linear").to_numpy(dtype=float)

    # 4. Collapse duplicate cut points and exclude min/max boundaries
    ref_min = float(np.min(ref_finite))
    ref_max = float(np.max(ref_finite))

    unique_cuts = sorted(list(set(raw_cuts.tolist())))
    # Filter strictly interior cut points: ref_min < c < ref_max
    interior_cuts = [c for c in unique_cuts if ref_min < c < ref_max]

    # 5. Degenerate distribution check (zero score variance or complete collapse)
    m = len(interior_cuts)
    if m == 0:
        return {
            "psi": None,
            "status": STATUS_NOT_EVALUABLE,
            "reason": "ZERO_SCORE_VARIANCE_COLLAPSED_BINS",
            "n_ref_finite": n_ref_finite,
            "n_eval_finite": n_eval_finite,
            "n_ref_nonfinite": n_ref_nonfinite,
            "n_eval_nonfinite": n_eval_nonfinite,
            "num_bins": 1,
            "cut_points": [],
            "q_proportions": [],
            "p_proportions": [],
        }

    # 6. Form M = m + 1 mutually exclusive, collectively exhaustive bins
    # Bin 1: (-inf, c_1]
    # Bin b: (c_{b-1}, c_b]
    # Bin M: (c_m, +inf)
    # Using np.digitize: bins = [c_1, c_2, ..., c_m], right=True
    # digitize returns 0 for <= c_1, 1 for (c_1, c_2], ..., m for > c_m
    ref_bin_indices = np.digitize(ref_finite, bins=interior_cuts, right=True)
    eval_bin_indices = np.digitize(eval_finite, bins=interior_cuts, right=True)

    num_total_bins = m + 1
    ref_counts = np.bincount(ref_bin_indices, minlength=num_total_bins)
    eval_counts = np.bincount(eval_bin_indices, minlength=num_total_bins)

    # 7. Raw bin proportions
    q_raw = ref_counts.astype(float) / n_ref_finite
    p_raw = eval_counts.astype(float) / n_eval_finite

    # 8. Selective smoothing: add epsilon ONLY to zero-valued cells
    q_tilde = np.where(q_raw == 0.0, q_raw + epsilon, q_raw)
    p_tilde = np.where(p_raw == 0.0, p_raw + epsilon, p_raw)

    # 9. Independent renormalization
    q_star = q_tilde / np.sum(q_tilde)
    p_star = p_tilde / np.sum(p_tilde)

    # 10. PSI Summation
    # Each term: (p_b - q_b) * ln(p_b / q_b)
    psi_terms = (p_star - q_star) * np.log(p_star / q_star)
    psi_value = float(np.sum(psi_terms))

    return {
        "psi": float(round(psi_value, 6)),
        "status": STATUS_COMPLETED,
        "reason": None,
        "n_ref_finite": n_ref_finite,
        "n_eval_finite": n_eval_finite,
        "n_ref_nonfinite": n_ref_nonfinite,
        "n_eval_nonfinite": n_eval_nonfinite,
        "num_bins": num_total_bins,
        "cut_points": [float(c) for c in interior_cuts],
        "q_proportions": [float(q) for q in q_star],
        "p_proportions": [float(p) for p in p_star],
        "bin_psi_contributions": [float(t) for t in psi_terms],
    }


# ==============================================================================
# GATE 6.1 DUAL-FRAMEWORK DIAGNOSTIC METRIC CALCULATOR
# ==============================================================================

def compute_gate6_diagnostic_metrics(
    eligible_count: int,
    scored_count: int,
    degraded_count: int,
    f_elig: int,
    f_scored: int,
    tp_k: int,
    k: int,
    score_psi: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute all seven approved Gate 6.1 diagnostic metrics adhering to boundary conditions.

    Metrics:
      1. T_deg: Degraded Unscorable Rate = degraded_count / eligible_count
      2. T_psi: Population Stability Index (provided from compute_psi)
      3. T_prec: Alert Precision = TP_k / k
      4. T_rec_scored: Scored Fraud Recall = TP_k / f_scored
      5. T_rec_elig: Eligible Fraud Recall = TP_k / f_elig
      6. T_cov: Fraud Scoring Coverage = f_scored / f_elig
      7. T_enrich: Fraud Enrichment Factor = Prec / (f_scored / scored_count)

    Boundary Rules:
      - If eligible_count == 0 -> T_deg is NOT_EVALUABLE.
      - If k == 0 -> T_prec is NOT_EVALUABLE.
      - If f_scored == 0:
          T_rec_scored is NOT_EVALUABLE.
          If f_elig > 0: T_rec_elig is 0.0 (by primary definition TP_k / f_elig = 0 / f_elig).
          T_cov is 0.0 (0 / f_elig).
      - If f_elig == 0 -> T_rec_elig and T_cov are NOT_EVALUABLE.

    Returns:
      Dictionary mapping each target symbol and descriptive name to its computed value.
    """
    # 1. T_deg
    if eligible_count > 0:
        t_deg: Optional[float] = float(degraded_count) / float(eligible_count)
    else:
        t_deg = None

    # 2. T_psi
    t_psi = score_psi

    # 3. T_prec
    if k > 0:
        t_prec: Optional[float] = float(tp_k) / float(k)
    else:
        t_prec = None

    # 4. T_rec_scored
    if f_scored > 0:
        t_rec_scored: Optional[float] = float(tp_k) / float(f_scored)
    else:
        t_rec_scored = None

    # 5. T_rec_elig & 6. T_cov
    if f_elig > 0:
        t_rec_elig: Optional[float] = float(tp_k) / float(f_elig)
        t_cov: Optional[float] = float(f_scored) / float(f_elig)
    else:
        t_rec_elig = None
        t_cov = None

    # 7. T_enrich (Lift over base fraud prevalence in scored population)
    if t_prec is not None and scored_count > 0 and f_scored > 0:
        scored_prevalence = float(f_scored) / float(scored_count)
        t_enrich: Optional[float] = t_prec / scored_prevalence if scored_prevalence > 0 else None
    else:
        t_enrich = None

    return {
        "T_deg": t_deg,
        "T_psi": t_psi,
        "T_prec": t_prec,
        "T_rec_scored": t_rec_scored,
        "T_rec_elig": t_rec_elig,
        "T_cov": t_cov,
        "T_enrich": t_enrich,
    }


# ==============================================================================
# RETROSPECTIVE ALERT-BUDGET SENSITIVITY EVALUATOR
# ==============================================================================

def evaluate_budget_sensitivity(
    scored_df: pd.DataFrame,
    y_true: pd.Series,
    scenarios: Tuple[float, ...] = APPROVED_ALERT_BUDGET_SCENARIOS,
    eligible_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Conduct retrospective top-K sensitivity analysis across approved budget scenarios.

    Sorting & Slicing:
      - Denominator N_S = count of rows with status=='SCORED' and finite score.
      - For each alpha: K_alpha = floor(alpha * N_S).
      - Candidates sorted by composite key: (-anomaly_score, row_index).
      - Top K_alpha candidates receive alert.
      - Evaluates TP_alpha, Precision, Scored Recall, Eligible Recall, Coverage, and Enrichment.

    Args:
        scored_df: Scored DataFrame adhering to AnomalyOutputSchema.
        y_true: Ground truth target Series indexed by row_index or position-aligned.
        scenarios: Tuple of budget rates (default: 0.10%, 0.50%, 1.00%, 2.00%).
        eligible_count: Optional total eligible count (if None, derived from scored_df).

    Returns:
        Structured dictionary of sensitivity metrics across all scenarios.
    """
    if "row_index" not in scored_df.columns:
        raise ValueError("Input scored_df must contain 'row_index'.")
    if "anomaly_score" not in scored_df.columns:
        raise ValueError("Input scored_df must contain 'anomaly_score'.")
    if "anomaly_status" not in scored_df.columns:
        raise ValueError("Input scored_df must contain 'anomaly_status'.")

    # Map target series by row_index for deterministic O(1) label lookup
    if not isinstance(y_true.index, pd.Index) or not pd.api.types.is_integer_dtype(y_true.index):
        # Position aligned
        target_map = dict(zip(scored_df["row_index"], y_true))
    else:
        target_map = y_true.to_dict()

    # Identify scored candidates with finite scores
    scored_mask = (scored_df["anomaly_status"] == AnomalyStatus.SCORED.value) & scored_df["anomaly_score"].notnull()
    finite_mask = scored_mask & np.isfinite(scored_df["anomaly_score"])

    scored_candidates = scored_df.loc[finite_mask].copy()
    degraded_candidates = scored_df.loc[~finite_mask].copy()

    n_s = len(scored_candidates)
    n_degraded = len(degraded_candidates)
    n_elig = eligible_count if eligible_count is not None else (n_s + n_degraded)

    # Compute fraud counts in eligible and scored populations
    all_row_indices = scored_df["row_index"].tolist()
    f_elig = sum(1 for r in all_row_indices if target_map.get(r, 0) == 1)

    scored_row_indices = scored_candidates["row_index"].tolist()
    f_scored = sum(1 for r in scored_row_indices if target_map.get(r, 0) == 1)
    f_unscored = f_elig - f_scored

    # Sort scored candidates deterministically by (-anomaly_score, row_index)
    sorted_candidates = scored_candidates.sort_values(
        by=["anomaly_score", "row_index"],
        ascending=[False, True],
    ).reset_index(drop=True)

    sensitivity_results: Dict[str, Any] = {
        "n_eligible": n_elig,
        "n_scored": n_s,
        "n_degraded": n_degraded,
        "f_eligible": f_elig,
        "f_scored": f_scored,
        "f_unscored": f_unscored,
        "scenarios": {},
    }

    for alpha in scenarios:
        pct_key = f"{alpha * 100:.2f}%"
        k_alpha = int(math.floor(alpha * n_s))

        if k_alpha == 0 or n_s == 0:
            sensitivity_results["scenarios"][pct_key] = {
                "alpha": alpha,
                "K": 0,
                "status": STATUS_NOT_EVALUABLE,
                "TP": 0,
                "FP": 0,
                "precision": None,
                "scored_fraud_recall": None,
                "eligible_fraud_recall": 0.0 if f_elig > 0 else None,
                "fraud_scoring_coverage": float(f_scored) / float(f_elig) if f_elig > 0 else None,
                "enrichment_factor": None,
                "effective_score_threshold": None,
            }
            continue

        # Top K alerts
        top_k_rows = sorted_candidates.iloc[:k_alpha]
        selected_indices = top_k_rows["row_index"].tolist()
        threshold_score = float(top_k_rows.iloc[-1]["anomaly_score"])

        tp = sum(1 for r in selected_indices if target_map.get(r, 0) == 1)
        fp = k_alpha - tp

        # Calculate metrics using Gate 6.1 helper
        metrics = compute_gate6_diagnostic_metrics(
            eligible_count=n_elig,
            scored_count=n_s,
            degraded_count=n_degraded,
            f_elig=f_elig,
            f_scored=f_scored,
            tp_k=tp,
            k=k_alpha,
            score_psi=None,
        )

        sensitivity_results["scenarios"][pct_key] = {
            "alpha": alpha,
            "K": k_alpha,
            "status": STATUS_EVALUATED,
            "TP": tp,
            "FP": fp,
            "precision": metrics["T_prec"],
            "scored_fraud_recall": metrics["T_rec_scored"],
            "eligible_fraud_recall": metrics["T_rec_elig"],
            "fraud_scoring_coverage": metrics["T_cov"],
            "enrichment_factor": metrics["T_enrich"],
            "effective_score_threshold": threshold_score,
        }

    return sensitivity_results


# ==============================================================================
# PROTOCOL EVALUATION REPORT FORMATTER
# ==============================================================================

def format_evaluation_report(
    config_digests: Tuple[str, str],
    population_metrics: Dict[str, Any],
    psi_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Format the complete evaluation report adhering to Protocol Section 7 JSON schema.

    Enforces mandatory caveats:
      - Synthetic PaySim simulation disclaimer
      - Prohibited marketing claims prohibition
      - Explicit in-sample baseline limitation disclosure for PSI

    Args:
        config_digests: Tuple of (raw_sha256, semantic_sha256).
        population_metrics: Summary of population counts and degradation rates.
        psi_results: Channel-specific PSI results.
        sensitivity_results: 4-scenario sensitivity metrics.
        notes: Optional extra narrative notes.

    Returns:
        Strict JSON-serializable report dictionary.
    """
    raw_sha, ast_sha = config_digests

    report: Dict[str, Any] = {
        "protocol_version": PROTOCOL_VERSION,
        "config_provenance": {
            "raw_sha256": raw_sha,
            "ast_sha256": ast_sha,
        },
        "mandatory_caveats": [
            "All findings reflect evaluation on the synthetic PaySim mobile money agent simulation; "
            "performance does not guarantee real-world banking detection efficacy against human adversaries.",
            "Universal fraud prevention, zero-day interception, and complete account takeover immunity "
            "are strictly prohibited claims.",
            "The standalone anomaly engine is defined as an unsupervised behavioral surveillance layer "
            "operating independently of supervised ML models.",
            "PSI measures divergence against an in-sample reference baseline (steps 1-400); "
            "differences may partly reflect in-sample vs out-of-sample scoring rather than pure temporal drift.",
        ],
        "populations": population_metrics,
        "psi_stability": psi_results,
        "budget_sensitivity": sensitivity_results,
        "governance_status": {
            "alert_budget_rates": list(APPROVED_ALERT_BUDGET_SCENARIOS),
            "psi_smoothing_epsilon": DEFAULT_PSI_EPSILON,
            "gate_6_1_framework": "Dual Evaluation Framework (Unsupervised Characterization & Fraud Alignment)",
        },
        "notes": notes or [],
    }

    return report

