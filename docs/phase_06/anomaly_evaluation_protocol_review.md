# Phase 06 — Independent Evaluation Protocol Source-Code Audit Report

**Document Title**: Phase 06 — Independent Evaluation Protocol Source-Code Audit Report  
**Document Path**: `docs/phase_06/anomaly_evaluation_protocol_review.md`  
**Audit Target**: Standalone Anomaly Detection Engine (`src/anomaly/`)  
**Specification Baseline**: Phase 05 Approved Specification v2.3.2  
**Configuration Baseline**: `configs/anomaly_detection.yaml` (FROZEN BASELINE)  
**Evaluation Protocol**: `docs/models/anomaly_evaluation_protocol.md` (Version `v1.3.0`)  
**Audit Date**: November 2026  
**Audit Status**: **AUDIT COMPLETE — TECHNICAL READINESS CONFIRMED (BASELINE FOR PROTOCOL v1.3.0)**  

---

## 1. Executive Summary & Audit Scope

This document provides a strict, independent, read-only technical audit of the Phase 05 Anomaly Detection Engine implementation against the official evaluation protocol **`docs/models/anomaly_evaluation_protocol.md` (v1.3.0)**.

### Core Audit Objectives:
1. **Invariant Verification**: Determine whether the existing implementation under `src/anomaly/` satisfies all technical assumptions, input validation rules, state semantics, and mathematical invariants defined in the evaluation protocol.
2. **Metric Feasibility Assessment**: Verify whether the existing engine exposes sufficient outputs to compute the proposed evaluation metrics (unsupervised characterization, PSI stability, fraud alignment recall/coverage) without requiring alterations to frozen code.
3. **Tooling & Interface Gap Analysis**: Identify existing reusable interfaces and document missing components (e.g., model serialization, CLI orchestration, evaluation data loaders) required for Phase 06 execution.
4. **Governance Assurance**: Confirm zero mutations to source code, configurations, test suites, or artifacts, and zero execution of unauthorized scoring or model fitting.

### Overall Audit Verdict:
- **Core Engine Conformance**: **PASS (100% Invariant Compliance)**. The implementation in `src/anomaly/` strictly complies with every mandatory protocol invariant (zero prohibited field leakage, immutable row indexing, channel-specific fitting, 4-tier fallback hierarchy, global alert budget ranking, deterministic tie-breaking, and explicit state discrimination).
- **Metric Feasibility**: **PASS (Feasible via Post-Hoc Tooling)**. All metrics formalized in `v1.3.0` are either directly available from engine outputs or deterministically derivable from output rows joined with the ground-truth target Series.
- **Evaluation Tooling Implementation**: Initial pure evaluation tooling has been implemented in `src/anomaly/evaluation.py` (660 lines) and verified by 22 synthetic unit tests in `tests/test_anomaly_evaluation.py` (463 lines, 22/22 passing). Operational model bundle serialization (`src/anomaly/artifacts.py`) and CLI integration (`src/cli.py`) remain deferred pending future operational orchestrator design. Real-data scoring remains strictly **NOT AUTHORIZED**.

---

## 2. Repository State & File Inventory

### 2.1 Git Repository State
- **Current Branch**: `main` (synchronized with `origin/main`).
- **HEAD Commit**: `95f40c55efa924c31e453c67a3a3e82a472a35cf` (*"test(anomaly): add unit, edge-case, temporal-window, and real-data integration test suites"*).
- **Working Tree Status**: Clean against tracked files; zero tracked files modified; single untracked draft document (`docs/models/anomaly_evaluation_protocol.md`).

