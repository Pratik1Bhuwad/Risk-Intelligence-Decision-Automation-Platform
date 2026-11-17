# Phase 07.2 — Architecture Specification & Feasibility Design
## Multi-Model Signal Integration (Option A — Signal Integration Only)

- **Document Version:** `1.4.5 (Gate 7.1 & Gate 7.2 Formal Project Owner Decision Recording)`
- **Specification Status:** `FORMALLY RATIFIED ARCHITECTURE SPECIFICATION (GATE 7.1 APPROVED; GATE 7.2 DECIDED WITH LIMITATIONS; GATE 7.3 NOT AUTHORIZED)`
- **Governing Phase:** Phase 07 — Multi-Model Signal Integration
- **Selected Architecture Scope:** `Option A — Signal Integration Only`
- **Implementation Status:** `NOT AUTHORIZED — SPECIFICATION AND FEASIBILITY DESIGN ONLY`
- **Date of Baseline Inspection (Antigravity-Reported):** 2026-11-05 (Amended: 2026-11-11; Ratified: 2026-11-17)
- **Primary Repository Branch:** `main`

---

## 1. Executive Summary

### 1.1 Purpose and Mandate
This document establishes the amended architectural specification, data contract, lifecycle model, and technical feasibility design for **Phase 07 — Multi-Model Signal Integration** within the Risk Intelligence & Decision Automation Platform. 

Following the completion and remote release of Phase 06 (Anomaly Evaluation & Validation, Protocol v1.3.0), the project transitions into Phase 07. The mandate for Phase 07 is governed strictly by **Option A — Signal Integration Only**, as established in the project governance baseline and Project Owner instructions.

### 1.2 Core Architectural Principle
The primary architectural objective of Phase 07 within its **Mode 1 Historical Integration Design** is to integrate the distinct, independent historical outputs of:
1. **Phase 04 Supervised ML Risk Modeling** (LightGBM model probability-score interface and decision recommendation), and
2. **Phase 05 Unsupervised Anomaly Detection** (Isolation Forest outlier severity score and budget-constrained alert flag)

into a single, identity-safe, versioned, historical signal record (`IntegratedSignalRecord`) without mutating, blending, recalculating, or overriding the independent semantics, thresholds, probability scores, anomaly scores, or decisions of either upstream model.

**Crucial Governance Distinction:** This specification establishes the **architectural design** for signal integration. Architecture definition does **NOT** constitute execution authorization. The document defines two strictly separated design contexts:
- **Mode 1 — Historical Integration Design:** An architecture defined for historical evaluation populations (`row_index` authoritative); execution remains subject to separate explicit authorization and approval gates. Historical `IntegratedSignalRecord` applies strictly to Mode 1.
- **Mode 2 — Operational Identity-Contract Design Only:** A design-only interface specification defining the separate proposed stable operational identity contract (`Incoming Transaction → Proposed Stable Identity Contract` using `transaction_id`). Operational Phase 07 fan-out, scoring, joining, `IntegratedSignalRecord` construction, and record emission are strictly absent and prohibited. Future operational Phase 04/05 dependencies are out-of-scope deferred architecture considerations, not Mode 2 execution flows.

### 1.3 Strict Scope Boundaries (Option A Mandate)
Under Option A, Phase 07 is strictly bounded as a **signal integration and alignment layer**. Phase 07 explicitly **DOES NOT**:
- Produce a fused risk score, blended probability, or unified score index.
- Produce a unified or composite risk level (e.g., "CRITICAL", "VERY_HIGH").
- Produce a transaction prioritization score, composite ranking, or escalation category.
- Produce a new operational decision (e.g., `fused_decision`, automated block, hold, or manual review trigger).
- Train, fit, or deploy a learned fusion model (e.g., meta-classifier, logistic fuser, neural aggregator).
- Implement a decision engine, business rules framework, or policy arbitration mechanism.
- Bloat the integrated signal record by embedding the 36 raw feature inputs or live model object pointers for downstream explainability (Phase 08); raw features and model references are decoupled and linked strictly via transaction identity.

All score blending, composite scoring, and threshold fusion belong exclusively to **Phase 09 — Risk Scoring**. All automated decisioning, business routing, action policies, and manual investigation triggers belong exclusively to **Phase 10 — Decision Automation**.

```
========================================================================================
CONTEXT A: MODE 1 — HISTORICAL INTEGRATION DESIGN
[Architecture Defined — Execution Subject to Separate Explicit Authorization]
========================================================================================
[ Historical Dataset / Ingestion ] ────────> Raw Feature Store (Historical Partition)
              │                                      │
      ┌───────┴───────┐                              │
      ▼               ▼                              │
┌───────────┐   ┌───────────┐                        │
│ Phase 04  │   │ Phase 05  │                        │
│ Supervised│   │ Unsup. IF │                        │
│ LightGBM  │   │ Anomaly   │                        │
└─────┬─────┘   └─────┬─────┘                        │
      │               │                              │
      ▼               ▼                              │
┌───────────────────────────┐                        │
│ Phase 07 Signal           │                        │
│ Integration Layer (Mode 1)│                        │
│ (Hist. Integrated Record) │                        │
└─────────────┬─────────────┘                        │
              │                                      │
              ├───────────────────────────────┐      │
              ▼                               ▼      │
    ┌───────────────────┐           ┌───────────────────┐
    │ Phase 08: XAI     │ ◄─────────┴── Identity Linkage│ (Raw Features + Models
    │ Feature Attrib.   │               (No Schema Bloat)  Consumed Separately)
    │ SHAP & Reason Cds │           ┌───────────────────┐
    └───────────────────┘           │ Phase 09: Scoring │
                                    │ Score Blending &  │
                                    │ Unified Policy    │
                                    └─────────┬─────────┘
                                              ▼
                                    ┌───────────────────┐
                                    │ Phase 10: Decision│
                                    │ Automated Routing │
                                    │ Action Engine     │
                                    └───────────────────┘

========================================================================================
CONTEXT B: MODE 2 — OPERATIONAL IDENTITY-CONTRACT DESIGN ONLY
[Design-Only Interface Specification — Phase 07 Operational Execution NOT AUTHORIZED]
========================================================================================
Incoming Transaction ──> ┌────────────────────────────────────────────────────────┐
                         │ Proposed Stable Identity Contract                      │
                         │ (Mandatory Unique transaction_id: str Only)            │
                         │ [Separate Design-Only Contract; No Signal Integration] │
                         └────────────────────────────────────────────────────────┘
```

*Mode 2 Boundary & Future Dependencies Note (Explanatory Only):* Mode 2 establishes only the boundary from an incoming operational transaction to the separate proposed stable identity contract. Future Phase 04/05 operational dependencies are architectural prerequisites deferred to future operational design; they are **NOT** executable Mode 2 flows. Under the current governance boundary:
- Phase 07 Implementation: **NOT AUTHORIZED** (Gate 7.3)
- Operational Phase 05 Scoring: **NOT AUTHORIZED**
- Operational Relational Join & State Synthesis: **NOT AUTHORIZED**
- Operational `IntegratedSignalRecord` Construction / Emission: **STRICTLY PROHIBITED**
- Operational Population / Window Policy: **DEFERRED (Owner Unassigned)**
- Gate 7.1: **APPROVED** | Gate 7.2: **DECIDED (Approval Object A APPROVED; Approval Object B APPROVED WITH LIMITATIONS)** | Gate 7.3: **NOT AUTHORIZED**

---

## 2. Scope & Governance Authorization

### 2.1 Governance Authorization Status
- **Current Operating Mode:** STRICT READ-ONLY INSPECTION AND DOCUMENTATION CORRECTION.
- **Implementation Scope:** SPECIFICATION AND FEASIBILITY DESIGN ONLY. Implementation is **NOT AUTHORIZED**.
- **Source Code & Test Mutation:** STRICTLY PROHIBITED. No modifications to `src/`, `tests/`, `configs/`, `models/`, or `data/`.
- **Execution Restrictions:** No fitting, scoring, benchmarking, real PaySim evaluation, real PSI computation, test execution (`pytest`), or Git release operations are authorized.
- **Mode 1 Execution Status:** **DESIGN DEFINED — EXECUTION NOT AUTHORIZED**. Defining historical integration architecture does NOT constitute authorization to process evaluation datasets. With Gate 7.1 approved and Gate 7.2 Approval Object A approved, execution remains strictly subject to Gate 7.3 implementation authorization (which remains NOT AUTHORIZED).
- **Mode 2 Operational Execution Status:** **DESIGN ONLY — OPERATIONAL EXECUTION STRICTLY PROHIBITED**.
- **Operational Phase 05 Scoring Authorization:** **STRICTLY NOT AUTHORIZED**.
- **Operational `IntegratedSignalRecord` Emission:** **STRICTLY PROHIBITED** until operational population/window policy and execution contracts receive separate explicit Project Owner approval.
- **Operational Population / Window Policy Status:** **DEFERRED — GOVERNING PHASE / OWNER NOT YET ASSIGNED**.

### 2.2 Phase Functional Boundaries Matrix

| Functional Capability | Phase 07 (Multi-Model Signal Integration) | Phase 08 (Explainable AI) | Phase 09 (Risk Scoring) | Phase 10 (Decision Automation) |
| :--- | :---: | :---: | :---: | :---: |
| Identity preservation & alignment | **AUTHORITY (Mode 1 Hist. Design; Mode 2 Operational Design Only)** | Consumer | Consumer | Consumer |
| Side-by-side signal integration | **AUTHORITY (Mode 1 Hist. Design Only; Execution Subject to Auth.)** | Consumer | Consumer | Consumer |
| Unsupervised & supervised provenance tracking | **AUTHORITY (Mode 1 Hist. Design Only)** | Consumer | Consumer | Consumer |
| Channel eligibility & state mapping | **AUTHORITY (Mode 1 Hist. Design Only)** | Consumer | Consumer | Consumer |
| Raw feature access for explainability | Out of Scope (Preserved in Store) | **AUTHORITY** (Via Identity Linkage) | Out of Scope | Consumer |
| Feature attribution & SHAP values | Prohibited | **AUTHORITY** | Out of Scope | Consumer |
| Human-readable reason explanations | Prohibited | **AUTHORITY** | Out of Scope | Consumer |
| Mathematical score fusion / weightings | Prohibited | Prohibited | **AUTHORITY** | Consumer |
| Unified / composite risk scores (0–100) | Prohibited | Prohibited | **AUTHORITY** | Consumer |
| Action policies (APPROVE / MONITOR / BLOCK) | Prohibited | Prohibited | Prohibited | **AUTHORITY** |
| Queue assignment & SLA escalation | Prohibited | Prohibited | Prohibited | **AUTHORITY** |

*Governance Authority Clarification:* Phase 07 authority in the matrix defines **architectural responsibility only**. It does NOT constitute authorization to execute Phase 04 inference, Phase 05 scoring, relational joining, or record emission.

---

## 3. Source-of-Truth Hierarchy & References

### 3.1 Governing Hierarchy of Authority
1. **Project Owner Instructions:** Explicit constraints and directives communicated directly by the Project Owner.
2. **Confirmed Project Decisions:** Approved baseline gates (including Phase 06 Gates 6.1–6.8 and Phase 07 Option A selection).
3. **`00 — MASTER DASHBOARD`:** Project master control dashboard establishing phase boundaries and milestones. *(Repository status: Not committed to Git working tree; maintained as active project governance context).*
4. **Existing Specifications & Protocols:**
   - Phase 04 Modeling Specification: [ml_risk_modeling.md](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/docs/models/ml_risk_modeling.md)
   - Phase 05 Anomaly Detection Specification: v2.3.2 (Approved 2026-10-31) in [anomaly_detection.yaml](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/configs/anomaly_detection.yaml)
   - Phase 06 Anomaly Evaluation Protocol: v1.3.0 in [anomaly_evaluation_protocol.md](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/docs/models/anomaly_evaluation_protocol.md)
   - Phase 06 Closure Documentation: [phase_06_completion_report.md](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/docs/phase_06/phase_06_completion_report.md)
5. **Existing Source Code & Contracts:**
   - Phase 04 Inference Interface: [src/models/inference.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/models/inference.py)
   - Phase 04 Threshold Optimizer: [src/models/threshold.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/models/threshold.py)
   - Phase 04 Model Metadata: [models/risk_model_v1/model_metadata.json](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/models/risk_model_v1/model_metadata.json)
   - Phase 05 Anomaly Engine: [src/anomaly/engine.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py)
   - Phase 05 Output Schema & Contract: [src/anomaly/schema.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/schema.py)
   - Phase 05 Preprocessing & Fallbacks: [src/anomaly/preprocessing.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/preprocessing.py)
   - Phase 05 Alert Budget Selection: [src/anomaly/budget.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/budget.py)
   - Phase 06 Evaluation Tooling: [src/anomaly/evaluation.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/evaluation.py)
6. **Previous Execution Reports:** Antigravity inspection and audit records (subordinate to source code and formal specifications).

### 3.2 Execution Model & Operating Modes Definition
To eliminate all ambiguity between architectural definition, technical specification, execution authorization, and execution completion, this specification establishes exactly two distinct architectural design contexts:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ FOUR DISTINCT ARCHITECTURAL STATES:                                                    │
│ 1. Architecture Defined      ──> Conceptual structure & interface design established   │
│ 2. Execution Specified       ──> Technical algorithms, schemas & invariants documented │
│ 3. Execution Authorized      ──> Formal Project Owner approval granted (Gate 7.3)      │
│ 4. Execution Completed       ──> Pipeline executed; outputs generated & verified       │
│                                                                                        │
│ CURRENT PLATFORM STATE: States 1 and 2 are established. States 3 and 4 are NOT.       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.1 Mode 1 — Historical Integration Design
- **Definition:** Mode 1 defines the historical Phase 04 and Phase 05 integration architecture for evaluation populations.
- **Scope:** Defines historical input identity (`row_index`), historical Phase 04 prediction outputs, historical Phase 05 anomaly outputs, historical identity reconciliation, historical relational join, historical integration-state semantics, historical `IntegratedSignalRecord` schema, historical completeness and integrity checks, and historical integration test design.
- **Execution Boundary Invariant:** **Mode 1 architecture definition does NOT authorize execution.** Despite formal approval of Gate 7.1 and Gate 7.2 Approval Object A, implementation and execution remain strictly subject to Gate 7.3 implementation authorization (which remains NOT AUTHORIZED). No execution, PaySim data processing, model scoring, or detector scoring is permitted by this document.

#### 3.2.2 Mode 2 — Operational Identity-Contract Design Only
- **Definition:** Mode 2 is strictly a **proposed operational stable identity-contract design**.
- **Scope:** Defines proposed operational transaction identity (`transaction_id: str`), proposed identity contract rules, and proposed future interface prerequisites (`Incoming Transaction → Proposed Stable Identity Contract`). Mode 2 contains **no `IntegratedSignalRecord` schema, dependency, or reference mapping** and defines no Phase 04/05 execution flow.
- **Strict Prohibitions under Mode 2 Phase 07 Integration:** The following operations are strictly prohibited and unauthorized under Mode 2:
  1. Phase 07 operational Phase 04 / Phase 05 fan-out.
  2. Phase 04 inference or `RiskPredictor` adapter wrapping under Mode 2 Phase 07 integration (does not prohibit separately authorized standalone Phase 04 operational inference).
  3. Phase 05 detector fitting.
  4. Phase 05 anomaly scoring.
  5. Operational Phase 04 / Phase 05 fan-in.
  6. Operational relational joining of prediction and anomaly outputs.
  7. Operational integration-state synthesis.
  8. Operational `IntegratedSignalRecord` schema definition or construction.
  9. Operational `IntegratedSignalRecord` emission.
  10. Transient ordinal generation or use as a substitute for stable identity during operational Phase 05 execution.
  11. Claims of production-serving readiness or service readiness.
  12. Claims of operational integration readiness.

#### 3.2.3 Proposed Operational Identity Mapping Status
Any transient ordinal mapping discussed in this specification is strictly:
$$\textbf{PROPOSED INTERFACE DESIGN ONLY — NOT AUTHORIZED FOR GENERATION OR EXECUTION}$$
The platform distinguishes:
- **Stable operational transaction identity:** Unique, immutable identifier (`transaction_id`) assigned at ingestion.
- **Out-of-scope conceptual ordinal mapping note:** Hypothetical bijective ordinal translation discussed for future Phase 05 compatibility (NOT an active Mode 2 adapter flow and NOT authorized for generation or execution).
- **Historical `row_index`:** Authoritative dataset ordinal strictly restricted to historical evaluation populations.
- **Temporary positional information:** Implementation-level array offsets with zero identity semantics.
Transient ordinals must never be described as valid transaction identities. Actual generation, propagation, scoring, and output construction require separate policy and integration-execution approval.

---

## 4. Current-State Technical Inventory (Antigravity-Reported Baseline Inspection)

**Evidence & Verification Provenance Classification (V143-M10):** To preserve strict traceability and prevent conflation of inspection sources, this document explicitly separates four categories of technical evidence:
1. **Source inspection reported by Antigravity:** Static code and configuration inspections reported by Antigravity during the baseline repository audit (2026-11-05).
2. **Findings documented from that reported inspection:** Interface schemas, contracts, and incompatibilities recorded below based on that reported inspection.
3. **Document-level review and correction:** Consistency, schema, and boundary reviews performed strictly on specification documentation (including independent document review findings, the documentation-only v1.4.4 correction pass, and the v1.4.5 formal governance decision recording pass).
4. **Independent source-code verification:** Independent repository inspection or runtime source verification by an independent reviewer (**NOT PERFORMED** during documentation reviews or this documentation-only correction task; zero unperformed source-code verification or invented source evidence is claimed).

