"""
Model Evaluation and Error Analysis module.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


class ModelEvaluator:
    """
    Computes comprehensive binary classification metrics and domain-specific error analysis.
    """

    @staticmethod
    def evaluate_predictions(
        y_true: pd.Series,
        y_prob: np.ndarray,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Compute standard fraud risk metrics at a given decision threshold.
        """
        y_true = np.asarray(y_true).astype(int)
        y_prob = np.asarray(y_prob).astype(float)
        y_pred = (y_prob >= threshold).astype(int)

        # ROC-AUC & PR-AUC
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = 0.5

        try:
            pr_auc = float(average_precision_score(y_true, y_prob))
        except Exception:
            pr_auc = float(y_true.mean())

        # Classification metrics at threshold
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = [int(v) for v in cm.ravel()]
        else:
            tn, fp, fn, tp = 0, 0, 0, 0
            if len(np.unique(y_true)) == 1 and y_true[0] == 0:
                tn = int((y_pred == 0).sum())
                fp = int((y_pred == 1).sum())
            elif len(np.unique(y_true)) == 1 and y_true[0] == 1:
                tp = int((y_pred == 1).sum())
                fn = int((y_pred == 0).sum())

        # Rates
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        # Probabilistic losses
        brier = float(brier_score_loss(y_true, y_prob))
        try:
            ll = float(log_loss(y_true, y_prob, eps=1e-15))
        except Exception:
            ll = 0.0

        return {
            "threshold": round(threshold, 4),
            "total_samples": int(len(y_true)),
            "positive_prevalence_pct": round(float(y_true.mean() * 100), 5),
            "roc_auc": round(roc_auc, 5),
            "pr_auc": round(pr_auc, 5),
            "precision": round(prec, 5),
            "recall": round(rec, 5),
            "f1_score": round(f1, 5),
            "fpr": round(fpr, 6),
            "specificity": round(specificity, 5),
            "brier_score": round(brier, 6),
            "log_loss": round(ll, 5),
            "confusion_matrix": {
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "true_positives": tp,
            },
        }

    @staticmethod
    def perform_error_analysis(
        X: pd.DataFrame,
        y_true: pd.Series,
        y_prob: np.ndarray,
        threshold: float,
    ) -> Dict[str, Any]:
        """
        Segment-level diagnostic analysis on false positives and false negatives.
        """
        y_true = np.asarray(y_true).astype(int)
        y_prob = np.asarray(y_prob).astype(float)
        y_pred = (y_prob >= threshold).astype(int)

        fp_mask = (y_true == 0) & (y_pred == 1)
        fn_mask = (y_true == 1) & (y_pred == 0)

        n_fp = int(fp_mask.sum())
        n_fn = int(fn_mask.sum())

        fp_samples = []
        if n_fp > 0:
            fp_df = X.loc[fp_mask].copy()
            fp_df["prob"] = y_prob[fp_mask]
            for _, r in fp_df.head(10).iterrows():
                fp_samples.append({
                    "prob": round(float(r.get("prob", 0.0)), 4),
                    "amount": float(r.get("amount", 0.0)),
                    "oldbalanceOrg": float(r.get("oldbalanceOrg", 0.0)),
                    "is_transfer": int(r.get("is_transfer", 0)),
                    "is_cash_out": int(r.get("is_cash_out", 0)),
                    "is_full_balance_drain": int(r.get("is_full_balance_drain", 0)),
                    "dest_prior_tx_count": int(r.get("dest_prior_tx_count", 0)),
                })

        fn_samples = []
        if n_fn > 0:
            fn_df = X.loc[fn_mask].copy()
            fn_df["prob"] = y_prob[fn_mask]
            for _, r in fn_df.head(10).iterrows():
                fn_samples.append({
                    "prob": round(float(r.get("prob", 0.0)), 4),
                    "amount": float(r.get("amount", 0.0)),
                    "oldbalanceOrg": float(r.get("oldbalanceOrg", 0.0)),
                    "is_transfer": int(r.get("is_transfer", 0)),
                    "is_cash_out": int(r.get("is_cash_out", 0)),
                    "is_full_balance_drain": int(r.get("is_full_balance_drain", 0)),
                    "dest_prior_tx_count": int(r.get("dest_prior_tx_count", 0)),
                })

        # Channel breakdown for errors
        channel_errors = {}
        for channel_col in ["is_transfer", "is_cash_out", "is_payment", "is_cash_in", "is_debit"]:
            if channel_col in X.columns:
                ch_mask = X[channel_col] == 1
                ch_total = int(ch_mask.sum())
                ch_fn = int((fn_mask & ch_mask).sum())
                ch_fp = int((fp_mask & ch_mask).sum())
                channel_errors[channel_col] = {
                    "total": ch_total,
                    "false_negatives": ch_fn,
                    "false_positives": ch_fp,
                }

        return {
            "false_positive_count": n_fp,
            "false_negative_count": n_fn,
            "channel_error_breakdown": channel_errors,
            "sample_false_positives": fp_samples,
            "sample_false_negatives": fn_samples,
        }
