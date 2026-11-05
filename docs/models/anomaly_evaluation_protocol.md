# Phase 06 — Standalone Anomaly Detection Evaluation & Validation Protocol Specification

**Document Title**: Phase 06 — Standalone Anomaly Detection Evaluation & Validation Protocol Specification  
**Document Path**: `docs/models/anomaly_evaluation_protocol.md`  
**Document Status**: `APPROVED SPECIFICATION — PROJECT-OWNER SIGN-OFF COMPLETED`  
**Protocol Version**: `v1.3.0`  
**Specification Baseline**: Phase 05 Approved Specification v2.3.2  
**Configuration Baseline**: `configs/anomaly_detection.yaml` (FROZEN BASELINE)  
**Target Engine**: Standalone `AnomalyDetectionEngine` (`src/anomaly/`)  
**Target Platform**: Risk Intelligence & Decision Automation Platform  
**Date**: November 2026  

### Document Revision History

| Version | Status | Date | Scope of Revision |
| :---: | :---: | :---: | :--- |
| `v1.0.0-DRAFT` | Draft | Oct 2026 | Initial reconnaissance and standalone evaluation protocol draft. |
| `v1.1.0-DRAFT` | Draft | Oct 2026 | Formal disclosure of diagnostic fitting benchmark, Qualified Holdout exposure disclosures, and operational alert budget semantics. |
| `v1.2.0-DRAFT` | Draft | Nov 2026 | Addition of lifecycle implementation evidence, descriptive PSI caveats, and complete fraud coverage decomposition. |
| `v1.2.1-DRAFT` | Draft | Nov 2026 | Linear quantile interpolation, deterministic tied-score edge collapsing, Gate 6 target list alignment, and holdout one-shot rules. |
| `v1.2.2-DRAFT` | Draft | Nov 2026 | Deterministic internal decile cut points, finite score binning (zero inclusion), selective smoothing on zero cells, and Isolation Forest rationale refinement. |
| `v1.2.3-DRAFT` | Draft | Nov 2026 | Correction of PSI matrix contradiction, explicit disclosure of reference score in-sample generation, formal governance for steps 401–550 pre-holdout use, and non-finite score accounting. |
| `v1.2.4-DRAFT` | Draft | Nov 2026 | Explicit disclosure of in-sample vs. out-of-sample PSI baseline limitation and deterministic handling of empty reference/evaluation populations (NOT_EVALUABLE with no smoothing). |
| `v1.2.5-DRAFT` | Draft | Nov 2026 | Explicit PSI execution precedence (empty-population short-circuit strictly precedes quantile and cut-point calculation) and sensitivity table denominator qualification (eligible vs. scored rows under 100% coverage assumption). |
| `v1.2.6-DRAFT` | Draft | Nov 2026 | Correction of pandas quantile API parameter (`interpolation='linear'`) and exact specification of fraud recall decomposition boundary condition when $F_{\text{scored}} = 0$ ($\text{Rec}_{\text{elig}} = 0.0$). |
| `v1.2.7-DRAFT` | Draft Proposal | Nov 2026 | Evaluation-population denominator reconciliation for steps 401–550 (158,652 physical eligible count with 32,723 TRANSFER + 125,929 CASH_OUT decomposition; replacing 139,028), recalculated sensitivity alert counts, and Gate 3 evaluation baseline clarification preserving frozen Phase 05 fitting boundaries. |
| `v1.3.0` | **Approved Baseline** | Nov 2026 | **Formal Protocol Release**: Formally approved by Project Owner (November 2026). Ratifies Gates 1–8: Option 3 Dual-Stage evaluation (158,652 Val, 82,221 Holdout, 240,873 Continuous); Qualified Holdout One-Shot policy; Full Reference baseline (5,787,030 total / 2,529,536 eligible); Alert budgets 0.10%, 0.50%, 1.00%, 2.00%; Dual Metric Framework; Gate 6.1 Option 6B exploratory diagnostics (hard thresholds deferred to Phase 07); Gate 6.2 epsilon = 1e-4 selective zero-cell smoothing; Permissible Business Claims policy; and frozen global 1.00% alert budget. Incorporates accepted initial evaluation tooling (src/anomaly/evaluation.py, 22 synthetic tests passing). Defers persistent serialization and CLI integration. Real-data execution strictly unauthorized without separate approval. |

---

## 1. Executive Summary & Governance Notice

This specification establishes the official evaluation and validation protocol for **Phase 06 — Anomaly Evaluation & Validation**. Operating under strict governance boundaries, this protocol defines the evaluation populations, baseline operational alert-selection semantics, retrospective sensitivity analysis, unsupervised characterization metrics, fraud alignment diagnostics, and governance approval gates for validating the standalone Phase 05 Anomaly Detection Engine.

> [!IMPORTANT]
> **Strict Governance Status & Negative Declarations**:
> 1. **APPROVED SPECIFICATION**: This document is the approved specification (v1.3.0) with formal Project-Owner sign-off completed in November 2026.
> 2. **NO REAL-DATA SCORING EXECUTED**: Zero full-dataset scoring, zero holdout scoring, and zero Phase 06 evaluation scoring on real data has been executed. Real-data execution remains strictly unauthorized without separate explicit authorization.
> 3. **NO CODE OR CONFIG MUTATIONS TO PHASE 05**: Phase 05 source code, Phase 04 models/artifacts, datasets, and frozen configuration `configs/anomaly_detection.yaml` remain 100% unaltered and protected.
> 4. **INITIAL EVALUATION TOOLING ACCEPTED (SYNTHETIC FIXTURES ONLY)**: Pure evaluation tooling (`src/anomaly/evaluation.py` and `tests/test_anomaly_evaluation.py`) is implemented and accepted, verified exclusively via 22 synthetic in-memory unit tests. Persistent model serialization (`artifacts.py`) and CLI integration (`cli.py`) remain deferred.
> 5. **GATE 6.1 OPTION 6B EXPLORATORY DIAGNOSTICS ADOPTED**: In accordance with approved Gate 6.1 Option 6B, quantitative targets ($T_{\text{deg}}$ through $T_{\text{enrich}}$) are ratified as exploratory benchmark diagnostics with full tracking of degraded/unscored states; hard pass/fail thresholds are deferred to Phase 07 multi-model fusion. Gate 6.2 smoothing floor $\epsilon = 10^{-4}$ on zero cells is ratified.

---

## 2. Governance Disclosures & Audit History

### 2.1 Disclosure & Disposition of Diagnostic Fitting Benchmark
During the Command 01 technical reconnaissance, a diagnostic benchmark was executed via a temporary script in the session scratch directory to measure the computational runtime of fitting on the full training partition ($\text{steps} \le 400$).

**Transparent Governance Audit of the Execution**:
- **Authorization Status**: **UNAUTHORIZED DIAGNOSTIC PROBE**. The benchmark was run by the agent to assess feasibility without explicit project-owner pre-approval. This governance deviation is formally recorded here.
- **Scratch File Disposition**: The script resides at `scratch/benchmark_ref.py` in external scratch space (`<appDataDir>/brain/<conversation-id>/scratch/`). It is **inert, quarantined, not tracked in Git, and will NOT be re-executed**. Its audit history is preserved transparently rather than concealed or erased.
- **Persistence State**: **ZERO PERSISTENCE**. Fitted preprocessor and detector objects were instantiated in transient Python runtime memory only. **No model bundles, weights, parameters, or artifacts were serialized, saved to disk, or committed to `models/`**.
- **System Integrity**: **ZERO MUTATION**. No source files under `src/`, configuration files under `configs/`, datasets under `data/`, or existing test suites under `tests/` were altered or overwritten.
- **Historical Diagnostic Nature of Timing Results**:
  The recorded execution times (ingestion & step reconstruction: 1.62s; `AnomalyPreprocessor.fit()`: 4.98s; `TRANSFER` detector fit: 0.38s; `CASH_OUT` detector fit: 1.36s; total fit: 6.72s) represent a **single historical diagnostic observation** on local hardware. **They do not constitute a performance guarantee, SLA, or acceptance criterion**. The architectural recommendation to use the full reference partition rests upon statistical and governance principles, not on benchmark speed alone.
