"""YAML設定ファイルをpydanticモデルとして読み込む。

仕様書セクション9 (Config Driven Architecture) に準拠し、重み・閾値・モデル名等を
コードにハードコードせず、すべてYAML経由で変更可能にする。
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    name: str = "baseline"
    seed: int = 42


class VideoConfig(BaseModel):
    input: str | None = None


class DetectionConfig(BaseModel):
    model: str = "yolo11n.pt"
    confidence: float = 0.3
    iou_threshold: float = 0.5


class TrackingConfig(BaseModel):
    type: Literal["bytetrack"] = "bytetrack"


class FeatureToggle(BaseModel):
    enabled: bool = True


class FeaturesConfig(BaseModel):
    dwell_time: FeatureToggle = FeatureToggle()
    speed: FeatureToggle = FeatureToggle()
    body_direction: FeatureToggle = FeatureToggle(enabled=False)
    face_direction: FeatureToggle = FeatureToggle(enabled=False)


class ScoringWeights(BaseModel):
    dwell_time: float = 0.0
    speed: float = 0.0
    body_direction: float = 0.0
    face_direction: float = 0.0


class ScoringConfig(BaseModel):
    version: str = "v1"
    weights: ScoringWeights = ScoringWeights()
    output_scale: float = 100.0


class OutputConfig(BaseModel):
    save_video: bool = True
    save_frame_data: bool = True
    save_person_data: bool = True


class RuntimeConfig(BaseModel):
    device: Literal["auto", "cuda", "cpu"] = "auto"


class AppConfig(BaseModel):
    experiment: ExperimentConfig = ExperimentConfig()
    video: VideoConfig = VideoConfig()
    detection: DetectionConfig = DetectionConfig()
    tracking: TrackingConfig = TrackingConfig()
    features: FeaturesConfig = FeaturesConfig()
    scoring: ScoringConfig = ScoringConfig()
    output: OutputConfig = OutputConfig()
    runtime: RuntimeConfig = RuntimeConfig()


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path)
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return AppConfig(**raw)
