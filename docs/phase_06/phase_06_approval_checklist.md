# Phase 06 — Governance Approval Checklist & Decision Dossier

**Document Title**: Phase 06 — Governance Approval Checklist & Decision Dossier  
**Document Path**: `docs/phase_06/phase_06_approval_checklist.md`  
**Protocol Baseline**: `docs/models/anomaly_evaluation_protocol.md` (Version `v1.3.0`)  
**Audit Baseline**: `docs/phase_06/anomaly_evaluation_protocol_review.md`  
**Target Subsystem**: Standalone Anomaly Detection Engine (`src/anomaly/`)  
**Configuration Baseline**: `configs/anomaly_detection.yaml` (FROZEN BASELINE)  
**Date**: November 2026  
**Status**: **APPROVED BY PROJECT OWNER — FORMAL SIGN-OFF COMPLETED (2026-11-04)**  

---

## 1. Executive Summary & Purpose

This decision dossier establishes the official, actionable governance checklist for **Project-Owner Review and Approval** of the Phase 06 Anomaly Evaluation & Validation Protocol.

Following the independent technical reconnaissance (Command 01), protocol design and corrections (Command 02), and source-code audit (Command 03), this dossier packages all technical evidence, methodological proposals, and governance choices into eight distinct, self-contained decision gates.

> [!IMPORTANT]
> **Strict Governance Principle & Execution Prerequisites**:
> Approval of any individual gate below confirms that specific policy, boundary, or parameter definition only.
> **No individual gate approval constitutes authorization for model scoring or evaluation execution.**
> Full Phase 06 evaluation execution strictly requires:
> 1. Complete resolution and sign-off across all eight governance gates.
> 2. Explicit Project-Owner approval of the evaluation protocol.
> 3. Separate, subsequent authorization for Phase 06 tooling implementation and execution.

---

## 2. Eight-Gate Governance Approval Checklist

### Gate 1 — Evaluation Population Selection
- **Gate ID & Title**: `GATE-01: Evaluation Population Partition Design`
- **Protocol Proposal**: **Option 3: Dual-Stage Evaluation**
  - Preliminary Anomaly Validation Partition: Discrete simulation $\text{steps } 401\text{--}550$ (378,989 total transactions; 158,652* eligible `TRANSFER`/`CASH_OUT` transactions: 32,723 `TRANSFER` + 125,929 `CASH_OUT`; 1,588 fraud events; *ratified by Project Owner 2026-11-04, replacing the obsolete 139,028 draft figure).
  - Final Qualified Holdout Partition: Discrete simulation $\text{steps } 551\text{--}743$ (196,601 total transactions; 82,221 eligible `TRANSFER`/`CASH_OUT` transactions: 17,219 `TRANSFER` + 65,002 `CASH_OUT`; 2,148 fraud events).
  - Continuous Evaluation Stream (Option 4 comparison): Discrete simulation $\text{steps } 401\text{--}743$ (575,590 total transactions; 240,873* eligible transactions: 49,942 `TRANSFER` + 190,931 `CASH_OUT`; 3,736 fraud events; *DERIVED CONTINUOUS-STREAM ELIGIBLE DENOMINATOR = 158,652 + 82,221 = 240,873, ratified by Project Owner 2026-11-04; replacing obsolete 221,249).
- **Mandatory Prior Exposure Disclosure (Steps 401–550)**:
  - **Outside Anomaly Fitting Window**: Steps 401–550 are strictly outside the Phase 05 detector fitting partition ($\text{steps } \le 400$).
  - **Prior Phase 04 Supervised Exposure**: Steps 401–550 were actively utilized during Phase 04 as the validation fold for supervised classifier comparison (LightGBM, XGBoost, Random Forest), hyperparameter tuning, probability calibration (Platt scaling), and decision-threshold optimization.
  - **Not Pristine**: Steps 401–550 **must not be described as globally untouched or unexposed**. Their use in Phase 06 is strictly as an intermediate diagnostic validation horizon to test dispersion, active feature counts, and sensitivity queues prior to touching the holdout.
