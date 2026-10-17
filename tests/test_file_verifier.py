"""
Tests for file verification and read-only integrity check.
"""

from pathlib import Path
from src.audit.file_verifier import compute_sha256, verify_file, verify_read_only_integrity


def test_verify_file_success(synthetic_csv_file):
    info = verify_file(synthetic_csv_file)
    assert info["exists"] is True
    assert info["read_success"] is True
    assert info["row_count"] == 10
    assert info["column_count"] == 11
    assert info["malformed_rows"] == 0
    assert info["sha256"] is not None
    assert len(info["sha256"]) == 64


def test_verify_file_not_found():
    info = verify_file("non_existent_file.csv")
    assert info["exists"] is False
    assert info["read_success"] is False
    assert info["row_count"] == 0
    assert "File not found" in info["error"]


def test_read_only_integrity_pass(synthetic_csv_file):
    baseline = verify_file(synthetic_csv_file)
    is_intact, msg = verify_read_only_integrity(synthetic_csv_file, baseline)
    assert is_intact is True
    assert "identical" in msg


def test_read_only_integrity_fail_on_modification(synthetic_csv_file):
    baseline = verify_file(synthetic_csv_file)

    # Simulate modification
    with open(synthetic_csv_file, "a") as f:
        f.write("\n99,PAYMENT,1.0,C999,0,0,M999,0,0,0,0")

    is_intact, msg = verify_read_only_integrity(synthetic_csv_file, baseline)
    assert is_intact is False
    assert "mismatch" in msg or "size changed" in msg
