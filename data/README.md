# PaySim Dataset Documentation

## Overview
- **Dataset Name**: PaySim
- **Expected Raw Filename**: `PaySimData.csv`
- **Raw Dataset Location**: `data/raw/paysim/PaySimData.csv`
- **Source / Reference**: PaySim synthetic financial dataset (Lopez-Rojas et al., simulating mobile money transactions) [Source origin to be confirmed with official documentation]
- **Dataset / License Information**: UNKNOWN (pending official licensing review)
- **Acquisition / Download Date**: UNKNOWN
- **SHA-256 Checksum**: `16910f90577b0d981bf8ff289714510bb89bc71bff7d3f220f024e287e4eea6b`
- **File Size**: `493,534,783` bytes (~470.7 MB)
- **Git Tracking Status**: Gitignored (excluded via `.gitignore` to prevent committing large raw data)

## Raw Data Immutability Rule
The raw dataset in `data/raw/paysim/PaySimData.csv` is strictly **IMMUTABLE** and **READ-ONLY**. 
- No script, pipeline, or audit tool may overwrite, modify, truncate, or rewrite this file.
- All transformations, intermediate files, and audit outputs must be written to external directories (e.g., `audit_output/`, `data/interim/`, `data/processed/`).
- Cryptographic integrity (SHA-256) is checked before and after all audit executions to verify that no bytes have changed.

## How the Audit References the Raw File
The audit engine accesses the dataset in a configuration-driven manner:
- Default path configured in `configs/paysim_audit.yaml` (`data_path: data/raw/paysim/PaySimData.csv`).
- Overridable via CLI argument: `--data <path_to_csv>`.