- **Technical Evidence**:
  - Eliminates mixing validation and test exposures into a single monolithic stream.
  - Steps 401–550 provide an independent post-training horizon to validate active feature stability, dispersion properties, and retrospective sensitivity queues prior to touching the final holdout.
  - Steps 551–743 remain reserved strictly for final, one-shot reporting.
- **Audit Verification Finding**:
  - The physical parquet dataset contains exactly **158,652 eligible rows** in steps 401–550 (32,723 TRANSFER + 125,929 CASH_OUT). The figure of 139,028 in protocol draft v1.2.6-DRAFT and prior was an analytical estimate derived during reconnaissance. The actual verified count of 158,652 (and DERIVED CONTINUOUS-STREAM ELIGIBLE DENOMINATOR = 158,652 + 82,221 = 240,873) was ratified by Project Owner (2026-11-04) as the official denominator.
- **Recommendation**: **APPROVE Option 3 (Dual-Stage)** with the verified eligible denominator $N_{\text{elig}} = 158,652$ (ratified 2026-11-04) for Anomaly Validation.
- **Remaining Uncertainty**: None on partition boundaries; both partitions are chronologically disjoint and forward-chained.
- **Explicit Decision Required**: Does the Project Owner approve Option 3 Dual-Stage evaluation as the official partition design and ratify $N_{\text{elig}} = 158,652^*$ for steps 401–550?
- **Consequence of Approval**: Confirms the Option 3 Dual-Stage population partition boundaries and denominator definitions only. **Does NOT independently authorize model scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Population partition design remains unapproved; evaluation planning is blocked until an alternative partition design is resolved.
- **Status**: `APPROVED (2026-11-04)`

---

### Gate 2 — Qualified Holdout Acceptance & One-Shot Protection Policy
- **Gate ID & Title**: `GATE-02: Qualified Holdout Acceptance & One-Shot Policy`
- **Protocol Proposal**: Formally accept simulation $\text{steps } 551\text{--}743$ as a **QUALIFIED HOLDOUT (PRIOR PHASE 04 TEST EXPOSURE)** governed by a strict **One-Shot Evaluation Policy**.
- **Technical Evidence**:
  - Prior Phase 04 supervised modeling evaluated all 196,601 transactions in this partition, computing test classification metrics.
  - Two specific false-negative transactions were manually inspected during Phase 04 error analysis:
    1. Row Index `6281484` (Step 646, amount \$399,045.08, channel TRANSFER, partial balance drain).
    2. Row Index `6362462` (Step 730, amount \$7,316,255.05, channel TRANSFER, partial balance drain).
  - Code audit verified that both transactions are physically present at row indices `6281484` and `6362462` in `data/processed/paysim_features_full.parquet` and match the reported characteristics.
- **One-Shot Protection Rules**:
  1. Steps 551–743 are scored **exactly once** under the approved frozen protocol.
  2. Pre-approved retrospective sensitivity analyses ($0.10\%, 0.50\%, 1.00\%, 2.00\%$) utilize the single output score array via post-hoc rank slicing without rescoring.
  3. Rescoring, tuning, feature selection, or budget recalibration using holdout results is strictly prohibited.
  4. Any subsequent modification informed by holdout results permanently invalidates holdout status and requires reserving a fresh, unexposed partition.
- **Recommendation**: **ACCEPT as Qualified Holdout** under the one-shot protection policy.
- **Remaining Uncertainty & Fallback Analysis**:
  - Inherent limitation of reusing a previously benchmarked simulation slice; mitigated by the complete absence of anomaly tuning on this fold.
  - **Clarification on Truncation Fallback (Option 2)**: Truncating the partition at step 645 (Option 2, discarding 80,831 rows) avoids the two specifically inspected false-negative rows (`6281484` and `6362462`), but does **NOT** establish a pristine or unexposed holdout, because steps 551–645 were still part of Phase 04 aggregate supervised test evaluation. Truncating the partition does not eliminate prior exposure.
  - If a genuinely pristine, unexposed holdout is required by governance, an independent, unexposed dataset or partition must be acquired or identified. Truncation cannot be claimed to remove prior exposure.