### 2.2 Phase 05 & Phase 06 Source Code Inventory
| Source File | Line Count | SHA-256 Digest | Architectural Role | Status |
| :--- | :---: | :---: | :--- | :---: |
| [`src/anomaly/schema.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/schema.py) | 187 | `4c8d5236` | Eight-field decoupled output contract, `AnomalyOutputRow`, state validation | **PRESENT (FROZEN)** |
| [`src/anomaly/config.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/config.py) | 166 | `664c3983` | Config loader, 16-section validation, raw & semantic AST SHA-256 verifier | **PRESENT (FROZEN)** |
| [`src/anomaly/preprocessing.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py) | 284 | `26ff0185` | Input validator, 4-tier fallback hierarchy, robust centering/scaling | **PRESENT (FROZEN)** |
| [`src/anomaly/detector.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/detector.py) | 117 | `99e693ee` | Deterministic scikit-learn IsolationForest wrapper ($s_{\text{raw}} = -\text{score\_samples}$) | **PRESENT (FROZEN)** |
| [`src/anomaly/budget.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py) | 180 | `47c6e001` | Global alert budget ($K = \lfloor 0.0100 \times N_S \rfloor$), tie-breaker ($-\text{score}, \text{row\_index}$) | **PRESENT (FROZEN)** |
| [`src/anomaly/engine.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py) | 195 | `c6cb3e63` | End-to-end orchestration, channel dispatching, temporal boundary guard | **PRESENT (FROZEN)** |
| [`src/anomaly/__init__.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/__init__.py) | 38 | `bb3a9254` | Public API exports for anomaly detection subsystem | **PRESENT (FROZEN)** |
| [`src/anomaly/evaluation.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/evaluation.py) | 660 | `0144d8ff` | Pure evaluation math, contract checks, reconstruction, PSI, metrics, reports | **IMPLEMENTED & ACCEPTED** |
| `src/anomaly/artifacts.py` | — | — | Model bundle serialization / deserialization | **DEFERRED (OUT OF PURE SCOPE)** |