- **Prohibition on Repetition**: In accordance with governance instructions, this benchmark will **NOT be repeated**.
- **Memory Usage Note**: Resident memory usage was not instrumented with formal memory profilers during the diagnostic probe. Any claims of "minimal memory usage" are retracted; formal RAM profiling remains to be conducted during authorized execution.

---

## 3. Evaluation Populations & Temporal Partition Policies

### 3.1 Classification of Steps 551–743: Qualified Holdout with Known Prior Exposure
The simulation partition spanning discrete simulation steps 551–743 (196,601 transactions; 2,148 fraud events) is formally classified as:

$$\mathbf{STATUS:\;QUALIFIED\;HOLDOUT\;(PRIOR\;PHASE\;04\;TEST\;EXPOSURE)}$$

> [!WARNING]
> **Not Pristine / Not Untouched**:
> - Steps 551–743 **must never be described as pristine, untouched, or leakage-free**.
> - **Prior Exposure Disclosure**: In Phase 04, the supervised modeling pipeline evaluated its champion LightGBM model and baseline classifiers across all 196,601 transactions of steps 551–743, computing full test confusion matrices and classification metrics.
> - **Row-Level Inspection Disclosure**: As documented in commit `7118ee8` and Section 7 of [`docs/models/ml_risk_modeling.md`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/docs/models/ml_risk_modeling.md#L64-L73), two specific false-negative transactions within this partition were manually inspected during Phase 04 error analysis:
>   1. Row Index `6281484`: Step `646`, amount \$399,045.08, channel `TRANSFER`.
>   2. Row Index `6362462`: Step `730`, amount \$7,316,255.05, channel `TRANSFER`.
> - **Qualified Holdout One-Shot Protection Policy**:
>   1. **Single Scoring Execution**: The Qualified Holdout (steps 551–743) is scored **exactly once** under the approved frozen evaluation protocol.
>   2. **Pre-Approved Sensitivity Slicing**: The pre-approved retrospective sensitivity analyses (at $0.10\%, 0.50\%, 1.00\%, 2.00\%$) may utilize that same single scoring output array via post-hoc rank slicing without rescoring.
>   3. **Strict Prohibition on Rescoring & Tuning**: Steps 551–743 must **never** be used for rescoring, detector selection, hyperparameter tuning, active feature selection, threshold tuning, or alert-budget calibration.
>   4. **Subsequent Modification Invalidation**: Any subsequent use of Qualified Holdout results to motivate model changes, feature modifications, or parameter adjustments invalidates its holdout status; any subsequent final evaluation would require governance review and the **reservation of a fresh, unexposed evaluation population** to provide an unbiased final assessment.

### 3.2 Disclosure of Prior Phase 04 Validation Exposure & Permitted Use of Steps 401–550

#### Prior Supervised Exposure Disclosure
Steps 401–550 (378,989 transactions; 1,588 fraud events) cannot be treated as an unexposed partition. In Phase 04, steps 401–550 were actively utilized as the validation fold for:
- Hyperparameter tuning and model comparison.
- Post-hoc Platt scaling probability calibration.
- Decision threshold optimization (establishing the operating threshold $0.9771$).

If steps 401–550 are utilized in Phase 06 as an Anomaly Validation Partition (under Option 3 Dual-Stage Evaluation), their prior supervised exposure must be formally acknowledged.

#### Permitted Diagnostic & Validation Use of Steps 401–550
Under Option 3, discrete steps 401–550 serve as an **Anomaly Validation Partition** for preliminary diagnostic analysis, baseline PSI drift calibration, operational degradation checks, and retrospective sensitivity exploration.

Specifically, findings from the evaluation of steps 401–550 **MAY** legitimately inform:
1. **Detector or Feature Changes**: Diagnostic analysis of active feature attribution, dispersion stability, or hyperparameter behavior on steps 401–550 may motivate proposals to adjust detector settings or feature inclusion logic.
2. **Alert-Budget Selection**: Empirical alert concentration and trade-off curves observed on steps 401–550 across candidate budget levels ($0.10\%, 0.50\%, 1.00\%, 2.00\%$) may inform operational recommendations for alert queue sizing.
3. **Evaluation Methodology Changes**: Diagnostic findings on steps 401–550 may inform refinements to binning rules, reporting granularities, or stability metrics.

#### Mandatory Pre-Holdout Governance & Invalidation Boundary
To maintain the methodological integrity of the final evaluation, strict sequencing and invalidation rules are enforced:
1. **Mandatory Documentation and Approval Prior to Holdout Scoring**:
   Any proposed changes to detectors, active features, alert budgets, or evaluation methodology informed by steps 401–550 **MUST be formally documented in a change proposal and explicitly approved by the Project Owner BEFORE the Qualified Holdout (steps 551–743) is ever scored, accessed, or evaluated**.
2. **One-Shot Qualified Holdout Invariant**:
   The Qualified Holdout (steps 551–743) remains strictly a **one-shot final evaluation population**. It is scored exactly once under the approved frozen protocol.
3. **Permanent Holdout Invalidation Rule**:
   If the results or findings from scoring the Qualified Holdout (steps 551–743) are ever used to influence subsequent detector modifications, feature alterations, alert budget adjustments, or evaluation methodology revisions:
   - The holdout status of steps 551–743 is **immediately and permanently invalidated**.
   - Steps 551–743 can no longer be represented as an unbiased or untouched final holdout population.
   - Any subsequent official evaluation requires governance review and the **reservation and approval of a fresh, completely unexposed evaluation population**.

---

### 3.3 Candidate Evaluation Population Designs

To avoid assuming automatic reuse of Phase 04 partitions, four candidate partition designs are formulated for project-owner review:

```
Candidate Evaluation Designs:

Option 1: Standard Qualified Holdout
Reference: [ Steps 1 - 400 ]  ──►  Unused: [ 401 - 550 ]  ──►  Qualified Holdout: [ Steps 551 - 743 ]

Option 2: Pre-Inspection Holdout Slice
Reference: [ Steps 1 - 400 ]  ──►  Unused: [ 401 - 550 ]  ──►  Slice: [ 551 - 645 ] | (646 - 743 Excluded)

Option 3: Dual-Stage Evaluation (Recommended Proposal)
Reference: [ Steps 1 - 400 ]  ──►  Anomaly Val: [ 401 - 550 ]  ──►  Qualified Holdout: [ Steps 551 - 743 ]

Option 4: Continuous Out-of-Time Stream
Reference: [ Steps 1 - 400 ]  ──►  Continuous Stream: [ Steps 401 - 743 ] (Segmented Analysis)
```

#### Detailed Empirical Breakdown of Candidate Designs:

| Design Option | Sub-Partition Role | Step Range | Total Rows | Eligible Rows (`TRANSFER` + `CASH_OUT`) | Fraud Count | Fraud Prevalence | Exposure Status & Methodological Assessment |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Option 1: Standard Qualified Holdout** | Final Evaluation | 551–743 | 196,601 | 82,221 | 2,148 | 1.0926% | Reuses Phase 04 test partition. Subject to Qualified Holdout disclosure (aggregate exposure + 2 inspected rows). |
| **Option 2: Pre-Inspection Slice** | Final Evaluation | 551–645 | 115,770 | 47,936 | 1,126 | 0.9726% | **Avoids specifically inspected rows**: Ends at step 645 prior to row 6281484 (step 646). **Not pristine**: Steps 551–645 were still part of Phase 04 aggregate test evaluation. Discards 80,831 later transactions. |
| **Option 3: Dual-Stage (Recommended)** | Anomaly Val<br>Qualified Holdout | 401–550<br>551–743 | 378,989<br>196,601 | 158,652*<br>82,221 | 1,588<br>2,148 | 0.4190% (1.0009% elig)<br>1.0926% (2.6125% elig) | **Recommended evaluation separation**: Steps 401–550 used for retrospective sensitivity analysis, diagnostic PSI baselines, and stability monitoring. Steps 551–743 reserved strictly for one-shot Qualified Holdout reporting. (*158,652 physical eligible count: 32,723 TRANSFER + 125,929 CASH_OUT, ratified by Project Owner; replacing obsolete 139,028 draft figure). |
| **Option 4: Continuous Stream** | Continuous Evaluation | 401–743 | 575,590 | 240,873* | 3,736 | 0.6491% (1.5510% elig) | Evaluates entire post-training simulation horizon. Maximizes sample size but mixes validation-era and test-era exposure regimes. (*DERIVED CONTINUOUS-STREAM ELIGIBLE DENOMINATOR = 158,652 + 82,221 = 240,873, ratified by Project Owner; replacing obsolete 221,249 draft figure). |

---

## 4. Implementation Evidence & Exact Lifecycle Population Mapping

In accordance with Requirement 4, the exact populations and data paths utilized across each stage of the engine lifecycle are documented with precise source references.

> [!NOTE]
> **Source Inspection Status Notice**:
> The source file and line references documented below reflect the current static code state inspected during reconnaissance. **Documenting these references does NOT constitute independent audit verification; all implementation claims remain subject to independent source inspection and verification in Command 03.**

### 4.1 Implementation Evidence by Engine Component

1. **`AnomalyPreprocessor.fit(self, reference_df)`**:
   - **Source File**: [`src/anomaly/preprocessing.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L192-L232) (`fit` method, lines 192–232).
   - **Input Population**: `reference_df` (must contain `type` and the 36 canonical features).
   - **Execution Mechanics**: Filters `reference_df` by channel (`type == "TRANSFER"` and `type == "CASH_OUT"`). For each channel slice, computes 36-feature robust statistics (`compute_feature_dispersion`) through the 4-tier fallback hierarchy (MAD $\to$ IQR $\to$ positive-subset std $\to$ exclusion).
   - **Exclusion**: Non-eligible channels (`PAYMENT`, `CASH_IN`, `DEBIT`) are ignored during fitting.
2. **`TRANSFER` Detector Fitting**:
   - **Source File**: [`src/anomaly/engine.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L79-L92) (`fit` method, lines 79–92).
   - **Input Population**: Subsets `reference_df` strictly where `reference_df["type"] == "TRANSFER"`.
   - **Feature Matrix**: Standardized robust feature matrix $X_{\text{robust}}$ generated by `AnomalyPreprocessor.transform_channel(ch_df, "TRANSFER")` containing only active features for TRANSFER ($|A_{\text{TRANSFER}}| = 20$).
   - **Detector**: `IsolationForestDetector.from_config(self.config.detector_hyperparameters).fit(X_robust)`.
3. **`CASH_OUT` Detector Fitting**:
   - **Source File**: [`src/anomaly/engine.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L79-L92) (`fit` method, lines 79–92).
   - **Input Population**: Subsets `reference_df` strictly where `reference_df["type"] == "CASH_OUT"`.
   - **Feature Matrix**: Standardized robust feature matrix $X_{\text{robust}}$ generated by `AnomalyPreprocessor.transform_channel(ch_df, "CASH_OUT")` containing only active features for CASH_OUT ($|A_{\text{CASH\_OUT}}| = 19$).
   - **Detector**: `IsolationForestDetector.from_config(self.config.detector_hyperparameters).fit(X_robust)`.
4. **Evaluation Scoring & Global Alert Ranking**:
   - **Source File**: [`src/anomaly/engine.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L96-L195) (`score` method) and [`src/anomaly/budget.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py#L51-L180) (`select_alerts` method).
   - **Input Population**: Input scoring DataFrame `df` (must contain `row_index`, `type`, and the 36 features).
   - **Execution Mechanics**:
     - `ineligible_count` tallies non-eligible channels (`PAYMENT`, `CASH_IN`, `DEBIT`).
     - Eligible rows segregated into TRANSFER and CASH_OUT; active features transformed and scored via respective channel detectors: $s_{\text{raw}}(x) = -\text{score\_samples}(x)$.
     - Any channel with zero active features outputs State C (`DEGRADED_UNSCORABLE`).
     - Scored candidates from both channels combined into `scored_rows` ($N_S$).
     - Global ranking: `sorted(scored_rows, key=lambda r: (-float(r.anomaly_score), int(r.row_index)))`.
     - Top $K = \lfloor \text{budget\_rate} \times N_S \rfloor$ selected; flagged records receive `is_anomaly_flagged = True` and `alert_budget_selected = True`.

---

## 5. Reference Population Analysis: Full Partition vs. Channel-Stratified Sampling

Requirement 3 and Requirement 9 mandate evaluating the reference population choice with rigorous statistical and architectural justification.

### 5.1 Channel Imbalance in Reference History
Within the finite training partition ($\text{steps} \le 400$), eligible transaction counts exhibit substantial channel asymmetry:
- **`TRANSFER`**: 481,440 transactions ($19.03\%$ of eligible reference).
- **`CASH_OUT`**: 2,048,096 transactions ($80.97\%$ of eligible reference).
- **Asymmetry Ratio**: Approximately $4.25 : 1$.

*Methodological Correction*: An arbitrary combined 50k/50k reference sample is methodologically flawed because it artificially equalizes channel representation, distorting the empirical density landscape. Any sampling scheme must be designed **per channel** with proportional stratification.

### 5.2 Comparative Analysis: Full Partition vs. Channel-Stratified Sample

| Evaluation Dimension | Full Reference Partition ($\text{steps} \le 400$) | Channel-Stratified Sample (e.g., 100k TRANSFER, 425k CASH_OUT) |
| :--- | :--- | :--- |
| **Statistical Representation** | **Exact empirical statistics relative to the selected finite reference partition**. Zero subsampling variance on medians, MAD, or IQR. | Approximates reference partition statistics subject to sampling error. Risk of marginal features flipping active/inactive states across fallback tiers. |
| **Tail & Outlier Coverage** | Complete representation of rare high-value legitimate transfers occurring across all 400 simulation steps. | Risk of omitting extreme legitimate percentiles ($> 99.9\%$), potentially causing false outlier alerts during evaluation. |
| **Algorithmic Mechanics** | scikit-learn `IsolationForest` default `max_samples="auto"` draws $256$ samples per tree. Fitting on the full reference partition provides a larger empirical sampling pool (481k for TRANSFER, 2.05M for CASH_OUT) and avoids an additional external subsampling decision or hyperparameter. | Draws samples from a smaller pre-filtered subset, requiring an additional external subsampling decision, sampling fraction, and random seed. |
| **Governance Overhead** | Zero additional parameters. No sampling seed, sampling fraction, or stratification weights required. | Requires formal governance approval of sampling seed, sampling fractions, and stratification algorithms. |
| **Historical Timing Note** | Recorded at 6.72s in single diagnostic probe; noted as absence of obvious computational bottleneck, but **not a performance guarantee**. | Estimated ~1–3 seconds. |

**Provisional Recommendation (Pending Approval Gate 3)**:  
The recommendation to use the **full training partition ($\text{steps} \le 400$)** rests primarily on **statistical and architectural considerations**: it provides exact empirical statistics relative to the selected reference partition without sampling variance, provides a larger empirical sampling pool for tree construction, and avoids introducing an additional external subsampling decision or sampling hyperparameters. This recommendation remains strictly provisional pending formal project-owner approval.

> [!IMPORTANT]
> **Gate 3 Governance Clarification & Scope Boundaries**:
> To prevent governance ambiguity, the evaluation protocol explicitly distinguishes three distinct concepts:
> 1. **Existing Phase 05 Fitting Boundary ($\text{steps} \le 400$)**: The architectural implementation boundary where preprocessor baselines and detectors are fitted on discrete simulation steps 1–400 is frozen under approved Specification v2.3.2 and `configs/anomaly_detection.yaml` Section 15. Gate 3 does NOT reopen, alter, or question this established implementation boundary.
> 2. **Reference Population for Evaluation Characterization**: Gate 3 specifically governs whether the evaluation protocol uses the complete empirical training partition ($\text{steps} \le 400$, 5.78M transactions; 2.53M eligible) or an analytical subsample as the baseline population against which evaluation populations are characterized.
> 3. **Reference-Score Observations ($S_{\text{ref}}$)**: Gate 3 ratifies scoring that reference population using the frozen fitted engine to generate the in-sample baseline score distribution ($S_{\text{ref}}$) for linear decile cut-point calculation ($c_1 < \dots < c_m$) and PSI stability monitoring.
> 
> **Explicit Negative Declaration**: Gate 3 ratifies evaluation baseline population scope only. It does **NOT** authorize refitting or retraining the Phase 05 detector, changing the frozen Phase 05 configuration, altering preprocessing or scoring behavior, refitting transformations, or modifying existing Phase 05 model code or artifacts.

### 5.3 Reference Score Generation Procedure & Mandatory In-Sample Disclosure

To establish the reference distribution $Q$ and decile cut points $c_1 < \dots < c_m$ required for PSI stability calculations, the reference scoring protocol is defined as follows:

1. **Fitting Scope**:
   - `AnomalyPreprocessor` and `IsolationForestDetector` (for both `TRANSFER` and `CASH_OUT` channels) are fitted strictly on the finite reference population spanning discrete simulation $\text{steps} \le 400$ ([`src/anomaly/preprocessing.py#L192-L232`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py#L192-L232), [`src/anomaly/engine.py#L79-L92`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L79-L92)).
2. **Subsequent Scoring of Reference Population**:
   - After fitting is complete, **that same reference population ($\text{steps} \le 400$) is subsequently scored using the fitted detectors** to generate the baseline reference anomaly score array $S_{\text{ref}}$.
3. **MANDATORY IN-SAMPLE DISCLOSURE**:
   - Because the reference population is fitted and scored on the exact same set of historical observations ($\text{steps} \le 400$), **all reference scores $S_{\text{ref}}$ are strictly IN-SAMPLE SCORES**.
   - They **must NEVER be described or represented as out-of-sample scores, holdout scores, or generalization benchmarks**.
   - The in-sample reference distribution functions solely as the empirical baseline against which subsequent out-of-sample evaluation distributions ($S_{\text{eval}}$ on steps 401–550 and steps 551–743) are compared via PSI to detect post-training distributional drift.
4. **Execution Path Symmetry**:
   - Both the reference population ($\text{steps} \le 400$) and all evaluation populations (steps 401–550, steps 551–743) utilize the **exact same frozen preprocessing and scoring execution path**:
     $$\text{Input Payload} \xrightarrow{\text{validate\_inputs()}} \text{transform\_channel()} \xrightarrow{X_{\text{robust}}} \text{detector.score\_samples()} \xrightarrow{-s(x)} s_{\text{raw}}(x)$$
   - Both pipelines enforce identical input validation rules, active feature attribution masks, and channel dispatching.
5. **Eligibility and Finite Score Requirement for PSI**:
   - In both reference and evaluation populations, the finite-score PSI comparison includes **only successfully scored eligible transactions** (State A / State B records with finite numeric scores).
   - Ineligible channels (`PAYMENT`, `CASH_IN`, `DEBIT`) are excluded from scoring.
6. **Accounting of Scoring Failures & Non-Finite Scores**:
   - Any transaction that cannot be successfully scored—whether due to zero active features (State C `DEGRADED_UNSCORABLE`) or any computational/numerical anomaly resulting in a non-finite score (`null`, `NaN`, `+Inf`, `-Inf`)—is **excluded from the finite-score PSI comparison**.
   - All such failures are **formally recorded and tracked in operational degradation reporting** (under Degraded Unscorable Rate $T_{\text{deg}}$ and Fraud Scoring Coverage $T_{\text{cov}}$), ensuring zero silent dropouts.
   - **PSI Execution Precedence Guard**: In accordance with Section 7.1 Metric 4, if either the finite reference score population ($|S_{\text{ref}}|$) or finite evaluation score population ($|S_{\text{eval}}|$) has zero observations, PSI returns `NOT_EVALUABLE` immediately; reference quantiles, internal cut points, raw bin proportions, and smoothing are never computed on empty arrays.
7. **Explicit Methodological Limitation of In-Sample Reference Baseline**:
   - Because the reference population is scored using detectors fitted on that same population, while evaluation populations are scored out-of-sample, differences between reference and evaluation score distributions may partly reflect the **in-sample versus out-of-sample scoring distinction** rather than pure temporal drift alone.
   - Therefore:
     - PSI is strictly a **descriptive comparison against an in-sample reference score distribution**.
     - PSI **must not automatically be interpreted as pure temporal drift**.
     - PSI **does not establish detector degradation, accuracy, or fraud detection performance**.
     - All Phase 06 evaluation reports and presentations **must explicitly disclose this limitation** when reporting PSI results.

---

## 6. Operational Alert-Selection Semantics & Sensitivity Design

Requirement 4, Requirement 5, and Requirement 13 govern the operational baseline and analytical sensitivity evaluation structure.

### 6.1 Phase 05 Frozen Operational Baseline Semantics
The frozen baseline configuration `configs/anomaly_detection.yaml` Section 11 and implementation [`src/anomaly/budget.py`](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py) enforce the following explicit operational semantics:

1. **Global Combined Scope**:
   - The alert budget is evaluated **globally across combined eligible channels** (`TRANSFER` and `CASH_OUT`).
   - It is **NOT** evaluated as independent per-channel quotas (e.g., it does NOT take 1% of TRANSFER and 1% of CASH_OUT separately).
   - If one channel exhibits higher anomaly scores, it may legitimately consume a higher proportion of the budget.
2. **Budget Denominator ($N_S$)**:
   - The denominator is strictly the count of **successfully scored eligible transactions**:
     $$N_S = |S_{\text{TRANSFER}}| + |S_{\text{CASH\_OUT}}|$$
   - Ineligible transactions (`PAYMENT`, `CASH_IN`, `DEBIT`) and unscored/degraded transactions (`DEGRADED_UNSCORABLE`) are strictly excluded from $N_S$.
3. **Budget Capacity ($K$)**:
   - The number of alerts selected is computed as:
     $$K = \lfloor 0.0100 \times N_S \rfloor$$
   - If $N_S < 100$, $K = 0$ (zero alerts selected).
   - If $N_S == 0$, budget status is `NOT_EVALUABLE` and alert rate is `None` (not $0.0$).
4. **Dynamic Rank-Based Thresholding**:
   - There is **no fixed numerical score cutoff** (e.g., $s > 0.70$).
   - Scored candidates are sorted globally by `anomaly_score` in descending order. The effective operating threshold is dynamically defined as the score of the $K$-th ranked transaction.
5. **Deterministic Secondary Tie-Breaking**:
   - In the event of identical anomaly scores, ties are broken strictly by **immutable `row_index` in ascending order**:
     $$\text{Sort Key:}\quad (-s_{\text{raw}}(x),\; \text{row\_index})$$
   - The lower `row_index` receives deterministic priority for budget inclusion.

---

### 6.2 Retrospective Top-K Sensitivity Evaluation Framework
To evaluate capacity trade-offs without modifying the frozen configuration baseline, Phase 06 evaluation reporting will conduct retrospective top-K sensitivity analyses across four analytical scenarios:

$$\alpha \in \{0.0010,\; 0.0050,\; 0.0100,\; 0.0200\} \quad (0.10\%,\; 0.50\%,\; 1.00\%,\; 2.00\%)$$

For any successfully scored finite-score population of size $N_S$, the analytical budget capacity is:

$$K_\alpha = \lfloor \alpha \cdot N_S \rfloor$$

> [!NOTE]
> **Denominator Qualification & Scoring Coverage Semantics**:
> - **Eligible-Row Counts ($N_{\text{elig}}$)**: The figures $82,221$ (Qualified Holdout, steps 551–743) and $158,652^*$ (Anomaly Validation, steps 401–550; decomposition: 32,723 TRANSFER + 125,929 CASH_OUT; ratified by Project Owner; replacing obsolete 139,028 draft figure) represent exact **eligible transaction counts** (`TRANSFER` and `CASH_OUT`), **not verified successfully scored counts ($N_S$)**.
> - **Illustrative Nature of Estimates**: The alert counts shown in the sensitivity matrix below ($\approx 82, 411, 822, 1,644$ for Holdout and $\approx 158, 793, 1,586, 3,173$ for Validation) are strictly **illustrative estimates ($\lfloor \alpha \times N_{\text{elig}} \rfloor$) conditional on the hypothetical assumption of 100% successful scoring coverage** ($N_S = N_{\text{elig}}$).
> - **Actual Operational Capacity Definition**: Because no Phase 06 scoring has been executed, actual successfully scored finite counts $N_S$ remain currently **UNKNOWN**. Actual operational capacity during separately authorized Phase 06 evaluation execution is computed strictly from the observed count of successfully scored finite-score rows:
>   $$K_\alpha = \lfloor \alpha \cdot N_S \rfloor$$
> - **Exclusion of Degraded & Non-Finite Rows**: Transactions falling into State C (`DEGRADED_UNSCORABLE`) or producing non-finite scores (`null`, `NaN`, $+Inf$, $-Inf$) do **NOT** contribute to $N_S$. If any eligible transaction is unscored, $N_S < N_{\text{elig}}$, which proportionally reduces actual alert capacity $K_\alpha$.
> - **No Presumption of Scoring Coverage**: Neither actual scoring coverage nor actual alert counts are claimed to be known prior to authorized scoring execution.

#### Sensitivity Matrix across Evaluation Partitions:
| Budget Scenario ($\alpha$) | Operational Role | Analytical Budget Formula | Illustrative Alerts on Qualified Holdout (Eligible $N_{\text{elig}} = 82,221$; assumes 100% coverage) | Illustrative Alerts on Anomaly Validation (Eligible $N_{\text{elig}} = 158,652^*$; assumes 100% coverage) |
| :---: | :--- | :--- | :---: | :---: |
| **0.10%** | Critical Escalation Queue | $K_{0.1\%} = \lfloor 0.0010 \times N_S \rfloor$ | $\approx 82$ alerts (illustrative) | $\approx 158$ alerts (illustrative) |
| **0.50%** | Constrained Investigation Queue | $K_{0.5\%} = \lfloor 0.0050 \times N_S \rfloor$ | $\approx 411$ alerts (illustrative) | $\approx 793$ alerts (illustrative) |
| **1.00%** | **Frozen Baseline Reference Implementation** | $K_{1.0\%} = \lfloor 0.0100 \times N_S \rfloor$ | $\approx 822$ alerts (illustrative) | $\approx 1,586$ alerts (illustrative) |
| **2.00%** | Expanded Surveillance Queue | $K_{2.0\%} = \lfloor 0.0200 \times N_S \rfloor$ | $\approx 1,644$ alerts (illustrative) | $\approx 3,173$ alerts (illustrative) |

*Boundary Rule*: These sensitivity analyses are strictly retrospective evaluations calculated from the single holdout scoring output array during reporting. They do not alter engine state, trigger rescoring, or mutate configuration files. (*Note: $N_{\text{elig}} = 158,652$ reflects physical dataset count ratified by Project Owner; replacing obsolete 139,028 draft figure).

---

## 7. Metrics & Methodology Specification

### 7.1 Unsupervised Anomaly Characterization (Primary Evaluation)
Requirement 1 mandates explicitly replacing "Genuine Anomaly Ground-Truth Evaluation" with **Unsupervised Anomaly Characterization**.

> [!CAUTION]
> **No Genuine Anomaly Ground-Truth Labels**:
> - PaySim contains **no ground-truth labels for behavioral anomalies**.
> - The target variable `isFraud` reflects synthetic fraud agent attacks, not statistical anomaly ground truth.
> - **Descriptive Nature**: Metrics such as score distributions, kurtosis, active feature counts, and Population Stability Index (PSI) **do NOT establish anomaly-detection accuracy or operational efficacy**. They measure mathematical properties and distributional stability of the model output.

#### Primary Unsupervised Metrics:
1. **Anomaly Score Spread**:
   - Median, Interquartile Range (IQR), 90th percentile, 99th percentile, and maximum of $s_{\text{raw}}(x)$ per channel.
2. **Active Feature Set Attribution ($|A(x)|$)**:
   - Mean, min, and max active feature counts per channel slice.
   - Frequency breakdown of features entering Stage 4 fallback (exclusion).
3. **Degraded Unscorable Rate**:
   $$\text{Degraded Rate} = \begin{cases} \frac{\text{degraded\_count}}{\text{eligible\_count}}, & \text{if } \text{eligible\_count} > 0 \\ \text{NOT\_EVALUABLE}, & \text{if } \text{eligible\_count} == 0 \end{cases}$$
   - *Governance Status*: Degraded rate is an empirical diagnostic metric under Gate 6.1 Option 6B. Zero degraded rows is an architectural diagnostic expectation on standard data, but is **NOT an approved invariant**.
4. **Population Stability Index (PSI) Reproducibility Specification (Tasks 1–3)**:
   - **Mathematical Formulation**:
     $$\text{PSI} = \sum_{b=1}^{M} (P_b^* - Q_b^*) \cdot \ln\left(\frac{P_b^*}{Q_b^*}\right)$$
     where $P_b^*$ is the smoothed and renormalized proportion of evaluation scores in bin $b$, and $Q_b^*$ is the smoothed and renormalized proportion of reference scores in bin $b$.
   - **Scope and Eligibility of Scores**:
     - **Finite Score Requirement**: Every finite real-valued score $s \in \mathbb{R}$, **including numerical zero ($s = 0.0$)**, negative values, and values outside the empirical reference range, is assigned to **exactly one PSI bin**. Zero-valued finite scores are never silently discarded, filtered, or left unassigned.
     - **Null and Non-Finite Score Accounting**: A row with a `null`, `NaN`, positive infinity (`+Inf`), or negative infinity (`-Inf`) score is **not a successfully scored row**. Such records are excluded from the finite-score evaluation population, alert ranking, and the finite-score PSI calculation. Null and non-finite score records are separately accounted for in operational degradation reporting (under Degraded Unscorable Rate $T_{\text{deg}}$ and Fraud Scoring Coverage $T_{\text{cov}}$) and excluded only from the finite-score PSI calculation.
   - **Strict Execution Precedence & Empty-Population Guard**:
     To prevent runtime exceptions (e.g., quantile functions on empty arrays) and invalid statistical artifacts, the PSI calculation pipeline must strictly adhere to the following deterministic execution sequence:
     1. **Step 1 — Population Census**:
        Count the number of finite, successfully scored reference observations ($|S_{\text{ref}}|$) and evaluation observations ($|S_{\text{eval}}|$) for the specific channel.
     2. **Step 2 — Immediate Empty-Population Short-Circuit**:
        If either population has zero finite observations:
        $$|S_{\text{ref}}| == 0 \quad \text{or} \quad |S_{\text{eval}}| == 0$$
        the calculation **terminates immediately and returns $\text{PSI} = \mathbf{NOT\_EVALUABLE}$**.
     3. **Step 3 — Absolute Prohibition of Downstream Calculations on Empty Sets**:
        Whenever $|S_{\text{ref}}| == 0$ or $|S_{\text{eval}}| == 0$:
        - Do **NOT** calculate reference quantiles.
        - Do **NOT** calculate internal cut points.
        - Do **NOT** calculate raw bin proportions ($Q_b$ or $P_b$).
        - Do **NOT** apply smoothing floor ($\epsilon$) or synthesize/manufacture distributions.
        - Do **NOT** calculate smoothed proportions ($Q_b^*$ or $P_b^*$) or PSI.
     4. **Step 4 — Diagnostic Reporting of Empty Populations**:
        The observed population counts ($|S_{\text{ref}}| = 0$ or $|S_{\text{eval}}| = 0$) and operational degradation metrics ($\text{eligible\_count}$, $\text{unscored\_count}$, degraded rate $T_{\text{deg}}$, and failure reason codes) must be reported separately in operational degradation reporting.
     5. **Step 5 — Conditional Downstream Execution**:
        Only if **both** populations contain at least one finite score ($|S_{\text{ref}}| > 0$ and $|S_{\text{eval}}| > 0$) may quantile calculation, bin construction, proportion computation, selective smoothing, and PSI summation proceed as specified below.
   - **Quantile Interpolation Convention (Executed Only When $|S_{\text{ref}}| > 0$)**:
     Reference decile quantiles are computed strictly using **linear interpolation** matching `numpy.percentile(..., method='linear')` and `pandas.Series.quantile(..., interpolation='linear')` on the finite reference scores of the channel slice ($\text{steps} \le 400$) at decile probabilities:
     $$p_k = 0.10 \times k, \quad k \in \{1, 2, \dots, 9\}$$
   - **Deterministic Internal Cut Points & Collapsing**:
     - The minimum ($p=0.0$) and maximum ($p=1.0$) reference quantiles are explicitly **excluded** from the internal cut points.
     - Let the candidate internal decile cut points be $q_1, q_2, \dots, q_9$.
     - Any duplicate cut point values resulting from tied scores or low-cardinality reference distributions are collapsed, yielding a strictly ascending sequence of $m$ unique internal cut points:
       $$c_1 < c_2 < \dots < c_m, \quad \text{where } 0 \le m \le 9$$
   - **Deterministic Bin Interval Definitions**:
     - If $m \ge 1$, the internal cut points partition the entire real line $(-\infty, +\infty)$ into $M = m + 1$ mutually exclusive, collectively exhaustive bins ($2 \le M \le 10$):
       - **Bin 1**: $(-\infty,\; c_1]$ (includes all finite scores $\le c_1$, including $s=0.0$ when $0.0 \le c_1$, and any evaluation scores $< \min(S_{\text{ref}})$).
       - **Intermediate Bins $b \in \{2, \dots, m\}$** (present when $m \ge 2$): $(c_{b-1},\; c_b]$ (left-exclusive, right-inclusive).
       - **Top Bin $M$ ($m+1$)**: $(c_m,\; +\infty)$ (includes all finite scores $> c_m$, including any evaluation scores $> \max(S_{\text{ref}})$).
     - Every finite score $s \in (-\infty, +\infty)$ belongs to exactly one bin.
   - **Degenerate Reference Distributions & Low Cardinality**:
     - If all reference scores are identical (zero score variance) or heavy score ties cause all decile cut points to collapse such that zero internal cut points remain ($m = 0$), then $M = 1$. In this degenerate case, the distribution cannot be partitioned into valid quantile bins, and PSI is formally assigned **`NOT_EVALUABLE`**.
   - **Raw Bin Proportions (Defined Only for Non-Empty Finite Populations $|S_{\text{ref}}| > 0$ and $|S_{\text{eval}}| > 0$)**:
     For each bin $b \in \{1, \dots, M\}$:
     $$Q_b = \frac{|\{s \in S_{\text{ref}} : s \in \text{Bin } b\}|}{|S_{\text{ref}}|}, \quad P_b = \frac{|\{s \in S_{\text{eval}} : s \in \text{Bin } b\}|}{|S_{\text{eval}}|}$$
     where $|S_{\text{ref}}|$ and $|S_{\text{eval}}|$ denote the non-zero counts of finite scores in the reference and evaluation partitions, respectively.
   - **Selective Smoothing & Independent Renormalization**:
     - A ratified smoothing floor $\epsilon = 10^{-4}$ (approved under Gate 6.2) is added **only to zero-valued cells** in the corresponding distribution:
       $$\tilde{P}_b = \begin{cases} P_b + \epsilon, & \text{if } P_b == 0 \\ P_b, & \text{if } P_b > 0 \end{cases}, \qquad \tilde{Q}_b = \begin{cases} Q_b + \epsilon, & \text{if } Q_b == 0 \\ Q_b, & \text{if } Q_b > 0 \end{cases}$$
     - Cells with non-zero proportions ($P_b > 0$, $Q_b > 0$) are left unaltered.
     - Smoothing is strictly prohibited if a population has zero observations ($|S| == 0$), as enforced by Step 2 and Step 3 above.
     - **Independent Renormalization**: Both smoothed distributions are renormalized independently:
       $$P_b^* = \frac{\tilde{P}_b}{\sum_{j=1}^M \tilde{P}_j}, \qquad Q_b^* = \frac{\tilde{Q}_b}{\sum_{j=1}^M \tilde{Q}_j}$$
       guaranteeing that $\sum_{b=1}^M P_b^* = 1.0$ and $\sum_{b=1}^M Q_b^* = 1.0$.
   - **Channel-Level Scope**: Computed **separately per channel** ($\text{PSI}_{\text{TRANSFER}}$ and $\text{PSI}_{\text{CASH\_OUT}}$). Combining scores across channels into a single pooled PSI is mathematically invalid.
   - **Governance Status & In-Sample Baseline Limitation**:
     - **In-Sample Baseline Caveat**: PSI measures divergence against an in-sample reference baseline ($S_{\text{ref}}$ fitted and scored on steps 1–400). Because evaluation scores are generated out-of-sample while reference scores are in-sample, differences between reference and evaluation score distributions may partly reflect the in-sample versus out-of-sample scoring distinction rather than pure temporal drift alone.
     - PSI must **not** automatically be interpreted as pure temporal drift.
     - PSI is **purely descriptive**; it does **not** prove detector accuracy, detector degradation, or fraud detection performance.
     - Unapproved PSI interpretation bands ($<0.10, 0.10-0.25, \ge 0.25$) are **removed from acceptance criteria language** and serve only as reference guidelines.
     - Automated tuning triggers based on PSI are prohibited under config Section 14.
     - All Phase 06 reports and presentations must explicitly disclose this in-sample baseline limitation when presenting PSI results.

---

### 7.2 Fraud Alignment Diagnostics & Recall Coverage (Secondary Diagnostic)
Correction 2 governs the comprehensive definition of fraud capture and scoring coverage metrics.

#### Exact Fraud Metrics & Denominators:
Let the target evaluation partition have:
- $F_{\text{elig}}$: Total fraud transactions among all eligible transactions (`TRANSFER` and `CASH_OUT`).
- $F_{\text{scored}}$: Total fraud transactions among successfully scored transactions ($N_S$).
- $F_{\text{unscored}} = F_{\text{elig}} - F_{\text{scored}}$: Count of eligible fraud transactions that were unscored, degraded, or produced non-finite scores (`null`, `NaN`, `+Inf`, `-Inf`).
- $\text{TP}_\alpha$: Count of transactions selected by budget $K_\alpha$ where $\text{isFraud} == 1$.

> [!IMPORTANT]
> **Non-Finite Score Accounting in Fraud Scoring Coverage**:
> If an eligible transaction with $\text{isFraud} == 1$ yields a `null`, `NaN`, `+Inf`, or `-Inf` score, it is **not a successfully scored row**. Such rows:
> 1. Are strictly excluded from the successfully scored fraud count $F_{\text{scored}}$.
> 2. Remain fully included in total eligible fraud events $F_{\text{elig}}$.
> 3. Are explicitly counted as unscored fraud cases in $F_{\text{unscored}} = F_{\text{elig}} - F_{\text{scored}}$.
> 4. Directly reduce Fraud Scoring Coverage: $\text{Cov}_{\text{fraud}} = \frac{F_{\text{scored}}}{F_{\text{elig}}} < 1.0$.
> 5. Directly reduce Eligible-Population Fraud Recall: $\text{Rec}_{\text{elig}}@K_\alpha = \text{Rec}_{\text{scored}}@K_\alpha \times \text{Cov}_{\text{fraud}}$ (for $F_{\text{scored}} > 0$; when $F_{\text{scored}} == 0$ and $F_{\text{elig}} > 0$, $\text{Rec}_{\text{elig}}@K_\alpha = 0.0$ by direct primary definition while $\text{Rec}_{\text{scored}}@K_\alpha$ is $\text{NOT\_EVALUABLE}$).
> This formulation mathematically guarantees that fraud events associated with numerical or pipeline failure can never silently disappear from reporting.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Fraud Capture Population Decomposition                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total Eligible Frauds (F_elig)                                              │
│ ├── Successfully Scored Frauds (F_scored)                                   │
│ │   ├── Captured Alerts at Budget K (TP_alpha)                              │
│ │   └── Missed Scored Frauds (F_scored - TP_alpha)                          │
│ └── Unscored / Degraded Frauds (F_unscored = F_elig - F_scored)             │
│     └── CANNOT SILENTLY DISAPPEAR FROM REPORTING                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Exact Mathematical Definitions:
1. **Scored-Population Fraud Recall ($\text{Rec}_{\text{scored}}@K_\alpha$)**:
   $$\text{Rec}_{\text{scored}}@K_\alpha = \begin{cases} \frac{\text{TP}_\alpha}{F_{\text{scored}}}, & \text{if } F_{\text{scored}} > 0 \\ \text{NOT\_EVALUABLE}, & \text{if } F_{\text{scored}} == 0 \end{cases}$$
   Measures fraud detection rate among transactions the engine successfully scored.
2. **Fraud Scoring Coverage ($\text{Cov}_{\text{fraud}}$)**:
   $$\text{Cov}_{\text{fraud}} = \begin{cases} \frac{F_{\text{scored}}}{F_{\text{elig}}}, & \text{if } F_{\text{elig}} > 0 \\ \text{NOT\_EVALUABLE}, & \text{if } F_{\text{elig}} == 0 \end{cases}$$
   Measures the proportion of eligible fraud transactions that received a score rather than falling into degraded unscorable states. If any fraud is unscored, $\text{Cov}_{\text{fraud}} < 1.0$.
3. **Eligible-Population Fraud Recall ($\text{Rec}_{\text{elig}}@K_\alpha$)**:
   $$\text{Rec}_{\text{elig}}@K_\alpha = \begin{cases} \frac{\text{TP}_\alpha}{F_{\text{elig}}}, & \text{if } F_{\text{elig}} > 0 \\ \text{NOT\_EVALUABLE}, & \text{if } F_{\text{elig}} == 0 \end{cases}$$
   Measures true end-to-end fraud capture over all eligible fraud events in the partition.

   **Multiplicative Decomposition & Boundary Condition ($F_{\text{scored}} = 0$)**:
   - **Case $F_{\text{scored}} > 0$ (and $F_{\text{elig}} > 0$)**: The exact algebraic identity holds:
     $$\text{Rec}_{\text{elig}}@K_\alpha = \text{Rec}_{\text{scored}}@K_\alpha \times \text{Cov}_{\text{fraud}} = \left(\frac{\text{TP}_\alpha}{F_{\text{scored}}}\right) \times \left(\frac{F_{\text{scored}}}{F_{\text{elig}}}\right) = \frac{\text{TP}_\alpha}{F_{\text{elig}}}$$
   - **Case $F_{\text{scored}} == 0$ (while $F_{\text{elig}} > 0$)**:
     - No fraud transactions were successfully scored, which strictly implies $\text{TP}_\alpha = 0$ (since $\text{TP}_\alpha \le F_{\text{scored}} = 0$).
     - Scored fraud recall is $\text{Rec}_{\text{scored}}@K_\alpha = \mathbf{NOT\_EVALUABLE}$ because its denominator $F_{\text{scored}}$ is zero.
     - Fraud scoring coverage evaluates to $\text{Cov}_{\text{fraud}} = \frac{0}{F_{\text{elig}}} = 0.0$.
     - Eligible-population fraud recall evaluates deterministically from its primary definition to zero:
       $$\text{Rec}_{\text{elig}}@K_\alpha = \frac{\text{TP}_\alpha}{F_{\text{elig}}} = \frac{0}{F_{\text{elig}}} = 0.0$$
     - In this boundary case, the product expression $\text{Rec}_{\text{scored}} \times \text{Cov}_{\text{fraud}}$ is **not evaluated** (preventing an undefined arithmetic operation on $\mathbf{NOT\_EVALUABLE}$); $\text{Rec}_{\text{elig}}@K_\alpha$ evaluates as $0.0$ directly from its primary definition.
   This formulation guarantees that degraded or unscored fraud transactions **cannot silently disappear** from reporting.
4. **Precision at Budget $K_\alpha$ ($\text{Prec}@K_\alpha$)**:
   $$\text{Prec}@K_\alpha = \begin{cases} \frac{\text{TP}_\alpha}{K_\alpha}, & \text{if } K_\alpha > 0 \\ \text{NOT\_EVALUABLE}, & \text{if } K_\alpha == 0 \end{cases}$$
5. **Fraud Enrichment Factor ($\text{Enrichment}@K_\alpha$)**:
   $$\text{Enrichment}@K_\alpha = \begin{cases} \frac{\text{Prec}@K_\alpha}{F_{\text{scored}} / N_S}, & \text{if } F_{\text{scored}} > 0 \text{ and } N_S > 0 \\ \text{NOT\_EVALUABLE}, & \text{otherwise} \end{cases}$$

#### Attack-Level Metrics Status: UNAVAILABLE
- PaySim transactions simulate automated multi-step balance liquidations (e.g. `TRANSFER` followed by `CASH_OUT`).
- However, raw PaySim records provide **no official attack campaign identifiers, fraud ring IDs, or session linkage tokens**.
- Grouping transactions into synthetic "attacks" without verified ground-truth clustering introduces arbitrary heuristic bias.
- Therefore, attack-level evaluation metrics are formally marked **`UNAVAILABLE`** for Phase 06. All fraud alignment metrics are strictly transaction-level.

---

## 8. Hard Engineering Invariants vs. Owner-Approved Targets

In accordance with Correction 4 and Correction 5, non-negotiable engineering invariants are formally separated from project-owner quantitative acceptance targets.

### 8.1 Hard Engineering Invariants (Mandatory Binary Checks — Non-Negotiable)
1. **Zero Prohibited Field Leakage**: Input validation in `AnomalyPreprocessor.validate_inputs()` must reject any payload containing post-event fields (`newbalanceOrig`, `newbalanceDest`), unverified fields (`oldbalanceDest`), proxy flags (`isFlaggedFraud`), or target labels (`isFraud`).
2. **Target Isolation**: Target column `isFraud` must be explicitly dropped before passing to `AnomalyDetectionEngine.score()`.
3. **Immutable Row Index Integrity**: Every input row must possess a unique, non-null, 0-based integer `row_index`.
4. **Population Accounting Invariant & Non-Finite Score Definitions**:
   - A transaction is defined as **successfully scored** if and only if it produces a finite real-valued score ($s \in \mathbb{R}$, where $-\infty < s < +\infty$).
   - A row with a `null`, `NaN`, positive infinity (`+Inf`), or negative infinity (`-Inf`) score is **not a successfully scored row**.
   - All rows with null or non-finite scores are strictly classified as **unscored / degraded** rows.
   - Such rows are excluded from the successfully scored evaluation population ($N_S$), excluded from global alert ranking (cannot receive alerts under budget capacity $K$), and excluded from finite-score PSI calculation.
   - Such rows are tallied in $\text{unscored\_count}$ and reported under operational degradation metrics ($T_{\text{deg}}$).
   - If a row with a null or non-finite score has $\text{isFraud} == 1$, it remains included in eligible fraud accounting ($F_{\text{elig}}$) as an unscored fraud case ($F_{\text{unscored}}$), directly reducing Fraud Scoring Coverage ($\text{Cov}_{\text{fraud}}$).
   - The strict population accounting identity holds across all inputs:
     $$\text{eligible\_count} = \text{successfully\_scored\_count} + \text{unscored\_count}$$
     $$\text{input\_count} = \text{eligible\_count} + \text{ineligible\_count}$$
5. **Deterministic Tie-Breaking**: Budget ranking must sort strictly by $(-s_{\text{raw}}(x), \text{row\_index})$ over all successfully scored rows ($N_S$).
6. **Output Contract Semantics & Operational States**:
   - **State A / B (`SCORED`)**: Non-null, finite real-valued `anomaly_score` ($-\infty < s < +\infty$), null `reason_code`, and $\text{is\_anomaly\_flagged} == \text{alert\_budget\_selected}$. Only State A / B rows contribute to $\text{successfully\_scored\_count}$ ($N_S$).
   - **State C (`DEGRADED_UNSCORABLE`) & Non-Finite Fallbacks**: Null `anomaly_score` (or any non-finite score `NaN`/`Inf`), null `is_anomaly_flagged`, non-null machine-readable `reason_code`, and $\text{alert\_budget\_selected} == \text{False}$. All such rows contribute to $\text{unscored\_count}$ and cannot consume alert budget.
7. **Environment-Specific Bitwise Repeatability**:
   Scoring repeatability must produce bitwise-identical results under the following **strictly identical execution conditions**:
   - Same Python runtime (`3.12.10`) and package dependencies (`scikit-learn 1.7.2`, `numpy 2.5.3`, `pandas 2.3.3`, `scipy 1.16.2`).
   - Same detector hyperparameters (`random_state=42`, `n_jobs=1`, `max_samples="auto"`, `n_estimators=100`).
   - Same input dataset and identical 0-based integer `row_index` assignment.
   - Same single-threaded CPU execution environment.
   *Cross-environment bitwise repeatability across different CPU architectures, OS platforms, or BLAS/LAPACK implementations is NOT claimed and remains unverified.*

### 8.2 Owner-Approved Targets (Pending Formal Project-Owner Threshold Setting)
The following quantitative performance metrics are **NOT approved invariants**; their target numerical values must be established by the Project Owner under Approval Gate 6:
- Maximum permissible Degraded Unscorable Rate ($T_{\text{deg}}$).
- Maximum permissible Score Population Stability Index ($T_{\text{psi}}$).
- Minimum permissible Top-1.0% Fraud Precision ($T_{\text{prec}}$).
- Minimum permissible Top-1.0% Scored Fraud Recall ($T_{\text{rec\_scored}}$).
- Minimum permissible Top-1.0% Eligible Fraud Recall ($T_{\text{rec\_elig}}$).
- Minimum permissible Fraud Scoring Coverage ($T_{\text{cov}}$).
- Minimum permissible Fraud Enrichment Factor ($T_{\text{enrich}}$).

---

## 9. Formal Governance Approval Gates

> [!IMPORTANT]
> **Strict Governance Principle & Execution Prerequisites**:
> Approval of any individual gate below confirms that specific policy, boundary, or parameter definition only.
> **No individual gate approval constitutes authorization for model scoring or evaluation execution.**
> Full Phase 06 evaluation execution strictly requires:
> 1. Complete resolution and sign-off across all eight governance gates.
> 2. Explicit Project-Owner approval of the evaluation protocol.
> 3. Separate, subsequent authorization for Phase 06 tooling implementation and execution.

The Project Owner has reviewed and formally signed off on each of the following 8 governance approval gates:

| Approval Gate | Governance Decision Scope | Options Under Review | Recommended Proposal | Status |
| :---: | :--- | :--- | :---: | :---: |
| **Approval Gate 1** | **Evaluation Population Selection** | Option 1: Steps 551–743 (Qualified Holdout)<br>Option 2: Steps 551–645 (Pre-Inspection Slice)<br>Option 3: Steps 401–550 (Val; $N_{\text{elig}}=158,652$) + 551–743 (Holdout; $N_{\text{elig}}=82,221$)<br>Option 4: Steps 401–743 (Continuous Stream; DERIVED CONTINUOUS-STREAM ELIGIBLE DENOMINATOR = 158,652 + 82,221 = 240,873) | **Option 3 (Dual-Stage)**<br>(Counts verified & ratified) | `APPROVED (OPTION 3)` |
| **Approval Gate 2** | **Qualified Holdout Acceptance** | Acceptance of Steps 551–743 under the Section 3.1 prior exposure disclosure and one-shot protection rule. | **Accept as Qualified Holdout** | `APPROVED` |
| **Approval Gate 3** | **Reference Population Scope** | Adoption of the full 5.78M training partition ($\text{steps} \le 400$) vs. a defined channel-stratified reference sample as the evaluation characterization baseline. *Clarification: Evaluates reference baseline scope only; preserves frozen Phase 05 fitting boundary and does NOT authorize refitting, retraining, or configuration mutation.* | **Full 5.78M Training Partition** (Evaluation baseline only; zero refitting authorized) | `APPROVED` |
| **Approval Gate 4** | **Sensitivity Evaluation Suite Ratification** | Approval of the 4 retrospective budget scenarios ($0.10\%, 0.50\%, 1.00\%, 2.00\%$) as analytical reporting suites. | **Approve Sensitivity Suite** | `APPROVED` |
| **Approval Gate 5** | **Evaluation Metric Suite Adoption** | Formalization of the dual evaluation framework: Primary Unsupervised Characterization vs. Secondary Fraud Diagnostics. | **Approve Dual Framework** | `APPROVED` |
| **Approval Gate 6** | **Quantitative Acceptance Thresholds & Smoothing** | Formal establishment by governance of numerical pass/fail thresholds vs. Option 6B exploratory diagnostics for $T_{\text{deg}}, T_{\text{psi}}, T_{\text{prec}}, T_{\text{rec\_scored}}, T_{\text{rec\_elig}}, T_{\text{cov}}, T_{\text{enrich}}$ (Decision 6.1), and ratification of proposed smoothing parameter $\epsilon = 10^{-4}$ (Decision 6.2). | **Option 6B Exploratory Diagnostics** (Hard thresholds deferred to Phase 07); **Smoothing floor $\epsilon = 10^{-4}$ Ratified** | `APPROVED (OPTION 6B & RATIFIED)` |
| **Approval Gate 7** | **Permissible Business Claims Policy** | Ratification of synthetic dataset disclaimers prohibiting claims of real-world production "zero-day" protection. | **Approve Disclaimers** | `APPROVED` |
| **Approval Gate 8** | **Operational Alert-Policy Semantics** | Confirmation of single global alert budget ($K = \lfloor 0.0100 \times N_S \rfloor$ across combined channels) as the baseline operational policy. *Clarification: Rejecting/deferring does NOT authorize modifying frozen config; any change requires architectural review, owner authorization, versioned change control, and regression testing.* | **Confirm Global Budget Baseline** | `APPROVED` |

---

## 10. Permissible Business Claims & Mandatory Caveats

All reports, dashboards, and communications generated under Phase 06 must strictly enforce the following disclosure rules:

1. **Synthetic Agent Simulation Disclaimer**:
   All findings reflect evaluation on the PaySim mobile money agent simulation. PaySim fraud mechanisms represent automated, scripted balance draining. Performance on PaySim does not guarantee real-world banking detection efficacy against sophisticated human adversaries.
2. **Prohibited Marketing / Production Claims**:
   It is strictly prohibited to claim that the standalone anomaly detector provides "universal fraud prevention," "zero-day fraud interception," or "complete account takeover protection."
3. **Surveillance Role Definition**:
   The standalone anomaly engine is officially defined as an **unsupervised behavioral surveillance layer** designed to detect distributional and multivariate outliers, functioning independently of supervised classification models.

---

## 11. Architecture Status & Execution Authorization Pre-Conditions

The Phase 06 evaluation governance structure and tooling lifecycle are established as follows:

```
[ Step 1: Project Owner Approval & Governance Ratification (COMPLETED) ]
  - Formal sign-off on Gates 1 through 8 completed (Nov 2026)
  - Protocol baseline v1.3.0 formally approved
                               │
                               ▼
[ Step 2: Implementation & Acceptance of Initial Tooling (COMPLETED) ]
  - Implemented src/anomaly/evaluation.py (pure calculations, contracts, metrics, formatting)
  - Verified via tests/test_anomaly_evaluation.py (22/22 synthetic unit tests passed)
  - Persistent serialization (artifacts.py) and CLI tasks (cli.py) deferred
                               │
                               ▼
[ Step 3: Separate Authorization Required for Real-Data Execution ]
  - Real-data execution remains strictly unauthorized
  - Requires separate explicit Project-Owner execution directive
  - Upon separate authorization:
      • Verify frozen config cryptographic digests (compute_config_digests)
      • Generate reference scores using the frozen Phase 05 detector on steps <= 400
      • Execute scoring on approved evaluation populations (steps 401-550, 551-743)
      • Generate reports/anomaly_evaluation_report.json
```