- **Explicit Decision Required**: Does the Project Owner accept steps 551–743 as the Qualified Holdout under these exact exposure disclosures and one-shot protection rules?
- **Consequence of Approval**: Confirms steps 551–743 as the Qualified Holdout definition and adopts the One-Shot Protection Policy. **Does NOT independently authorize holdout scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Rejects steps 551–743 as the holdout; requires identifying an independent unexposed dataset or resolving holdout governance through separate review before evaluation can proceed.
- **Status**: `APPROVED (2026-11-04)`

---

### Gate 3 — Reference Population Scope
- **Gate ID & Title**: `GATE-03: Reference Population Scope (Full Partition vs. Subsample)`
- **Threefold Architectural Distinction**:
  To prevent any confusion between detector training and evaluation baseline characterization, the protocol explicitly distinguishes three separate concepts:
  1. **Existing Frozen Phase 05 Detector Fitting Boundary**: Strictly $\text{steps } \le 400$, frozen in `src/anomaly/engine.py` and `configs/anomaly_detection.yaml`.
  2. **Reference Population for Evaluation Characterization**: The historical population subset evaluated to establish baseline feature distributions and score distributions (Full Partition $\text{steps } \le 400$ vs. an artificial subsample).
  3. **Reference-Score Observations ($S_{\text{ref}}$) for Protocol Evaluation**: The frozen array of scores generated under the protocol to compute empirical deciles and cut points for PSI comparison.
- **Negative Authorization Declaration**:
  > [!IMPORTANT]
  > Gate 3 governs strictly the scope of evaluation baseline characterization and reference-score generation ($S_{\text{ref}}$). Gate 3 does **NOT** authorize refitting or retraining the Phase 05 detectors, changing the frozen configuration, refitting preprocessor transformations, or modifying Phase 05 model artifacts. Phase 05 implementation and configuration remain frozen.
- **Protocol Proposal**: Establish baseline evaluation characterization on the **full reference partition ($\text{steps } \le 400$)** encompassing 5,787,030 total rows (2,529,536 eligible rows: 481,440 TRANSFER and 2,048,096 CASH_OUT).
- **Technical Evidence & Subsampling Mechanics**:
  - **Preprocessor Baseline Characterization**: Computes exact empirical statistics (medians, MAD, IQR) across all 36 features using the full eligible pool (2,529,536 eligible rows: 481,440 TRANSFER and 2,048,096 CASH_OUT), eliminating subsampling variance on feature scaling.
  - **Isolation Forest Tree Subsampling**: Utilizing the full reference population does **NOT** mean each Isolation Forest tree processes 2.53 million transactions. In scikit-learn, under `max_samples="auto"`, each individual tree draws a random sub-sample of $\min(256, n) = 256$ samples drawn from the reference pool (yielding 100 trees $\times$ 256 samples = 25,600 tree-sample exposures). The full reference pool provides maximum empirical diversity from which these 256-sample tree subsets are drawn, without introducing artificial external subsampling hyperparameters or arbitrary sampling seeds.
  - **Historical Runtime Evidence Qualification**: The 6.72-second fitting time recorded during Command 01 technical reconnaissance represents a **single historical diagnostic observation** on local developer hardware. It is **NOT** a formal benchmark, performance SLA, or acceptance guarantee.
- **Recommendation**: **APPROVE Full Reference Partition ($\text{steps } \le 400$) for Evaluation Baseline Characterization**.
- **Remaining Uncertainty & Hardware Constraints**:
  - Resident memory profile on lower-specification hardware was not instrumented with formal memory profilers and remains unverified.
  - Reference-score generation ($S_{\text{ref}}$) on the full reference partition remains subject to complete eight-gate approval and separate implementation authorization.
