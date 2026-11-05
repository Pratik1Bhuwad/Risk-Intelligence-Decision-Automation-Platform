# Phase 06 — Future Tooling Interface Inventory

**Document Title**: Phase 06 — Future Tooling Interface Inventory  
**Document Path**: `docs/phase_06/phase_06_interface_inventory.md`  
**Target Subsystem**: Phase 05 Standalone Anomaly Engine & Phase 06 Evaluation Harness  
**Specification Baseline**: Phase 05 Approved Specification v2.3.2  
**Evaluation Protocol Baseline**: `docs/models/anomaly_evaluation_protocol.md` (`v1.3.0`)  
**Date**: November 2026  
**Status**: **INVENTORY COMPLETE — IMPLEMENTATION ARCHITECTURE UPDATED (PROTOCOL v1.3.0)**  

---

## 1. Objective & Purpose

This inventory establishes the precise existing interfaces, classes, and utility functions available in the Risk Intelligence & Decision Automation Platform that can be reused for Phase 06 evaluation tooling, alongside an exhaustive gap analysis identifying missing components (`NOT PRESENT`) that must be developed in subsequent authorized implementation commands.

---

## 2. Existing Interface Audit by Functional Area

### 2.1 Configuration Loading & Verification Interface
- **File & Line Range**: [`src/anomaly/config.py#L128-L165`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/config.py#L128-L165)
- **Function/Class Name**: `load_anomaly_config(yaml_path: str | Path, verify_provenance: bool = True) -> AnomalyConfig`
- **Inputs**:
  - `yaml_path`: Path to `configs/anomaly_detection.yaml` (default: `"configs/anomaly_detection.yaml"`).
  - `verify_provenance`: Boolean flag asserting match against frozen SHA-256 digests.
- **Outputs**:
  - Validated immutable `AnomalyConfig` dataclass containing typed attributes (`budget_rate`, `feature_names`, `detector_hyperparameters`, `random_seed`, etc.).
- **Dependencies**: `pyyaml`, `hashlib`, `json`, `pathlib.Path`.
- **Reusability Assessment**: **REUSABLE AS-IS (SAFE)**.
- **Missing Functionality**: None.
- **Risks & Compatibility**: If the YAML file is modified, provenance checks fail immediately.

---

### 2.2 End-to-End Anomaly Scoring & Fitting Engine
- **File & Line Range**: [`src/anomaly/engine.py#L28-L195`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L28-L195)
- **Function/Class Name**: `AnomalyDetectionEngine`
- **Methods**:
  1. `fit(reference_df: pd.DataFrame) -> AnomalyDetectionEngine` ([lines 55–94](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L55-L94)):
     - **Inputs**: `reference_df` (must contain `type` and 36 canonical features; `step <= 400`).
     - **Outputs**: Fitted engine instance (`self.is_fitted = True`).
     - **Dependencies**: `AnomalyPreprocessor.fit()`, `IsolationForestDetector.fit()`.
  2. `score(df: pd.DataFrame, enforce_temporal_split: bool = False) -> Tuple[List[AnomalyOutputRow], pd.DataFrame, BudgetResult]` ([lines 96–195](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L96-L195)):
     - **Inputs**: `df` (must contain `row_index`, `type`, and 36 canonical features; no prohibited fields).
     - **Outputs**: Tuple of:
       - `List[AnomalyOutputRow]`: Row-level dataclass records.
       - `output_df`: Structured 8-column pandas DataFrame.
       - `BudgetResult`: Run-level population summary (`eligible_count`, `n_scored`, $K$, `channel_breakdown`).
- **Dependencies**: `src/anomaly/preprocessing.py`, `src/anomaly/detector.py`, `src/anomaly/budget.py`, `src/anomaly/schema.py`.
- **Reusability Assessment**: **REUSABLE AS-IS (SAFE)**.
- **Missing Functionality**: Does not persist fitted detectors to disk or load pre-fitted detector weights from disk.
- **Risks & Compatibility**: Input DataFrame must have `isFraud` removed prior to invocation.

---

### 2.3 Output Contract & Schema Definitions
- **File & Line Range**: [`src/anomaly/schema.py#L34-L187`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/schema.py#L34-L187)
- **Function/Class Name**: `AnomalyOutputRow`, `AnomalyOutputSchema`, `validate_output_row`
- **Inputs & Outputs**:
  - `AnomalyOutputRow`: Immutable 8-field dataclass (`schema_version`, `row_index`, `channel`, `anomaly_score`, `is_anomaly_flagged`, `anomaly_status`, `reason_code`, `alert_budget_selected`).
  - `AnomalyOutputSchema.to_dataframe(rows)`: Converts row records to DataFrame enforcing exact column order.
- **Dependencies**: `dataclasses`, `enum`, `pandas`.
- **Reusability Assessment**: **REUSABLE AS-IS (SAFE)**.
- **Missing Functionality**: None.
- **Risks & Compatibility**: Zero compatibility risks; output contract is decoupled from Phase 04.

---

### 2.4 Robust Preprocessing & Fallback Hierarchy
- **File & Line Range**: [`src/anomaly/preprocessing.py#L38-L284`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L38-L284)
- **Function/Class Name**: `AnomalyPreprocessor`
- **Key Methods**:
  - `fit(reference_df)`: Fits robust medians and scales per channel slice across the 4-tier hierarchy.
  - `get_active_features(channel)`: Returns list of active features with positive robust scale.
  - `transform_channel(df, channel)`: Returns standardized $X_{\text{robust}}$, active feature names, and composite $z$-scores.
  - `validate_inputs(df, require_row_index)`: Enforces zero prohibited fields and integer row indexing.
- **Dependencies**: `numpy`, `pandas`, `src.features.policy.STRICTLY_EXCLUDED_FIELDS`.
- **Reusability Assessment**: **REUSABLE AS-IS (SAFE)**.
- **Missing Functionality**: Preprocessor parameters (`channel_baselines`) are held in memory; no serialization method currently exists.

---

### 2.5 Deterministic Isolation Forest Wrapper
- **File & Line Range**: [`src/anomaly/detector.py#L13-L117`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/detector.py#L13-L117)
- **Function/Class Name**: `IsolationForestDetector`
- **Key Methods**:
  - `from_config(hyperparameters)`: Instantiates detector with `random_state=42`, `n_jobs=1`.
  - `fit(X)`: Fits scikit-learn `IsolationForest`.
  - `score_samples(X)`: Computes negated raw anomaly score: $s_{\text{raw}}(x) = -\text{score\_samples}(x)$.
- **Dependencies**: `scikit-learn.ensemble.IsolationForest`, `numpy`.
- **Reusability Assessment**: **REUSABLE AS-IS (SAFE)**.
- **Missing Functionality**: No `save()` or `load()` methods.

---

### 2.6 Alert Budget & Ranking Engine
- **File & Line Range**: [`src/anomaly/budget.py#L39-L180`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py#L39-L180)
- **Function/Class Name**: `AlertBudgetSelector`
- **Key Methods**:
  - `select_alerts(scored_rows, degraded_rows, ineligible_count, unscored_eligible_count)`: Evaluates global combined top $K = \lfloor \alpha \times N_S \rfloor$ alerts breaking ties deterministically by `row_index` ascending.
- **Dependencies**: `src.anomaly.schema`.
- **Reusability Assessment**: **REUSABLE AS-IS (SAFE)**.
- **Missing Functionality**: Evaluates a single budget rate (`budget_rate`). For retrospective sensitivity analysis across multiple $\alpha \in \{0.0010, 0.0050, 0.0100, 0.0200\}$, post-hoc slicing functions or multi-budget selectors are required in Phase 06 reporting tooling.

---

### 2.7 Supervised Model Artifacts Manager (Phase 04 Reference)
- **File & Line Range**: [`src/models/artifacts.py#L13-L71`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/models/artifacts.py#L13-L71)
- **Function/Class Name**: `ModelArtifactManager`
- **Scope**: Supervised LightGBM model bundle manager (`save_bundle`, `load_bundle`).
- **Dependencies**: `joblib`, `json`, `os`.
- **Reusability Assessment**: **CANNOT BE REUSED DIRECTLY**.
- **Reason**: Expects Phase 04 supervised objects (`calibrator`, `threshold_optimizer`, `preprocessor`). It cannot store channel-conditioned anomaly preprocessors and dual `IsolationForest` detectors without interface distortion. A dedicated anomaly artifact manager is required.

---

### 2.8 Command Line Interface (CLI) Entry Point
- **File & Line Range**: [`src/cli.py#L12-L136`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/cli.py#L12-L136)
- **Function/Class Name**: `main()`, `parse_args()`
- **Existing Tasks**: `choices=["audit", "features", "train", "evaluate"]`.
- **Reusability Assessment**: **EXTENSIBLE ONLY**.
- **Missing Functionality**: Has no `--task anomaly-eval` or `--task anomaly-train`.
- **Risks & Compatibility**: Modifying `src/cli.py` is deferred pending operational orchestrator design.

---

### 2.9 Implemented Pure Evaluation Library Interface
- **File & Line Range**: [`src/anomaly/evaluation.py#L1-L660`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/evaluation.py#L1-L660)
- **Status**: **IMPLEMENTED & ACCEPTED (SYNTHETIC FIXTURES ONLY; 22/22 TESTS PASSING)**
- **Role**: Pure mathematical library implementing data-contract validation, reconstruction, population slicing, PSI computation, Gate 6 diagnostics, sensitivity analysis, and report formatting.
- **Key Functions**:
  1. `validate_evaluation_data_contract(df, required_features=None, require_target=True) -> bool`:
     - Asserts presence of 36 canonical features, `day_of_simulation`, `hour_of_day`, channel indicators, and non-empty row count.
  2. `reconstruct_step_and_channel(df, inplace=False) -> pd.DataFrame`:
     - Deterministically reconstructs `step` ($\text{day} \times 24 + \text{hour}$) and `type` from channel indicators.
  3. `extract_clean_features_and_target(df, target_col="isFraud", drop_target=True) -> Tuple[pd.DataFrame, pd.Series]`:
     - Decouples ground-truth target label from clean feature DataFrame.
  4. `slice_evaluation_population(df, step_col="step", window="validation") -> pd.DataFrame`:
     - Slices temporal populations: `"reference"` ($\le 400$), `"validation"` ($401\text{--}550$), `"holdout"` ($551\text{--}743$), or `"continuous"` ($401\text{--}743$).
  5. `compute_psi(reference_scores, evaluation_scores, num_bins=10, epsilon=1e-4, interpolation="linear") -> float`:
     - Implements 5-step precedence guard, linear quantile deciles (`pandas.Series.quantile(..., interpolation="linear")`), internal cut point collapsing, selective zero-cell smoothing ($\epsilon=10^{-4}$), and divergence summation.
  6. `compute_gate6_diagnostic_metrics(output_df, y_true, reference_scores_by_channel=None, alert_budget_rate=0.01) -> Dict[str, Any]`:
     - Calculates all seven Gate 6.1 diagnostic metrics ($T_{\text{deg}}, T_{\text{psi}}, T_{\text{prec}}, T_{\text{rec\_scored}}, T_{\text{rec\_elig}}, T_{\text{cov}}, T_{\text{enrich}}$).
  7. `evaluate_budget_sensitivity(output_df, y_true, target_budget_rates=None) -> Dict[str, Any]`:
     - Post-hoc slicing across $\{0.10\%, 0.50\%, 1.00\%, 2.00\%\}$ computing alert counts, true positives, precision, scored recall, and eligible recall from the single scored array.
  8. `format_evaluation_report(run_metadata, diagnostic_metrics, sensitivity_results, population_summary) -> Dict[str, Any]`:
     - Formats structured JSON report dictionary.
- **Dependencies**: `numpy`, `pandas`, `scipy.stats`.
- **Reusability Assessment**: **IMPLEMENTED & VERIFIED**.

---

## 3. Inventory of Deferred Interfaces (`DEFERRED`)

The pure mathematical evaluation library is fully implemented in `src/anomaly/evaluation.py`. The remaining operational components are deferred pending future orchestrator design:

| Interface Component | Location | Required Capabilities & Contract | Status |
| :--- | :--- | :--- | :---: |
| **Anomaly Model Artifact Manager** | `src/anomaly/artifacts.py` | `save_anomaly_bundle()` and `load_anomaly_bundle()`. Serializes preprocessor channel baselines, TRANSFER detector, CASH_OUT detector, config digests, and environment metadata via `joblib`/`json`. | **DEFERRED** |
| **Evaluation CLI Task** | `src/cli.py` (`--task anomaly-eval`) | CLI task accepting `--config`, `--data`, `--mode`, and `--output-dir`. Orchestrates loading parquet, reference score generation, scoring evaluation populations, and outputting JSON reports. | **DEFERRED** |

---

## 4. Phase 06 Tooling Interface Architecture

The architectural boundary cleanly delineates frozen Phase 05 execution modules, accepted Phase 06 evaluation library routines, and deferred operational components:

```
src/anomaly/
├── config.py              <-- FROZEN (Reusable as-is)
├── schema.py              <-- FROZEN (Reusable as-is)
├── preprocessing.py       <-- FROZEN (Reusable as-is)
├── detector.py            <-- FROZEN (Reusable as-is)
├── budget.py              <-- FROZEN (Reusable as-is)
├── engine.py              <-- FROZEN (Reusable as-is)
├── evaluation.py          <-- IMPLEMENTED & ACCEPTED (Phase 06 pure evaluation library)
└── artifacts.py           <-- DEFERRED (Phase 06 operational bundle serialization)

src/cli.py                 <-- DEFERRED (Phase 06 CLI entry point: --task anomaly-eval)

tests/
├── test_anomaly_evaluation.py <-- IMPLEMENTED & ACCEPTED (22 synthetic tests passing)
```

### Key Architectural Interface Principles for Phase 06:
1. **Zero Mutation of Frozen Classes**: Tooling in `src/anomaly/evaluation.py` functions as an external library without modifying or subclassing frozen Phase 05 classes.
2. **Deterministic Data Separation**: `extract_clean_features_and_target()` guarantees zero leakage of `isFraud` into feature sets.
3. **Pure Post-Hoc Slicing**: Retrospective sensitivity scenarios ($0.10\%, 0.50\%, 2.00\%$) operate purely on the single output array generated under the frozen $1.00\%$ baseline.
4. **Prohibition of Real-Data Execution**: Scoring and evaluation on real PaySim data remain strictly **NOT AUTHORIZED**.
5. **Phase 07 Multi-Model Fusion**: Remains strictly **NOT STARTED**.

