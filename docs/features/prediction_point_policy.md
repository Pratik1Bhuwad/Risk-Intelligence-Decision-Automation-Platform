# Field-Availability Policy & Operational Prediction Boundary

## Platform: Risk Intelligence & Decision Automation Platform
**Status**: `CONFIRMED (PROJECT POLICY)`  
**Audit Reference**: PaySim Data Audit v0.1.0  
**Implementation Package**: `src/features/policy.py`

---

## 1. Operational Prediction Boundary Definitions

- **Prediction Event**:
  The arrival of a transaction authorization request at the scoring/decision boundary of the platform.
- **Prediction Point**:
  **Pre-Authorization Inline Evaluation (Gate 3 in the Transaction Lifecycle)**.
  The risk score and decision recommendation (Approve / Monitor / Manual Investigation) are evaluated *before* funds are debited from the sender, credited to the recipient, or committed to the ledger.
- **Prediction-Time Temporal Index**:
  `step` — Discrete simulation-time index representing an integer hour elapsed since the simulation began (range: 1 to 743).
  *(Note: `step` is NOT a production wall-clock timestamp; it serves as the discrete sequencing and hourly cyclical index).*
- **Same-Step Temporal Policy**:
  `EXCLUDE_SAME_STEP`. All historical features strictly enforce `historical_step < current_step`. Transactions occurring within the same discrete simulation hour index cannot establish a verified intra-hour arrival order and are strictly excluded from each other's prior history.

---

## 2. Field Classification Matrix

Each field in the raw dataset is classified across three distinct dimensions to separate factual dataset properties from operational assumptions and project policies:

| Field Name | Dataset Availability | Production Availability | Current Project Feature Policy | Rationale & Handling |
| :--- | :--- | :--- | :--- | :--- |
| `step` | `AVAILABLE_IN_DATASET` | `AVAILABLE_DURING_TRANSACTION` | `PERMITTED_INPUT` | Discrete simulation index available at transaction arrival. Used for sequencing, cyclical time-of-day features, and day-of-simulation calculations. |
| `type` | `AVAILABLE_IN_DATASET` | `AVAILABLE_DURING_TRANSACTION` | `PERMITTED_INPUT` | Transaction channel / payment method specified in the authorization payload (CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER). |
| `amount` | `AVAILABLE_IN_DATASET` | `AVAILABLE_DURING_TRANSACTION` | `PERMITTED_INPUT` | Requested transfer/payment currency volume specified in authorization payload. |
| `nameOrig` | `AVAILABLE_IN_DATASET` | `AVAILABLE_BEFORE_TRANSACTION` | `PERMITTED_INPUT` | Authenticated originating customer account identifier. |
| `oldbalanceOrg` | `AVAILABLE_IN_DATASET` | `AVAILABLE_BEFORE_TRANSACTION` | `PERMITTED_INPUT` | Originating account balance queryable from internal ledger immediately before authorization. |
| `newbalanceOrig` | `AVAILABLE_IN_DATASET` | `AVAILABLE_ONLY_AFTER_TRANSACTION` | `EXCLUDED_POST_EVENT` | **Post-event ledger balance**. In an inline pre-authorization engine, this balance does not exist at decision time. If a transaction is blocked/declined, it is never realized. Using it creates severe post-event leakage. |
| `nameDest` | `AVAILABLE_IN_DATASET` | `AVAILABLE_DURING_TRANSACTION` | `PERMITTED_INPUT` | Recipient account identifier provided in routing instructions. Prefix distinguishes Merchant (`M*`) from Customer (`C*`). |
| `oldbalanceDest` | `AVAILABLE_IN_DATASET` | `UNKNOWN_ARCHITECTURE_DEPENDENT` | `EXCLUDED_UNVERIFIED_SOURCE` | **Project Policy Decision**: While available in PaySim, an authorization engine should not depend on recipient-side ledger information unless its availability at the authorization boundary can be verified. In open-loop banking rails, recipient balance is inaccessible to the sender. For merchant destinations in PaySim, it is always 0.0. Excluded to ensure production realism. |
| `newbalanceDest` | `AVAILABLE_IN_DATASET` | `AVAILABLE_ONLY_AFTER_TRANSACTION` | `EXCLUDED_POST_EVENT` | **Post-event recipient balance**. Posted strictly after clearing/settlement. Excluded to prevent post-event leakage. |
| `isFraud` | `AVAILABLE_IN_DATASET` | `AVAILABLE_ONLY_AFTER_TRANSACTION` | `EXCLUDED_TARGET` | **Ground truth target label**. Ascertained post-event via dispute, chargeback, or fraud investigation. Strictly excluded from feature sets. |
| `isFlaggedFraud` | `AVAILABLE_IN_DATASET` | `UNKNOWN_ARCHITECTURE_DEPENDENT` | `EXCLUDED_PROXY` | **Legacy heuristic rule output**. Documented as an existing rule flag for transfers > 200,000. Excluded from feature inputs to prevent circular rule replication and target proxy leakage. |

---

## 3. Strict Temporal Boundary & Same-Step Policy

```
PAST HISTORY (PERMITTED)               CURRENT STEP S           FUTURE (EXCLUDED)
───────────────────────────────┬───────────────────────────────┬─────────────────►
 historical_step < S           │ current_step == S             │ step > S
 (Committed entity history)    │ (Current transaction T)       │ (Strictly unreachable)
                               │ [Same-step events EXCLUDED]   │
```

1. **Non-Self-Contamination**: Transaction $T$ can never contribute to its own historical counts, sums, or frequency indicators.
2. **Same-Step Exclusion**: PaySim raw records only record discrete hours (`step`). Multiple transactions sharing the same step cannot prove arrival order. Therefore, records at step $S$ cannot read other records at step $S$.
3. **Future Invariance**: Any modification, insertion, or deletion of transactions at step $S' > S$ (whether for the same entity or different entities) has mathematical zero effect on features calculated for transactions at step $S$.

---

## 4. Leakage Boundary Implementation

In code, the leakage boundary is strictly enforced by:
- `src/features/policy.py`: Enforces `STRICTLY_EXCLUDED_FIELDS`.
- `src/features/transformers.py`: Implements step-buffered lazy commitment ensuring only records with `historical_step < current_step` are queryable.
- `src/features/validator.py`: Automated assertions raising critical errors if any post-event field (`newbalanceOrig`, `newbalanceDest`), unverified field (`oldbalanceDest`), proxy (`isFlaggedFraud`), or target (`isFraud`) infiltrates the feature matrix.