- **Explicit Decision Required**: Does the Project Owner approve evaluating baseline characterization against the full 5.78M reference partition, or mandate an artificial channel-stratified subsample?
- **Consequence of Approval**: Confirms adoption of the full reference partition for evaluation baseline characterization while preserving frozen Phase 05 models. **Does NOT authorize reference-score generation, model fitting, or evaluation execution.**
- **Consequence of Rejection/Deferral**: Reference baseline scope remains unapproved; requires defining, justifying, and approving sampling fractions, random seeds, and stratification rules through separate governance review.
- **Status**: `APPROVED (2026-11-04)`

---

### Gate 4 — Retrospective Sensitivity Evaluation Suite
- **Gate ID & Title**: `GATE-04: Retrospective Sensitivity Suite Ratification`
- **Protocol Proposal**: Authorize retrospective top-K sensitivity analysis across four pre-defined analytical scenarios:
  $$\alpha \in \{0.0010,\; 0.0050,\; 0.0100,\; 0.0200\} \quad (0.10\%,\; 0.50\%,\; 1.00\%,\; 2.00\%)$$
  evaluated strictly from the single scoring output array via post-hoc rank slicing ($K_\alpha = \lfloor \alpha \times N_S \rfloor$).
- **Illustrative Capacity Projections ($\lfloor \alpha \times N_{\text{elig}} \rfloor$, Conditional on 100% Scoring Coverage)**:
  - **Preliminary Anomaly Validation Partition ($\text{steps } 401\text{--}550$, eligible $N_{\text{elig}} = 158,652^*$)**:
    - $\alpha = 0.10\%$: $\lfloor 0.0010 \times 158,652 \rfloor = 158$ alerts (illustrative)
    - $\alpha = 0.50\%$: $\lfloor 0.0050 \times 158,652 \rfloor = 793$ alerts (illustrative)
    - $\alpha = 1.00\%$: $\lfloor 0.0100 \times 158,652 \rfloor = 1,586$ alerts (illustrative)
    - $\alpha = 2.00\%$: $\lfloor 0.0200 \times 158,652 \rfloor = 3,173$ alerts (illustrative)
  - **Final Qualified Holdout Partition ($\text{steps } 551\text{--}743$, eligible $N_{\text{elig}} = 82,221$)**:
    - $\alpha = 0.10\%$: $\lfloor 0.0010 \times 82,221 \rfloor = 82$ alerts (illustrative)
    - $\alpha = 0.50\%$: $\lfloor 0.0050 \times 82,221 \rfloor = 411$ alerts (illustrative)
    - $\alpha = 1.00\%$: $\lfloor 0.0100 \times 82,221 \rfloor = 822$ alerts (illustrative)
    - $\alpha = 2.00\%$: $\lfloor 0.0200 \times 82,221 \rfloor = 1,644$ alerts (illustrative)
- **Denominator Qualification & Technical Evidence**:
  - Strict distinction: $N_{\text{elig}}$ is the raw eligible transaction population. Actual successfully scored finite-score count $N_S$ is currently **UNKNOWN** because no Phase 06 scoring has been executed.
  - Illustrative capacity is $\lfloor \alpha \times N_{\text{elig}} \rfloor$, explicitly conditional on the assumption of 100% scoring coverage ($N_S = N_{\text{elig}}$).
  - Actual operational capacity is $K_\alpha = \lfloor \alpha \times N_S \rfloor$, calculated strictly from observed finite scored rows only during separately authorized evaluation execution. Any degraded or non-finite rows will reduce $N_S < N_{\text{elig}}$, proportionally lowering actual alert capacity.
  - Sensitivity analysis does not modify engine code or configuration baseline (`configs/anomaly_detection.yaml` remains frozen at 1.00%).
  - Evaluates operational trade-offs across critical escalation (0.10%), constrained investigation (0.50%), baseline (1.00%), and expanded surveillance (2.00%) queues.
- **Recommendation**: **APPROVE Sensitivity Evaluation Suite**.
- **Remaining Uncertainty**: None; strictly post-hoc reporting calculation.
- **Explicit Decision Required**: Does the Project Owner ratify the 4 sensitivity scenarios as official Phase 06 reporting dimensions?
- **Consequence of Approval**: Confirms the four sensitivity scenarios as authorized analytical reporting dimensions. **Does NOT independently authorize model scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Reporting is restricted exclusively to the 1.00% operational baseline once evaluation execution is authorized.
- **Status**: `APPROVED (2026-11-04)`