### 4.1 Phase 04 Supervised Model System Inventory
- **Model Architecture:** Champion LightGBM classifier (`LGBMClassifier`), version 1.0.0. `[REPORTED IN BASELINE SOURCE INSPECTION: models/risk_model_v1/model_metadata.json]`
- **Inference Entry Point:** `RiskPredictor.predict_decision(data)` in [src/models/inference.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/models/inference.py#L90-L135). `[REPORTED IN BASELINE SOURCE INSPECTION]`
- **Feature Contract:** Exactly 36 canonical features defined in `FEATURE_CATALOG`. `[REPORTED IN BASELINE SOURCE INSPECTION: src/features/metadata.py]`
- **Leakage Enforcement:** Hard rejection (`ValueError`) if input contains any column in `STRICTLY_EXCLUDED_FIELDS` (`isFraud`, `isFlaggedFraud`, post-event transaction amounts). `[REPORTED IN BASELINE SOURCE INSPECTION: src/models/inference.py#L63-L68]`
- **Threshold Policy:**
  - $p < 0.30 \implies \text{LOW} \implies \text{APPROVE}$ (`is_fraud_flagged = 0`)
  - $0.30 \le p < 0.9771 \implies \text{MEDIUM} \implies \text{MONITOR}$ (`is_fraud_flagged = 0`)
  - $p \ge 0.9771 \implies \text{HIGH} \implies \text{MANUAL_INVESTIGATION}$ (`is_fraud_flagged = 1`)
  `[REPORTED IN BASELINE SOURCE INSPECTION: models/risk_model_v1/model_metadata.json#L57-L77]`
- **Output Schema:** 5 fields returned as a pandas DataFrame (batch) or dict (single-record):
  1. `risk_score`: `float64`, range $[0.0, 1.0]$.
  2. `risk_score_100`: `int64` / `int`, range $[0, 100]$.
  3. `risk_level`: `str`, values `{"LOW", "MEDIUM", "HIGH"}`.
  4. `decision`: `str`, values `{"APPROVE", "MONITOR", "MANUAL_INVESTIGATION"}`.
  5. `is_fraud_flagged`: `int64` / `int`, values $\{0, 1\}$.
  `[REPORTED IN BASELINE SOURCE INSPECTION: src/models/threshold.py#L115-L125]`
- **Inference Failure Semantics & Mandatory Execution (Mode 1 Context):**
  In Mode 1 Historical Integration Design, Phase 04 is **strictly mandatory** for all transactions across all 5 channels. Phase 04 has **no degraded inference state**. Any failure in Phase 04 constitutes a fatal pipeline error and causes **batch-level fail-closed abort** (no integrated records emitted; `p4_status = "SUCCESS"` strictly in all emitted records). All Phase 04 output fields are non-nullable. In Mode 2, Phase 04 adapter execution is NOT part of Phase 07 integration; Mode 2 is design-only for stable identity definition. This does not preclude separately authorized standalone Phase 04 operational inference. `[SPECIFIED IN ARCHITECTURAL CONTRACT]`
- **Probability-Score Semantics & Calibration Realities (F08):**
  Phase 04 outputs must be understood as the **existing Phase 04 model probability-score interface**. Platt sigmoid calibration was implemented (`RiskCalibrator`), but empirical benefit was **not demonstrated**. On the out-of-time test partition:
  - **Raw Test Brier Score:** `0.00001072` ($\approx 0.000011$)
  - **Calibrated Test Brier Score:** `0.00001389` ($\approx 0.000014$)
  The evaluated calibrated output exhibited a higher Brier score than the raw output. An output ceiling ($\approx 0.9816$) was also observed as a separate empirical characteristic. The evidence does not establish that the output ceiling caused the Brier score deterioration. Consequently, **calibrated posterior reliability has not been demonstrated**. The integration layer must preserve Phase 04 `risk_score` and `risk_score_100` as supplied, must NOT claim verified posterior probability reliability, and must NOT recalculate, rescale, or reinterpret these values. `[REPORTED IN BASELINE SOURCE INSPECTION: docs/models/ml_risk_modeling.md#L118-L132, models/risk_model_v1/model_metadata.json#L95-L110]`
- **Transaction Identity Handling & Verification Limitations (F01, A09):**
  - **Discarded in Predictor:** `RiskPredictor._prepare_dataframe` executes `return df[self.expected_features], is_single`, explicitly stripping `row_index` or any external transaction identifier. Furthermore, `ThresholdOptimizer.classify_batch` instantiates a new DataFrame from raw NumPy arrays, creating a default `RangeIndex(0, N)`. `[REPORTED IN BASELINE SOURCE INSPECTION: src/models/inference.py#L76, src/models/threshold.py#L115-L125]`
  - **Cardinality vs. Row-Order Verification Distinction:**
    1. *Cardinality Verification:* Checking that output row count equals input row count ($N_{\text{out}} == N_{\text{in}}$) confirms only that no rows were dropped or multiplied.
    2. *Upstream Row-Order Preservation Contract:* Positional identity reattachment depends on whether `RiskPredictor.predict_decision` preserves input sequence without internal sorting, shuffling, or asynchronous reordering.
    3. *Evidence Status (A09):* A synthetic unit test probe design has been defined, but probe implementation and execution remain **PENDING**. Row-order preservation remains an **unverified design assumption**. Equal row counts do NOT independently prove identity correspondence.
    - *Classification:* **DESIGN CONTROL DEFINED; ASSUMPTION OF ROW-ORDER PRESERVATION UNVERIFIED; IMPLEMENTATION VERIFICATION PENDING**.
- **Channel Population Scope:** Scores **all 5 transaction channels** (`TRANSFER`, `CASH_OUT`, `PAYMENT`, `CASH_IN`, `DEBIT`). Output cardinality equals input cardinality ($N_{\text{out}} = N_{\text{in}}$). `[REPORTED IN BASELINE SOURCE INSPECTION]`
- **Upstream Version & Schema Exposure:** `RiskPredictor.predict_decision` output DataFrame does NOT contain model version metadata or output schema version columns. While model artifact version `"1.0.0"` exists in static `models/risk_model_v1/model_metadata.json`, its runtime extraction mechanism into integrated records is `TO BE DEFINED` (adapter injection). Upstream Phase 04 output schema version does not exist (`UNKNOWN / NONE`), and is therefore **EXCLUDED** from the schema. `[REPORTED IN BASELINE SOURCE INSPECTION]`

### 4.2 Phase 05 Unsupervised Anomaly Detection System Inventory
- **Detector Architecture:** scikit-learn `IsolationForest`, $n\_estimators=100$, $max\_samples=\text{"auto"}$ (256 samples/tree), $random\_state=42$, $n\_jobs=1$. `[REPORTED IN BASELINE SOURCE INSPECTION: configs/anomaly_detection.yaml#L19-L31]`
- **Scoring Entry Point:** `AnomalyDetectionEngine.score(df, enforce_temporal_split=False)` in [src/anomaly/engine.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/engine.py#L88-L186). `[REPORTED IN BASELINE SOURCE INSPECTION]`
- **Anomaly Score Semantics:** $s_{\text{raw}}(x) = -\text{score_samples}(x)$. Continuous float metric where higher values indicate greater isolation/outlier severity. **STRICTLY NOT A FRAUD PROBABILITY**. Must never be interpreted as, calibrated into, or blended as a probability. `[REPORTED IN BASELINE SOURCE INSPECTION: src/anomaly/detector.py#L125-L130]`
- **Eligible Channels:** Strictly restricted to `TRANSFER` and `CASH_OUT`. Prohibited/ineligible channels are `PAYMENT`, `CASH_IN`, `DEBIT`. `[REPORTED IN BASELINE SOURCE INSPECTION: configs/anomaly_detection.yaml#L33-L41, src/anomaly/preprocessing.py#L22-L25]`
- **Alert Budget & Historical Selection Formula (F07):** Frozen global alert budget rate of 1.00% ($\alpha = 0.0100$). The alert-selection denominator is strictly the successfully scored, finite-score eligible population, denoted $N_S$. Budget capacity:
  $$K = \lfloor 0.0100 \times N_S \rfloor$$
  Observations are ranked by `anomaly_score` descending, with deterministic tie-breaking on `(-score, row_index)` ascending using immutable evaluation `row_index`. Unscored eligible observations are excluded from the denominator $N_S$ and reported separately as `DEGRADED_UNSCORABLE`. If $N_S = 0$, the population outcome is `NOT_EVALUABLE`. `[REPORTED IN BASELINE SOURCE INSPECTION: src/anomaly/budget.py#L80-L115]`
- **Scored Population & Execution Scope Boundaries (F02, F07):**
  1. *Mode 1 Historical Integration Design Scope:* Evaluates a declared complete historical evaluation population partition ($N_S^{\text{eval}}$). The 1.00% budget $K = \lfloor 0.0100 \times N_S^{\text{eval}} \rfloor$ is computed globally across the entire evaluated partition. Tie-breaking on `(-score, row_index)` ascending is stable and globally deterministic because `row_index` is an immutable, unique dataset ordinal. Defining this design does NOT authorize execution.
  2. *Mode 2 Operational Identity-Contract Design Scope:* Mode 2 is strictly a design-only interface specification. It does **NOT** authorize operational Phase 05 detector scoring, independent micro-batch scoring, batch-local alert selection, or operational record emission.
  3. *Consequences of Batch-Local Alert Selection:* In operational serving, transactions arrive in discrete batches or sliding micro-batches of size $N_{\text{batch}}$. Applying the frozen 1.00% budget formula independently to each batch introduces severe distortions:
     - **Small-Batch Alert Suppression:** When $N_S^{\text{batch}} < 100$, the integer floor $K = \lfloor 0.0100 \times N_S^{\text{batch}} \rfloor$ truncates to zero ($K = 0$), completely suppressing all alerts regardless of outlier severity.
     - **Batch-Composition Sensitivity:** The effective alert threshold fluctuates unpredictably based on the arbitrary score distribution of transactions co-occurring within that specific batch.
     - **Tie-Breaking Instability:** Transient adapter ordinals ($0, \dots, N_S^{\text{batch}}-1$) generated within a batch are batch-local. Tie-breaking on `(-score, transient_ordinal)` is only deterministic within that single batch and does not provide global determinism across different batch sizes, partitions, arrival timings, or reorderings.
     - **Mathematical Non-Equivalence:** Repeated independent batch-local calls are **NOT mathematically or operationally equivalent** to the historical global population selection policy.
  4. *Strict Operational Emission Restriction:*
     - The current Phase 05 alert-selection policy is defined strictly for a declared complete scoring population.
     - The Phase 07 specification does **NOT** define or approve an operational scoring population or window.
     - Incoming operational transactions or arbitrary batches must **NOT** independently invoke Phase 05 scoring and claim the frozen global alert-budget semantics.
     - Batch-local top-K selection is **STRICTLY NOT AUTHORIZED**.
     - **Emission Restriction Invariant:** **No operational `IntegratedSignalRecord` may be emitted until the operational Phase 05 population/window policy and the corresponding Phase 07 integration execution contract receive separate explicit approval.**
     - The platform must not represent an unavailable operational Phase 05 result as `NOT_APPLICABLE`, `DEGRADED_UNSCORABLE`, `NOT_EVALUABLE`, or any other existing state without an approved semantic basis.
     - Operational population/window policy is formally **DEFERRED — GOVERNING PHASE / OWNER NOT YET ASSIGNED** (see Section 17, Deferred Decision 6).
     - Production streaming anomaly-scoring authorization is **NOT ESTABLISHED**.
- **Output Schema:** 8-field contract defined in [src/anomaly/schema.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/schema.py#L40-L65):
  1. `schema_version`: `str` (explicitly `"1.0.0"`)
  2. `row_index`: `int` (immutable, non-negative)
  3. `channel`: `str` (`"TRANSFER"` or `"CASH_OUT"`)
  4. `anomaly_score`: `Optional[float]` (float for SCORED, `None` for DEGRADED)
  5. `is_anomaly_flagged`: `Optional[bool]` (bool for SCORED in declared evaluation population, `None` for DEGRADED)
  6. `anomaly_status`: `str` (`"SCORED"` or `"DEGRADED_UNSCORABLE"`)
  7. `reason_code`: `Optional[str]` (`None` for SCORED, machine-readable string for DEGRADED)
  8. `alert_budget_selected`: `bool` (`True` if in top $K$, else `False`)
- **Transaction Identity Handling:** **MANDATORY ORDINAL REQUIREMENT IN HISTORICAL EVALUATION DESIGN (MODE 1)**. `AnomalyPreprocessor.validate_inputs` enforces presence, non-nullability, integer type, and absolute uniqueness of `row_index`. In Mode 2 design, any conceptual discussion of bijective ordinal translation for future Phase 05 compatibility is an **out-of-scope explanatory boundary note only — NOT AUTHORIZED FOR GENERATION OR EXECUTION**, and the separate proposed operational identity contract defines `transaction_id: str` only. Implementation verification is PENDING. `[REPORTED IN BASELINE SOURCE INSPECTION: src/anomaly/preprocessing.py#L65-L78]`
- **Population Slicing & Channel Output:** `AnomalyDetectionEngine.score` only returns rows for eligible channels (`TRANSFER` and `CASH_OUT`). Ineligible channels (`PAYMENT`, `CASH_IN`, `DEBIT`) are excluded from the output DataFrame and only counted in `BudgetResult.ineligible_count`. Output cardinality is strictly $N_{\text{elig}} = N_{\text{TRANSFER}} + N_{\text{CASH_OUT}} \le N_{\text{total}}$. `[REPORTED IN BASELINE SOURCE INSPECTION: src/anomaly/engine.py#L130-L186]`
- **Lifecycle & Persistence (F09):** **IN-MEMORY ONLY**. `src/anomaly/artifacts.py` does NOT exist. Engine must be fitted in-memory on reference data prior to scoring. If the engine is not fitted, `score()` raises `RuntimeError`. While in-memory detector fitting satisfies the logical fit-before-score requirement for Mode 1 historical evaluation runner design, it does **NOT** establish production service readiness, service startup readiness, persistent artifact availability, cross-process reproducibility, runtime recovery, operational scoring authorization, or streaming readiness. `[REPORTED IN BASELINE SOURCE INSPECTION: Test-Path confirmed False, src/anomaly/engine.py:94]`
- **Upstream Version & Schema Exposure (F10):** `AnomalyOutputRow` exposes `schema_version` (`"1.0.0"`). Detector configuration release version (`"1.0.0"`) is specified only in configuration (`configs/anomaly_detection.yaml#L18`) and is not present in output records; retrieval mechanism is `TO BE DEFINED` (adapter injection). This version identifies **configuration release metadata only**, NOT a fitted model artifact identity or runtime instance ID. `[REPORTED IN BASELINE SOURCE INSPECTION]`

### 4.3 Technical Inventory Classification Summary (Antigravity-Reported vs. Unverified)

| Technical Finding | Status Classification | Evidence Citation |
| :--- | :--- | :--- |
| Phase 04 is mandatory in Mode 1; failure causes batch-level fail-closed abort | **SPECIFIED IN CONTRACT** | Architectural boundary; fail-closed Mode 1 integration design |
| `p4_status` is strictly `"SUCCESS"` in all emitted Mode 1 records; no degraded inference state | **SPECIFIED IN CONTRACT** | Reported `src/models/threshold.py:115-125`; zero degraded state |
| Phase 04 drops `row_index` and resets index to RangeIndex(0, N) | **REPORTED BASELINE SOURCE** | Reported `src/models/inference.py:76`, `src/models/threshold.py:115` |
| Phase 04 row-order preservation probe design defined; implementation verification pending | **DESIGN DEFINED / PENDING** | Positional reattachment requires empirical probe verification (F01, A09) |
| Phase 04 scores all 5 channels ($N_{\text{total}}$ rows) | **REPORTED BASELINE SOURCE** | Reported `src/models/inference.py:90`, `models/risk_model_v1/model_metadata.json:115` |
| Phase 04 outputs 5 non-nullable fields: `risk_score`, `risk_score_100`, `risk_level`, `decision`, `is_fraud_flagged` | **REPORTED BASELINE SOURCE** | Reported `src/models/threshold.py:115-125` |
| Phase 04 calibration benefit was not demonstrated (Test Brier 0.00001072 raw vs 0.00001389 cal; causality unproven) | **REPORTED BASELINE SOURCE** | Reported `docs/models/ml_risk_modeling.md:121-124`, `model_metadata.json:95-100` (F08) |
| Phase 04 prediction DataFrame lacks version and schema metadata | **REPORTED BASELINE SOURCE** | Reported `src/models/inference.py:128-134` |
| Phase 05 mandates unique integer `row_index` in historical evaluation (Mode 1) | **REPORTED BASELINE SOURCE** | Reported `src/anomaly/preprocessing.py:65-78` |
| Phase 05 alert denominator is finite scored observations ($N_S$) in declared complete evaluation population | **REPORTED BASELINE SOURCE** | Reported `src/anomaly/budget.py:80-115` (F07) |
| Phase 05 operational scoring authorization & population/window policy | **NOT AUTHORIZED / DEFERRED** | DEFERRED — GOVERNING PHASE / OWNER NOT YET ASSIGNED; batch-local top-K selection unauthorized (F02, F07) |
| Operational `IntegratedSignalRecord` emission | **STRICTLY PROHIBITED** | Prohibited pending explicit policy and contract approvals (F07-R5, V143-M07) |
| Phase 05 uninitialized detector raises `RuntimeError` (fail-closed engine/runner guard) | **REPORTED BASELINE SOURCE** | Reported `src/anomaly/engine.py:94` (F03, V143-M08) |
| Phase 05 detector fitting lifecycle (Mode 1 runner precondition vs. unestablished future service startup) | **DESIGN-DEFINED / UNVALIDATED** | Section 10 lifecycle design; runner readiness does NOT establish service readiness (F09, V143-M08) |
| Phase 05 `p5_detector_version` identifies config version, NOT fitted artifact ID | **REPORTED BASELINE SOURCE** | Reported `configs/anomaly_detection.yaml:18` (F10) |
| Phase 05 only scores and outputs TRANSFER and CASH_OUT ($N_{\text{elig}}$ rows) | **REPORTED BASELINE SOURCE** | Reported `src/anomaly/engine.py:130-186`, `src/anomaly/budget.py:180` |
| Phase 05 outputs 8-field contract with `schema_version` | **REPORTED BASELINE SOURCE** | Reported `src/anomaly/schema.py:40-65` |
| Direct positional concatenation `pd.concat([p4, p5], axis=1)` causes severe row misalignment | **REPORTED BASELINE SOURCE** | Structural mismatch: $N_{\text{total}} \neq N_{\text{elig}}$ and dropped index |
| Phase 05 persistence module `src/anomaly/artifacts.py` is absent | **REPORTED BASELINE SOURCE** | Reported non-existent on disk (baseline inspection 2026-11-05) |
| Processed Parquet dataset lacks persistent transaction ID column | **CONFLICT / UNKNOWN** | Reported Parquet schema lacks persistent UUID; requires authoritative `row_index` in Mode 1 |
| Independent source-code verification of baseline inventory by external reviewer | **NOT PERFORMED** | Documentation-only review/correction scope; independent repository verification pending (V143-M10) |
| Runtime performance, throughput, latency, and memory metrics | **UNKNOWN** | Unmeasured; empirical benchmarks not conducted |
| Empirical performance lift from combining Phase 04 and Phase 05 | **UNKNOWN** | Unverified; real-data evaluation prohibited |

---

## 5. Architecture Decision Record: ADR-07-001

### 5.1 Context
Phase 04 provides a supervised fraud risk score and decision recommendation trained on labeled historical data. Phase 05 provides an unsupervised outlier severity score and budget-constrained alert flag tuned to detect structural behavioral anomalies. Downstream consumers (Phase 08 Explainable AI, Phase 09 Risk Scoring, and Phase 10 Decision Automation) require access to both model signals for a given transaction.

In the initial Phase 07.1 interface inventory report, the architecture was colloquially described as "Multi-Model Fusion & Decision Engine" and proposed a `fused_decision` field. This formulation violated the project master governance hierarchy, which explicitly reserves score blending to Phase 09 and operational decisioning to Phase 10.

### 5.2 Decision
We formally adopt **Option A — Side-by-Side Signal Integration without Decision Fusion**:
1. Phase 07 shall define a historical signal record (`IntegratedSignalRecord`) for **Mode 1 Historical Integration Design only** containing the verbatim, unmodified historical outputs of Phase 04 and Phase 05 joined on validated historical `row_index` within authorized evaluation scopes. Mode 2 does NOT define or emit an operational `IntegratedSignalRecord`.
2. Phase 07 shall NOT compute any blended risk score, combined score, priority index, or fused decision.
3. Phase 07 shall NOT alter, recalibrate, or re-threshold Phase 04 probability scores or Phase 05 anomaly scores.
4. Phase 07 shall preserve the exact Phase 04 `risk_score_100` as supplied by Phase 04 without independent recomputation.
5. Phase 07 shall treat Phase 04 as strictly mandatory in Mode 1: any failure in Phase 04 causes batch-level fail-closed abort (no integrated records emitted).
6. Phase 07 shall handle channel eligibility asymmetries by providing explicit sentinel states (`NOT_APPLICABLE`) rather than imputing zeros or suppressing transactions in Mode 1.
7. Phase 07 defines two distinct architectural design contexts:
   - **Mode 1 (Historical Integration Design):** Architectural definition using authoritative `row_index` over declared complete historical evaluation populations (no synthetic IDs fabricated). Architecture defined; execution remains subject to separate authorization.
   - **Mode 2 (Operational Identity-Contract Design Only):** Design-only interface specification defining mandatory `transaction_id`. Operational Phase 07 execution, scoring, joining, and record emission are strictly prohibited.
8. Phase 07 shall NOT embed raw feature inputs or model pointers into historical `IntegratedSignalRecord` (Mode 1); Phase 08 consumes raw features and models independently via identity linkage.
9. Phase 07 strictly preserves the frozen Phase 05 alert selection formula $K = \lfloor 0.0100 \times N_S \rfloor$ over the declared historical complete population (Mode 1). Independent batch-local alert selection, operational Phase 05 scoring, and operational record emission are **STRICTLY PROHIBITED** without an approved operational population/window policy and execution contract.
10. All downstream policy decisions and composite scoring belong to Phase 09 and Phase 10. The operational population/window policy is formally **DEFERRED — GOVERNING PHASE / OWNER NOT YET ASSIGNED**.

### 5.3 Rationale
1. **Mathematical Independence & Semantic Preservation:** Phase 04 outputs a model probability score via its existing interface (where calibrated posterior reliability has not been demonstrated), whereas Phase 05 outputs an unsupervised outlier severity score $-\text{score_samples}(x)$. The anomaly score is strictly not a probability and must not be treated as such. Linearly or non-linearly blending these metrics without formal empirical validation in Phase 09 corrupts the distinct semantic meaning of both signals.
2. **Operational Decoupling & Explainability Hand-Off:** Downstream consumers have disparate needs. Phase 08 (Explainable AI) requires raw feature matrices and live model object references to compute Shapley values and tree feature attributions. Embedding 36 raw features into `IntegratedSignalRecord` would massively bloat per-record serialization, blur architectural responsibilities, and violate Option A. Decoupling the feature store from the integrated signal record and linking them via authoritative transaction identity preserves architectural purity and high throughput.
3. **Auditability & Regulatory Provenance:** In financial risk intelligence, maintaining the clear separation between supervised risk prediction and unsupervised anomaly detection is essential for model governance, SR 11-7 compliance, and explainability.

### 5.4 Consequences
- **Positive:**
  - Preserves exact model contracts and existing test suites.
  - Zero risk of regression in Phase 04 decision thresholds or Phase 05 alert budgets.
  - Leaves downstream optimization fully unconstrained for Phase 08, 09, and 10.
  - Provides a clean, typed contract for all downstream consumers without payload bloat.
- **Negative:**
  - Downstream consumers cannot obtain a single "all-in-one" score directly from Phase 07; they must consume both signals side-by-side until Phase 09 is implemented.
- **Neutral:**
  - Requires maintaining a Mode 1 identity-preservation adapter to reconcile Phase 04's index-dropping behavior with Phase 05's mandatory `row_index` in historical evaluation, while maintaining a separate proposed operational stable identity contract (`transaction_id`) for Mode 2 design without assigning any `RiskPredictor` adapter to Mode 2.

### 5.5 Alternatives Considered and Rejected
- **Option B — Heuristic Rule-Based Decision Fusion:** Rejected. Violates Master Dashboard governance by introducing decision automation before Phase 10.
- **Option C — Learned Meta-Model Fusion:** Rejected. Requires training a secondary meta-classifier, violating the read-only and no-training constraints of Phase 07 and conflating signal integration with Phase 09 scoring.
- **Monolithic Single-Pipeline Execution:** Rejected. Couples Phase 04 and Phase 05 runtimes, making independent model upgrades or channel-specific routing impossible.
- **Monolithic Record Expansion (Embedding Raw Features in Phase 07):** Rejected. Duplicating 36 raw features in `IntegratedSignalRecord` for Phase 08 causes payload bloat and conflates signal integration with feature serving.

---

## 6. Logical Architecture & Ingestion Topology

### 6.1 Ingestion and Execution Topology (F07-R3, A01)
The logical architecture establishes an unambiguous separation between the **Mode 1 Historical Integration Design** and the **Mode 2 Operational Identity-Contract Design Only**:

```
========================================================================================
TOPOLOGY A: MODE 1 — HISTORICAL INTEGRATION DESIGN
[Architecture Defined — Execution Subject to Separate Explicit Authorization]
========================================================================================
                         Historical Evaluation Dataset
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │    Identity Ingestion &     │
                      │    Lineage Verification     │
                      │   (Authoritative row_index) │
                      └──────────────┬──────────────┘
                                     │
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
       ┌───────────────────────┐           ┌───────────────────────┐
       │  Phase 04 Adapter     │           │  Phase 05 Adapter     │
       │  (Hist. Feature Prep) │           │  (Filter ELIGIBLE_CH) │
       │  (Predictor Execution)│           │  (Validate row_index) │
       │  (Reattach row_index) │           │  (AnomalyEngine.score)│
       └───────────┬───────────┘           └───────────┬───────────┘
                   │ (Fail-Closed on Error)            │
                   ▼                                   ▼
       ┌───────────────────────┐           ┌───────────────────────┐
       │ Phase 04 Predictions  │           │ Phase 05 Signals      │
       │ (N_total rows, P4 cols│           │ (N_elig rows, P5 cols)│
       │  p4_status = SUCCESS) │           │ (Declared Population) │
       └───────────┬───────────┘           └───────────┬───────────┘
                   │                                   │
                   └─────────────────┬─────────────────┘
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │    Relational Join Layer    │
                      │  (Mode 1: 10-Point Checks,  │
                      │   1:1 Join on row_index,    │
                      │   Anti-Join Orphan Check,   │
                      │   Fail-Closed Guard)        │
                      └──────────────┬──────────────┘
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │  Integrated Signal Emitter  │
                      │ (Hist. IntegratedSignalRec) │
                      └──────────────┬──────────────┘
                                     │
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
       ┌───────────────────────┐           ┌───────────────────────┐
       │ Phase 08: Explainable │           │ Phases 09 & 10:       │
       │ AI (SHAP & Reasons)   │           │ Scoring & Automation  │
       │ (Mode 1 Hist. Stream) │           │ (Mode 1 Hist. Stream) │
       └───────────────────────┘           └───────────────────────┘

========================================================================================
TOPOLOGY B: MODE 2 — OPERATIONAL IDENTITY-CONTRACT DESIGN ONLY
[Design-Only Interface Specification — Phase 07 Operational Execution NOT AUTHORIZED]
========================================================================================
Incoming Transaction ──> ┌────────────────────────────────────────────────────────┐
                         │ Proposed Stable Identity Contract                      │
                         │ (Mandatory Unique transaction_id: str Only)            │
                         │ [Separate Design-Only Contract; No Signal Integration] │
                         └────────────────────────────────────────────────────────┘
```

*Mode 2 Topology Boundary Note (Explanatory Only):* Mode 2 specifies only the ingestion-to-identity contract boundary (`Incoming Transaction → Proposed Stable Identity Contract`). No Phase 04 or Phase 05 execution branches, model scoring, anomaly scoring, fan-in, relational join, integration-state synthesis, or `IntegratedSignalRecord` construction/emission exist in Mode 2. Future operational Phase 04/05 interface dependencies are deferred architectural considerations outside Mode 2's diagrammed flow.
- **Current Governance Boundary:** Phase 07 Implementation: **NOT AUTHORIZED** (Gate 7.3) | Operational Phase 05 Scoring: **NOT AUTHORIZED** | Operational `IntegratedSignalRecord` Construction/Emission: **STRICTLY PROHIBITED** | Operational Population/Window Policy: **DEFERRED (Owner Unassigned)** | Gate 7.1: **APPROVED** | Gate 7.2: **DECIDED (Approval Object A APPROVED; Approval Object B APPROVED WITH LIMITATIONS)**.

### 6.2 Execution Sequence and Invariants (F07-R1, F07-R2, F07-R4, F07-R6, V143-B03, V143-B04)
The pipeline design strictly separates the Mode 1 historical integration execution sequence from Mode 2's design-only operational identity contract:

1. **Step 1 (Ingestion & Mode-Specific Identity Resolution):**
   - *Mode 1 (Historical Integration Design):* `row_index` is verified as an authoritative non-negative ordinal sequence ($0, 1, \dots, N-1$). Reconstructing via `np.arange(len(df))` is permissible ONLY for complete datasets where sequential row lineage has been verified. Historical `IntegratedSignalRecord` contains only `row_index` (no `transaction_id` field, and no synthetic transaction IDs are fabricated).
   - *Mode 2 (Operational Identity-Contract Design Only):* `transaction_id` is mandatory in the separate proposed operational stable identity contract (`transaction_id: str`), assigned once at ingestion or at the platform boundary and preserved across retries or downstream boundaries. Independent identifier generation inside processing stages and regeneration on retry are strictly prohibited. Mode 2 has zero dependency on `IntegratedSignalRecord`, and historical `row_index` is excluded from the operational identity contract. Operational identity support defines contract requirements only and **DOES NOT authorize operational detector execution, operational join execution, or operational record emission**.
2. **Step 2 (Adapter Design & Execution Boundaries):**
   - **Branch A (Phase 04 Adapter — Strictly Mode 1 Historical Integration Only):**
     - *Mode 1 (Historical Integration Design):* When executed under separate authorization, the Mode 1 Phase 04 adapter retains the active `row_index` identity mapping outside the predictor, strips excluded leakage fields, invokes `RiskPredictor.predict_decision`, verifies output cardinality ($N_{\text{out}} == N_{\text{in}}$), and reattaches `row_index` based on the design assumption of upstream row-order preservation. If Phase 04 fails, execution halts immediately; the entire batch fails closed (`p4_status = "SUCCESS"` strictly in emitted records).
     - *Mode 2 (Operational Identity-Contract Design Only):* **Phase 07 defines NO `RiskPredictor` execution or Phase 04 adapter wrapper in Mode 2.** Operational stable identity propagation belongs strictly to the separate proposed operational identity contract, not to a Mode 2 Phase 04 adapter. This does not preclude separately authorized standalone Phase 04 operational inference outside Phase 07.
   - **Branch B (Phase 05 Adapter & Operational Authorization Boundary):**
     - *Mode 1 (Historical Integration Design):* When executed under separate authorization, the adapter filters eligible channels (`TRANSFER`, `CASH_OUT`), validates `row_index`, and executes scoring across the declared complete historical evaluation population partition.
     - *Mode 2 (Operational Identity-Contract Design Only):* Any conceptual discussion of bijective transient ordinal mapping for future Phase 05 compatibility is an **out-of-scope proposed interface note only — NOT AUTHORIZED FOR GENERATION OR EXECUTION**, and no Mode 2 Phase 05 execution branch exists. Operational Phase 05 anomaly scoring and batch-local top-K alert selection are **STRICTLY NOT AUTHORIZED**. Until a separately approved operational population/window policy exists, operational transactions must not independently invoke Phase 05 scoring or emit operational flagged/unflagged anomaly statuses.
3. **Step 3 (Relational Merge):**
   - *Mode 1 (Historical Integration Design):* Predictions from Branch A ($N_{\text{total}}$) and Branch B ($N_{\text{elig}}$) undergo ten mandatory pre-join integrity checks before relational merging on `row_index`.
   - *Mode 2 (Operational Identity-Contract Design Only):* **Operational fan-in and relational merge execution are NOT AUTHORIZED.** Mode 2 defines no executable Phase 07 join.
4. **Step 4 (State Synthesis):**
   - *Mode 1 (Historical Integration Design):* Non-eligible transactions (`PAYMENT`, `CASH_IN`, `DEBIT`) receive explicit `NOT_APPLICABLE` sentinels (`integration_status = "INTEGRATED_INELIGIBLE"`). Scored transactions in declared evaluation populations receive `integration_status = "INTEGRATED_SCORED"`. Degraded transactions receive `integration_status = "INTEGRATED_DEGRADED"` with degradation reason codes.
   - *Mode 2 (Operational Identity-Contract Design Only):* **Operational state synthesis is NOT AUTHORIZED.** No operational transaction can receive an authorized Phase 05 flagged/unflagged result without an approved operational population/window policy.
5. **Step 5 (Post-Join Validation & Record Emission):**
   - *Mode 1 (Historical Integration Design):* Output cardinality assertion ($N_{\text{integrated}} == N_{\text{input}}$) and anti-join orphan detection are executed. Any integrity violation triggers immediate failure and aborts record emission. Successfully validated records are emitted as historical `IntegratedSignalRecord`s.
   - *Mode 2 (Operational Emission Restriction):* **Mode 2 has no operational `IntegratedSignalRecord` schema, construction, or emission.** Operational record construction and emission remain unapproved and strictly prohibited until the operational population/window policy and corresponding execution contract receive separate explicit Project Owner approval.

---

## 7. Identity & Join Design

### 7.1 Historical Integration Design (Mode 1) vs Operational Identity-Contract Design (Mode 2)
A rigorous, unambiguous separation is maintained between the historical integration design and the operational identity design:

#### 7.1.1 Mode 1: Historical Integration Design (`row_index` Authoritative)
- **Status:** **ARCHITECTURE DEFINED — EXECUTION NOT AUTHORIZED** (Gate 7.1 and Gate 7.2 Approval Object A approved; execution strictly subject to Gate 7.3 implementation authorization).
- **Authoritative Identity:** `row_index: int`.
- **Nullability & Type:** Strictly non-null, non-negative integer ($\ge 0$).
- **Uniqueness Invariant:** Must be strictly unique across the evaluation population ($|U(\text{row\_index})| == N_{\text{input}}$).
- **`transaction_id` Exclusion Policy:** Historical `IntegratedSignalRecord` contains **no `transaction_id` field**. Transaction IDs must **NOT** be fabricated, synthesized, or generated for historical PaySim records.
- **Sequential Lineage Rule:** Reconstructing `row_index` using `np.arange(len(df))` is permissible **only for the complete dataset when sequential row lineage has been verified**. It is strictly invalid to apply `np.arange` to filtered subsets, shuffled partitions, or out-of-order batches.
- **Phase 05 Requirement:** In Phase 05, `row_index` is an explicit, mandatory integer requirement used for deterministic alert-budget tie-breaking on `(-score, row_index)`.
- **Join Key:** Relational join executes on `on="row_index"`.
- *Status:* **DESIGN CONTROL DEFINED; IMPLEMENTATION & EXECUTION PENDING AUTHORIZATION**.

#### 7.1.2 Mode 2: Operational Identity-Contract Design Only (`transaction_id` Authoritative; Separate Design-Only Contract)
- **Status:** **DESIGN-ONLY MODE** (NOT an executable Phase 07 integration mode; defines Gate 7.2 Approval Object B, which is APPROVED WITH LIMITATIONS for design-level identity contract only).
- **Authoritative Identity:** `transaction_id: str`.
- **Nullability & Type:** Strictly non-null, non-empty unique string (e.g., UUIDv4 or GUID) within the separate proposed operational identity contract.
- **Uniqueness Invariant:** Must be strictly unique across all active transactions ($|U(\text{transaction\_id})| == N_{\text{input}}$).
- **Strict Schema Separation & Exclusion of `row_index` (V143-B01, V143-B03, F05):** Historical `row_index` is strictly a Mode 1 field and is **absent from the proposed operational stable identity contract**. Mode 2 has **no `IntegratedSignalRecord` schema or dependency**. Internal ordinals or temporary positional markers must never leak into the operational identity contract or any external interface.
- **Lifecycle & Governance:** In future production processing, `transaction_id` must be assigned **exactly once** at ingestion or at the authoritative transaction boundary (e.g., enterprise API gateway).
- **Strict Prohibition 1:** Identifiers must NOT be independently generated inside downstream branches or adapters.
- **Strict Prohibition 2:** Identifiers must NOT be regenerated on pipeline or stage retry.
- **Operational Identity Support vs. Scoring Authorization (F07):** Mode 2 defines only the standalone proposed stable identity contract (`Incoming Transaction → Proposed Stable Identity Contract`). It does **NOT** authorize operational Phase 04/05 fan-out, Phase 05 detector scoring, micro-batch scoring, batch-local alert selection, operational join execution, or operational `IntegratedSignalRecord` construction/emission.
- **Future Interface Boundary Note:** Any future relational join across operational model outputs would require a separately designed and approved operational integration contract keyed on `transaction_id`; Mode 2 performs NO relational join.
- *Status:* **DESIGN CONTROL DEFINED; OPERATIONAL EXECUTION STRICTLY PROHIBITED**.

#### 7.1.3 Model Adapter Identity-Preservation Requirements (Mode 1 Historical Scope Only)
To satisfy identity controls without altering frozen Phase 04 or Phase 05 source code:
1. **Phase 04 Adapter Contract & Identity Verification (F01, A09, V143-B04):**
   - **Strictly Scoped to Mode 1 Historical Integration Design:** The Phase 04 adapter wraps `RiskPredictor` exclusively for Mode 1 historical evaluation batches.
   - Cache the input `row_index` identity Series prior to predictor invocation, strip excluded leakage fields, pass the feature DataFrame to `predict_decision`, verify output cardinality ($N_{\text{out}} == N_{\text{in}}$), and reattach `row_index`.
   - **Mode 2 Exclusion (V143-B04):** Operational stable identity propagation (`transaction_id`) under Mode 2 is kept strictly separate from the Phase 04 adapter. Phase 07 introduces **no `RiskPredictor` execution or Phase 04 adapter wrapper into Mode 2**. Phase 04 prediction behavior remains untouched.
   - **Verification Strategy & Unverified Assumption (A09):** Rebinding cached historical identities by positional order relies on the **unverified assumption that `RiskPredictor` and `ThresholdOptimizer` strictly preserve row order**. Equal cardinality does not independently prove correspondence. A synthetic probe design has been specified, but implementation and execution verification remain **PENDING**.
2. **Phase 05 Adapter Contract (Mode 1 Historical Integration; F02, F05, F07, F07-R4):**
   - Wrap `AnomalyDetectionEngine` strictly for Mode 1 historical evaluation batches, validating immutable integer `row_index` directly on input across the declared complete scoring population upon separate execution authorization.
   - **Out-of-Scope Operational Note:** Any conceptual bijective mapping between internal transient ordinals ($0, \dots, N_{\text{elig}}-1$) and `transaction_id` for hypothetical future Phase 05 execution is **NOT part of Mode 2's active flow — PROPOSED FUTURE INTERFACE CONCEPT ONLY AND NOT AUTHORIZED FOR GENERATION OR EXECUTION**.
   - **Non-Leakage Invariant (F05, V143-B03):** Internal transient ordinals must never replace authoritative `transaction_id` and must never appear in the proposed operational identity contract or any external interface. Mode 2 has no `IntegratedSignalRecord` dependency or emission.
   - **Operational Scoring Authorization Boundary:** Operational Phase 05 scoring, ordinal generation, and batch-local top-K alert selection are **STRICTLY NOT AUTHORIZED**. Emitting operational flagged/unflagged statuses without an approved population/window policy is prohibited.
3. *Implementation Verification:* Implementation verification of Mode 1 adapter controls is **PENDING**.

### 7.2 Strict Rejection of Positional Concatenation
Direct positional concatenation via `pd.concat([p4_df, p5_df], axis=1)` is **strictly rejected** as structurally invalid and unsafe:
1. **Cardinality Asymmetry:** Phase 04 outputs predictions for all 5 channels ($N_{\text{total}}$ rows). Phase 05 outputs predictions only for `TRANSFER` and `CASH_OUT` ($N_{\text{elig}}$ rows). Positional concatenation would misalign every transaction immediately following the first non-eligible transaction (`PAYMENT`, `CASH_IN`, or `DEBIT`), assigning Anomaly scores of transaction $M$ to transaction $K$ where $M \neq K$.
2. **Index Reset Hazard:** Phase 04's `classify_batch` constructs a DataFrame with a fresh `RangeIndex(0, N)`. If Phase 05 output retains original row indices, an outer join or index concat results in NaN fragmentation or corrupt row pairings.

### 7.3 Relational Join Integrity and Completeness Validation (F07-R6, A03)
The relational join merges Phase 04 and Phase 05 outputs exclusively within the **Mode 1 Historical Integration Design**:

$$\text{IntegratedBatch}_{\text{Mode 1}} = \text{P4\_Historical\_Output} \underset{\text{row\_index}}{\bowtie_{\text{left}}} \text{P5\_Historical\_Output}$$

**Operational Join Boundary:** Mode 2 has **NO executable Phase 07 join**. The operational identity key (`transaction_id`) is a proposed future interface key only.

#### 7.3.1 Inadequacy of `validate="1:1"` Alone
A pandas left join with `validate="1:1"` alone **DOES NOT guarantee complete or correct integration**. While `validate="1:1"` verifies that merge keys are unique within each DataFrame, it fails to detect:
- Missing eligible transactions dropped by upstream failure.
- Ineligible transactions incorrectly routed to Branch B.
- Right-side orphan transactions not present in the input population.
- Partial batch truncation or dropped rows.

Therefore, `validate="1:1"` is retained strictly as an **additional defensive control** during execution, not as a substitute for explicit pre-join and post-join validation.

#### 7.3.2 Ten Mandatory Pre-Join and Join Integrity Checks (Mode 1 Scoped)
**Scope of Application:** The following ten validation checks apply strictly to **Mode 1 Historical Integration Design** using `row_index`. They must **NOT** be represented as executable operational requirements while operational Phase 05 scoring and operational join execution remain unauthorized:

1. **Input Identity Non-Nullity & Uniqueness:** All input transaction identities must be non-null and unique ($|U(\text{input\_ids})| == N_{\text{input}}$).
2. **Phase 04 Output Identity Non-Nullity & Uniqueness:** All Phase 04 output identities must be non-null and unique ($|U(\text{p4\_ids})| == N_{\text{p4}}$).
3. **Phase 05 Output Identity Non-Nullity & Uniqueness:** All Phase 05 output identities must be non-null and unique ($|U(\text{p5\_ids})| == N_{\text{p5}}$).
4. **Phase 04 Population Coverage:** Every Phase 04 output identity must belong to the input population, and Phase 04 output cardinality must equal input cardinality ($\text{p4\_ids} \subseteq \text{input\_ids}$ and $|\text{p4\_ids}| == N_{\text{input}}$). Positional correspondence requires empirical verification of upstream row-order preservation (F01 — probe design defined; verification pending).
5. **Phase 05 Population Membership:** Every Phase 05 output identity must belong to the input population ($\text{p5\_ids} \subseteq \text{input\_ids}$).
6. **Eligible Transaction Coverage:** Every eligible input transaction (`TRANSFER` and `CASH_OUT`) must have an expected Phase 05 outcome in Branch B outputs ($|\text{p5\_ids}| == N_{\text{elig}}$).
7. **Noneligible Channel State Assignment:** Every noneligible input transaction (`PAYMENT`, `CASH_IN`, `DEBIT`) must receive an explicit `NOT_APPLICABLE` anomaly state sentinel.
8. **Missing Eligible Outcome Rejection:** An eligible input transaction with an unexpectedly missing Phase 05 outcome must immediately trigger a validation failure (`MissingSignalOutcomeError`).
9. **Unexpected / Orphan Identity Rejection (Anti-Join Validation):** Unexpected right-side / orphan identities in Phase 04 or Phase 05 outputs (identities not present in the input population) must be detected using an explicit anti-join or set-difference assertion ($\text{output\_ids} \setminus \text{input\_ids} == \emptyset$). Any detected orphan record must cause immediate validation failure (`OrphanIdentityError`).
10. **Final Cardinality & Bijective Preservation:** The final integrated output must preserve input cardinality ($N_{\text{integrated}} == N_{\text{input}}$) and contain exactly one integrated record per input identity.

#### 7.3.3 Fail-Closed Failure Behavior
If any check fails in Mode 1 (Phase 04 error, duplicate identity, missing identity, orphan record, missing eligible outcome, or cardinality discrepancy), the pipeline must **fail closed**:
- Raise an explicit typed exception (e.g., `Phase04InferenceError`, `JoinIntegrityError`, `CardinalityMismatchError`).
- Halt batch processing immediately.
- Never silently impute missing records, drop unaligned transactions, or emit a partially trusted or corrupted integrated output.
- *Status:* **DESIGN CONTROLS DEFINED; SOURCE CODE IMPLEMENTATION NOT AUTHORIZED**.

---

## 8. Proposed Integrated Signal Schema

### 8.1 Data Structure Separation: Historical `IntegratedSignalRecord` vs. Separate Operational Identity Contract (F07-R5, V143-B01, V143-M07)
The platform establishes a strict separation between Gate 7.2 Approval Object A (historical integration record) and Gate 7.2 Approval Object B (proposed operational identity contract), each governed by separate formal Project Owner decisions:
1. **Historical `IntegratedSignalRecord` Contract (Gate 7.2 Approval Object A — APPROVED):** Formally approved by the Project Owner on 2026-11-17. Architecture and schema defined strictly for **Mode 1 Historical Integration Design only**, using historical `row_index: int` exclusively and containing **no `transaction_id` field**. Approval does NOT authorize execution or implementation (Gate 7.3 remains NOT AUTHORIZED).
2. **Proposed Operational Stable Identity Contract (Gate 7.2 Approval Object B — APPROVED WITH LIMITATIONS):** Formally approved with explicit limitations by the Project Owner on 2026-11-17 (`approve_limited`). Separate **Mode 2 design-only** interface contract specifying `transaction_id: str` only. It is **NOT** an integrated prediction/anomaly output record schema, contains no `row_index` field, and has zero schema dependency on `IntegratedSignalRecord`. Historical and operational identities are **NOT interchangeable**. Approval is strictly limited to the design-level operational identity contract and does NOT authorize operational Phase 04 execution, operational Phase 05 scoring, operational signal integration, operational relational joins, operational state synthesis, operational `IntegratedSignalRecord` schema/construction/emission, operational population/window policy, or any production-serving readiness claim.
3. **Operational `IntegratedSignalRecord`:** **DOES NOT EXIST AS AN APPROVED OR DEFINED SCHEMA.** Operational record construction and emission remain unapproved and strictly prohibited under Mode 2.

**Operational Emission Restriction Invariant:** **No operational `IntegratedSignalRecord` may be defined, constructed, or emitted until the operational Phase 05 population/window policy and the corresponding Phase 07 integration execution contract receive separate explicit approval.**

#### 8.1.1 Historical `IntegratedSignalRecord` Schema (Mode 1 Only — Gate 7.2 Approval Object A — APPROVED)

```python
# ======================================================================================
# RATIFIED SCHEMA DESIGN — IMPLEMENTATION NOT AUTHORIZED (GATE 7.3 REQUIRED)
# Gate 7.2 Approval Object A (APPROVED) — Strictly Mode 1 Historical Integration Design Only
# Note: Historical IntegratedSignalRecord uses ONLY historical row_index identity.
# Contains NO operational transaction_id field. Historical and operational schemas are separate.
# Operational IntegratedSignalRecord construction or emission under Mode 2 is STRICTLY PROHIBITED.
# ======================================================================================
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class IntegratedSignalRecord:
    # 1. Historical Identity Field (Section 7.1.1 — Mode 1 Only)
    row_index: int                 # Historical Evaluation Mode (non-null ordinal >= 0); NO transaction_id

    # 2. Phase 04 Supervised Signal Fields (Mode 1 Historical Integration; Strictly Mandatory)
    risk_score: float
    risk_score_100: int
    risk_level: str
    decision: str
    is_fraud_flagged: int
    p4_model_version: Optional[str]
    p4_status: str                 # Strictly "SUCCESS" in all emitted Mode 1 records (fail-closed on failure)

    # 3. Phase 05 Anomaly Signal Fields (Mode 1 Historical Integration; Unchanged Semantics)
    channel: str
    anomaly_status: str
    anomaly_score: Optional[float]
    is_anomaly_flagged: Optional[bool]
    alert_budget_selected: bool
    reason_code: Optional[str]
    p5_schema_version: str
    p5_detector_version: Optional[str] # Configuration release version, NOT fitted artifact ID (F10)

    # 4. Integration Metadata Fields
    schema_version: str            # Integrated signal contract schema version ("1.0.0")
    integration_timestamp: str
    identity_validation_status: str # Strictly "PASSED" in all emitted Mode 1 records
    integration_status: str
```

#### 8.1.2 Separate Proposed Operational Stable Identity Contract (Mode 2 Design Only — Gate 7.2 Approval Object B — APPROVED WITH LIMITATIONS)
- **Formal Approval Status:** `APPROVED WITH LIMITATIONS` (`approve_limited`, Decision Date: 2026-11-17).
- **Approved Scope:** Standalone design-only operational identity boundary (`Incoming Transaction → Proposed Stable Identity Contract`). Not an operational `IntegratedSignalRecord` schema.
- **Required Field:** `transaction_id: str` (strictly non-null, non-empty, immutable, unique string assigned once at ingestion boundary; see Section 8.2.2).
- **Prohibited Contents & Explicit Limitations:** Excludes `row_index`, transient internal ordinals, Phase 04 prediction fields, and Phase 05 anomaly fields. Approval of Gate 7.2 Approval Object A does not approve Object B, and limited approval of Object B does NOT authorize operational Phase 04 execution, operational Phase 05 scoring, operational signal integration, operational relational joins, operational state synthesis, operational `IntegratedSignalRecord` schema definition or record emission, operational population/window policy, or production-serving readiness claims.

### 8.2 Comprehensive Data Field Dictionaries (A02, F07-R5, V143-B01)

#### 8.2.1 Historical `IntegratedSignalRecord` Field Dictionary (Mode 1 Historical Design Only — Gate 7.2 Approval Object A — APPROVED)

| Group | Field Name | Data Type | Nullable | Allowed Values / Ranges | Upstream Source | Semantic Definition & Validation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **ID** | `row_index` | `int` | **No** | Non-negative integer $\ge 0$ | Ingestion / CSV | Authoritative historical evaluation ordinal (Mode 1 Design Only). Non-null, unique across evaluation population. Historical `IntegratedSignalRecord` has no `transaction_id` field; historical and operational identities are not interchangeable. |
| **P4** | `risk_score` | `float` | **No** | $[0.0, 1.0]$ | Phase 04 `risk_score` | Existing Phase 04 model probability-score interface (Mode 1). Preserved verbatim. Calibrated posterior reliability has not been demonstrated. |
| **P4** | `risk_score_100` | `int` | **No** | $[0, 100]$ | Phase 04 `risk_score_100` | Integer scaled risk score supplied by Phase 04 (Mode 1). Preserved as supplied; must NOT be independently recomputed or reinterpreted. |
| **P4** | `risk_level` | `str` | **No** | `{"LOW", "MEDIUM", "HIGH"}` | Phase 04 `risk_level` | Categorical risk band based on Phase 04 threshold policy (Mode 1). Preserved verbatim; not overwritten. |
| **P4** | `decision` | `str` | **No** | `{"APPROVE", "MONITOR", "MANUAL_INVESTIGATION"}` | Phase 04 `decision` | Phase 04 standalone recommendation (Mode 1). Preserved verbatim; not overwritten. |
| **P4** | `is_fraud_flagged` | `int` | **No** | $\{0, 1\}$ | Phase 04 `is_fraud_flagged` | Binary flag: 1 if `risk_score` $\ge 0.9771$, else 0 (Mode 1). Preserved verbatim; not overwritten. |
| **P4** | `p4_model_version` | `str` | Yes | `"1.0.0"` / `None` | Phase 04 Metadata | Model artifact version from `model_metadata.json`. Upstream output does not expose this field; retrieval mechanism is TO BE DEFINED (adapter injection). |
| **P4** | `p4_status` | `str` | **No** | `{"SUCCESS"}` | Phase 04 Adapter | Historical integration execution status of Phase 04 in Mode 1. Strictly `"SUCCESS"` in all emitted Mode 1 records; any failure in Phase 04 aborts batch emission entirely (fail-closed). Does NOT represent current operational inference status (A02). |
| **P5** | `channel` | `str` | **No** | `{"TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"}` | Ingestion / `type` | Transaction channel. Preserved for downstream routing and state validation. |
| **P5** | `anomaly_status` | `str` | **No** | `{"SCORED", "NOT_APPLICABLE", "DEGRADED_UNSCORABLE"}` | Phase 05 `anomaly_status` + Adapter | Primary anomaly state discriminator (see Section 9). Authoritative Phase 05 signal in Mode 1 declared complete population evaluation. |
| **P5** | `anomaly_score` | `float` | Yes | Finite float $(-\infty, \infty)$ | Phase 05 `anomaly_score` | Outlier severity score $-\text{score_samples}(x)$ in Mode 1. Continuous float; strictly NOT a probability. Null if not SCORED. Operational scoring is NOT AUTHORIZED. |
| **P5** | `is_anomaly_flagged`| `bool` | Yes | `{True, False}` | Phase 05 `is_anomaly_flagged` | Budget selection indicator under Mode 1 declared complete evaluation population. Null otherwise. Operational flagged/unflagged statuses NOT AUTHORIZED. |
| **P5** | `alert_budget_selected`| `bool` | **No** | `{True, False}` | Phase 05 `alert_budget_selected` | True if selected in top $K = \lfloor 0.0100 \times N_S \rfloor$ in Mode 1 historical declared complete scoring population; False if unselected/degraded/ineligible (F07). Operational alert selection NOT AUTHORIZED. |
| **P5** | `reason_code` | `str` | Yes | Machine-readable string | Phase 05 `reason_code` + Adapter | Reason code for degradation or ineligibility in Mode 1 (e.g., `"UNSUPPORTED_CHANNEL"`, `"ALL_ANOMALY_FEATURES_INACTIVE"`, `"SEVERE_NON_FINITE_INPUT"`). Null for SCORED. |
| **P5** | `p5_schema_version`| `str` | **No** | `"1.0.0"` | Phase 05 Schema | Schema version of Phase 05 output contract (`CURRENT_SCHEMA_VERSION`). `[REPORTED IN BASELINE SOURCE INSPECTION]` |
| **P5** | `p5_detector_version`| `str` | Yes | `"1.0.0"` / `None` | Phase 05 Config | Configuration release version from `anomaly_detection.yaml#L18`. Identifies config release version, NOT a fitted artifact ID or runtime instance ID (F10). Retrieval mechanism is TO BE DEFINED (adapter injection). |
| **Meta**| `schema_version` | `str` | **No** | `"1.0.0"` | Phase 07 Integration | Schema version of the Mode 1 historical integrated signal contract. |
| **Meta**| `integration_timestamp` | `str` | **No** | ISO 8601 UTC timestamp | Phase 07 Integration | System timestamp at time of Mode 1 signal integration. |
| **Meta**| `identity_validation_status`| `str` | **No** | `{"PASSED"}` | Phase 07 Join Layer | Single canonical successful status (F06). Strictly `"PASSED"` in all emitted Mode 1 records; confirms all 10 pre-join and join checks succeeded in Mode 1. Any check failure triggers fail-closed abort. |
| **Meta**| `integration_status`| `str` | **No** | `{"INTEGRATED_SCORED", "INTEGRATED_INELIGIBLE", "INTEGRATED_DEGRADED"}` | Phase 07 Join Layer | Integration-layer completeness status in Mode 1 (see Section 8.4). |

#### 8.2.2 Proposed Operational Stable Identity Contract Field Dictionary (Mode 2 Design Only — Gate 7.2 Approval Object B — APPROVED WITH LIMITATIONS)

| Contract Element | Field Name | Data Type | Nullable | Allowed Values / Ranges | Origin | Semantic Definition & Governance Boundary |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Operational ID** | `transaction_id` | `str` | **No** | Non-empty unique string (e.g., UUIDv4 / GUID) | Ingestion Boundary | Proposed operational stable transaction identifier (Mode 2 Design Only). Assigned once at ingestion boundary; immutable across retries. Separate from historical `IntegratedSignalRecord`; excludes `row_index` and transient ordinals. Does NOT define an operational integrated record schema and does NOT authorize operational scoring or emission. |

### 8.3 Version and Provenance Metadata Architecture (F04, F10)
To eliminate ambiguity between configuration releases, fitted artifact identities, runtime instances, and contract versions, provenance concepts are strictly separated across four distinct operational layers:

1. **Detector Configuration Release Provenance (`p5_detector_version`):**
   - Identifies the Phase 05 detector configuration/release specification (`"1.0.0"` in `configs/anomaly_detection.yaml#L18`).
   - Represents the declared hyperparameter specification and channel rules.
   - Does **NOT** identify a specific fitted detector artifact on disk, a serialized model file, or an in-memory runtime instance.
2. **Fitted Detector Artifact Identity (`p5_artifact_id`):**
   - Identifies a specific persisted, serialized fitted model artifact bundle on disk.
   - **Status: UNKNOWN / NOT AVAILABLE**. Phase 05 has no persistent artifact serialization module (`src/anomaly/artifacts.py` does not exist).
3. **In-Memory Detector Instance Identity (`p5_instance_id`):**
   - Identifies a specific transient, in-memory initialized detector instance at runtime.
   - **Status: UNKNOWN / TO BE DEFINED**. Generation, assignment, and tracking of runtime memory instance IDs are not currently implemented.
4. **Integration Contract & Implementation Provenance:**
   - Contract schema version (`schema_version = "1.0.0"`) resides at transaction level.
   - Implementation build version (`integration_impl_version`) resides at batch/manifest level.

| Provenance Concept | Field Name | Classification Scope | Schema Location | Authoritative Source | Present in Upstream Output? | Retrieval Mechanism Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **1. Phase 04 Model Artifact Version** | `p4_model_version` | Transaction-Level | `IntegratedSignalRecord` (`Optional[str]`) | `models/risk_model_v1/model_metadata.json` | **NO** | `TO BE DEFINED` (Adapter injection from metadata) |
| **2. Phase 05 Detector Configuration Version** | `p5_detector_version` | Transaction-Level | `IntegratedSignalRecord` (`Optional[str]`) | `configs/anomaly_detection.yaml#L18` | **NO** | `TO BE DEFINED` (Adapter injection from config; represents config release version, NOT fitted artifact ID) |
| **3. Phase 05 Fitted Artifact Identity** | `p5_artifact_id` | N/A (Non-Existent) | **EXCLUDED** from `IntegratedSignalRecord` | Phase 05 filesystem | **NO** | `UNKNOWN / NOT AVAILABLE` (No serialization contract exists) |
| **4. Phase 05 In-Memory Instance Identity** | `p5_instance_id` | Runtime Instance | **EXCLUDED** from `IntegratedSignalRecord` | Runtime Memory | **NO** | `UNKNOWN / TO BE DEFINED` (No instance ID tracking implemented) |
| **5. Phase 04 Upstream Schema Version** | `p4_schema_version` | N/A (Non-Existent) | **EXCLUDED** from `IntegratedSignalRecord` | Phase 04 threshold DataFrame | **NO** | `UNKNOWN / NONE` (Upstream schema version not defined) |
| **6. Phase 05 Upstream Schema Version** | `p5_schema_version` | Transaction-Level | `IntegratedSignalRecord` (`str`) | `src/anomaly/schema.py` | **YES** | `REPORTED IN BASELINE SOURCE INSPECTION` (Direct read from `AnomalyOutputRow`) |
| **7. Phase 07 Integrated Contract Version** | `schema_version` | Transaction-Level | `IntegratedSignalRecord` (`str`) | Phase 07 specification | N/A | `DESIGN DEFINED` (Proposed contract: `"1.0.0"`) |
| **8. Phase 07 Implementation Version** | `integration_impl_version` | **Batch / Manifest-Level** | **EXCLUDED** from `IntegratedSignalRecord` | Phase 07 package / build metadata | N/A | `TO BE DEFINED` (Pipeline execution manifest metadata) |

#### 8.3.1 Downstream Provenance Resolution & Phase 08 Hand-Off Limitations (F04, F10)
Downstream consumers such as Phase 08 (Explainable AI) require model and signal references for explanation workflows. Downstream resolution must distinguish between configuration resolution, artifact resolution, and explanation modes:

1. **Phase 04 Supervised Model Artifact Resolution:**
   - *Tier 1 (Direct Record Resolution):* If `p4_model_version` is populated in `IntegratedSignalRecord`, Phase 08 consumes it directly.
   - *Tier 2 (Batch Manifest Fallback):* If `p4_model_version` is `None`, Phase 08 resolves the version from the **Batch Execution Manifest Metadata** associated with the pipeline run.
   - *Tier 3 (Fail-Closed Rejection):* If unresolved, Phase 08 must fail closed and halt (`UnresolvedModelVersionError`).
2. **Phase 05 Anomaly Detector Provenance & Explainability Limitations (F10):**
   - **Configuration Resolution Only:** `p5_detector_version` resolves or identifies the applicable Phase 05 configuration release (`configs/anomaly_detection.yaml#L18`). It does **NOT** identify or retrieve a fitted detector artifact or instance.
   - **Exact Fitted-Detector Explanation NOT CURRENTLY EXECUTABLE:** Because the current documented architecture does not establish persistent detector artifact serialization, instance tracking, or artifact retrieval, exact fitted-detector explanation and reproduction are **NOT CURRENTLY EXECUTABLE** based on the documented system.
   - **Fail-Closed Resolution Behavior:** If Phase 08 requires the exact fitted Phase 05 detector object (e.g. for tree-based path traversal) and its identity or artifact cannot be resolved:
     - Phase 08 must **fail closed**.
     - Phase 08 must NOT silently substitute another detector or reference fit.
     - Phase 08 must NOT infer the fitted detector from `p5_detector_version`.
     - Phase 08 must NOT claim exact artifact reproducibility.
     - Phase 08 must surface an explicit unresolved fitted-detector identity error: proposed contract name `UnresolvedFittedDetectorIdentityError` (explicitly labeled **PROPOSED CONTRACT; IMPLEMENTATION PENDING**).
3. **Alternative Signal / Feature-Based Explanation Pathway (Proposed Future Design):**
   - If a Phase 08 explanation workflow does NOT require the original fitted detector object and can operate from preserved anomaly signals (`anomaly_score`, `anomaly_status`), raw feature vectors, and documented feature-level context:
     - This pathway is a **proposed future design**, not a validated existing XAI capability.
     - It is explicitly scoped to **signal/feature-level explanations** (e.g., empirical percentile positioning, feature deviation analysis, or surrogate attribution).
     - It does **NOT** retrieve or reproduce the exact fitted detector.
     - Preserves the architectural distinction between explaining an observed signal versus explaining the internal mechanics of the original fitted model.
     - Any limitations of this approach must be documented honestly.
     - This alternative is an architecture boundary option; Phase 07 does NOT pre-select or implement downstream explanation methods.
4. *Model Registry Governance Status:* A centralized Model Registry is a **PROPOSED DESIGN PATTERN; IMPLEMENTATION PENDING**. The specification does NOT claim an operational Model Registry or automated version resolution capability exists at present.

### 8.4 `integration_status` Semantics and Taxonomy
The `integration_status` field tracks the **batch integration completeness of the multi-model signal join process in Mode 1 (Historical Integration Design)**. Because Phase 04 is mandatory in Mode 1 (any Phase 04 failure aborts the batch before emission), all emitted records have `p4_status = "SUCCESS"`. The `integration_status` values are defined independently from Phase 05's `anomaly_status` and strictly avoid labeling expected channel ineligibility as an integration defect:

1. `INTEGRATED_SCORED`:
   - Phase 04 succeeded (`p4_status = "SUCCESS"`), and Phase 05 was applicable, executed successfully, and produced an active anomaly score under Mode 1 historical evaluation population partition upon authorization.
   - Corresponds to Phase 05 `anomaly_status = "SCORED"` (`SCORED_FLAGGED` or `SCORED_UNFLAGGED` in historical evaluation). Operational scoring and operational record emission remain strictly unauthorized.
2. `INTEGRATED_INELIGIBLE`:
   - Phase 04 succeeded (`p4_status = "SUCCESS"`); Phase 05 was not applicable due to channel eligibility policy (`PAYMENT`, `CASH_IN`, `DEBIT`).
   - Corresponds to Phase 05 `anomaly_status = "NOT_APPLICABLE"`.
   - **Critical Semantic Rule:** This is **fully successful, expected integration behavior under platform policy**, NOT an integration failure, partial defect, or data error.
3. `INTEGRATED_DEGRADED`:
   - Phase 04 succeeded (`p4_status = "SUCCESS"`); Phase 05 was eligible (`TRANSFER` or `CASH_OUT`) but encountered documented degraded conditions (e.g., all anomaly features inactive or severe non-finite inputs).
   - Corresponds to Phase 05 `anomaly_status = "DEGRADED_UNSCORABLE"`.
   - Represents an eligible-row scoring limitation within Mode 1 historical integration.

*Note on Integration Failures:* Any Phase 04 failure, unmatched keys, orphan records, missing expected outcomes, or cardinality violations trigger immediate fail-closed exceptions (Section 7.3.3) and do not emit a record with a "failed" status.

---

## 9. Channel and Anomaly State Semantics

### 9.1 State Hierarchy and Specification (A04, V143-B05)
Phase 07 establishes strict invariant rules across four distinct transaction-level anomaly states and one run-level summary state. In all four Mode 1 transaction states, Phase 04 output is valid within the Mode 1 historical integration design (`p4_status = "SUCCESS"`). This Mode 1 validity does not imply production-serving approval or operational readiness.

**Mode 1 Historical Scope & Operational Prohibition:** Transaction States A (`SCORED_UNFLAGGED`), B (`SCORED_FLAGGED`), C (`NOT_APPLICABLE`), and D (`DEGRADED_UNSCORABLE`) are strictly scoped to **Mode 1 Historical Integration Design**. They do **NOT** authorize Mode 2 operational execution. Operational transactions cannot receive authorized Phase 05 flagged or unflagged anomaly statuses without a separately approved operational population/window policy. The platform must NOT represent unavailable operational Phase 05 results as `NOT_APPLICABLE`, `DEGRADED_UNSCORABLE`, `NOT_EVALUABLE`, or any other existing state without an approved semantic basis.

```
                      Transaction Arrives (Mode 1 Design)
                                │
                Is channel TRANSFER or CASH_OUT?
                     /                \
                   YES                 NO
                   /                     \
       Are anomaly features active?       TRANSACTION STATE C: NOT_APPLICABLE
          /          \                    - p4_status = "SUCCESS" (MODE 1 VALID)
        YES           NO                  - anomaly_status = "NOT_APPLICABLE"
        /               \                 - anomaly_score = None
   Score sample     TRANSACTION STATE D:  - is_anomaly_flagged = None
   (Declared Pop)   DEGRADED_UNSCORABLE   - alert_budget_selected = False
        │           - p4_status = SUCCESS - reason_code = "UNSUPPORTED_CHANNEL"
        │           - anomaly_status =    - integration_status = "INTEGRATED_INELIGIBLE"
        │             "DEGRADED_UNSCORABLE"- Phase 04 Output: VALID IN MODE 1 DESIGN
        │           - anomaly_score = None
        ▼           - reason_code populated
   Is score in top  - integration_status = "INTEGRATED_DEGRADED"
   1.00% budget
   (K = floor(0.0100 * N_S))?
      /         \
    YES          NO
    /             \
TRANSACTION     TRANSACTION
STATE B:        STATE A:
SCORED_FLAGGED  SCORED_UNFLAGGED
- p4_status =   - p4_status =
  "SUCCESS"       "SUCCESS"
- is_flagged    - is_flagged
  = True          = False
- integration_  - integration_
  status =        status =
  "INTEGRATED_    "INTEGRATED_
  SCORED"         SCORED"
(Mode 1 Pop)    (Mode 1 Pop)
```

### 9.2 Four Transaction-Level Anomaly States (Mode 1 Scoped)

#### State A: `SCORED_UNFLAGGED`
- **Trigger:** Channel is `TRANSFER` or `CASH_OUT`; detector is fitted; features active; raw score calculated in a declared complete historical evaluation population (Mode 1); transaction score is **below** the 1.00% alert budget cutoff ($K = \lfloor 0.0100 \times N_S \rfloor$) for that population scope.
- **Operational Serving Restriction:** Emitting this status for operational transactions is **NOT AUTHORIZED** without an approved operational population/window policy and execution contract.
- **Required Invariants:**
  - `p4_status = "SUCCESS"` (strictly mandatory in Mode 1)
  - `anomaly_status = "SCORED"`
  - `anomaly_score`: Finite float (e.g. `0.421509`)
  - `is_anomaly_flagged = False`
  - `alert_budget_selected = False`
  - `reason_code = None`
  - `integration_status = "INTEGRATED_SCORED"`
- **Integration Behavior:** Fully populated side-by-side record passed downstream in Mode 1.

#### State B: `SCORED_FLAGGED`
- **Trigger:** Channel is `TRANSFER` or `CASH_OUT`; detector is fitted; features active; raw score calculated in a declared complete historical evaluation population (Mode 1); transaction score ranks within the top $K = \lfloor 0.0100 \times N_S \rfloor$ transactions for that population scope.
- **Operational Serving Restriction:** Emitting this status for operational transactions is **NOT AUTHORIZED** without an approved operational population/window policy and execution contract.
- **Required Invariants:**
  - `p4_status = "SUCCESS"` (strictly mandatory in Mode 1)
  - `anomaly_status = "SCORED"`
  - `anomaly_score`: Finite float (e.g. `0.789124`)
  - `is_anomaly_flagged = True`
  - `alert_budget_selected = True`
  - `reason_code = None`
  - `integration_status = "INTEGRATED_SCORED"`
- **Integration Behavior:** Fully populated side-by-side record passed downstream in Mode 1.

#### State C: `NOT_APPLICABLE`
- **Trigger:** Transaction channel belongs to the non-eligible set (`PAYMENT`, `CASH_IN`, `DEBIT`).
- **Required Invariants:**
  - `p4_status = "SUCCESS"` (strictly mandatory in Mode 1)
  - `anomaly_status = "NOT_APPLICABLE"`
  - `anomaly_score = None`
  - `is_anomaly_flagged = None`
  - `alert_budget_selected = False`
  - `reason_code = "UNSUPPORTED_CHANNEL"`
  - `integration_status = "INTEGRATED_INELIGIBLE"`
- **Integration Behavior:**
  - **CRITICAL INVARIANT:** Under no circumstances shall `NOT_APPLICABLE` be converted to an anomaly score of `0.0`, `-inf`, or interpreted as "normal behavior". The anomaly score is strictly `None`.
  - **NO FAILURE CONFLATION:** This state is **expected behavior under platform scope**, NOT an integration or scoring failure.
  - Phase 04 output remains valid within the Mode 1 historical integration design (`p4_status = "SUCCESS"`), without implying production-serving approval or operational readiness.
  - Does NOT authorize Mode 2 operational execution.

#### State D: `DEGRADED_UNSCORABLE` (F03)
- **Trigger:** Channel is `TRANSFER` or `CASH_OUT`; detector is fitted; but row cannot be scored due to documented Phase 05 row-level fallback conditions (e.g., all anomaly features inactive or severe non-finite inputs).
- **Required Invariants:**
  - `p4_status = "SUCCESS"` (strictly mandatory in Mode 1)
  - `anomaly_status = "DEGRADED_UNSCORABLE"`
  - `anomaly_score = None`
  - `is_anomaly_flagged = None`
  - `alert_budget_selected = False`
  - `reason_code`: Mandatory machine-readable string (e.g. `"ALL_ANOMALY_FEATURES_INACTIVE"`, `"SEVERE_NON_FINITE_INPUT"`, `"INSUFFICIENT_HISTORY"`).
  - `integration_status = "INTEGRATED_DEGRADED"`
- **Fail-Closed Initialization Distinction (F03, V143-M08):** An uninitialized detector is a detector initialization / historical runner readiness failure that aborts scoring with `RuntimeError` at the engine boundary. It is **NOT** a transaction-level degradation. Transaction-level `DEGRADED_UNSCORABLE` records must **never be fabricated** for an uninitialized detector.
- **Integration Behavior:** Anomaly score is strictly `None`. Must never be imputed or defaulted to zero. Phase 04 output remains valid within Mode 1 historical integration design. Record is passed downstream with degradation metadata. Excluded from the alert budget denominator $N_S$.

### 9.3 Population-Level Outcome: `NOT_EVALUABLE` (F07)
- **Trigger:** A declared evaluation population contains zero successfully scored eligible transactions ($N_S = 0$).
- **Strict Semantic Scope:** `NOT_EVALUABLE` is strictly a **run-level / batch-level summary outcome** (`BudgetResult.status`), **NOT a transaction-level anomaly state**. Individual rows within such a batch remain typed as `DEGRADED_UNSCORABLE` or `NOT_APPLICABLE`.
- **Integration Behavior:** If an entire population partition is `NOT_EVALUABLE`, the integration layer records this in the batch execution manifest. It does **NOT** introduce `NOT_EVALUABLE` into the transaction-level `IntegratedSignalRecord` schema.

---

## 10. Phase 05 Detector Lifecycle & Runtime Initialization

### 10.1 In-Memory Fit-Before-Score Invariant
Phase 05 does not possess a persistent serialized model artifact on disk (`src/anomaly/artifacts.py` was deferred in Phase 05). The `AnomalyDetectionEngine` enforces a strict runtime invariant:

```python
if not self.is_fitted:
    raise RuntimeError("AnomalyDetectionEngine must be fitted on reference data before scoring.")
```

### 10.2 Reference Population Requirements (Controlled Historical Evaluation Scope)
When initializing Phase 05 for controlled historical evaluation:
1. **Temporal Boundaries:** Reference data must be strictly drawn from simulation steps $1 \le \text{step} \le 400$ (`train_max_step = 400`).
2. **Population Cardinality:**
   - Full reference population: $5,787,030$ transactions.
   - Eligible reference population (`TRANSFER` and `CASH_OUT`): $2,529,536$ transactions.
3. **Temporal Partition Integrity:** Steps $> 400$ (Validation steps 401–550 and Test steps 551–743) are strictly prohibited from reference fitting.
4. **Scope Limitation:** Phase 05 initialization is currently defined and evaluated **only for controlled historical evaluation contexts**. Production serving initialization and operational execution remain unapproved and unauthorized.

### 10.3 Phase 05 Detector Initialization & Lifecycle Architecture (F03, F09, V143-M08)
**Runner Readiness vs. Service Readiness Distinction (V143-M08):** Mode 1 in-memory fit-before-score requirements specify **historical evaluation runner readiness** (preconditions for running controlled offline evaluation batches). They are strictly distinct from **future operational service readiness** and do **NOT** establish production service readiness, service startup readiness, operational recovery, or streaming readiness. This lifecycle is categorized across three distinct operational domains:

#### 10.3.1 Domain A: DESIGN-DEFINED (Mode 1 Historical Evaluation Runner Readiness vs. Future Service Proposals)
- **Fit-Before-Score Invariant (Historical Runner):** `AnomalyDetectionEngine` must be fitted on reference data before scoring (`is_fitted == True`).
- **Reference Population Boundaries (Historical Evaluation):** Reference data must be strictly drawn from simulation steps $1 \le \text{step} \le 400$ ($5,787,030$ total records; $2,529,536$ eligible `TRANSFER` and `CASH_OUT` records).
- **Fail-Closed Engine / Runner Guard (F03):** An uninitialized or unfitted engine raises `RuntimeError` at the `AnomalyDetectionEngine.score()` boundary. In a future operational service architecture (not implemented or authorized here), this invariant would dictate failing startup readiness probes rather than serving uninitialized.
- **Zero Fallback Fabrication:** No default, dummy, or fallback detector may be fabricated, and no silent uninitialized scoring is permitted. State D (`DEGRADED_UNSCORABLE`) is never emitted for an uninitialized detector.
- **Lifecycle Qualification (F09, V143-M08):** While in-memory detector fitting on simulation steps 1–400 satisfies the logical fit-before-score requirement for **Mode 1 historical evaluation runner readiness**, it does **NOT** establish:
  1. Production service readiness or service startup readiness.
  2. Persistent artifact availability.
  3. Cross-process reproducibility.
  4. Operational recovery.
  5. Operational scoring authorization.
  6. Streaming readiness.

#### 10.3.2 Domain B: IMPLEMENTATION PENDING (Future Operational Service Infrastructure)
The following future operational service orchestration components are unimplemented and remain outside Phase 07 authorization:
- Production service / container startup orchestration and Lifecycle Manager implementation.
- Automated loading of the 2.5M-record reference dataset partition into memory.
- Reference-data schema and temporal integrity validation.
- In-memory `.fit(reference_df)` execution routine within an evaluation runner or service bootstrap.
- Operational failure recovery, retry mechanisms, and alerting.
- Resource management and CPU core binding during fitting.
- Hot-reload / reinitialization lifecycle behavior.
- Future operational service readiness probe integration (`/healthz`, `/readyz`).

#### 10.3.3 Domain C: UNKNOWN / NOT VALIDATED (Runtime & Operational)
The following runtime operational properties are **EMPIRICALLY UNMEASURED and UNVALIDATED**:
- **Startup Latency:** The wall-clock time required to load and fit Isolation Forest on 2.5M reference records is empirically unmeasured. Previous informal estimates (30–60s) were unsupported and are formally retracted.
- **Peak Memory Footprint:** Peak RAM required during reference loading and tree fitting is unknown.
- **CPU Consumption:** Multi-core utilization during fitting is unknown.
- **Throughput & Concurrency:** Concurrency limits and inference latency under multi-threaded requests are unknown.
- **Operational Reliability:** Recovery under out-of-memory or fitting timeout conditions is unvalidated.
- **Production Streaming Readiness:** Operational viability of fitting 2.5M records at container launch in production Kubernetes/cloud environments is unproven.

#### 10.3.4 Pre-Fitted Artifact Alternative (Future Design Option)
If future operational benchmarking reveals that in-memory reference fitting at startup imposes prohibitive latency or memory overhead, serializing a pre-fitted detector artifact (`src/anomaly/artifacts.py`) represents a viable alternative. However, this is a **potential future alternative requiring a separate architecture design and validation decision**. The current Option A specification does NOT assume or silently substitute a serialized artifact.

#### 10.3.5 Mandatory Future Operational Validation
Prior to any production deployment, the platform must execute an authorized operational validation measuring:
1. Reference population data integrity.
2. Container startup latency and peak memory.
3. Fit reproducibility and random seed determinism.
4. Scoring latency and correctness post-initialization.
5. Fail-closed behavior upon reference data corruption or fitting failure.

---

## 11. Temporal & Data-Leakage Controls

### 11.1 Prediction Point Invariant: Pre-Authorization Inline Evaluation (A05)
All signal integration operates strictly under the approved project prediction point:
$$\textbf{Pre-Authorization Inline Evaluation (Gate 3)}$$

Scoring occurs at the exact moment a transaction authorization request is received, prior to account balance mutation, ledger update, or settlement.

**Authorization Boundary Clarification (A05):** The Pre-Authorization Inline Evaluation prediction point describes the **business decision point and intended information-availability boundary** for platform architecture. It does **NOT** independently authorize production serving or operational Phase 05 scoring. Operational execution remains strictly unauthorized until an operational population/window policy and corresponding execution contract receive separate explicit Project Owner approval.

### 11.2 Historical Step Invariant
To prevent lookahead leakage in sequential and evaluation environments:
$$\text{historical\_step} < \text{current\_step}$$

- Same-step future transactions are excluded from behavioral histories.
- Reference population maximum step ($\text{step} \le 400$) is strictly lower than evaluation steps ($\text{step} \ge 401$).

### 11.3 Strictly Excluded Prohibited Fields
Input data to the signal integration layer must NOT contain any of the prohibited leakage fields defined in `src/features/policy.py`:
- `isFraud` (Ground-truth label)
- `isFlaggedFraud` (Post-event simulation flag)
- `newbalanceOrig` / `newbalanceDest` (Post-authorization balances)

Both Phase 04 (`RiskPredictor._prepare_dataframe`) and Phase 05 (`AnomalyPreprocessor.validate_inputs`) independently raise a `ValueError` if any prohibited field is detected. Phase 07 preserves and reinforces this enforcement.

---

## 12. Testing & Verification Strategy

The following comprehensive test suite structure is designed for future Phase 07 implementation. **No tests are executed during this specification phase.** Test plans explicitly reflect the distinction between Mode 1 (historical integration design) and Mode 2 (design-only operational identity contracts).

### 12.1 Identity & Join Integrity Test Plan (`test_identity_alignment.py`) (Mode 1 Integration vs. Separate Mode 2 Identity Contract)
- `test_mode1_historical_identity_invariants`: Asserts that in Mode 1 (Historical Integration Design), historical `row_index: int` is non-null, non-negative, and unique, no synthetic `transaction_id` is fabricated, and historical `IntegratedSignalRecord` contains `row_index` only (no `transaction_id` field). Asserts Mode 1 record generation only under verified full-dataset lineage upon separate execution authorization.
- `test_mode2_operational_identity_contract_invariants`: Validates strictly against the **separate proposed operational stable identity contract** (`transaction_id: str` non-null, non-empty, and unique), confirming historical `row_index` is absent and zero dependency on `IntegratedSignalRecord` exists.
- `test_operational_identity_contract_excludes_ordinals (F05)`: Validates the standalone proposed operational stable identity contract design in isolation, ensuring transient internal ordinals and historical `row_index` cannot appear in or overwrite the operational identity contract (no `IntegratedSignalRecord` inspection or construction).
- `test_input_identity_uniqueness_and_non_nullity`: Asserts that null, empty, or duplicate identities in Mode 1 input trigger `MissingIdentityError` or `DuplicateIdentityError`.
- `test_identity_preservation_across_mode1_adapters`: Asserts that historical `row_index` is preserved across Phase 04 and Phase 05 adapters strictly within Mode 1.
- `test_p4_adapter_cardinality_and_order_probe (F01, A09)`: Mode 1 adapter test design (probe design defined; implementation and execution verification remain pending under Gate 7.4). Uses distinct synthetic probe vectors to empirically test whether `RiskPredictor` preserves row ordering before reattaching historical `row_index`.
- `test_p4_mandatory_execution_fail_closed`: Asserts that any simulated Phase 04 inference error in Mode 1 aborts the batch, raising `Phase04InferenceError` with zero emitted records.
- `test_rejection_of_orphan_identities_anti_join`: Asserts that right-side orphan identities in Phase 04 or Phase 05 outputs trigger `OrphanIdentityError` in Mode 1.
- `test_rejection_of_missing_eligible_p5_outcomes`: Asserts that eligible transactions lacking a Phase 05 output trigger `MissingSignalOutcomeError` in Mode 1.
- `test_cardinality_bijective_preservation`: Asserts that output length strictly equals input length ($N_{\text{out}} == N_{\text{input}}$) and exactly one historical record exists per `row_index` in Mode 1.
- `test_ordering_invariance`: Asserts that reordering input rows does not alter the output mapping of historical `row_index` to signals in Mode 1.

### 12.2 Channel Eligibility Test Plan (`test_channel_semantics.py`)
- `test_eligible_channel_transfer_scored_mode1`: Asserts `TRANSFER` produces `anomaly_status="SCORED"`, `p4_status="SUCCESS"`, and `integration_status="INTEGRATED_SCORED"` in Mode 1.
- `test_eligible_channel_cash_out_scored_mode1`: Asserts `CASH_OUT` produces `anomaly_status="SCORED"`, `p4_status="SUCCESS"`, and `integration_status="INTEGRATED_SCORED"` in Mode 1.
- `test_ineligible_channels_not_applicable`: Asserts `PAYMENT`, `CASH_IN`, and `DEBIT` produce `anomaly_status="NOT_APPLICABLE"`, `anomaly_score=None`, `reason_code="UNSUPPORTED_CHANNEL"`, `p4_status="SUCCESS"`, and `integration_status="INTEGRATED_INELIGIBLE"` in Mode 1.
- `test_unexpected_channel_rejection`: Asserts that unmapped channel strings trigger validation failure.

### 12.3 Anomaly State Handling Test Plan (`test_state_semantics.py`)
- `test_state_a_scored_unflagged_invariants`: Asserts valid score, `is_flagged=False`, `reason_code=None`, `p4_status="SUCCESS"`, `integration_status="INTEGRATED_SCORED"` in Mode 1 declared population evaluation.
- `test_state_b_scored_flagged_invariants`: Asserts valid score, `is_flagged=True`, `reason_code=None`, `p4_status="SUCCESS"`, `integration_status="INTEGRATED_SCORED"` in Mode 1 declared population evaluation.
- `test_state_c_not_applicable_invariants`: Asserts `score=None`, `is_flagged=None`, valid P4 signal, `p4_status="SUCCESS"`, `integration_status="INTEGRATED_INELIGIBLE"` in Mode 1.
- `test_state_d_degraded_unscorable_invariants`: Asserts `score=None`, `is_flagged=None`, non-null reason code (`ALL_ANOMALY_FEATURES_INACTIVE`), `p4_status="SUCCESS"`, `integration_status="INTEGRATED_DEGRADED"` in Mode 1.
- `test_unfitted_engine_readiness_failure (F03, V143-M08)`: Asserts that calling `score()` on an unfitted `AnomalyDetectionEngine` raises `RuntimeError` at the engine / historical runner boundary rather than emitting State D records.
- `test_population_not_evaluable_batch_outcome (F07)`: Asserts that a declared population with $N_S = 0$ scored rows produces batch-level `NOT_EVALUABLE` without corrupting row-level schemas in Mode 1.
- `test_alert_budget_denominator_finite_scored_only (F07)`: Asserts that degraded unscorable rows are strictly excluded from the budget capacity denominator $N_S$ in Mode 1.
- `test_p4_signal_availability_across_all_states`: Asserts Phase 04 `risk_score` and `decision` remain fully populated regardless of Phase 05 state in Mode 1.

### 12.4 Integration Contract Test Plan (`test_signal_contract.py`)
- `test_integrated_record_schema_conformance`: Validates all fields against `IntegratedSignalRecord` dataclass types in Mode 1.
- `test_immutability_of_upstream_outputs`: Asserts that `risk_score`, `risk_score_100`, `decision`, and `anomaly_score` exactly equal upstream model outputs without rounding or float drift.
- `test_zero_decision_fusion_invariant`: Asserts that no `fused_decision` or `fused_risk_score` exists in the output schema.
- `test_version_metadata_integrity`: Asserts that schema versions match expected constants, batch-level implementation version is excluded from per-record schemas, and unverified fields are not fabricated.
- `test_phase08_version_resolution_fallback (F04, F10)`: Asserts that Phase 08 resolves model versions via manifest fallback when record-level versions are `None`, and raises `UnresolvedModelVersionError` if unresolved.
- `test_phase08_fitted_detector_identity_fail_closed (F10)`: Asserts that if Phase 08 requires an exact fitted Phase 05 detector object and its identity cannot be resolved from `p5_detector_version` (which is configuration release version only), Phase 08 fails closed with proposed `UnresolvedFittedDetectorIdentityError`.

---

## 13. Feasibility Assessment

### 13.1 Feasibility Assessment Summary
To ensure rigorous engineering standards, logical design feasibility is strictly distinguished from empirically verified operational readiness:

| Evaluation Dimension | Feasibility Assessment | Evidence / Basis |
| :--- | :--- | :--- |
| **Logical Signal Integration** | **HIGH — DESIGN ASSESSMENT** | Deterministic relational merge pattern in Mode 1; standard Python/pandas data structures; clean separation of concerns. |
| **Identity Correctness** | **FEASIBLE IN DESIGN; IMPLEMENTATION VERIFICATION PENDING** | Separated identity contracts (`row_index` in Mode 1 historical `IntegratedSignalRecord` vs. separate `transaction_id` operational identity contract in Mode 2) are logically sound. Positional reattachment in Mode 1 Phase 04 adapter relies on an unverified order-preservation assumption (F01). |
| **Runtime Detector Lifecycle** | **FEASIBLE IN DESIGN; SERVICE READINESS NOT ESTABLISHED** | In-memory fit-before-score design satisfies historical evaluation runner preconditions for Mode 1, but does NOT establish production service readiness, service startup readiness, operational recovery, persistent artifacts, or streaming readiness (F09, V143-M08). |
| **Runtime Performance** | **UNKNOWN** | Unmeasured. Algorithmic complexity is theoretically $O(N)$, but empirical latency, throughput, and memory consumption are unverified. |
| **Production Streaming Readiness** | **UNKNOWN** | Unmeasured. Real-time streaming arrival, state synchronization, and retry behaviors are unverified. Operational scoring authorization is NOT ESTABLISHED; small-batch alert suppression ($K=0$ for $N_S<100$) and batch-composition sensitivity are unresolved limitations (F02, F07). |
| **Downstream Compatibility** | **PROPOSED; CONSUMER VALIDATION PENDING** | Historical integrated output compatibility (Mode 1) defined; proposed operational stable identity contract (Mode 2) defined separately in design; actual operational serving capability not established pending downstream phase approvals (F04, F10). |

### 13.2 Logical Signal Integration Feasibility: HIGH — DESIGN ASSESSMENT
Integrating two independent model outputs via a 1:1 relational join on transaction identity is a proven, deterministic software pattern. Both upstream models produce standard pandas/NumPy structures. 

*Algorithmic Note:* From a theoretical algorithmic standpoint, hash-based relational joins exhibit $O(N)$ computational complexity and $O(N)$ memory overhead. However, this theoretical observation is an algorithmic property, **not empirical evidence of production runtime performance**.

### 13.3 Identity Correctness Feasibility: FEASIBLE IN DESIGN; IMPLEMENTATION VERIFICATION PENDING (F01, F07-R7, A09, V143-B04)
While Phase 04's predictor preprocessing strips row indices, wrapping `RiskPredictor` in a **Mode 1 Phase 07 historical adapter** that caches input `row_index` and rebinds it is logically sound in design. Keeping the Mode 1 historical `IntegratedSignalRecord` (`row_index`) strictly separate from the proposed Mode 2 operational stable identity contract (`transaction_id`) avoids corrupting historical evaluation with fabricated UUIDs without introducing a `RiskPredictor` adapter or execution path into Mode 2.

*Crucial Verification Limitation (F07-R7, A09):* Cardinality equality alone ($N_{\text{out}} == N_{\text{in}}$) does not verify row correspondence. Positional reattachment rests on an **unverified design assumption of upstream row-order preservation**. The separate Mode 2 contract supports only future operational identity-contract design; it does not establish operational integration, production-serving readiness, runtime performance, or authorization to execute. Probe verification remains pending under Gate 7.4.

### 13.4 Runtime Detector Lifecycle Feasibility: FEASIBLE IN DESIGN; SERVICE READINESS NOT ESTABLISHED (F09, V143-M08)
Because Phase 05 requires fitting in-memory prior to scoring, Mode 1 historical evaluation runner initialization requires loading reference data from simulation steps 1–400. In-memory fitting satisfies the logical fit-before-score precondition for Mode 1 historical evaluation runner readiness.

*Qualification & Limits (F09, V143-M08):* Historical evaluation runner fit-before-score design does **NOT** establish production service readiness, service startup readiness, operational recovery, persistent artifact availability, cross-process reproducibility, operational scoring authorization, or streaming readiness. Previous estimates of cold-start latency (e.g. 30–60 seconds) were unsupported by empirical benchmarks in this environment and are **formally retracted**. Actual initialization latency, memory footprint during fitting on 2.5M reference records, and startup behavior are empirically unmeasured and therefore **UNKNOWN** pending authorized testing.

### 13.5 Runtime Performance & Production Streaming Readiness: UNKNOWN (F02, F07)
No throughput, latency, memory, reliability, or scalability benchmarks have been conducted for the integrated pipeline. Real-time streaming readiness, message broker integration, and retry handling under asynchronous execution have not been tested. 

*Operational Scoring Authorization Boundary:* Operational scoring on arbitrary incoming batches is **STRICTLY NOT AUTHORIZED**. Applying the frozen 1.00% budget to small streaming batches ($N_S < 100$) suppresses all alerts ($K = 0$). Furthermore, transient ordinal tie-breaking does not guarantee global determinism across micro-batches. Consequently, runtime performance and streaming readiness are formally classified as **UNKNOWN**.

### 13.6 Downstream Compatibility: PROPOSED; CONSUMER VALIDATION PENDING (F04, F07-R8, F10)
The specification establishes historical integrated output compatibility (Mode 1) for evaluation and proposed operational interface compatibility (Mode 2) for future design alignment. 

**Distinction of Compatibility Scopes (F07-R8):** The specification does **NOT** represent an actual operational serving capability. Downstream consumers (Phase 08 Explainable AI, Phase 09 Risk Scoring, and Phase 10 Decision Automation) **cannot currently receive operational integrated records**, as operational Phase 05 scoring and operational `IntegratedSignalRecord` emission are strictly unauthorized pending explicit Project Owner approvals. Downstream model version resolution is supported via record extraction or batch manifest fallback. Formal validation remains pending until downstream phase implementations consume the contract.

---

## 14. Risk Register

| Risk ID | Risk Description | Severity | Uncertainty | Impact | Mitigation Strategy | Owner / Decision Required | Status |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :---: |
| **R-07-01** | **Identity Misalignment:** Silent positional concat or unverified row-order causes wrong anomaly scores assigned to transactions. | **CRITICAL** | Low | Total data corruption; false fraud classifications. | Mandate 10-point pre-join checks in Mode 1; mandate empirical unit verification of Phase 04 row-order preservation using synthetic probe vectors; fail closed on discrepancy. | Lead Architect / Mandate join assertions & probe tests | **DESIGN CONTROL DEFINED; IMPLEMENTATION VERIFICATION PENDING** |
| **R-07-02** | **Evaluation Ordinal Mistaken for Production ID:** `row_index` assumed available in production streaming. | **HIGH** | Medium | Runtime crashes when streaming transactions lack row index. | Formally separate schemas: Mode 1 historical `IntegratedSignalRecord` (`row_index` only) vs. separate Mode 2 proposed operational identity contract (`transaction_id` only). Transient ordinals excluded from operational contract. Operational identity support does not authorize operational scoring. | Architecture / Schema definition | **DESIGN CONTROL DEFINED; IMPLEMENTATION VERIFICATION PENDING** |
| **R-07-03** | **Score Semantic Misinterpretation:** Downstream treats `anomaly_score` as a fraud probability. | **HIGH** | Low | Invalid probability blending; incorrect risk thresholds. | Formal schema documentation; explicit typing; education in ADR-07-001; Option A enforcement. | ML Governance / Enforce Option A | **MITIGATION PROPOSED** |
| **R-07-04** | **Ineligible Channel Corruption:** Non-eligible channel treated as "normal" (score = 0.0) or as failure. | **HIGH** | Low | Distorts downstream risk distribution; masks fraud; false alerts. | Mandate strict `None` nullability, `NOT_APPLICABLE` state sentinel, and `INTEGRATED_INELIGIBLE` status in Mode 1. | Platform Team / Schema contract | **DESIGN CONTROL DEFINED; IMPLEMENTATION VERIFICATION PENDING** |
| **R-07-05** | **Degraded Score Silent Imputation:** Degraded anomaly scores converted to mean or median. | **MEDIUM** | Low | Masks system failure; causes silent unmonitored decay. | Enforce `None` for score and populate mandatory machine-readable `reason_code` in Mode 1. Exclude from $N_S$ alert budget denominator. | Platform Team / Preprocessor policy | **DESIGN CONTROL DEFINED; IMPLEMENTATION VERIFICATION PENDING** |
| **R-07-06** | **Phase 04 Decision Overwrite / Failure Handling:** Pipeline attempts to overwrite Phase 04 or emit partial records on Phase 04 failure. | **CRITICAL** | Low | Violates Phase 04 champion governance; emits untrusted risk classifications. | Mandate Phase 04 as strictly mandatory in Mode 1; fail closed on any Phase 04 error; preserve Phase 04 outputs verbatim. | Project Owner / Scope enforcement | **GOVERNANCE CONTROL DEFINED** |
| **R-07-07** | **Operational Scoring & Alert Budget Authorization Absence:** Applying 1.00% budget to arbitrary operational batches produces alert suppression ($K=0$ for $N_S<100$) and batch-composition sensitivity. No operational scoring population or window policy is approved. | **HIGH** | Medium | Alerts suppressed in small batches; operational inconsistency. | Operational scoring and batch-local top-K selection are NOT AUTHORIZED; operational identity support is separated from scoring authorization; preserve declared historical complete-population scope; operational population/window policy is formally DEFERRED — GOVERNING PHASE / OWNER NOT YET ASSIGNED; document absence of approved operational scoring policy. Documenting mitigation does not eliminate operational risk. | Project Owner (Governing Phase / Owner Not Yet Assigned) | **POLICY BOUNDARY DEFINED; OPERATIONAL SCORING NOT AUTHORIZED** |
| **R-07-08** | **Uninitialized Detector at Runtime:** Phase 05 called before reference fitting. | **HIGH** | Low | Evaluation failure or uninitialized scoring attempts. | Enforce fail-closed engine/runner guard (`RuntimeError` before scoring); future service readiness probes remain unimplemented/unvalidated; do not fabricate State D records. | Platform Team / Runtime design | **DESIGN CONTROL DEFINED; SERVICE READINESS NOT ESTABLISHED** |
| **R-07-09** | **Phase 06 Helper Misuse:** Evaluation helper functions adopted directly into runtime pipeline. | **MEDIUM** | Medium | Brittle runtime code; unvalidated assumptions on features. | Reject Phase 06 evaluation helpers as runtime dependencies; use dedicated adapters. | Tech Lead / Architecture boundary | **ARCHITECTURAL BOUNDARY DEFINED** |
| **R-07-10** | **Phase Scope Creep:** Phase 07 expands into scoring weights or automated routing. | **CRITICAL** | Low | Conflates Phase 07 with Phases 09/10; breaks project plan. | Reiterate strict Option A boundaries; mandate Project Owner approval gates. | Project Owner / Governance baseline | **GOVERNANCE CONTROL DEFINED** |

*Governance Note:* No risk is described as operationally resolved merely because a design control has been defined. Operational resolution requires authorized implementation, testing, and runtime verification.

---

## 15. Phase Boundary & Scope Conflict Register

### 15.1 Conflict Resolution: "Multi-Model Fusion & Decision Engine" vs Option A
- **Prior Problematic Formulation:** The Phase 07.1 interface inventory report referred to Phase 07 as *"Multi-Model Fusion & Decision Engine"* and proposed an output schema containing a `fused_decision` field.
- **Identified Conflict:** This formulation conflated Phase 07 with Phase 09 (Risk Scoring) and Phase 10 (Decision Automation), violating the Project Master Dashboard.
- **Formal Resolution:** The Project Owner explicitly approved **Option A — Signal Integration Only**. 
   - The term "Decision Engine" is formally purged from Phase 07 scope.
   - The proposed `fused_decision` field is **permanently rejected and removed**.
   - Phase 07 defines solely historical `IntegratedSignalRecord` containing independent Phase 04 and Phase 05 signals side-by-side in Mode 1 only (Mode 2 defines no `IntegratedSignalRecord`).

### 15.2 Evaluation Helper Reusability Assessment
- **Subject Functions:**
  1. `reconstruct_step_and_channel` (in [src/anomaly/evaluation.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/evaluation.py#L76-L125))
  2. `extract_clean_features_and_target` (in [src/anomaly/evaluation.py](file:///c:/Pratik_Bhuwad/Risk%20Intelligence%20&%20Decision%20Automation%20Platform/src/anomaly/evaluation.py#L127-L165))
- **Evaluation Finding:** These functions were implemented specifically for Phase 06 offline evaluation to reconstruct missing simulation metadata from one-hot features in processed Parquet files.
- **Architectural Directive:** These helpers are **NOT approved as production runtime dependencies**. In a production runtime environment, transaction channel (`type`) and timestamp are native attributes of the authorization payload, not reconstructed from one-hot vectors. Any runtime adoption would introduce fragile assumptions. Dedicated, validated ingestion schemas must be used instead.

### 15.3 Phase 08 (Explainable AI) Input Hand-Off Architecture & Limitations (F04, F06, F07-R8, F10)
- **Identified Integration Dilemma:** Phase 08 requires the 36 raw features evaluated by Phase 04 and the anomaly features evaluated by Phase 05 to compute TreeSHAP values, feature attributions, and human-readable reason codes. A naive design would bloat `IntegratedSignalRecord` by embedding all 36 raw features and model object pointers directly into Phase 07 outputs.
- **Architectural Resolution (Decoupled Identity Linkage):**
  1. **Zero Record Bloat:** `IntegratedSignalRecord` strictly contains signal outputs, metadata, and identity. It does **NOT** embed raw feature arrays or live model instances.
  2. **Bijective Identity Linkage:**
     - **Historical Mode 1 Hand-Off:** A historical integration record design may be consumed by downstream Phase 08 architecture, subject to Phase 07 execution authorization and Phase 08 prerequisites. Joined on authoritative `row_index`.
     - **Future Mode 2 Hand-Off:** Only the separate proposed operational stable identity contract (`transaction_id` — Gate 7.2 Approval Object B, APPROVED WITH LIMITATIONS) may be referenced at the design level. Phase 08 cannot consume operational `IntegratedSignalRecord`s because no operational `IntegratedSignalRecord` schema or emission is defined or authorized.
     - **Feature Stream:** Canonical feature vector drawn directly from the upstream Ingestion / Feature Store partition for that exact identity.
     - **Model Artifact Resolution (F04, F10):** Phase 08 resolves Phase 04 model artifact versions via direct record extraction or fallback to the batch execution manifest metadata. For Phase 05, `p5_detector_version` provides configuration release metadata only, not fitted artifact identity.
  3. **Explainability Limitations (F10):**
     - Exact fitted-detector explanation and reproduction are **NOT CURRENTLY EXECUTABLE** based on the documented system.
     - If Phase 08 requires the exact fitted Phase 05 detector object and its identity cannot be resolved, Phase 08 must fail closed (`UnresolvedFittedDetectorIdentityError`).
     - Any feature-level or signal-level alternative explanation pathway is a **proposed future design**, not a validated existing XAI capability.
  4. **Governance Compliance:** Preserves strict Option A boundaries, avoids payload duplication across the message bus, and maintains Phase 07 strictly as a signal integration layer. Preserves Phase 08 as a separate future phase.

---

## 16. Acceptance Criteria Checklist (A06, V143-M09, V143-M10)

*Evidence Integrity Note (V143-M09):* Checklist statuses below strictly distinguish **formally approved specification text statements** (ratified by the Project Owner under Gate 7.1 and Gate 7.2) from **verified runtime/implementation/independent audit completion**. No checklist item self-certifies runtime execution or implementation.

| Ref # | Required Acceptance Criterion | Evidence / Specification Reference | Verification Status |
| :---: | :--- | :--- | :---: |
| 1 | Mode 1 is architecture-defined but execution is separately authorized | Stated in § 2.1, § 3.2.1, § 4.2, § 7.1.1, § 18 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 2 | Mode 2 is operational identity-contract design only (`Incoming Transaction → Proposed Stable Identity Contract`) | Stated & diagrammed in § 1.2, § 1.3, § 2.1, § 3.2.2, § 6.1, § 7.1.2 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 3 | Mode 2 defines no Phase 04 `RiskPredictor` execution or Phase 04 adapter wrapper | Prohibited & separated in § 3.2.2, § 6.2, § 7.1.3, § 13.3 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 4 | Mode 2 cannot execute Phase 05 scoring | Prohibited in § 2.1, § 3.2.2, § 4.2, § 6.2 (Step 2) | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 5 | Mode 2 cannot perform fan-in | Prohibited in § 3.2.2, § 6.1, § 6.2 (Step 3) | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 6 | Mode 2 cannot perform a relational join | Prohibited in § 3.2.2, § 6.2 (Step 3), § 7.3 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 7 | Mode 2 cannot synthesize integration states | Prohibited in § 3.2.2, § 6.2 (Step 4), § 9.1 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 8 | Mode 2 has no `IntegratedSignalRecord` schema, construction, or dependency | Separated & prohibited in § 3.2.2, § 6.2, § 7.1.2, § 8.1, § 12.1 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 9 | Mode 2 cannot emit operational `IntegratedSignalRecord` | Prohibited in § 2.1, § 3.2.2, § 6.2 (Step 5), § 8.1 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 10 | Any operational transient ordinal discussion is out-of-scope / proposed concept only | Stated in § 3.2.3, § 4.2, § 7.1.3 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 11 | Historical `IntegratedSignalRecord` (`row_index` only; no `transaction_id`) and Mode 2 identity contract (`transaction_id` only) are strictly separate schemas | Separated in § 7.1.1, § 7.1.2, § 8.1, § 8.2 | **DOCUMENTED IN SPEC (GATE 7.1 RATIFIED)** |
| 12 | Gate 7.2 Approval Object A (Hist. Record) and Approval Object B (Op. Identity Contract) are distinct objects | Distinguished in § 8.1, § 19; formally decided by Project Owner on 2026-11-17 | **DECIDED (OBJECT A: APPROVED; OBJECT B: APPROVED WITH LIMITATIONS)** |
| 13 | Operational population/window policy remains DEFERRED | Classified DEFERRED (Owner Unassigned) in § 2.1, § 4.2, § 14, § 17 | **DEFERRED (UNASSIGNED)** |
| 14 | F10 detector provenance limitation remains accurately stated | Config release version only; fail closed in § 8.3, § 8.3.1, § 15.3 | **DOCUMENTED IN SPEC (IMPLEMENTATION PENDING)** |
| 15 | Gate 7.1 formal architecture & scope approval recorded | Formally approved by Project Owner on 2026-11-17; ADR-07-001 ratified (§ 2.1, § 19, § 20) | **APPROVED (PROJECT OWNER DECISION)** |
| 16 | Gate 7.2 formal schema & identity contract decisions recorded | Formally decided by Project Owner on 2026-11-17 (§ 2.1, § 8.1, § 19, § 20): Object A APPROVED; Object B APPROVED WITH LIMITATIONS | **DECIDED WITH LIMITATIONS** |
| 17 | Phase 07 implementation & real PaySim evaluation remain NOT AUTHORIZED | Recorded NOT AUTHORIZED in Header, § 2.1, § 18, § 19 | **NOT AUTHORIZED** |
| 18 | Mode 1 runner readiness is distinguished from production service readiness; zero service readiness claimed | Qualified in § 4.2, § 9.2, § 10.3, § 13.1, § 13.4 | **DOCUMENTED IN SPEC (SERVICE READINESS NOT ESTABLISHED)** |
| 19 | F01 row-order preservation synthetic probe | Probe design defined; implementation & execution not performed (§ 4.1, § 7.1.3, § 12.1, § 20) | **PENDING (NOT VERIFIED)** |
| 20 | Independent full-document consistency review | Formal Gate 7.1 review conducted by Project Owner; v1.4.4 ratified on 2026-11-17 (§ 19, § 20) | **COMPLETED / RATIFIED (GATE 7.1)** |
| 21 | Independent adversarial review of v1.4.4 | Formal Gate 7.1 review conducted by Project Owner; ADR-07-001 ratified on 2026-11-17 (§ 19, § 20) | **COMPLETED / RATIFIED (GATE 7.1)** |
| 22 | Independent source-code verification of reported §4 inventory | Antigravity-reported baseline inspection cited in § 4; independent repository/runtime verification not performed in doc-only task | **NOT VERIFIED (DOCUMENTATION-ONLY SCOPE)** |

---

## 17. Deferred Architectural Decisions

The following architectural decisions are explicitly deferred to future project phases:

1. **Deferred Decision 1: Phase 05 Persistent Artifact Serialization (`src/anomaly/artifacts.py`)**
   - *Description:* Designing a persistent disk serialization format (joblib bundle) for fitted Isolation Forest detectors.
   - *Deferral Rationale:* Not required for Option A signal integration. In-memory fitting in an evaluation runner satisfies the logical fit-before-score precondition for Phase 07 Mode 1 historical runner readiness, but does NOT establish production service readiness, service startup readiness, persistent artifact availability, cross-process reproducibility, operational recovery, operational scoring authorization, or streaming readiness.
   - *Target Resolution:* Separate infrastructure maintenance command prior to multi-node cluster deployment.

2. **Deferred Decision 2: Downstream Risk Scoring Policy for Non-Eligible Channels**
   - *Description:* Formulating whether transactions with `anomaly_status = "NOT_APPLICABLE"` receive a default neutral risk adjustment or rely solely on Phase 04 supervised scores.
   - *Deferral Rationale:* Governed strictly by Phase 09 (Risk Scoring). Phase 07 merely exposes the `NOT_APPLICABLE` state sentinel without editorializing in Mode 1.
   - *Target Resolution:* Phase 09 Architecture Specification.

3. **Deferred Decision 3: Operational Escalation Policy for Degraded Anomaly Transactions**
   - *Description:* Determining whether `DEGRADED_UNSCORABLE` transactions should trigger automated alerts to SecOps or fall back to standard monitoring queues.
   - *Deferral Rationale:* Operational routing belongs exclusively to Phase 10 (Decision Automation).
   - *Target Resolution:* Phase 10 Decision Policy Design.

4. **Deferred Decision 4: Global Production Transaction ID Generator Infrastructure**
   - *Description:* Selection of global ID generation scheme (UUIDv4 vs ULID vs Snowflake ID) for the enterprise API gateway for future operational serving.
   - *Deferral Rationale:* Infrastructure platform decision external to model signal integration.
   - *Target Resolution:* Production Deployment Phase.

5. **Deferred Decision 5: Upstream Version Extraction & Model Registry Resolution (F04, F10)**
   - *Description:* Implementing adapter hooks to inject `p4_model_version` and `p5_detector_version` and integrating with a centralized Model Registry.
   - *Deferral Rationale:* Requires adapter and registry implementation, which is deferred to Phase 07 implementation authorization. `p5_detector_version` is configuration release metadata only, not a fitted artifact ID.
   - *Target Resolution:* Phase 07 Implementation Phase.

6. **Deferred Decision 6: Operational Anomaly-Scoring Population & Alert-Budget Policy (F02, F07)**
   - *Description:* Resolving alert budget truncation ($K=0$ for $N_S<100$) and batch-composition sensitivity in streaming micro-batches, including evaluating sliding-window alert buffers, cumulative quantile scoring, or static threshold conversion.
   - *Deferral Rationale:* Phase 05 baseline specifies a frozen global 1.00% formula over declared complete evaluation populations (Mode 1). The specification does not define or approve an operational scoring population/window. Operational scoring on arbitrary incoming batches and batch-local top-K selection are **NOT AUTHORIZED**. No operational `IntegratedSignalRecord` may be emitted until this policy is approved.
   - *Target Resolution:* **DEFERRED — GOVERNING PHASE / OWNER NOT YET ASSIGNED**. The Project Owner must explicitly determine the appropriate governing phase and ownership before operational policy design proceeds.

---

## 18. Implementation Prerequisites

Before any implementation work for Phase 07 may be authorized, the following prerequisites must be fulfilled:
1. **Project Owner Formal Ratification:** Project Owner approval of this Architecture Specification (v1.4.4 ratified under Gate 7.1 on 2026-11-17) and ADR-07-001. [FULFILLED]
2. **Explicit Scope Authorization:** A dedicated Project Owner instruction authorizing code creation strictly limited to `src/fusion/` (or `src/integration/`) and corresponding synthetic unit tests under `tests/`.
3. **Synthetic Fixture Authorization:** Confirmation that implementation verification shall rely exclusively on synthetic test fixtures, with real PaySim dataset access remaining strictly unauthorized.
4. **Frozen Baselines Preservation:** Reconfirmation that Phase 04, Phase 05, and Phase 06 source files and configurations shall remain 100% untouched.

---

## 19. Explicit Project Owner Approval Gates (A07, V143-M07)

To ensure rigorous governance, Phase 07 execution is divided into five sequential approval gates:

```
┌────────────────────────────────────────────────────────┐
│ Gate 7.1: Architecture & Scope Approval (Option A)     │  <--- [STATUS: APPROVED — 2026-11-17]
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Gate 7.2: Schema & Identity Contract Approval          │  <--- [STATUS: DECIDED WITH LIMITATIONS]
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Gate 7.3: Implementation Scope Authorization           │  <--- [CURRENT GATE: NOT AUTHORIZED]
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Gate 7.4: Synthetic Verification & Contract Unit Tests │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Gate 7.5: Downstream Hand-Off Approval (Phases 08–10)  │
└────────────────────────────────────────────────────────┘
```

- **Gate 7.1: Architecture & Scope Approval (`APPROVED`):** Formal Project Owner decision granted on 2026-11-17.
  - **Approved Specification:** Phase 07.2 Architecture Specification v1.4.4.
  - **Approved Architecture:** Option A — Independent Signal Integration Without Score Fusion.
  - **Decision Status:** Formal approval granted; ADR-07-001 ratified.
- **Gate 7.2: Schema & Identity Contract Approval (`DECIDED WITH LIMITATIONS`):** Formal Project Owner decision granted on 2026-11-17, strictly distinguishing and separately recording two distinct approval objects:
  - **Approval Object A — Historical Integration Record:**
    - **Decision:** `APPROVED`
    - **Approved Scope:** Mode 1 historical integration design; historical `IntegratedSignalRecord` dataclass schema; `row_index: int` as exclusive historical evaluation identity; existing documented Phase 04 and Phase 05 signal fields; existing nullability, state sentinels, and identity invariants.
    - **Governance Restriction:** Approval of Object A does NOT authorize execution or implementation (remains strictly subject to Gate 7.3).
  - **Approval Object B — Proposed Operational Identity Contract:**
    - **Decision:** `APPROVED WITH LIMITATIONS` (`approve_limited`)
    - **Approved Scope:** Mode 2 proposed operational stable identity contract (`transaction_id: str` as exclusive proposed operational identity); design-level interface contract only.
    - **Explicit Mandatory Limitations:**
      1. No operational Phase 04 execution authorization.
      2. No operational Phase 05 scoring authorization.
      3. No operational signal integration authorization.
      4. No operational relational join or state synthesis authorization.
      5. No operational `IntegratedSignalRecord` schema, construction, or emission authorization.
      6. No approval of an operational population/window policy.
      7. No production-serving readiness claim.
  - **Approval Separation & Invariants:**
    - Approval Object A and Approval Object B remain separately recorded.
    - Approval of Object B does NOT constitute approval of operational signal integration, operational execution, or operational record emission.
    - Historical `row_index` and operational `transaction_id` are strictly non-interchangeable.
    - Operational `IntegratedSignalRecord` schema does not exist and emission is strictly prohibited.
- **Gate 7.3 (Current): Implementation Scope Authorization (`NOT AUTHORIZED`):** Specific Project Owner command authorizing implementation of the Mode 1 signal adapter and join module (`NOT AUTHORIZED`). Phase 07 implementation remains completely unauthorized until a dedicated Project Owner instruction is issued.
- **Gate 7.4: Synthetic Verification & Test Approval:** Review of unit test results demonstrating 100% pass rate across identity, channel, state, and contract test suites using synthetic fixtures (including pending F01 probe verification). [PENDING GATE 7.3 AUTHORIZATION AND IMPLEMENTATION]
- **Gate 7.5: Downstream Hand-Off Approval (Phases 08–10) (A07):** Formal closure of Phase 07 and authorization to unblock Phase 08 (Explainable AI), Phase 09 (Risk Scoring), and Phase 10 (Decision Automation) based on validated historical integration deliverables and approved downstream consumption contracts. [PENDING GATES 7.3–7.4]

---

## 20. Version and Amendment History (A08, V143-B06, V143-M10)

*Evidence Integrity Notice (V143-M10):* Baseline technical references in Section 4 reflect **Antigravity-reported static source inspection** (2026-11-05) and findings documented from that inspection. Document reviews, corrections, and decision synchronizations (including v1.4.2–v1.4.4 reviews, the v1.4.4 correction pass, and the v1.4.5 formal decision recording) are **document-level activities only**; they do NOT constitute independent repository inspection or independent source-code verification unless separately performed and documented.

| Version | Date | Amendment Type | Governing Mandate | Key Changes & Findings Addressed | Author / Reviewer | Approval Status |
| :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| `1.0.0` | 2026-11-05 | Initial Specification | Option A Adoption | Initial architecture design for side-by-side integration. | Antigravity Lead Architect | Conditional — Not Approved |
| `1.1.0` | 2026-11-06 | Controlled Amendment | Findings C01–C08 | Resolved C01 (identity lifecycle), C02 (join checks), C03 (risk register statuses), C04 (feasibility calibration), C05 (Phase 04 score semantics), C06 (`NOT_EVALUABLE` population scope), C07 (`integration_status` independence), C08 (provenance definitions). | Antigravity Lead Architect | Pending Review |
| `1.2.0` | 2026-11-06 | Contract Correction | Review Inconsistencies | Dual identity modes defined (`row_index` vs `transaction_id`), Phase 04 mandatory fail-closed abort established, `integration_impl_version` assigned to manifest, Phase 08 decoupled hand-off specified. | Antigravity Lead Architect | Pending Review |
| `1.3.0` | 2026-11-06 | Controlled Amendment | Findings F01–F06 | **F01 Status (V143-B06):** Synthetic order-preservation probe design defined; probe implementation pending; probe execution pending; upstream row-order preservation not independently verified. Addressed F02 (operational budget limits), F03 (fail-closed detector readiness), F04 (three-tier version fallback), F05 (transient ordinal non-leakage), F06 (`PASSED` canonical status). | Antigravity Lead Architect | Pending Review |
| `1.4.0` | 2026-11-06 | Consolidated Amendment | Findings F07–F10 | Resolved F07 (alert budget denominator strictly $N_S$; operational batch serving deferred), F08 (removed unsupported calibration causality; reported Brier scores preserved), F09 (distinguished detector lifecycle across Design/Pending/Unvalidated domains), F10 (distinguished detector configuration release version from fitted artifact identity; Model Registry marked pending). | Antigravity Lead Architect | Conditional — Not Approved |
| `1.4.1` | 2026-11-06 | Controlled Architecture Correction | Findings F07, F10, F09 Clarification | Attempted F07 operational boundary separation and F10 provenance clarification. | Antigravity Lead Architect | Conditional — Not Approved |
| `1.4.2` | 2026-11-06 | Consolidated Architecture Correction | Review Inconsistencies | Attempted resolution of F07 scope contradictions and F10 explainability boundaries. Subsequent independent document review identified remaining findings F07-R1 through F07-R8 and A01 through A09. | Antigravity Lead Architect | Conditional — Not Approved |
| `1.4.3` | 2026-11-06 | Consolidated Architecture Correction & Remediation | Full-Document Consistency & Authorization Boundary Remediation | Attempted resolution of F07-R1–R8 and A01–A09 (execution boundary scoping, diagram separation, Gate 7.5 scope, F01 probe pending disclosure). Subsequent independent **document review** (without independent source-code inspection) identified remaining schema mixing (`V143-B01`), diagram fan-out (`V143-B02`), Mode 2 `IntegratedSignalRecord` references (`V143-B03`), Mode 2 `RiskPredictor` adapter overlap (`V143-B04`), historical Phase 04 operational wording (`V143-B05`), inaccurate v1.3.0 F01 history (`V143-B06`), and findings `V143-M07`–`M10`. | Antigravity Lead Architect | Conditional — Not Approved |
| `1.4.4` | 2026-11-11 | Minimal Controlled Schema & Regression Correction | Findings `V143-B01`–`B06`, `V143-M07`–`M10` | **V143-B01 (Schema Separation):** Removed `transaction_id` from historical `IntegratedSignalRecord` (`row_index: int` only) and split § 8.2 dictionaries; kept proposed Mode 2 stable identity contract (`transaction_id: str` only) strictly separate with zero operational `IntegratedSignalRecord` schema.<br>**V143-B02 (Mode 2 Diagrams):** Simplified Context B (§ 1.3) and Topology B (§ 6.1) strictly to `Incoming Transaction → Proposed Stable Identity Contract` (zero P04/P05 fan-out or integration arrows).<br>**V143-B03 (Mode 2 `IntegratedSignalRecord` Removal):** Removed all `IntegratedSignalRecord.row_index = None` assignments, Mode 2 examples, and Mode 2 test dependencies on `IntegratedSignalRecord` (§§ 6.2, 7.1.2, 7.1.3, 12.1).<br>**V143-B04 (Phase 04 Adapter Scope):** Restricted Phase 04 `RiskPredictor` adapter strictly to Mode 1 historical integration (§ 7.1.3, § 13.3); removed Mode 2 identity mapping from Phase 04 adapter.<br>**V143-B05 (Mode 1 Phase 04 Wording):** Replaced `"fully valid and operational"` with `"valid within the Mode 1 historical integration design"` (§§ 9.1, 9.2) and cleaned up Mode 1 completeness phrasing (§ 8.4).<br>**V143-B06 (F01 Amendment History):** Corrected v1.3.0 history to state probe design defined, implementation pending, execution pending, and order preservation not independently verified.<br>**V143-M07 (Gate 7.2 Objects):** Explicitly separated Gate 7.2 Approval Object A (Historical `IntegratedSignalRecord`) and Approval Object B (Proposed Operational Identity Contract) without adding gates.<br>**V143-M08 (Runner vs. Service Readiness):** Distinguished Mode 1 historical evaluation runner readiness from unestablished future service readiness (§§ 4.3, 9.2, 10.3, 12.3, 13.1, 13.4, 14, 17).<br>**V143-M09 (Checklist Integrity):** Converted § 16 statuses to evidence-based non-self-certifying states (`PENDING` / `NOT VERIFIED` where verification has not occurred).<br>**V143-M10 (Inspection vs. Verification):** Replaced unqualified `[VERIFIED IN SOURCE]` tags across § 4 & § 8 with `[REPORTED IN BASELINE SOURCE INSPECTION]` and documented four-tier provenance classification separating Antigravity-reported baseline inspection, documented findings, document review, and unperformed independent source verification.<br>*Author self-audit only; independent document & repository verification pending.* | Antigravity Lead Architect | **Awaiting Independent Review (Gate 7.1 — NOT APPROVED)** |
| `1.4.5` | 2026-11-17 | Governance Decision Recording | Formal Project Owner Ratification (Gate 7.1 & Gate 7.2) | **Gate 7.1 Ratification:** Recorded formal Project Owner approval of Phase 07.2 Architecture Specification v1.4.4 and Option A architecture (ADR-07-001 ratified).<br>**Gate 7.2 Object A Approval:** Recorded formal Project Owner approval of Approval Object A (Mode 1 historical `IntegratedSignalRecord` schema, `row_index: int` exclusive historical identity, Phase 04/05 signal fields, nullability, and state sentinels); execution/implementation remains unauthorized.<br>**Gate 7.2 Object B Limited Approval:** Recorded formal Project Owner decision for Approval Object B as `APPROVED WITH LIMITATIONS` (`approve_limited`: Mode 2 proposed operational identity contract `transaction_id: str` approved at design level only; explicit limitations enforce zero operational Phase 04 execution, zero operational Phase 05 scoring, zero operational signal integration, zero operational relational joins, zero operational state synthesis, zero operational `IntegratedSignalRecord` schema/emission, zero operational population/window policy approval, and zero production-serving readiness claims).<br>**Cross-Document Status Reconciliation:** Reconciled all governance references across Header, § 1.3, § 2.1, § 3.2.1, § 4 provenance note, § 6.1, § 6.2, § 8.1, § 8.2, § 15.3, § 16, § 18, and § 19. Preserved Gate 7.3 as NOT AUTHORIZED, Phase 07 implementation as NOT AUTHORIZED, and all historical and technical invariants intact. | Project Owner (Decision Authority) / Antigravity (Documentation Synchronization) | **Gate 7.1 APPROVED; Gate 7.2 DECIDED WITH LIMITATIONS (Object A APPROVED; Object B APPROVED WITH LIMITATIONS); Gate 7.3 NOT AUTHORIZED** |

---
*End of Phase 07.2 Architecture Specification & Feasibility Design (v1.4.5 — Formally Ratified under Gate 7.1; Gate 7.2 Decided with Limitations; Gate 7.3 Not Authorized).*
