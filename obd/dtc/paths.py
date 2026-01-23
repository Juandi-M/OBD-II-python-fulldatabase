from pathlib import Path


def project_root() -> Path:
    # obd/dtc/paths.py -> parents[2] = repo root
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return project_root() / "data"
