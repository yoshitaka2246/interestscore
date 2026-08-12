"""アプリ全体で使うファイルパスの定義。DB不使用で、これらのディレクトリを直接読み書きする。"""
from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
RESULTS_DIR = ROOT_DIR / "results"
CONFIGS_DIR = ROOT_DIR / "configs"

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
