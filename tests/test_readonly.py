"""
Tests verifying that raw input data files remain strictly read-only and unmodified.
"""

import os
from src.audit.file_verifier import compute_sha256, verify_file, verify_read_only_integrity
from src.audit.pipeline import run_audit


def test_raw_data_never_modified(test_config, synthetic_csv_file):
    # 1. Compute baseline before audit
    baseline_info = verify_file(synthetic_csv_file)
    initial_hash = baseline_info["sha256"]
    initial_size = baseline_info["file_size_bytes"]

    # 2. Run the audit
    run_audit(test_config)

    # 3. Verify integrity post-audit
    post_info = verify_file(synthetic_csv_file)
    assert post_info["sha256"] == initial_hash, "SHA-256 hash changed after audit run!"
    assert post_info["file_size_bytes"] == initial_size, "File size changed after audit run!"

    is_intact, msg = verify_read_only_integrity(synthetic_csv_file, baseline_info)
    assert is_intact is True
    assert "identical" in msg
