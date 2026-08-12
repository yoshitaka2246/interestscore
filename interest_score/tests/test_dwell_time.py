from interest_estimation.features.dwell_time import DwellTimeFeature
from interest_estimation.tracking.tracker import PersonTrack, TrackObservation, VideoMeta


def _obs(frame_idx: int, t: float, bbox=(0, 0, 10, 10)) -> TrackObservation:
    return TrackObservation(frame_idx=frame_idx, timestamp_sec=t, bbox=bbox, confidence=0.9)


def test_dwell_time_raw():
    track = PersonTrack(track_id=1, observations=[_obs(0, 0.0), _obs(30, 1.0), _obs(60, 2.0)])
    meta = VideoMeta(fps=30.0, width=640, height=480, frame_count=90)

    feature = DwellTimeFeature()
    assert feature.compute_raw(track, meta) == 2.0
