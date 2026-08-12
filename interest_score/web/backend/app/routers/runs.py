"""パイプライン実行のトリガー・状態取得API。"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.paths import CONFIGS_DIR, DATA_RAW_DIR, RESULTS_DIR
from app.runner import get_run_status, start_run
from app.schemas import PersonScoreRow, RunDetail, RunSummary, StartRunRequest
from interest_estimation.utils.config import load_config

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=RunSummary)
def create_run(body: StartRunRequest) -> RunSummary:
    video_path = DATA_RAW_DIR / body.video_name
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail=f"動画が見つかりません: {body.video_name}")

    config_path = CONFIGS_DIR / body.config_name
    if not config_path.is_file():
        raise HTTPException(status_code=404, detail=f"configが見つかりません: {body.config_name}")

    config = load_config(config_path)
    run_id = start_run(config, video_path, RESULTS_DIR)
    return RunSummary(run_id=run_id, status="running", input_video=body.video_name)


@router.get("", response_model=list[RunSummary])
def list_runs() -> list[RunSummary]:
    if not RESULTS_DIR.exists():
        return []
    run_dirs = sorted((d for d in RESULTS_DIR.iterdir() if d.is_dir()), reverse=True)
    return [_summarize(run_dir) for run_dir in run_dirs]


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str) -> RunDetail:
    run_dir = RESULTS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="runが見つかりません")

    metadata = None
    metadata_path = run_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    persons: list[PersonScoreRow] = []
    persons_path = run_dir / "persons.csv"
    if persons_path.exists():
        with persons_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                persons.append(
                    PersonScoreRow(
                        track_id=int(row["track_id"]),
                        start_time_sec=float(row["start_time_sec"]),
                        end_time_sec=float(row["end_time_sec"]),
                        dwell_time_raw=float(row["dwell_time_raw"]),
                        speed_raw=float(row["speed_raw"]),
                        interest_score=float(row["interest_score"]),
                    )
                )
    persons.sort(key=lambda p: p.interest_score, reverse=True)

    error_path = run_dir / "error.txt"
    error = error_path.read_text(encoding="utf-8") if error_path.exists() else None

    return RunDetail(
        run_id=run_id,
        status=get_run_status(run_dir),
        metadata=metadata,
        persons=persons,
        has_video=(run_dir / "result.mp4").exists(),
        error=error,
    )


def _summarize(run_dir: Path) -> RunSummary:
    metadata_path = run_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return RunSummary(
            run_id=run_dir.name,
            status=get_run_status(run_dir),
            input_video=metadata.get("input_video"),
            num_tracks=metadata.get("num_tracks"),
            num_frames=metadata.get("num_frames"),
            created_at=metadata.get("created_at"),
        )
    return RunSummary(run_id=run_dir.name, status=get_run_status(run_dir))
