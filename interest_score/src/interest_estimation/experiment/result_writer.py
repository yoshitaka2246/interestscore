"""実験結果の出力(run_id発行、metadata.json、config.yaml保存)。"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from interest_estimation.utils.config import AppConfig


def create_run_dir(results_root: str | Path, experiment_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{experiment_name}"
    run_dir = Path(results_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _git_commit_hash() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def write_config(run_dir: Path, config: AppConfig) -> None:
    with (run_dir / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(config.model_dump(), f, allow_unicode=True, sort_keys=False)


def write_metadata(run_dir: Path, input_video: str, extra: dict | None = None) -> None:
    metadata = {
        "run_id": run_dir.name,
        "created_at": datetime.now().isoformat(),
        "input_video": str(input_video),
        "git_commit_hash": _git_commit_hash(),
        "python_version": sys.version,
        "platform": platform.platform(),
        **(extra or {}),
    }
    with (run_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
