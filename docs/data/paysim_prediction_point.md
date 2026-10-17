# PaySim Prediction-Time Point Analysis

## Status
`STATUS: CONFIRMED (PROJECT POLICY)`

*The operational prediction point and field-availability policy are established and enforced in code (`src/features/policy.py`). The model operates strictly at Pre-Authorization Inline Evaluation (Gate 3).*

---

## 1. Candidate Decision Timeline & Established Prediction Point

In a real-time risk intelligence and decision automation system, transactions progress through distinct operational lifecycle phases:

```
┌─────────────────────────────────┐
│ 1. Before Transaction           │  Static account attributes, prior entity history (historical_step < s)
└───────────────┬─────────────────┘
                ▼
┌─────────────────────────────────┐
│ 2. Transaction Arrives          │  Requested amount, destination entity, transaction type, discrete step index
└───────────────┬─────────────────┘
                ▼
┌─────────────────────────────────┐
│ 3. Risk Decision Point [CONFIRMED PREDICTION POINT]
│    Pre-Authorization Inline     │  APPROVE / MONITOR / MANUAL INVESTIGATION
│    Evaluation                   │  (Model scoring & policy rules executed here)
└───────────────┬─────────────────┘
                ▼
┌─────────────────────────────────┐
│ 4. Transaction Outcome          │  Settlement, ledger update, post-tx balance, dispute/chargeback, fraud label
└─────────────────────────────────┘
```

---

## 2. Terminology & Specification

- **Prediction Event**: Transaction authorization request arrives at the scoring/authorization boundary.
- **Prediction Point**: Pre-Authorization Inline Evaluation (Gate 3).
- **Prediction-Time Temporal Index**: `step` — Discrete simulation-time index representing hours from simulation initiation (1 to 743). *(Not a production wall-clock timestamp; represents discrete simulation time).*
- **Same-Step Policy**: `EXCLUDE_SAME_STEP`. Historical records strictly require `historical_step < current_step`. Same-step transactions cannot enter prior history because raw intra-step row ordering cannot establish arrival chronology.

---

## 3. Field-by-Field Lifecycle & Availability Analysis

| Column | Candidate Phase | Dataset Availability | Production Availability | Current Project Feature Policy | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `step` | 2. Transaction Arrives | AVAILABLE | AVAILABLE_DURING_TX | PERMITTED_INPUT | Discrete simulation index. Used for sequencing, cyclical time-of-day features, and day-of-simulation. |
| `type` | 2. Transaction Arrives | AVAILABLE | AVAILABLE_DURING_TX | PERMITTED_INPUT | Payment channel / transaction method specified in the authorization payload. |
| `amount` | 2. Transaction Arrives | AVAILABLE | AVAILABLE_DURING_TX | PERMITTED_INPUT | Requested transfer/payment currency volume. |
| `nameOrig` | 2. Transaction Arrives | AVAILABLE | AVAILABLE_BEFORE_TX | PERMITTED_INPUT | Authenticated originating customer account identifier. |
| `oldbalanceOrg` | 1. Before Transaction | AVAILABLE | AVAILABLE_BEFORE_TX | PERMITTED_INPUT | Ledger balance of the originating account prior to execution, queryable internally. |
| `newbalanceOrig` | 4. Transaction Outcome | AVAILABLE | ONLY_AFTER_TX | EXCLUDED_POST_EVENT | Balance after execution. In real-time decisioning (Gate 3), transaction has not executed; if blocked, this balance is never realized. Post-event leakage. |
| `nameDest` | 2. Transaction Arrives | AVAILABLE | AVAILABLE_DURING_TX | PERMITTED_INPUT | Destination account identifier provided in routing instructions. |
| `oldbalanceDest` | 1. Before Transaction | AVAILABLE | UNKNOWN_ARCHITECTURE | EXCLUDED_UNVERIFIED | Excluded under project policy: assumed authorization engine should not depend on recipient-side ledger info unless verified in production architecture. |
| `newbalanceDest` | 4. Transaction Outcome | AVAILABLE | ONLY_AFTER_TX | EXCLUDED_POST_EVENT | Balance of destination account after transaction settlement. Post-event leakage. |
| `isFraud` | 4. Transaction Outcome | AVAILABLE | ONLY_AFTER_TX | EXCLUDED_TARGET | Ground truth fraud label established post-event via investigation or chargeback. Target only. |
| `isFlaggedFraud` | 3. Decision / Outcome | AVAILABLE | UNKNOWN_ARCHITECTURE | EXCLUDED_PROXY | Legacy heuristic rule output (>200k transfer). Excluded to prevent circular rule replication. |

---

## 4. Key Methodological Distinctions

- **CONFIRMED FROM DATASET/AUDIT**: PaySim dimensions (6,362,620 rows, 11 columns), absence of missing values, 100% confinement of fraud to TRANSFER and CASH_OUT, 99.85% single-transaction originators, 57.21% destination reuse.
- **PROJECT POLICY**: Exclusion of `oldbalanceDest`, exclusion of `newbalanceOrig`/`newbalanceDest`, exclusion of `isFlaggedFraud`, strict `historical_step < current_step` temporal boundary, same-step exclusion.
- **PRODUCTION ASSUMPTION**: Real-time evaluation occurs pre-authorization before ledger commit.
- **UNKNOWN**: Formal wall-clock acquisition date and licensing of raw PaySim source file.
