# Leakage Testing Strategy & Verification Protocol

## Platform: Risk Intelligence & Decision Automation Platform
**Status**: `CONFIRMED (TESTS PASSING: 44/44)`  
**Test Suite Reference**: `tests/test_feature_leakage.py`, `tests/test_feature_validator.py`

---

## 1. Overview & Objectives

In machine learning for fraud detection, data leakage occurs whenever information from the future, post-event outcomes, or unverified operational sources is allowed to influence model features. A model evaluated on leaky features will achieve artificially inflated benchmark metrics but will fail catastrophically in production.

This protocol documents the rigorous, automated test suite designed to verify that the feature engineering pipeline satisfies the **Pre-Authorization Inline Evaluation boundary**.

---

## 2. Leakage Test Suite Specifications

All tests are implemented in `tests/test_feature_leakage.py` and run on every build via `pytest`.

### Test 1: Complete Absence of Target and Post-Event Fields
- **Objective**: Ensure that prohibited raw columns never infiltrate the feature matrix.
- **Verification**: Asserts that `feature_cols.intersection(STRICTLY_EXCLUDED_FIELDS) == set()`.
- **Excluded Fields Verified**: `newbalanceOrig`, `newbalanceDest`, `oldbalanceDest`, `isFlaggedFraud`, and `isFraud` (unless explicitly requested as an aligned external target label).
- **Test Function**: `test_post_event_and_target_fields_absent_from_feature_matrix`

### Test 2: Same-Step Exclusion Policy
- **Objective**: Ensure that transactions occurring within the same discrete simulation hour index (`step`) do not contaminate each other's prior history.
- **Verification**: Given multiple transactions in `step = 1`, all must have `dest_prior_tx_count == 0`, `orig_prior_tx_count == 0`, and `dest_is_first_time_seen == 1`.
- **Test Function**: `test_same_step_exclusion_policy`

### Test 3: Strict Prior Temporal Boundary (`historical_step < current_step`)
- **Objective**: Ensure that at step $S$, only transactions from steps $< S$ contribute to counts and sums.
- **Verification**: Step $S$ records can see transactions from step $S-1$ and $S-2$, but cannot see records from step $S$.
- **Test Function**: `test_strict_prior_temporal_boundary`

### Test 4: General Future Transaction Invariance
- **Objective**: Changing, deleting, or adding future transactions (`step > step(T)`) must not alter feature values for transaction $T$.
- **Verification**: Evaluates features for transaction $T$ at step 2. Then drastically modifies future transactions at step 3 and 4 (amounts set to extreme values). Recomputes features. Asserts that all features for $T$ match within $10^{-9}$ tolerance.
- **Test Function**: `test_future_transaction_invariance`

### Test 5: Same-Entity Future Modification Invariance (Correction 6)
- **Objective**: Modifying future transactions belonging to the *same entity* as transaction $T$ must not alter features for $T$.
- **Verification**: Entity `M_DEST_1` transacts at step 1 and step 3. Modifies the step 3 transaction for `M_DEST_1`. Recomputes features. Asserts that step 1 features for `M_DEST_1` remain bitwise identical.
- **Test Function**: `test_same_entity_future_invariance`

### Test 6: Cross-Entity Future Modification Invariance (Correction 6)
- **Objective**: Modifying future transactions belonging to a *different entity* from transaction $T$ must not alter features for $T$.
- **Verification**: Modifies transaction at step 2 for entity `C_DEST_2`. Asserts that step 1 features for entity `M_DEST_1` remain bitwise identical.
- **Test Function**: `test_cross_entity_future_invariance`

### Test 7: Pipeline Determinism
- **Objective**: Feature generation must be 100% deterministic and reproducible across multiple runs on identical input data.
- **Verification**: Asserts `pd.testing.assert_frame_equal(pipeline.transform(df), pipeline.transform(df))` passes with zero tolerance.
- **Test Function**: `test_pipeline_determinism`

---

## 3. Automated Feature Quality Validation Suite

Implemented in `src/features/validator.py` and tested in `tests/test_feature_validator.py`:
- **Row Count Preservation**: Asserts output rows equal input rows exactly.
- **Null Value Rejection**: Raises errors if any feature column contains NaNs or missing cells.
- **Infinite Value Rejection**: Raises errors if floating-point division produces `+inf` or `-inf`.
- **Constant Feature Detection**: Flags warnings for features with 0 variance.
- **Critical Leakage Detection**: Raises fatal exception if any excluded post-event column is detected in features.
