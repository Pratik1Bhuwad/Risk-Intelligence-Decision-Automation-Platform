"""
Pytest configuration and synthetic PaySim fixtures.
"""

import os
import tempfile
import pandas as pd
import pytest
from src.config import AuditConfig


@pytest.fixture
def synthetic_df() -> pd.DataFrame:
    """
    Generate a small synthetic PaySim-like DataFrame for testing.
    Includes normal, fraud, edge cases, zero balances, and string markers.
    """
    data = {
        "step": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
        "type": [
            "PAYMENT",
            "TRANSFER",
            "CASH_OUT",
            "PAYMENT",
            "TRANSFER",
            "DEBIT",
            "CASH_IN",
            "TRANSFER",
            "CASH_OUT",
            "PAYMENT",
        ],
        "amount": [
            100.0,
            50000.0,
            50000.0,
            25.5,
            250000.0,
            150.0,
            1000.0,
            300000.0,
            300000.0,
            45.0,
        ],
        "nameOrig": [
            "C10001",
            "C10002",
            "C10003",
            "C10004",
            "C10005",
            "C10006",
            "C10007",
            "C10008",
            "C10009",
            "C10001",  # Repeat originator for testing repeat metrics
        ],
        "oldbalanceOrg": [
            200.0,
            50000.0,
            50000.0,
            100.0,
            250000.0,
            500.0,
            0.0,
            300000.0,
            300000.0,
            100.0,
        ],
        "newbalanceOrig": [
            100.0,
            0.0,
            0.0,
            74.5,
            0.0,
            350.0,
            1000.0,
            0.0,
            0.0,
            55.0,
        ],
        "nameDest": [
            "M20001",
            "C30001",
            "C30002",
            "M20001",  # Repeat destination
            "C30003",
            "M20002",
            "C30004",
            "C30005",
            "C30006",
            "M20003",
        ],
        "oldbalanceDest": [
            0.0,
            0.0,
            10000.0,
            0.0,
            5000.0,
            0.0,
            2000.0,
            0.0,
            50000.0,
            0.0,
        ],
        "newbalanceDest": [
            0.0,
            0.0,
            60000.0,
            0.0,
            255000.0,
            0.0,
            1000.0,
            0.0,
            350000.0,
            0.0,
        ],
        "isFraud": [0, 1, 1, 0, 1, 0, 0, 1, 1, 0],
        "isFlaggedFraud": [0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def synthetic_csv_file(synthetic_df: pd.DataFrame, tmp_path):
    """Save synthetic dataframe to a temporary CSV file."""
    csv_file = tmp_path / "test_paysim.csv"
    synthetic_df.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def test_config(synthetic_csv_file, tmp_path) -> AuditConfig:
    """Provide an AuditConfig targeting the synthetic CSV file and a temp output dir."""
    output_dir = tmp_path / "test_audit_output"
    output_dir.mkdir(exist_ok=True)
    return AuditConfig(
        dataset="test_paysim",
        data_path=synthetic_csv_file,
        output_dir=str(output_dir),
        mode="full",
    )
