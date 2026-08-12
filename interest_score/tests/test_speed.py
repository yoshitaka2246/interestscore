from interest_estimation.features.speed import SpeedFeature
from interest_estimation.tracking.tracker import PersonTrack, TrackObservation, VideoMeta


def _obs(frame_idx: int, t: float, cx: float, cy: float) -> TrackObservation:
    return TrackObservation(frame_idx=frame_idx, timestamp_sec=t, bbox=(cx - 5, cy - 5, cx + 5, cy + 5), confidence=0.9)


def test_speed_raw_constant_motion():
    # 1秒ごとにx方向へ10px移動 -> 10 px/sec
    track = PersonTrack(track_id=1, observations=[_obs(0, 0.0, 0, 0), _obs(30, 1.0, 10, 0), _obs(60, 2.0, 20, 0)])
    meta = VideoMeta(fps=30.0, width=640, height=480, frame_count=90)

    feature = SpeedFeature()
    assert feature.compute_raw(track, meta) == 10.0


def test_speed_raw_single_observation():
    track = PersonTrack(track_id=1, observations=[_obs(0, 0.0, 0, 0)])
    meta = VideoMeta(fps=30.0, width=640, height=480, frame_count=1)

    feature = SpeedFeature()
    assert feature.compute_raw(track, meta) == 0.0
