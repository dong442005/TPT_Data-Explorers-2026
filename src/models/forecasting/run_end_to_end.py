# implement/run_end_to_end.py
"""
End-to-end pipeline runner for Data Explorers project.

This script orchestrates the approved pipeline steps:
- Phase 1C: raw CSV reconciliation, metadata build, aggregation rebuild
- Phase 2A: Track 1 feature store generation and alignment
- Phase 3: audits, baselines, ML experiment, color forecast, dealer ranking

It does NOT discover arbitrary scripts. It only runs the approved scripts listed
in PIPELINE_STEPS.

Usage:
    python implement/run_end_to_end.py --dry-run
    python implement/run_end_to_end.py --allow-modeling --allow-overwrite
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[3]

RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
FEATURES_DIR = ROOT_DIR / "data" / "features"
CONFIG_DIR = ROOT_DIR / "data" / "metadata"
OUTPUTS_DIR = ROOT_DIR / "outputs"
AUDIT_DIR = OUTPUTS_DIR / "audit"
MODELING_DIR = OUTPUTS_DIR / "modeling"

RUN_LOG_DIR = AUDIT_DIR / "runs"


# ---------------------------------------------------------------------
# Required source-of-truth files
# ---------------------------------------------------------------------

REQUIRED_RAW_FILES = [
    RAW_DATA_DIR / "customer.csv",
    RAW_DATA_DIR / "email_log.csv",
    RAW_DATA_DIR / "fact_sales.csv",
    RAW_DATA_DIR / "order_line.csv",
    RAW_DATA_DIR / "product.csv",
    RAW_DATA_DIR / "product_group.csv",
    RAW_DATA_DIR / "product_line.csv",
    RAW_DATA_DIR / "product_price.csv",
    RAW_DATA_DIR / "province_clean.csv",
    RAW_DATA_DIR / "sales_order.csv",
]


# ---------------------------------------------------------------------
# Pipeline step definitions
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineStep:
    stage: str
    name: str
    script: Path
    allow_modeling: bool = False
    required_outputs: tuple[Path, ...] = ()


PIPELINE_STEPS = [
    PipelineStep(
        stage="phase1c",
        name="Raw CSV reconciliation audit",
        script=ROOT_DIR / "src/models/forecasting/phase1_data_foundation/phase1c_raw_csv_reconciliation/scripts/phase1c_audit_reconcile.py",
        required_outputs=(
            AUDIT_DIR / "phase1c_raw_csv_reconciliation_report.md",
        ),
    ),
    PipelineStep(
        stage="phase1c",
        name="Build clean product metadata",
        script=ROOT_DIR / "src/models/forecasting/phase1_data_foundation/phase1c_raw_csv_reconciliation/scripts/phase1c_build_metadata.py",
        required_outputs=(
            CONFIG_DIR / "product_metadata.parquet",
            CONFIG_DIR / "product_hierarchy_mapping.csv",
        ),
    ),
    PipelineStep(
        stage="phase1c",
        name="Rebuild monthly and weekly aggregations",
        script=ROOT_DIR / "src/models/forecasting/phase1_data_foundation/phase1c_raw_csv_reconciliation/scripts/build_phase1c_aggregations.py",
        required_outputs=(
            ROOT_DIR / "data/interim/fact_sales_monthly.parquet",
            ROOT_DIR / "data/interim/fact_sales_weekly.parquet",
        ),
    ),
    PipelineStep(
        stage="phase2a",
        name="Build Track 1 feature stores",
        script=ROOT_DIR / "src/models/forecasting/phase2_feature_store/track1_features/scripts/build_phase2a_features.py",
        required_outputs=(
            FEATURES_DIR / "track1_monthly_model_panel.parquet",
            FEATURES_DIR / "track1_weekly_model_panel.parquet",
            FEATURES_DIR / "track1_monthly_future_q2_rows.parquet",
            FEATURES_DIR / "track1_weekly_future_q2_rows.parquet",
            CONFIG_DIR / "feature_registry_track1.json",
            CONFIG_DIR / "track1_model_feature_sets.json",
        ),
    ),
    PipelineStep(
        stage="phase2a",
        name="Align Track 1 train and future features",
        script=ROOT_DIR / "src/models/forecasting/phase2_feature_store/track1_features/scripts/align_track1_features.py",
        required_outputs=(
            FEATURES_DIR / "track1_monthly_train_aligned.parquet",
            FEATURES_DIR / "track1_monthly_future_aligned.parquet",
            FEATURES_DIR / "track1_weekly_train_aligned.parquet",
            FEATURES_DIR / "track1_weekly_future_aligned.parquet",
        ),
    ),
    PipelineStep(
        stage="phase3",
        name="Phase 3 data audit",
        script=ROOT_DIR / "src/models/forecasting/phase3_modeling/phase3a_data_audit.py",
        allow_modeling=True,
        required_outputs=(
            AUDIT_DIR / "phase3_data_audit_report.md",
        ),
    ),
    PipelineStep(
        stage="phase3",
        name="Phase 3 cross-gap lag audit",
        script=ROOT_DIR / "src/models/forecasting/phase3_modeling/phase3a_bis_audit.py",
        allow_modeling=True,
        required_outputs=(
            AUDIT_DIR / "phase3a_bis_script_lineage_report.md",
        ),
    ),
    PipelineStep(
        stage="phase3",
        name="Track 1 core baselines and Group-Share forecast",
        script=ROOT_DIR / "src/models/forecasting/phase3_modeling/phase3b_core_baselines.py",
        allow_modeling=True,
        required_outputs=(
            MODELING_DIR / "phase3_group_share_forecast_q2_2026.csv",
            MODELING_DIR / "phase3_scenario_summary_q2_2026.csv",
            MODELING_DIR / "phase3_baseline_comparison.csv",
        ),
    ),
    PipelineStep(
        stage="phase3",
        name="Track 1 ML baseline / LightGBM experiment",
        script=ROOT_DIR / "src/models/forecasting/phase3_modeling/phase3c_ml_baseline.py",
        allow_modeling=True,
        required_outputs=(
            MODELING_DIR / "phase3c_ml_model_comparison.csv",
            MODELING_DIR / "phase3c_ml_forecast_q2_2026.csv",
            MODELING_DIR / "phase3c_ml_feature_importance.csv",
        ),
    ),
    PipelineStep(
        stage="phase3",
        name="Track 2 color forecast",
        script=ROOT_DIR / "src/models/forecasting/phase3_modeling/phase3f_color_forecast.py",
        allow_modeling=True,
        required_outputs=(
            MODELING_DIR / "phase3_color_summary_q2_2026.csv",
            MODELING_DIR / "phase3_color_forecast_q2_2026.csv",
        ),
    ),
    PipelineStep(
        stage="phase3",
        name="Track 3 dealer activity ranking",
        script=ROOT_DIR / "src/models/forecasting/phase3_modeling/phase3g_track3_dealer_activity.py",
        allow_modeling=True,
        required_outputs=(
            MODELING_DIR / "phase3_dealer_priority_ranking_q2_2026.csv",
            MODELING_DIR / "phase3_dealer_classifier_metrics.csv",
        ),
    ),
]


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def get_git_status_short() -> str | None:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def assert_files_exist(files: Iterable[Path], label: str) -> None:
    missing = [str(p.relative_to(ROOT_DIR)) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing {label} files:\n" + "\n".join(f"- {m}" for m in missing)
        )


def ensure_output_dirs() -> None:
    for path in [OUTPUTS_DIR, AUDIT_DIR, MODELING_DIR, RUN_LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def run_script(script: Path, env: dict[str, str]) -> dict:
    start = time.time()

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT_DIR,
        env=env,
        text=True,
        capture_output=True,
    )

    elapsed = round(time.time() - start, 2)

    return {
        "script": str(script.relative_to(ROOT_DIR)),
        "returncode": result.returncode,
        "elapsed_seconds": elapsed,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def validate_step_outputs(step: PipelineStep) -> list[str]:
    missing = []
    for out in step.required_outputs:
        if not out.exists():
            missing.append(str(out.relative_to(ROOT_DIR)))
    return missing


# ---------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Run approved E2E pipeline.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned steps and validate file paths, but do not run scripts.",
    )
    parser.add_argument(
        "--allow-modeling",
        action="store_true",
        help="Allow Phase 3 scripts to run. Without this flag, modeling steps are skipped.",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Acknowledge that output files may be overwritten by downstream scripts.",
    )
    parser.add_argument(
        "--stop-after",
        choices=["phase1c", "phase2a", "phase3"],
        default=None,
        help="Stop after a specific stage.",
    )

    args = parser.parse_args()

    ensure_output_dirs()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest_path = RUN_LOG_DIR / f"end_to_end_run_manifest_{run_id}.json"

    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "42"
    env["PYTHONIOENCODING"] = "utf-8"
    env["DATA_EXPLORERS_RUN_ID"] = run_id
    env["DATA_EXPLORERS_ALLOW_OVERWRITE"] = "1" if args.allow_overwrite else "0"

    manifest = {
        "run_id": run_id,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "root_dir": str(ROOT_DIR),
        "git_commit": get_git_commit(),
        "git_status_short_before": get_git_status_short(),
        "dry_run": args.dry_run,
        "allow_modeling": args.allow_modeling,
        "allow_overwrite": args.allow_overwrite,
        "raw_files": [],
        "steps": [],
        "final_status": "UNKNOWN",
    }

    try:
        assert_files_exist(REQUIRED_RAW_FILES, "raw source-of-truth")

        for raw_file in REQUIRED_RAW_FILES:
            manifest["raw_files"].append({
                "path": str(raw_file.relative_to(ROOT_DIR)),
                "sha256": sha256_file(raw_file),
                "size_bytes": raw_file.stat().st_size,
            })

        script_files = [step.script for step in PIPELINE_STEPS]
        assert_files_exist(script_files, "pipeline script")

        print("\n=== Planned Pipeline Steps ===")
        for i, step in enumerate(PIPELINE_STEPS, start=1):
            skip = step.allow_modeling and not args.allow_modeling
            status = "SKIP unless --allow-modeling" if skip else "RUN"
            print(f"{i:02d}. [{status}] {step.stage} | {step.name}")
            print(f"    {step.script.relative_to(ROOT_DIR)}")

        if args.dry_run:
            manifest["final_status"] = "DRY_RUN_PASS"
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\nDry run passed. Manifest saved to: {manifest_path.relative_to(ROOT_DIR)}")
            return 0

        if not args.allow_overwrite:
            raise RuntimeError(
                "Refusing to run without --allow-overwrite. "
                "This protects existing outputs from accidental overwrite."
            )

        for step in PIPELINE_STEPS:
            if step.allow_modeling and not args.allow_modeling:
                manifest["steps"].append({
                    **asdict(step),
                    "script": str(step.script.relative_to(ROOT_DIR)),
                    "status": "SKIPPED_MODELING_NOT_ALLOWED",
                })
                continue

            print(f"\n=== Running: {step.stage} | {step.name} ===")
            result = run_script(step.script, env)

            step_record = {
                **asdict(step),
                "script": str(step.script.relative_to(ROOT_DIR)),
                "required_outputs": [str(p.relative_to(ROOT_DIR)) for p in step.required_outputs],
                "run_result": result,
            }

            if result["returncode"] != 0:
                step_record["status"] = "FAILED"
                manifest["steps"].append(step_record)
                manifest["final_status"] = "FAILED"
                manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
                print(result["stdout_tail"])
                print(result["stderr_tail"], file=sys.stderr)
                print(f"\nFAILED at step: {step.name}")
                print(f"Manifest saved to: {manifest_path.relative_to(ROOT_DIR)}")
                return result["returncode"]

            missing_outputs = validate_step_outputs(step)
            if missing_outputs:
                step_record["status"] = "FAILED_MISSING_OUTPUTS"
                step_record["missing_outputs"] = missing_outputs
                manifest["steps"].append(step_record)
                manifest["final_status"] = "FAILED"
                manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"Missing expected outputs after step {step.name}:")
                for p in missing_outputs:
                    print(f"- {p}")
                return 1

            step_record["status"] = "PASS"
            manifest["steps"].append(step_record)

            if args.stop_after and step.stage == args.stop_after:
                print(f"\nStopping after requested stage: {args.stop_after}")
                break

        manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
        manifest["git_status_short_after"] = get_git_status_short()
        manifest["final_status"] = "PASS"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"\nEnd-to-end pipeline completed successfully.")
        print(f"Run manifest saved to: {manifest_path.relative_to(ROOT_DIR)}")
        return 0

    except Exception as exc:
        manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
        manifest["final_status"] = "FAILED_PRECHECK_OR_EXCEPTION"
        manifest["error"] = repr(exc)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nERROR: {exc}", file=sys.stderr)
        print(f"Manifest saved to: {manifest_path.relative_to(ROOT_DIR)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
