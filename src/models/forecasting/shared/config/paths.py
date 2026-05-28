import os
from pathlib import Path

current_file = Path(__file__).resolve()
ROOT_DIR = str(current_file.parents[5])

RAW_DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")
INTERIM_DATA_DIR = os.path.join(ROOT_DIR, "data", "interim")
METADATA_DIR = os.path.join(ROOT_DIR, "data", "metadata")
FEATURES_DIR = os.path.join(ROOT_DIR, "data", "features")

CONFIG_DIR = os.path.join(ROOT_DIR, "src", "models", "forecasting", "config")

OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")
MODELING_OUTPUTS_DIR = os.path.join(OUTPUTS_DIR, "modeling")
AUDIT_OUTPUTS_DIR = os.path.join(OUTPUTS_DIR, "audit")

os.makedirs(MODELING_OUTPUTS_DIR, exist_ok=True)
os.makedirs(AUDIT_OUTPUTS_DIR, exist_ok=True)

IMPLEMENT_DIR = os.path.join(ROOT_DIR, "src", "models", "forecasting")
