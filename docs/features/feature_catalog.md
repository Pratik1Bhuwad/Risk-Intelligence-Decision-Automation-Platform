# Feature Catalog & Feature Definitions

## Platform: Risk Intelligence & Decision Automation Platform
**Status**: `CONFIRMED (IMPLEMENTED)`  
**Configuration Reference**: `configs/feature_engineering.yaml`  
**Code Reference**: `src/features/metadata.py`, `src/features/transformers.py`

---

## 1. Feature Inventory Overview

A total of **36 leakage-safe model input features** are implemented across **6 logical feature groups**. In addition, the target label (`isFraud`) is preserved as a separate outcome column in the processed dataset for supervised model training and evaluation.

```
Processed Dataset Columns: 37 Total
├── Model Input Features: 36
│   ├── Group 1: Transaction & Channel (6 features)
│   ├── Group 2: Temporal & Cyclical (4 features)
│   ├── Group 3: Amount Behavior (5 features)
│   ├── Group 4: Origin Balance & Liquidation (8 features)
│   ├── Group 5: Counterparty Type (2 features)
│   └── Group 6: Historical Entity Velocity (11 features)
└── Target Outcome Label: 1
    └── isFraud (binary ground-truth outcome label)
```

---

## 2. Detailed Feature Specifications

### Group 1: Transaction & Channel Features
| Feature Name | Definition | Formula / Logic | Source Fields | Data Type | Null Handling | Leakage Risk | Expected Coverage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `is_transfer` | Binary indicator for TRANSFER payment method. | `int(type == 'TRANSFER')` | `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_cash_out` | Binary indicator for CASH_OUT payment method. | `int(type == 'CASH_OUT')` | `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_payment` | Binary indicator for PAYMENT method. | `int(type == 'PAYMENT')` | `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_cash_in` | Binary indicator for CASH_IN method. | `int(type == 'CASH_IN')` | `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_debit` | Binary indicator for DEBIT method. | `int(type == 'DEBIT')` | `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_high_risk_type` | Binary indicator for high-risk payment channels. | `int(type in ('TRANSFER', 'CASH_OUT'))` | `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |

### Group 2: Temporal & Cyclical Features
| Feature Name | Definition | Formula / Logic | Source Fields | Data Type | Null Handling | Leakage Risk | Expected Coverage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `hour_of_day` | Simulated hour of day (0–23). | `step % 24` | `step` | `int8` | None | NONE | HIGH | VALID_CANDIDATE |
| `day_of_simulation` | Cumulative elapsed simulation day. | `step // 24` | `step` | `int16` | None | NONE | HIGH | VALID_CANDIDATE |
| `day_of_week` | Simulated day of week index (0–6). | `(step // 24) % 7` | `step` | `int8` | None | NONE | HIGH | VALID_CANDIDATE |
| `is_night_hour` | Binary indicator for simulated night hours (0–6). | `int((step % 24) in (0, 1, 2, 3, 4, 5, 6))` | `step` | `int8` | None | NONE | HIGH | VALID_CANDIDATE |

### Group 3: Amount Behavior Features
| Feature Name | Definition | Formula / Logic | Source Fields | Data Type | Null Handling | Leakage Risk | Expected Coverage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `amount` | Requested nominal transaction amount. | `amount` | `amount` | `float64` | 0.0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `log_amount` | Natural logarithm of requested amount plus 1. | `log1p(amount)` | `amount` | `float32` | 0.0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_amount_zero` | Binary indicator for zero-amount transaction. | `int(amount == 0.0)` | `amount` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_amount_round_100` | Indicator that amount is round multiple of 100. | `int((amount > 0) & (amount % 100 == 0))` | `amount` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_amount_round_1000` | Indicator that amount is round multiple of 1000. | `int((amount > 0) & (amount % 1000 == 0))` | `amount` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |

### Group 4: Origin Balance & Liquidation Features
| Feature Name | Definition | Formula / Logic | Source Fields | Data Type | Null Handling | Leakage Risk | Expected Coverage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `oldbalanceOrg` | Originator pre-transaction ledger balance. | `oldbalanceOrg` | `oldbalanceOrg` | `float64` | 0.0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `log_oldbalanceOrg` | Natural log of pre-transaction origin balance + 1. | `log1p(oldbalanceOrg)` | `oldbalanceOrg` | `float32` | 0.0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_orig_zero_balance` | Indicator that sender balance was zero before transaction. | `int(oldbalanceOrg == 0.0)` | `oldbalanceOrg` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `amount_to_orig_balance_ratio` | Ratio of requested amount to pre-tx origin balance. | `amount / (oldbalanceOrg + 1.0)` | `amount`, `oldbalanceOrg` | `float32` | 0.0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `orig_balance_to_amount_ratio` | Ratio of pre-tx balance to requested amount. | `oldbalanceOrg / (amount + 1.0)` | `oldbalanceOrg`, `amount` | `float32` | 0.0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_amount_exceeds_orig_balance` | Indicator that amount strictly exceeds pre-tx balance. | `int(amount > oldbalanceOrg)` | `amount`, `oldbalanceOrg` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_full_balance_drain` | Indicator that amount matches origin balance within tolerance on a funded account. | `int((abs(amount - oldbalanceOrg) < 0.01) & (oldbalanceOrg > 0.0))` | `amount`, `oldbalanceOrg` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `is_zero_balance_transfer` | Indicator of TRANSFER initiated from zero balance. | `int((oldbalanceOrg == 0.0) & (type == 'TRANSFER'))` | `oldbalanceOrg`, `type` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |

