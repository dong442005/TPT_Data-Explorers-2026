# Implementation Details

This directory contains the pipeline implementation broken down by phases.
Scripts are designed to be run from the repository root.

### Structure
- `phase0_discovery_audit`: Initial data quality audits.
- `phase1_data_foundation`: Core verification, aggregations, and raw CSV reconciliations.
- `phase2_feature_store`: Feature engineering and alignments (Track 1 & Track 3).
- `phase3_modeling`: Experiments and baselines.
- `shared`: Configurations and utilities.

### How to Run
Always execute scripts from the root directory:
```bash
python implement/phase1_data_foundation/phase1a_verification/scripts/verify_phase1a.py
```
