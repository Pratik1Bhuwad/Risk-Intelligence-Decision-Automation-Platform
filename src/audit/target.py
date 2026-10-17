"""
Target distribution and stratification audit module.
"""

import pandas as pd
from src.config import AuditConfig


def audit_target(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """
    Audit target variable (isFraud) distribution overall, stratified by transaction type,
    and compared with baseline rule flag (isFlaggedFraud).
    """
    records = []
    total_rows = len(df)

    target_col = (
        config.target_cols[0]
        if config.target_cols and config.target_cols[0] in df.columns
        else None
    )
    if not target_col:
        return pd.DataFrame()

    # 1. Overall Target Distribution
    target_counts = df[target_col].value_counts()
    fraud_cnt = int(target_counts.get(1, 0))
    non_fraud_cnt = int(target_counts.get(0, 0))
    fraud_rate = (
        round(fraud_cnt / total_rows * 100.0, 5) if total_rows > 0 else 0.0
    )

    records.append(
        {
            "analysis_level": "OVERALL",
            "group_name": "ALL_TRANSACTIONS",
            "total_count": total_rows,
            "fraud_count": fraud_cnt,
            "non_fraud_count": non_fraud_cnt,
            "fraud_rate_pct": fraud_rate,
            "notes": f"Overall fraud prevalence: {fraud_rate}%. Extremely imbalanced class distribution.",
            "status": "CONFIRMED",
        }
    )

    # 2. Breakdown by Transaction Type
    type_col = (
        config.categorical_cols[0]
        if config.categorical_cols and config.categorical_cols[0] in df.columns
        else None
    )
    if type_col:
        for tx_type, group in df.groupby(type_col, observed=True):
            sub_total = len(group)
            sub_fraud = int((group[target_col] == 1).sum())
            sub_non_fraud = sub_total - sub_fraud
            sub_rate = (
                round(sub_fraud / sub_total * 100.0, 5) if sub_total > 0 else 0.0
            )

            records.append(
                {
                    "analysis_level": "TRANSACTION_TYPE",
                    "group_name": str(tx_type),
                    "total_count": sub_total,
                    "fraud_count": sub_fraud,
                    "non_fraud_count": sub_non_fraud,
                    "fraud_rate_pct": sub_rate,
                    "notes": (
                        "Fraud observed in this transaction type."
                        if sub_fraud > 0
                        else "Zero fraud instances observed in this transaction type."
                    ),
                    "status": "CONFIRMED",
                }
            )

    # 3. Target vs FlaggedFraud Comparison
    flag_col = (
        config.flag_cols[0]
        if config.flag_cols and config.flag_cols[0] in df.columns
        else None
    )
    if flag_col:
        flagged_cnt = int((df[flag_col] == 1).sum())
        flagged_fraud_cnt = int(
            ((df[flag_col] == 1) & (df[target_col] == 1)).sum()
        )
        flagged_non_fraud_cnt = flagged_cnt - flagged_fraud_cnt
        flagged_rate = (
            round(flagged_cnt / total_rows * 100.0, 6)
            if total_rows > 0
            else 0.0
        )

        records.append(
            {
                "analysis_level": "RULE_FLAG_COMPARISON",
                "group_name": f"{flag_col} == 1",
                "total_count": flagged_cnt,
                "fraud_count": flagged_fraud_cnt,
                "non_fraud_count": flagged_non_fraud_cnt,
                "fraud_rate_pct": (
                    round(flagged_fraud_cnt / flagged_cnt * 100.0, 4)
                    if flagged_cnt > 0
                    else 0.0
                ),
                "notes": (
                    f"Baseline rule {flag_col} flagged {flagged_cnt} transactions ({flagged_rate}% of all data). "
                    f"Of flagged transactions, {flagged_fraud_cnt} were actual fraud and {flagged_non_fraud_cnt} were false alarms."
                ),
                "status": "OBSERVED",
            }
        )

    return pd.DataFrame(records)
