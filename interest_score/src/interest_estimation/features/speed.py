"""歩行速度特徴量。bbox中心点の移動量から算出する(px/sec)。"""
from __future__ import annotations

import numpy as np

from interest_estimation.features.base import Feature
from interest_estimation.tracking.tracker import PersonTrack, VideoMeta


class SpeedFeature(Feature):
    name = "speed"

    def compute_raw(self, track: PersonTrack, video_meta: VideoMeta) -> float:
        observations = track.observations
        if len(observations) < 2:
            return 0.0

        total_distance = 0.0
        total_duration = 0.0
        for prev, curr in zip(observations, observations[1:]):
            (px, py), (cx, cy) = prev.center, curr.center
            total_distance += float(np.hypot(cx - px, cy - py))
            total_duration += curr.timestamp_sec - prev.timestamp_sec

        if total_duration <= 0:
            return 0.0

        return total_distance / total_duration
