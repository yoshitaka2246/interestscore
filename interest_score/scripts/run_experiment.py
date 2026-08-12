"""複数configを一括実行し、比較用サマリを出力するExperiment Runner(Phase 2)。

使い方:
    python scripts/run_experiment.py --experiment experiments/score_weight_sweep.yaml

実験定義YAML(experiments/*.yaml)の形式:
    name: score_weight_sweep
    video: data/raw/sample01.mp4
    configs:
      - configs/default.yaml
      - configs/experiments/dwell_heavy.yaml

各configについて通常のVideoPipelineをそのまま実行し、`results/<run_id>/`一式を出力する
(単発実行との差分はない)。加えて、全run分のInteres Scoreを比較できるサマリCSVを
`results/experiment_<name>_<timestamp>/summary.csv` に出力する。
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import yaml

from interest_estimation.pipeline.video_pipeline import VideoPipeline
from interest_estimation.utils.config import load_config

SUMMARY_FIELDNAMES = [
    "config",
    "run_id",
    "num_tracks",
    "num_frames",
    "mean_score",
    "max_score",
    "min_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="複数configの一括実行(Experiment Runner)")
    parser.add_argument("--experiment", required=True, help="実験定義YAMLへのパス")
    parser.add_argument("--results-root", default="results", help="結果出力先ルート")
    return parser.parse_args()


def load_experiment(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_scores(persons_csv: Path) -> list[float]:
    if not persons_csv.exists():
        return []
    with persons_csv.open(encoding="utf-8") as f:
        return [float(row["interest_score"]) for row in csv.DictReader(f)]


def main() -> None:
    args = parse_args()
    experiment = load_experiment(args.experiment)

    experiment_name = experiment["name"]
    video = experiment["video"]
    config_paths: list[str] = experiment["configs"]

    rows = []
    for config_path in config_paths:
        config = load_config(config_path)
        result = VideoPipeline(config).run(video, results_root=args.results_root)

        scores = read_scores(result.run_dir / "persons.csv")
        rows.append(
            {
                "config": config_path,
                "run_id": result.run_dir.name,
                "num_tracks": result.num_tracks,
                "num_frames": result.num_frames,
                "mean_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
                "max_score": round(max(scores), 2) if scores else 0.0,
                "min_score": round(min(scores), 2) if scores else 0.0,
            }
        )
        print(f"完了: {config_path} -> {result.run_dir.name}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_dir = Path(args.results_root) / f"experiment_{experiment_name}_{timestamp}"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "summary.csv"

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n実験完了: {summary_path}")


if __name__ == "__main__":
    main()