### 2.3 Anomaly Test Suite Inventory
The repository contains 9 frozen Phase 05 test suites under `tests/` (1,326 lines), plus the accepted Phase 06 evaluation test suite:
- `tests/test_anomaly_schema.py` (152 lines)
- `tests/test_anomaly_config.py` (81 lines)
- `tests/test_anomaly_preprocessing.py` (141 lines)
- `tests/test_anomaly_detector.py` (77 lines)
- `tests/test_anomaly_budget.py` (256 lines)
- `tests/test_anomaly_engine.py` (140 lines)
- `tests/test_anomaly_edge_cases.py` (247 lines)
- `tests/test_anomaly_temporal_windows.py` (235 lines)
- `tests/test_anomaly_real_data_integration.py` (362 lines)
- [`tests/test_anomaly_evaluation.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/tests/test_anomaly_evaluation.py) (463 lines, 22 synthetic unit tests — **IMPLEMENTED & ACCEPTED, 22/22 PASSING**)

---

## 3. Protocol-to-Implementation Audit Matrix

The following matrix maps each technical invariant and requirement from Protocol `v1.3.0` to the physical source code.

| Area | Requirement | Protocol Section | Implementation Source & Line Range | Implementation Behavior | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **A** | **Prohibited-Field Rejection** | §4.1, §8.1 Inv 1 | [`src/anomaly/preprocessing.py#L64-L69`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L64-L69) | Checks input columns against `STRICTLY_EXCLUDED_FIELDS` (`newbalanceOrig`, `newbalanceDest`, `oldbalanceDest`, `isFraud`, `isFlaggedFraud`). Raises `ValueError("Prediction Security Violation: Input contains prohibited fields...")`. | **PASS** |
| **A** | **Target Isolation (`isFraud`)** | §8.1 Inv 2 | [`src/features/policy.py#L128-L134`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/features/policy.py#L128-L134)<br>[`src/anomaly/engine.py#L118`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L118) | `isFraud` is defined as `ProjectFeaturePolicy.EXCLUDED_TARGET`. Neither `fit()` nor `score()` accesses it. If present in scoring payload, input validation immediately fails. | **PASS** |
| **A** | **Canonical 36-Feature Validation** | §4.1 | [`src/anomaly/preprocessing.py#L84-L89`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L84-L89) | Asserts all 36 canonical features from `FEATURE_CATALOG` are present in `df.columns`. Raises `ValueError` if any feature is missing. | **PASS** |
| **A** | **Feature NaN / Inf Guard** | §4.1, §8.1 Inv 4 | [`src/anomaly/preprocessing.py#L93-L101`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L93-L101) | Scans all feature columns for `isnull()` and `np.isneginf`/`np.isposinf`. Raises explicit `ValueError` identifying offending columns. | **PASS** |
| **B** | **Reference Fitting Boundary ($\text{steps} \le 400$)** | §5.3, §8.1 | [`src/anomaly/engine.py#L63-L73`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L63-L73) | If `step` column is present in `reference_df`, validates `max(reference_df['step']) <= train_max_step (400)`. Raises `ValueError("Temporal Leakage Violation...")` if violated. (Note: Gate 3 clarifies reference scope for evaluation baseline characterization while strictly preserving this frozen fitting boundary; zero refitting/retraining authorized). | **PASS** |
| **B** | **Four-Tier Fallback Hierarchy** | §4.1, §5.2 | [`src/anomaly/preprocessing.py#L103-L190`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L103-L190) | Evaluates Tier 1 (MAD $\times 1.4826$) $\to$ Tier 2 (IQR $/ 1.349$) $\to$ Tier 3 (positive-subset std with $\ge 10$ obs) $\to$ Tier 4 (exclusion with machine-readable reason). Zero arbitrary epsilon added. | **PASS** |
| **B** | **Channel-Conditioned Fitting Isolation** | §4.1, §5.1 | [`src/anomaly/preprocessing.py#L201-L230`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L201-L230) | Splits reference data strictly by `TRANSFER` and `CASH_OUT`. Computes separate medians, scales, and active feature masks for each channel. | **PASS** |
| **B** | **Fit/Transform Pipeline Symmetry** | §5.3 item 4 | [`src/anomaly/preprocessing.py#L245-L284`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L245-L284)<br>[`src/anomaly/engine.py#L88, L168`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L88) | Both reference fitting and evaluation scoring invoke identical `transform_channel(df, channel)` utilizing stored channel baselines. | **PASS** |
| **C** | **Row Index Contract & Immutability** | §8.1 Inv 3 | [`src/anomaly/preprocessing.py#L71-L82`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L71-L82)<br>[`src/anomaly/schema.py#L77-L79`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/schema.py#L77-L79) | Validates `row_index` presence, non-nullity, integer dtype, uniqueness, and non-negativity. Stored immutably on each `AnomalyOutputRow`. | **PASS** |
| **C** | **Output-to-Input Deterministic Alignment** | §8.1 Inv 3 | [`src/anomaly/budget.py#L178`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py#L178) | Combines scored and degraded rows and sorts output strictly by ascending `row_index`. Deterministic 1-to-1 mapping preserved. | **PASS** |
| **D** | **Eligible Channel Filtering** | §4.1, §6.1 | [`src/anomaly/engine.py#L142-L149`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L142-L149) | Evaluates only `TRANSFER` and `CASH_OUT`. Tallies non-eligible channels (`PAYMENT`, `CASH_IN`, `DEBIT`) in `ineligible_count`. | **PASS** |
| **D** | **All-Inactive Feature Fallback (State C)** | §8.1 Inv 6 | [`src/anomaly/engine.py#L155-L165`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L155-L165) | If $|A(x)| == 0$, emits `DEGRADED_UNSCORABLE` with reason code `ALL_ANOMALY_FEATURES_INACTIVE`, score `None`, and `alert_budget_selected = False`. | **PASS** |
| **E** | **Finite-Score Classification & Contract** | §8.1 Inv 4, Inv 6 | [`src/anomaly/schema.py#L86-L115`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/schema.py#L86-L115) | Validates: State A/B rows have non-null, finite score, null reason code, and flag parity; State C rows have null score, null flag, non-null reason code, and `alert_budget_selected = False`. | **PASS** |
| **F** | **Score Negation Convention** | §4.1, §6.1 | [`src/anomaly/detector.py#L115`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/detector.py#L115) | Computes $s_{\text{raw}}(x) = -\text{score\_samples}(x)$ so that higher values indicate greater anomaly severity. | **PASS** |
| **F** | **Global Alert Budget Capacity ($K$)** | §6.1, §8.1 Inv 5 | [`src/anomaly/budget.py#L104`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py#L104) | Evaluates $K = \lfloor \text{budget\_rate} \times N_S \rfloor$ using strictly successfully scored transactions ($N_S$). Excludes degraded and ineligible records. | **PASS** |
| **F** | **Deterministic Secondary Tie-Breaking** | §6.1, §8.1 Inv 5 | [`src/anomaly/budget.py#L109-L112`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py#L109-L112) | Sorts scored candidates globally by sort key `(-float(score), int(row_index))`. Lower `row_index` wins equal-score ties deterministically. | **PASS** |
| **F** | **Zero-Scored Boundary Condition ($N_S=0$)** | §6.1, §7.1 | [`src/anomaly/budget.py#L79-L101`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py#L79-L101) | When $N_S == 0$, returns `status="NOT_EVALUABLE"`, `alert_rate_scored=None` (not 0.0), and $K=0$. | **PASS** |
| **G** | **Ground-Truth Label Separation** | §7.1, §7.2 | [`src/features/policy.py#L128`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/features/policy.py#L128)<br>[`tests/test_anomaly_real_data_integration.py#L71`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/tests/test_anomaly_real_data_integration.py#L71) | `isFraud` is completely decoupled from the detector pipeline. Fraud evaluation is strictly post-hoc via external label join. | **PASS** |
| **H** | **Bitwise Reproducibility Controls** | §8.1 Inv 7 | [`src/anomaly/detector.py#L35, L46`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/detector.py#L35)<br>[`src/anomaly/config.py#L15-L16`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/config.py#L15-L16) | Enforces `random_state=42`, `n_jobs=1`, and dual cryptographic SHA-256 checks against frozen `configs/anomaly_detection.yaml`. | **PASS** |

---

## 4. Evaluation Protocol Metric Feasibility Assessment

The protocol `v1.3.0` specifies 10 key evaluation metrics and data structures. The table below evaluates whether the current implementation exposes sufficient outputs to support them without modifying frozen code:

| Metric / Output Requirement | Protocol Section | Feasibility Classification | Technical Evidence & Source Extraction Path |
| :--- | :--- | :---: | :--- |
| **Eligible Population Counts ($N_{\text{elig}}$)** | §6.2, §7.1 | **DIRECTLY AVAILABLE** | Exposed in `BudgetResult.eligible_count` returned directly by `engine.score()`. |
| **Successfully Scored Counts ($N_S$)** | §6.1, §6.2 | **DIRECTLY AVAILABLE** | Exposed in `BudgetResult.successfully_scored_count` and `BudgetResult.budget_denominator`. |
| **Unscored & Degraded Counts ($N_{\text{deg}}$)** | §7.1, §8.1 | **DIRECTLY AVAILABLE** | Exposed in `BudgetResult.degraded_count` and `BudgetResult.unscored_eligible_count`. |
| **Fraud Counts ($F_{\text{elig}}, F_{\text{scored}}, F_{\text{unscored}}$)** | §7.2 | **DERIVABLE FROM EXISTING OUTPUTS** | Because `isFraud` is excluded from the engine, fraud counts are derived by joining the input target Series `y_true` with `output_df["row_index"]`: $F_{\text{scored}} = y_{\text{true}}[\text{scored\_indices}].\text{sum}()$, $F_{\text{unscored}} = F_{\text{elig}} - F_{\text{scored}}$. |
| **Global Top-K Alert Selection ($K_{1.0\%}$)** | §6.1 | **DIRECTLY AVAILABLE** | Flagged records are directly marked with `is_anomaly_flagged = True` and `alert_budget_selected = True` in returned DataFrame. |
| **Retrospective Sensitivity Analysis ($K_{0.1\%}, K_{0.5\%}, K_{2.0\%}$)** | §6.2 | **DERIVABLE FROM EXISTING OUTPUTS** | Computed post-hoc from the single scored array `output_df` by sorting on `(-anomaly_score, row_index)` and slicing top $K_\alpha = \lfloor \alpha \times N_S \rfloor$ without rescoring. |
| **Precision & Recall ($\text{Prec}@K_\alpha, \text{Rec}_{\text{scored}}, \text{Rec}_{\text{elig}}$)** | §7.2 | **DERIVABLE FROM EXISTING OUTPUTS** | Derived by cross-tabulating flagged row indices with ground-truth fraud labels: $\text{TP}_\alpha = y_{\text{true}}[\text{alert\_indices}].\text{sum}()$. Boundary condition $F_{\text{scored}} = 0 \implies \text{Rec}_{\text{elig}} = 0.0$ evaluated cleanly. |
| **Fraud Scoring Coverage ($\text{Cov}_{\text{fraud}}$)** | §7.2 | **DERIVABLE FROM EXISTING OUTPUTS** | Derived as $\text{Cov}_{\text{fraud}} = F_{\text{scored}} / F_{\text{elig}}$ from ground-truth joined counts. |
| **Channel-Level Volume Breakdowns** | §5.1, §6.1 | **DIRECTLY AVAILABLE** | Exposed in `BudgetResult.channel_breakdown` dict containing eligible, scored, unscored, degraded, and alert counts per channel. |
| **Unsupervised Characterization & PSI** | §7.1 | **IMPLEMENTED & VERIFIED** | Anomaly score arrays $S_{\text{ref}}$ and $S_{\text{eval}}$ and active feature metadata are fully available in engine outputs and `preprocessor.channel_baselines`. Calculating linear deciles (`pandas.Series.quantile(..., interpolation='linear')`), cut points, selective smoothing ($\epsilon=10^{-4}$), PSI summation, Gate 6 diagnostic metrics, and structured reports is fully implemented in `src/anomaly/evaluation.py` and verified by 22 synthetic unit tests in `tests/test_anomaly_evaluation.py`. Zero modifications to Phase 05 source files (`src/anomaly/`). |

---

## 5. Protocol-Code Discrepancy & Finding Register

During static source analysis, five notable findings and architectural observations were recorded:

### Finding 1: Ingestion Data Format Mismatch (Severity: HIGH / Future Tooling Dependency)
- **Protocol Assumption**: The engine expects input DataFrames to contain `row_index` (integer), `type` (string), and the 36 canonical features, with `isFraud` omitted.
- **Implementation Reality**: The physical parquet files (`data/processed/paysim_features_full.parquet` and `paysim_features_100000.parquet`) contain the 36 features and `isFraud`. They do **not** store `step`, `type`, or `row_index`.
- **Risk**: Passing raw feature parquet files directly into `engine.score()` causes immediate failure (`ValueError("Prediction Security Violation: Input contains prohibited fields: ['isFraud']")` and missing `row_index`).
- **Required Resolution**: Phase 06 evaluation tooling (`src/anomaly/evaluation.py`) implements this exact deterministic transformation via pure functions:
  1. Assign immutable 0-based ordinal `row_index`: `df["row_index"] = np.arange(len(df), dtype=int)`.
  2. Reconstruct `step`: `(df["day_of_simulation"] * 24 + df["hour_of_day"]).astype(int)` via `reconstruct_step_and_channel()`.
  3. Reconstruct `type` from channel one-hot indicators via `reconstruct_step_and_channel()`.
  4. Decouple target label: `y_true = df["isFraud"].copy()`, `clean_df = df.drop(columns=["isFraud"])` via `extract_clean_features_and_target()`.

### Finding 2: Exclusion of Ineligible Channels from Output DataFrame (Severity: INFORMATIONAL)
- **Protocol Requirement**: Section 5.3 item 5 excludes non-eligible channels (`PAYMENT`, `CASH_IN`, `DEBIT`) from scoring.
- **Implementation State**: `engine.score()` omits ineligible channels from the returned `output_df` entirely (their volume is tallied in `BudgetResult.ineligible_count`). The output DataFrame contains only eligible transactions (`TRANSFER` and `CASH_OUT`).
- **Assessment**: Fully compliant with Schema specification Section 4.1 (`AnomalyOutputRow.channel` only permits `TRANSFER` or `CASH_OUT`).

### Finding 3: Model Bundle Serialization Not Implemented (Severity: MEDIUM / Deferred Architectural Scope)
- **Protocol Assumption**: Section 11 identifies `src/anomaly/artifacts.py` (`save_bundle`/`load_bundle`) as an operational serialization interface.
- **Implementation State**: `src/anomaly/artifacts.py` is `NOT PRESENT`.
- **Assessment**: Deferred pending future operational orchestrator design. Pure mathematical evaluation does not require persistent artifact bundles.

### Finding 4: CLI Evaluation Task Not Implemented (Severity: MEDIUM / Deferred Architectural Scope)
- **Protocol Assumption**: Section 11 identifies `src/cli.py` (`--task anomaly-eval`) as a CLI entry point.
- **Implementation State**: `src/cli.py` only implements `audit`, `features`, `train`, and `evaluate` (all Phase 04 / Phase 02/03 pipelines).
- **Assessment**: Deferred pending future operational orchestrator design. Pure mathematical evaluation logic is implemented and tested as importable library functions in `src/anomaly/evaluation.py`.

### Finding 5: Single-Step Eviction Boundary in Entity Velocity Transformers (Severity: LOW / Historical Context)
- **Protocol Requirement**: Section 5 historical reference windows require `historical_step < current_step`.
- **Implementation State**: `tests/test_anomaly_temporal_windows.py` lines 36–100 rigorously prove that `PointInTimeEntityVelocityTransformer` includes historical events strictly where $\text{step} \ge \text{current\_step} - 24$ and $\text{step} < \text{current\_step}$. Same-step observations are buffered and excluded.
- **Assessment**: Confirmed. Temporal isolation is verified by existing tests.

### Finding 6: Anomaly Validation Eligible Count Rectification & Denominator Classification (Severity: INFORMATIONAL / Governance Scope)
- **Protocol Draft Assumption**: Earlier drafts (`v1.2.6-DRAFT` and prior) listed 139,028 eligible transactions for steps 401–550 based on early analytical estimation.
- **Physical Data Reality & Classification**: Physical parquet audit confirmed steps 401–550 contain exactly **158,652 eligible rows** (32,723 `TRANSFER` + 125,929 `CASH_OUT`), and steps 551–743 contain exactly **82,221 eligible rows** (17,219 `TRANSFER` + 65,002 `CASH_OUT`). The continuous-stream figure (steps 401–743) is classified as: `DERIVED CONTINUOUS-STREAM ELIGIBLE DENOMINATOR = 158,652 + 82,221 = 240,873`.
- **Protocol Status**: Formally approved in Protocol `v1.3.0` and ratified by the Project Owner (2026-11-04) under Gate 1 ($N_{\text{elig}} = 158,652$ and derived continuous stream $240,873$). Illustrative top-K sensitivity projections ($\lfloor \alpha \times N_{\text{elig}} \rfloor$, conditional on 100% scoring coverage) are 158, 793, 1,586, 3,173 alerts, while operational capacity $K_\alpha = \lfloor \alpha \times N_S \rfloor$ depends strictly on observed finite scores ($N_S$).

---

## 6. Audit Conclusions & Technical Readiness Recommendation

1. **Protocol Technical Readiness**: **FORMALLY APPROVED (v1.3.0)**.
   The Phase 05 codebase in `src/anomaly/` satisfies 100% of the architectural invariants, input validation rules, and statistical mechanics specified in `docs/models/anomaly_evaluation_protocol.md` (v1.3.0).
2. **Zero Code Changes in Engine**:
   The frozen Phase 05 engine code (`src/anomaly/`) requires **zero modifications** and remains completely untouched.
3. **Evaluation Tooling Implemented & Accepted**:
   Pure mathematical evaluation functions, contract validations, and report formatters are implemented in `src/anomaly/evaluation.py` and accepted following Command 03 review and synthetic verification (22/22 unit tests passing).
4. **Deferred Components**:
   Model bundle serialization (`src/anomaly/artifacts.py`) and CLI integration (`src/cli.py`) are deferred pending future operational orchestrator design.
5. **Governance Sign-Off Completed**:
   All eight governance gates and Gate 6 parameters are formally approved and ratified (2026-11-04).
6. **Strict Negative Authorization Declaration**:
   Scoring and evaluation execution on real PaySim data remain strictly **NOT AUTHORIZED**. Phase 07 multi-model fusion remains **NOT STARTED**.

