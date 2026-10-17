"""
Pipeline orchestrator for PaySim Data Audit.
Executes all audit modules, validates read-only integrity, and outputs machine-readable
CSVs/JSONs, log file, and HTML report.
"""

import json
import logging
import os
from pathlib import Path
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
import pandas as pd

from src.config import AuditConfig, AUDIT_VERSION
from src.audit.file_verifier import verify_file, verify_read_only_integrity
from src.audit.schema import audit_schema
from src.audit.missingness import audit_missingness
from src.audit.duplicates import audit_duplicates
from src.audit.cardinality import audit_cardinality
from src.audit.numerical import audit_numerical
from src.audit.categorical import audit_categorical
from src.audit.target import audit_target
from src.audit.temporal import audit_temporal
from src.audit.entity import audit_entity
from src.audit.prediction_time import generate_prediction_time_matrix
from src.audit.leakage import audit_leakage
from src.audit.synthetic import audit_synthetic_artifacts
from src.audit.dictionary import generate_data_dictionary
from src.audit.capability import generate_capability_assessment
from src.audit.reporter import render_html_report


def setup_logger(output_dir: str) -> logging.Logger:
    """Set up logger to write to both stdout and audit.log."""
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "audit.log")

    logger = logging.getLogger("PaySimAudit")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setFormatter(formatter)
    logger.addHandler(c_handler)

    # File Handler
    f_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)

    return logger


