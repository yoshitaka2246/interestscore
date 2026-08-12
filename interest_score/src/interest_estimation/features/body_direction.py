"""体向き特徴量。Phase 1では未実装のためダミー(常に0)を返す(configでenabled=falseとして使用)。"""
from __future__ import annotations

from interest_estimation.features.base import Feature
from interest_estimation.tracking.tracker import PersonTrack, VideoMeta


class BodyDirectionFeature(Feature):
    name = "body_direction"

    def compute_raw(self, track: PersonTrack, video_meta: VideoMeta) -> float:
        return 0.0