---

### Gate 5 — Evaluation Metric Suite Adoption
- **Gate ID & Title**: `GATE-05: Dual Evaluation Metric Framework Adoption`
- **Protocol Proposal**: Formally adopt the decoupled dual evaluation framework:
  1. **Primary Unsupervised Anomaly Characterization**: Anomaly score spread, active feature counts, fallback tier frequencies, Degraded Unscorable Rate ($T_{\text{deg}}$), and channel-specific Population Stability Index (PSI).
  2. **Secondary Fraud Alignment Diagnostics**: Scored-Population Fraud Recall ($\text{Rec}_{\text{scored}}@K_\alpha$), Fraud Scoring Coverage ($\text{Cov}_{\text{fraud}}$), Eligible-Population Fraud Recall ($\text{Rec}_{\text{elig}}@K_\alpha$), Precision ($\text{Prec}@K_\alpha$), and Fraud Enrichment Factor ($\text{Enrichment}@K_\alpha$).
- **Technical Evidence**:
  - PaySim contains synthetic fraud agent attacks, not statistical anomaly ground truth.
  - Unsupervised metrics evaluate mathematical stability and distributional drift, not detector accuracy.
  - Fraud recall metrics measure alignment between statistical outliers and synthetic fraud, with exact accounting of unscored/degraded fraud events ($F_{\text{unscored}} = F_{\text{elig}} - F_{\text{scored}}$).
  - Mathematically sound boundary conditions: $F_{\text{scored}} = 0 \implies \text{Rec}_{\text{elig}} = 0.0$ evaluated without undefined division.
- **Recommendation**: **APPROVE Dual Metric Framework**.
- **Remaining Uncertainty**: None on metric formulations.
- **Explicit Decision Required**: Does the Project Owner adopt the dual evaluation framework and its explicit separation between unsupervised characterization and fraud alignment?
- **Consequence of Approval**: Confirms adoption of the dual evaluation metric definitions and boundary rules. **Does NOT independently authorize model scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Evaluation metric standards remain unresolved; evaluation planning is blocked until metric definitions are approved.
- **Status**: `APPROVED (2026-11-04)`

---

### Gate 6 — Quantitative Acceptance Thresholds & Smoothing Floor
- **Gate ID & Title**: `GATE-06: Quantitative Acceptance Targets & Smoothing Ratification`
- **Protocol Proposal**: Project Owner determines the quantitative evaluation framework (Decision 6.1: explicit numerical thresholds vs. exploratory benchmark diagnostics) and ratifies the proposed PSI smoothing floor $\epsilon = 10^{-4}$ (Decision 6.2).

#### Target Definitions:
| Target Symbol | Metric Description | Mathematical Definition | Proposed Value | Owner Status |
| :---: | :--- | :--- | :---: | :---: |
| **$T_{\text{deg}}$** | Max Permissible Degraded Unscorable Rate | $\frac{\text{degraded\_count}}{\text{eligible\_count}}$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$T_{\text{psi}}$** | Max Permissible Score Population Stability Index | $\sum_{b=1}^{M} (P_b^* - Q_b^*) \cdot \ln(P_b^* / Q_b^*)$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$T_{\text{prec}}$** | Min Permissible Top-1.0% Fraud Precision | $\frac{\text{TP}_{1.0\%}}{K_{1.0\%}}$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$T_{\text{rec\_scored}}$** | Min Permissible Top-1.0% Scored Fraud Recall | $\frac{\text{TP}_{1.0\%}}{F_{\text{scored}}}$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$T_{\text{rec\_elig}}$** | Min Permissible Top-1.0% Eligible Fraud Recall | $\frac{\text{TP}_{1.0\%}}{F_{\text{elig}}}$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$T_{\text{cov}}$** | Min Permissible Fraud Scoring Coverage | $\frac{F_{\text{scored}}}{F_{\text{elig}}}$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$T_{\text{enrich}}$** | Min Permissible Fraud Enrichment Factor | $\frac{\text{Prec}_{1.0\%}}{F_{\text{scored}} / N_S}$ | *Exploratory Diagnostic* | `OPTION 6B (EXPLORATORY DIAGNOSTICS — RATIFIED 2026-11-04)` |
| **$\epsilon$** | PSI Zero-Cell Smoothing Floor | Floor added only to zero-valued quantile cells | `1e-4` | `RATIFIED (1e-4) (2026-11-04)` |

