"""滞在時間特徴量。legacy_reference/summarize_tracks.py の first_seen/last_seen ロジックを移植。

ROI(広告周辺エリア)の概念は未実装のため、現状は「動画に映っていた時間」を滞在時間とする。
"""
from __future__ import annotations

from interest_estimation.features.base import Feature
from interest_estimation.tracking.tracker import PersonTrack, VideoMeta


class DwellTimeFeature(Feature):
    name = "dwell_time"

    def compute_raw(self, track: PersonTrack, video_meta: VideoMeta) -> float:
        return track.end_time_sec - track.start_time_sec
