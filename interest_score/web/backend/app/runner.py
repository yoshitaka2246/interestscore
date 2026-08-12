"""動画処理をバックグラウンドスレッドで実行する。

DBを使わず、`results/<run_id>/` の中身(metadata.json / error.txtの有無)を
実行状態のソースオブトゥルースとする。Celery等のジョブキューは導入しない方針
(interest_score/CLAUDE.md参照)のため、標準threadingで十分とする。
"""
from __future__ import annotations

import logging
import threading
import traceback
from pathlib import Path

from interest_estimation.experiment.result_writer import create_run_dir
from interest_estimation.pipeline.video_pipeline import VideoPipeline
from interest_estimation.utils.config import AppConfig

logger = logging.getLogger("interest_estimation.web")


def start_run(config: AppConfig, video_path: Path, results_root: Path) -> str:
    run_dir = create_run_dir(results_root, config.experiment.name)

    def _target() -> None:
        try:
            VideoPipeline(config).run(video_path, run_dir=run_dir)
        except Exception:
            (run_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            logger.exception("run failed: %s", run_dir.name)

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    return run_dir.name


def get_run_status(run_dir: Path) -> str:
    if (run_dir / "error.txt").exists():
        return "failed"
    if (run_dir / "metadata.json").exists():
        return "done"
    return "running"