### Group 5: Counterparty Type Features
| Feature Name | Definition | Formula / Logic | Source Fields | Data Type | Null Handling | Leakage Risk | Expected Coverage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dest_is_merchant` | Binary indicator for Merchant recipient (`M*`). | `int(nameDest.startswith('M'))` | `nameDest` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |
| `dest_is_customer` | Binary indicator for Customer recipient (`C*`). | `int(nameDest.startswith('C'))` | `nameDest` | `int8` | 0 if missing | NONE | HIGH | VALID_CANDIDATE |

### Group 6: Point-in-Time Historical Entity Velocity Features
*Strictly enforces `historical_step < current_step`. Same-step transactions cannot enter prior history.*

| Feature Name | Definition | Formula / Logic | Source Fields | Data Type | Null Handling | Leakage Risk | Expected Coverage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dest_prior_tx_count` | Count of transactions received by destination across all prior steps. | `count(historical_step < current_step)` | `nameDest`, `step` | `int32` | 0 if first seen | NONE | HIGH | VALID_CANDIDATE |
| `dest_prior_total_amount` | Cumulative amount received by destination across all prior steps. | `sum(amount where historical_step < current_step)` | `nameDest`, `amount`, `step` | `float64` | 0.0 if first seen | NONE | HIGH | VALID_CANDIDATE |
| `dest_prior_avg_amount` | Average transaction amount received by destination across prior steps. | `total_amount / count if count > 0 else 0.0` | `nameDest`, `amount`, `step` | `float32` | 0.0 if first seen | NONE | HIGH | VALID_CANDIDATE |
| `dest_time_since_last_tx` | Step delta since most recent step where destination was observed. | `current_step - max(historical_step < current_step)` | `nameDest`, `step` | `float32` | -1.0 if first seen | NONE | HIGH | VALID_CANDIDATE |
| `dest_is_first_time_seen` | Indicator that destination has 0 prior transactions. | `int(dest_prior_tx_count == 0)` | `nameDest`, `step` | `int8` | 1 if first seen | NONE | HIGH | VALID_CANDIDATE |
| `dest_tx_count_prior_24h` | Transactions received by destination in `[current_step - 24, current_step)`. | `count(current_step - 24 <= historical_step < current_step)` | `nameDest`, `step` | `int32` | 0 if none | NONE | HIGH | VALID_CANDIDATE |
| `dest_amount_sum_prior_24h` | Sum of amounts received by destination in `[current_step - 24, current_step)`. | `sum(amount where current_step - 24 <= historical_step < current_step)` | `nameDest`, `amount`, `step` | `float64` | 0.0 if none | NONE | HIGH | VALID_CANDIDATE |
| `orig_prior_tx_count` | Count of transactions initiated by originator across prior steps. | `count(historical_step < current_step)` | `nameOrig`, `step` | `int32` | 0 if first seen | NONE | **LOW** | VALID_CANDIDATE |
| `orig_prior_total_amount` | Cumulative amount initiated by originator across prior steps. | `sum(amount where historical_step < current_step)` | `nameOrig`, `amount`, `step` | `float64` | 0.0 if first seen | NONE | **LOW** | VALID_CANDIDATE |
| `orig_time_since_last_tx` | Step delta since most recent step where originator was observed. | `current_step - max(historical_step < current_step)` | `nameOrig`, `step` | `float32` | -1.0 if first seen | NONE | **LOW** | VALID_CANDIDATE |
| `orig_is_first_time_seen` | Indicator that originator has 0 prior transactions. | `int(orig_prior_tx_count == 0)` | `nameOrig`, `step` | `int8` | 1 if first seen | NONE | **LOW** | VALID_CANDIDATE |

---

## 3. Methodological Note on Originator Historical Features

PaySim exhibits **very limited originator entity reuse** (audit confirmed 99.8537% of originating accounts appear only once). 
- Consequently, originator historical features (`orig_prior_tx_count`, `orig_prior_total_amount`, `orig_time_since_last_tx`, `orig_is_first_time_seen`) are expected to have **low coverage / usefulness**.
- They are retained in the catalog as `STATUS: VALID FEATURE CANDIDATES` to satisfy complete entity profiling architecture, with `EXPECTED COVERAGE: LOW` and `MODEL VALUE: TO BE EVALUATED LATER`.
- In contrast, destination accounts (`nameDest`) exhibit a **57.21% reuse rate**, providing strong historical coverage for destination velocity profiling.

---

## 4. Rejected Features & Reasons for Exclusion

1. **`newbalanceOrig`**: REJECTED. Post-event balance updated after authorization and debit execution. If a transaction is blocked pre-auth, this balance never occurs.
2. **`newbalanceDest`**: REJECTED. Post-event balance updated after recipient credit and clearing.
3. **`oldbalanceDest`**: REJECTED UNDER CURRENT PROJECT POLICY. Assumed authorization engine should not depend on recipient-side ledger balance unless verified in the target architecture. (Also 100% 0.0 for merchants).
4. **`balance_error_orig` (`oldbalanceOrg - amount - newbalanceOrig`)**: REJECTED. Directly uses `newbalanceOrig`, creating post-event leakage.
5. **`balance_error_dest` (`oldbalanceDest + amount - newbalanceDest`)**: REJECTED. Directly uses `newbalanceDest`, creating post-event leakage.
6. **`isFlaggedFraud`**: REJECTED. Output of a legacy heuristic rule (>200k transfer); target proxy when 1, misses 99.8% of fraud.
7. **Global Entity Target Encoding / Full-Dataset Fraud Rates**: REJECTED. Leaks future labels across transactions.
