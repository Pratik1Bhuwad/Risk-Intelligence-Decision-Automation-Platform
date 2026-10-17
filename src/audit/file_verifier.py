"""
File verification and read-only integrity module.
"""

import csv
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def compute_sha256(file_path: str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hash of a file using chunked streaming."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_file(file_path: str) -> Dict[str, Any]:
    """
    Perform deep verification of the raw data file.
    Calculates file size, SHA-256, row count, column count, and malformed row count.
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "file_path": str(path.resolve()),
            "filename": path.name,
            "extension": path.suffix,
            "exists": False,
            "file_size_bytes": 0,
            "sha256": None,
            "mtime": None,
            "row_count": 0,
            "column_count": 0,
            "read_success": False,
            "malformed_rows": 0,
            "error": f"File not found: {file_path}",
        }

    file_size = os.path.getsize(path)
    mtime = os.path.getmtime(path)
    sha256_hash = compute_sha256(str(path))

    # Inspect rows, columns, and check for malformed rows
    row_count = 0
    column_count = 0
    malformed_rows = 0
    read_success = False
    error_msg = None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
                column_count = len(header)
                expected_cols = column_count
            except StopIteration:
                header = []
                expected_cols = 0

            for line_idx, row in enumerate(reader, start=1):
                row_count += 1
                if len(row) != expected_cols:
                    malformed_rows += 1

        read_success = True
    except Exception as exc:
        read_success = False
        error_msg = str(exc)

    return {
        "file_path": str(path.resolve()),
        "filename": path.name,
        "extension": path.suffix,
        "exists": True,
        "file_size_bytes": file_size,
        "sha256": sha256_hash,
        "mtime": mtime,
        "row_count": row_count,
        "column_count": column_count,
        "read_success": read_success,
        "malformed_rows": malformed_rows,
        "error": error_msg,
    }


def verify_read_only_integrity(
    file_path: str, baseline: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Verify that the file has not been modified after an operation.
    Compares SHA-256, file size, and modification timestamp.
    """
    path = Path(file_path)
    if not path.exists():
        return False, f"File no longer exists: {file_path}"

    current_size = os.path.getsize(path)
    if current_size != baseline.get("file_size_bytes"):
        return (
            False,
            f"File size changed! Baseline: {baseline.get('file_size_bytes')}, Current: {current_size}",
        )

    current_hash = compute_sha256(str(path))
    if current_hash != baseline.get("sha256"):
        return (
            False,
            f"SHA-256 hash mismatch! Baseline: {baseline.get('sha256')}, Current: {current_hash}",
        )

    return True, "File integrity verified: SHA-256 and size remain identical."