- **Technical Evidence & Boundary Invariants**:
  - In accordance with governance principles, zero pass/fail thresholds were invented or presumed approved by the agent.
  - Smoothing floor $\epsilon = 10^{-4}$ prevents $\ln(0)$ and division by zero while preserving distribution shape under independent renormalization.
  - Boundary condition $F_{\text{scored}} == 0 \implies \text{Rec}_{\text{elig}} = 0.0$ evaluated cleanly from primary definition without undefined division.
- **Clarification on Option 6B (Exploratory Benchmark Diagnostics)**:
  - Option 6B designates targets as *exploratory benchmark diagnostics* for Phase 06 baseline characterization, deferring hard pass/fail gates to Phase 07 multi-model fusion.
  - **Option 6B is NOT permission to ignore degraded, unscored, or non-evaluable outcomes.**
  - All operational degradation metrics ($T_{\text{deg}}$), non-evaluable states, unscored fraud events ($F_{\text{unscored}}$), and coverage reductions ($\text{Cov}_{\text{fraud}} < 1.0$) must be fully tracked, accounted for, and reported with complete transparency.
- **Separation of Governance Decisions**:
  - **Decision 6.1 (Quantitative Performance Framework)**:
    - *Option 6A (Standard Baseline)*: Project Owner establishes explicit numerical pass/fail thresholds for targets $T_{\text{deg}}$ through $T_{\text{enrich}}$.
    - *Option 6B (Exploratory Diagnostics)*: Project Owner designates targets as exploratory benchmark diagnostics, deferring hard pass/fail thresholds to Phase 07, while enforcing full accounting of degraded/non-evaluable states.
  - **Decision 6.2 (PSI Smoothing Parameter Ratification)**:
    - Project Owner explicitly ratifies (or modifies) the proposed zero-cell smoothing floor $\epsilon = 10^{-4}$.
- **Explicit Decisions Required**:
  1. Does the Project Owner select Option 6A (with defined thresholds) or Option 6B (exploratory diagnostics) for targets $T_{\text{deg}}$ through $T_{\text{enrich}}$?
  2. Does the Project Owner ratify $\epsilon = 10^{-4}$ as the PSI zero-cell smoothing floor?
- **Consequence of Approval**: Establishes the quantitative acceptance criteria framework and smoothing parameters. **Does NOT independently authorize model scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Quantitative targets and smoothing parameter remain undefined; evaluation reporting criteria remain blocked until resolved.
- **Status**: `APPROVED — OPTION 6B RATIFIED (2026-11-04); EPSILON = 1e-4 RATIFIED (2026-11-04)`

---

### Gate 7 — Permissible Business Claims Policy
- **Gate ID & Title**: `GATE-07: Permissible Business Claims & Mandatory Caveats Policy`
- **Protocol Proposal**: Enforce strict mandatory caveats across all Phase 06 reports, dashboards, and publications:
  1. **Synthetic Simulation Caveat**: Findings reflect evaluation on the PaySim mobile money agent simulation; performance does not guarantee real-world banking efficacy against human adversaries.
  2. **Prohibited Claims**: Strictly prohibits claiming "universal fraud prevention," "zero-day interception," or "complete account takeover immunity."
  3. **Role Definition**: Officially defines the engine as an **unsupervised behavioral surveillance layer** operating independently of supervised ML models.
