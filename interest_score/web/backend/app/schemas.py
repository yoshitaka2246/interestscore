"""APIレスポンス用のPydanticモデル。"""
from __future__ import annotations

from pydantic import BaseModel


class VideoInfo(BaseModel):
    name: str
    size_bytes: int


class ConfigInfo(BaseModel):
    name: str
    valid: bool


class RunSummary(BaseModel):
    run_id: str
    status: str  # "running" | "done" | "failed"
    input_video: str | None = None
    num_tracks: int | None = None
    num_frames: int | None = None
    created_at: str | None = None


class PersonScoreRow(BaseModel):
    track_id: int
    start_time_sec: float
    end_time_sec: float
    dwell_time_raw: float
    speed_raw: float
    interest_score: float


class RunDetail(BaseModel):
    run_id: str
    status: str
    metadata: dict | None = None
    persons: list[PersonScoreRow] = []
    has_video: bool = False
    error: str | None = None


class StartRunRequest(BaseModel):
    video_name: str
    config_name: str = "default.yaml"
