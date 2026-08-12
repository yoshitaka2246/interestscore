"""特徴量の抽象インターフェース。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from interest_estimation.tracking.tracker import PersonTrack, VideoMeta


class Feature(ABC):
    name: str

    @abstractmethod
    def compute_raw(self, track: PersonTrack, video_meta: VideoMeta) -> float:
        """1トラックあたりの生の特徴量値を返す(正規化前)。"""
