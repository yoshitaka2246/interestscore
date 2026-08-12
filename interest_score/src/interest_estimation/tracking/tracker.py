"""人物追跡の抽象インターフェースとPersonTrackデータ構造。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np


@dataclass(frozen=True)
class TrackedBox:
    track_id: int
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float


@dataclass(frozen=True)
class FrameTracks:
    """Trackerが1フレームごとにyieldするストリーミング結果。frameは呼び出し側で
    描画等に使い終えたら保持しないこと(動画全体を保持するとメモリを圧迫するため)。
    """

    frame_idx: int
    timestamp_sec: float
    frame: np.ndarray
    boxes: list[TrackedBox]


@dataclass(frozen=True)
class TrackObservation:
    frame_idx: int
    timestamp_sec: float
    bbox: tuple[float, float, float, float]
    confidence: float

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return (x1 + x2) / 2, (y1 + y2) / 2


@dataclass
class PersonTrack:
    track_id: int
    observations: list[TrackObservation] = field(default_factory=list)

    def add(self, observation: TrackObservation) -> None:
        self.observations.append(observation)

    @property
    def start_frame(self) -> int:
        return self.observations[0].frame_idx

    @property
    def end_frame(self) -> int:
        return self.observations[-1].frame_idx

    @property
    def start_time_sec(self) -> float:
        return self.observations[0].timestamp_sec

    @property
    def end_time_sec(self) -> float:
        return self.observations[-1].timestamp_sec

    @property
    def num_frames(self) -> int:
        return len(self.observations)


@dataclass(frozen=True)
class VideoMeta:
    fps: float
    width: int
    height: int
    frame_count: int

    @property
    def duration_sec(self) -> float:
        return self.frame_count / self.fps if self.fps else 0.0


class Tracker(ABC):
    @abstractmethod
    def track_video(self, video_path: str | Path) -> Iterator[FrameTracks]:
        """動画をフレームごとに検出・追跡し、track_id付きのbboxをyieldする。"""

    @abstractmethod
    def get_video_meta(self) -> VideoMeta:
        """直近の track_video() 呼び出し対象動画のメタ情報を返す。"""