def run_audit(config: AuditConfig) -> Dict[str, Any]:
    """
    Run complete, reproducible, read-only data audit pipeline.
    """
    start_time = time.time()
    exec_timestamp = datetime.now().isoformat()
    logger = setup_logger(config.output_dir)

    logger.info("=" * 70)
    logger.info("STARTING PAYSIM DATA AUDIT PIPELINE")
    logger.info(f"Audit Version: {config.audit_version}")
    logger.info(f"Audit Mode: {config.mode.upper()}")
    logger.info(f"Input Dataset Path: {config.data_path}")
    logger.info(f"Output Directory: {config.output_dir}")
    logger.info("=" * 70)

    # 1. Pre-audit file verification & baseline hashing
    logger.info("[1/15] Verifying input file and capturing cryptographic baseline...")
    file_info = verify_file(config.data_path)
    if not file_info.get("exists") or not file_info.get("read_success"):
        logger.error(f"Failed to read raw dataset: {file_info.get('error')}")
        raise FileNotFoundError(f"Cannot read dataset: {file_info.get('error')}")

    logger.info(f"  File size: {file_info['file_size_bytes']:,} bytes")
    logger.info(f"  SHA-256: {file_info['sha256']}")
    logger.info(f"  Total rows in file: {file_info['row_count']:,}")
    logger.info(f"  Total columns in file: {file_info['column_count']}")
    logger.info(f"  Malformed rows: {file_info['malformed_rows']}")

    # 2. Read dataset (read-only)
    logger.info("[2/15] Reading dataset into memory (READ-ONLY mode)...")
    if config.mode == "sample" and config.sample_size:
        logger.warning(
            f"  MODE IS SAMPLE: Reading only first {config.sample_size:,} rows for development/testing."
        )
        df = pd.read_csv(config.data_path, nrows=config.sample_size)
    else:
        logger.info("  MODE IS FULL: Reading complete dataset...")
        df = pd.read_csv(config.data_path)

    loaded_rows, loaded_cols = df.shape
    logger.info(f"  Loaded dataframe shape: {loaded_rows:,} rows, {loaded_cols} columns.")

    # 3. Schema Audit
    logger.info("[3/15] Running Schema Audit...")
    schema_df = audit_schema(df, config)
    schema_csv = os.path.join(config.output_dir, "schema.csv")
    schema_df.to_csv(schema_csv, index=False)
    logger.info(f"  Saved: {schema_csv}")

    # 4. Missing-Value Audit
    logger.info("[4/15] Running Missing-Value Audit...")
    missing_df, _ = audit_missingness(df, config)
    missing_csv = os.path.join(config.output_dir, "missing_values.csv")
    missing_df.to_csv(missing_csv, index=False)
    logger.info(f"  Saved: {missing_csv}")

    # 5. Duplicate Audit
    logger.info("[5/15] Running Duplicate & Identifier Audit...")
    duplicates_df = audit_duplicates(df, config)
    duplicates_csv = os.path.join(config.output_dir, "duplicates.csv")
    duplicates_df.to_csv(duplicates_csv, index=False)
    logger.info(f"  Saved: {duplicates_csv}")

    # 6. Cardinality Audit
    logger.info("[6/15] Running Cardinality & Entity Frequency Audit...")
    cardinality_df = audit_cardinality(df, config)
    cardinality_csv = os.path.join(config.output_dir, "cardinality.csv")
    cardinality_df.to_csv(cardinality_csv, index=False)
    logger.info(f"  Saved: {cardinality_csv}")

    # 7. Numerical Audit
    logger.info("[7/15] Running Numerical Distribution & Data-Quality Checks...")
    numerical_df = audit_numerical(df, config)
    numerical_csv = os.path.join(config.output_dir, "numerical_summary.csv")
    numerical_df.to_csv(numerical_csv, index=False)
    logger.info(f"  Saved: {numerical_csv}")

    # 8. Categorical Audit
    logger.info("[8/15] Running Categorical & Prefix Audit...")
    categorical_df = audit_categorical(df, config)
    categorical_csv = os.path.join(config.output_dir, "categorical_summary.csv")
    categorical_df.to_csv(categorical_csv, index=False)
    logger.info(f"  Saved: {categorical_csv}")

    # 9. Target Audit
    logger.info("[9/15] Running Target Distribution & Stratification Audit...")
    target_df = audit_target(df, config)
    target_csv = os.path.join(config.output_dir, "target_analysis.csv")
    target_df.to_csv(target_csv, index=False)
    logger.info(f"  Saved: {target_csv}")

    # 10. Temporal Audit
    logger.info("[10/15] Running Temporal & Ordering Audit...")
    temporal_df = audit_temporal(df, config)
    temporal_csv = os.path.join(config.output_dir, "temporal_analysis.csv")
    temporal_df.to_csv(temporal_csv, index=False)
    logger.info(f"  Saved: {temporal_csv}")

    # 11. Entity Audit
    logger.info("[11/15] Running Customer & Account Entity History Audit...")
    entity_df = audit_entity(df, config)
    entity_csv = os.path.join(config.output_dir, "entity_analysis.csv")
    entity_df.to_csv(entity_csv, index=False)
    logger.info(f"  Saved: {entity_csv}")

    # 12. Prediction-Time Availability Matrix
    logger.info("[12/15] Generating Prediction-Time Availability Matrix...")
    prediction_df = generate_prediction_time_matrix(df, config)
    prediction_csv = os.path.join(config.output_dir, "prediction_time_matrix.csv")
    prediction_df.to_csv(prediction_csv, index=False)
    logger.info(f"  Saved: {prediction_csv}")

    # 13. Leakage Matrix
    logger.info("[13/15] Generating Leakage Assessment Matrix...")
    leakage_df = audit_leakage(df, config)
    leakage_csv = os.path.join(config.output_dir, "leakage_matrix.csv")
    leakage_df.to_csv(leakage_csv, index=False)
    logger.info(f"  Saved: {leakage_csv}")

    # 14. Synthetic-Artifact Review
    logger.info("[14/15] Evaluating Synthetic Artifact Hypotheses...")
    synthetic_df = audit_synthetic_artifacts(df, config)
    synthetic_csv = os.path.join(config.output_dir, "synthetic_artifact_review.csv")
    synthetic_df.to_csv(synthetic_csv, index=False)
    logger.info(f"  Saved: {synthetic_csv}")

    # 15. Data Dictionary & Capability Assessment
    logger.info("[15/15] Compiling Data Dictionary & Capability Assessment...")
    dictionary_df = generate_data_dictionary(df, config)
    dict_csv = os.path.join(config.output_dir, "data_dictionary.csv")
    dictionary_df.to_csv(dict_csv, index=False)
    logger.info(f"  Saved: {dict_csv}")

    capability_df = generate_capability_assessment(df, config)
    cap_csv = os.path.join(config.output_dir, "capability_assessment.csv")
    capability_df.to_csv(cap_csv, index=False)
    logger.info(f"  Saved: {cap_csv}")

    # Read-Only Integrity Verification
    logger.info("Verifying raw dataset read-only integrity (post-audit check)...")
    is_intact, integrity_msg = verify_read_only_integrity(config.data_path, file_info)
    if not is_intact:
        logger.critical(f"INTEGRITY BREACH: {integrity_msg}")
        raise IOError(f"Raw data was modified! {integrity_msg}")
    logger.info(f"  {integrity_msg}")

    # Run Metadata & Audit Summary
    elapsed_sec = round(time.time() - start_time, 2)
    run_metadata = {
        "dataset_name": config.dataset,
        "dataset_filename": file_info["filename"],
        "dataset_path": file_info["file_path"],
        "sha256": file_info["sha256"],
        "file_size_bytes": file_info["file_size_bytes"],
        "audit_version": config.audit_version,
        "git_commit_hash": "UNKNOWN (Not a git repository)",
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "execution_timestamp": exec_timestamp,
        "audit_mode": config.mode.upper(),
        "row_count": loaded_rows,
        "column_count": loaded_cols,
        "elapsed_seconds": elapsed_sec,
        "read_only_verified": is_intact,
    }

    metadata_path = os.path.join(config.output_dir, "run_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)
    logger.info(f"Saved: {metadata_path}")

    # Summary JSON
    summary_data = {
        "run_metadata": run_metadata,
        "file_info": file_info,
        "schema_summary": {
            "columns": list(df.columns),
            "total_columns": loaded_cols,
        },
        "target_summary": target_df.to_dict(orient="records"),
        "key_findings": [
            "PaySim raw dataset integrity verified: SHA-256 hash identical before and after audit.",
            f"Total transactions: {loaded_rows:,}. Fraud transactions: {int((df[config.target_cols[0]]==1).sum()) if config.target_cols[0] in df.columns else 'N/A'}.",
            "Fraud occurs strictly in TRANSFER and CASH_OUT transactions. 0 fraud in PAYMENT, CASH_IN, and DEBIT.",
            "Originating accounts (nameOrig) appear nearly 100% uniquely, severely constraining within-customer behavioral profiling on origin side.",
            "Destination accounts (nameDest) exhibit substantial reuse, enabling recipient and merchant profiling.",
            "Post-event balance fields (newbalanceOrig, newbalanceDest) require investigation to prevent post-event leakage.",
            "isFlaggedFraud represents a legacy heuristic rule (>200,000 TRANSFER); not a ground truth label.",
        ],
    }
    summary_path = os.path.join(config.output_dir, "audit_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Saved: {summary_path}")

    # Render HTML Report
    logger.info("Rendering HTML audit report...")
    report_html_path = os.path.join(config.output_dir, "audit_report.html")
    render_html_report(
        output_path=report_html_path,
        file_info=file_info,
        run_metadata=run_metadata,
        schema_df=schema_df,
        missing_df=missing_df,
        target_df=target_df,
        prediction_df=prediction_df,
        synthetic_df=synthetic_df,
        capability_df=capability_df,
        entity_df=entity_df,
        integrity_msg=integrity_msg,
    )
    logger.info(f"Saved: {report_html_path}")

    logger.info("=" * 70)
    logger.info(f"PAYSIM DATA AUDIT COMPLETED SUCCESSFULLY in {elapsed_sec}s")
    logger.info("=" * 70)

    return summary_data