- **Technical Evidence**:
  - Supervised error analysis in Phase 04 revealed that PaySim fraud mechanisms represent scripted balance drains. Anomaly detection provides orthogonal outlier coverage, not a replacement for rule engines or supervised models.
- **Recommendation**: **APPROVE Permissible Business Claims Policy**.
- **Remaining Uncertainty**: None.
- **Explicit Decision Required**: Does the Project Owner ratify the synthetic simulation caveats and marketing prohibitions?
- **Consequence of Approval**: Confirms mandatory synthetic PaySim agent simulation caveats and marketing prohibitions for all Phase 06 deliverables. **Does NOT independently authorize model scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Exposes project documentation to compliance risk; blocks external communication until policy is approved.
- **Status**: `APPROVED (2026-11-04)`

---

### Gate 8 — Operational Alert-Policy Semantics Confirmation
- **Gate ID & Title**: `GATE-08: Frozen Operational Alert Policy Baseline Confirmation`
- **Protocol Proposal**: Confirm the frozen operational policy baseline defined in `configs/anomaly_detection.yaml` Section 11:
  - Global combined alert budget across `TRANSFER` and `CASH_OUT` ($K = \lfloor 0.0100 \times N_S \rfloor$).
  - Denominator $N_S$ is strictly successfully scored finite transactions.
  - Deterministic tie-breaking on `row_index` ascending.
  - $N_S == 0 \implies \text{status} = \mathbf{NOT\_EVALUABLE}$, rate is `None`.
  - Zero rescoring, zero configuration mutation.
- **Technical Evidence**:
  - Source code in `src/anomaly/budget.py` and `src/anomaly/engine.py` implements these exact semantics and has passed all edge-case tests.
- **Recommendation**: **CONFIRM Global Alert Policy Baseline**.
- **Remaining Uncertainty**: None; implementation is verified.
- **Explicit Decision Required**: Does the Project Owner confirm the frozen 1.00% global alert budget as the operational baseline?
- **Consequence of Approval**: Confirms the frozen 1.00% global alert budget semantics as the baseline evaluation policy without reopening frozen configuration. **Does NOT independently authorize model scoring or evaluation execution.**
- **Consequence of Rejection/Deferral**: Rejecting or deferring Gate 8 does **NOT** automatically authorize modification of the frozen Phase 05 configuration (`configs/anomaly_detection.yaml`) or codebase (`src/anomaly/`). Any proposed modification to the frozen operational alert policy strictly requires:
  1. Separate architectural review.
  2. Explicit Project-Owner authorization.
  3. Formal versioned change control.
  4. Full regression and verification test suite re-execution.
  Phase 06 governance approval alone does NOT authorize modifying Phase 05 configuration or code. Until such separate authorization occurs, Phase 06 evaluation remains blocked on alert policy definition.
- **Status**: `APPROVED (2026-11-04)`

---

## 3. Project-Owner Sign-Off Block

| Approval Gate | Short Title | Project-Owner Determination | Signature / Decision Reference | Date |
| :--- | :--- | :---: | :---: | :---: |
| **Gate 1** | Population Selection | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 2** | Qualified Holdout Acceptance | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 3** | Reference Population Scope | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 4** | Sensitivity Evaluation Suite | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 5** | Evaluation Metric Suite | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 6.1** | Quantitative Targets Framework | `[ ] OPTION 6A (Thresholds)  [X] OPTION 6B (Exploratory)` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 6.2** | PSI Smoothing Floor ($\epsilon=10^{-4}$) | `[X] RATIFIED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 7** | Business Claims Policy | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |
| **Gate 8** | Operational Alert Baseline | `[X] APPROVED  [ ] REJECTED` | Project Owner Approval Directive | 2026-11-04 |

*Project Owner Sign-Off*: Project Owner Sign-Off Completed (Formal Ratification Directive)  
*Date of Determination*: 2026-11-04  

> [!NOTE]
> Formal sign-off on the gates above confirms governance policies, boundaries, metric definitions, and evaluation protocol v1.3.0.
> In accordance with strict project rules, **model scoring and evaluation execution on real data remain strictly UNAUTHORIZED**.

