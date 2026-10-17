"""
Command-line interface (CLI) for PaySim Data Audit & Feature Engineering Pipeline.
"""

import argparse
import sys
from src.config import AuditConfig, AUDIT_VERSION
from src.audit.pipeline import run_audit
from src.features.pipeline import FeaturePipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PaySim Data Audit and Feature Engineering Pipeline."
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=["audit", "features"],
        default="audit",
        help="Task to execute: 'audit' (default) or 'features'.",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to raw PaySim CSV file.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file (audit or feature engineering).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save audit outputs or processed features.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "sample", "features"],
        default="full",
        help="Execution mode: 'full' for official complete run, 'sample' for development testing.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50000,
        help="Number of rows to read when mode is 'sample'.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"PaySim Platform Pipeline v{AUDIT_VERSION}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Determine whether task is audit or features
    task = args.task
    if args.mode == "features":
        task = "features"

    if task == "features":
        config_path = args.config or "configs/feature_engineering.yaml"
        data_path = args.data or "data/raw/paysim/PaySimData.csv"
        out_dir = args.output_dir or "data/processed"
        nrows = args.sample_size if args.mode == "sample" else None

        pipeline = FeaturePipeline(config_path=config_path)
        try:
            pipeline.run(
                raw_csv_path=data_path,
                output_dir=out_dir,
                nrows=nrows,
                save_csv=True,
                save_parquet=True,
                include_target_label=True,
            )
        except Exception as exc:
            print(f"\n[ERROR] Feature engineering failed: {exc}", file=sys.stderr)
            sys.exit(1)

    else:
        # Default: audit task
        config_path = args.config or "configs/paysim_audit.yaml"
        overrides = {}
        if args.data:
            overrides["data_path"] = args.data
        if args.output_dir:
            overrides["output_dir"] = args.output_dir
        if args.mode in ("full", "sample"):
            overrides["mode"] = args.mode
        if args.sample_size:
            overrides["sample_size"] = args.sample_size

        config = AuditConfig.from_yaml(config_path, overrides=overrides)

        try:
            run_audit(config)
        except Exception as exc:
            print(f"\n[ERROR] Audit execution failed: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
