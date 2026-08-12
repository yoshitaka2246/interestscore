"""特徴量計算から正規化・Interest Score算出までを統合するScorer。"""
from __future__ import annotations

from interest_estimation.features.base import Feature
from interest_estimation.features.body_direction import BodyDirectionFeature
from interest_estimation.features.dwell_time import DwellTimeFeature
from interest_estimation.features.face_direction import FaceDirectionFeature
from interest_estimation.features.speed import SpeedFeature
from interest_estimation.scoring import score_v1
from interest_estimation.scoring.normalization import normalize_min_max
from interest_estimation.tracking.tracker import PersonTrack, VideoMeta
from interest_estimation.utils.config import AppConfig

_SCORE_VERSIONS = {"v1": score_v1}

_ALL_FEATURES: dict[str, Feature] = {
    "dwell_time": DwellTimeFeature(),
    "speed": SpeedFeature(),
    "body_direction": BodyDirectionFeature(),
    "face_direction": FaceDirectionFeature(),
}


class PersonScore:
    def __init__(
        self,
        track_id: int,
        raw_features: dict[str, float],
        normalized_features: dict[str, float],
        score: float,
    ) -> None:
        self.track_id = track_id
        self.raw_features = raw_features
        self.normalized_features = normalized_features
        self.score = score


class Scorer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

        version = config.scoring.version
        if version not in _SCORE_VERSIONS:
            raise ValueError(f"未対応のscoring.versionです: {version}")
        self._score_module = _SCORE_VERSIONS[version]

        self._enabled_features: dict[str, Feature] = {
            name: feature
            for name, feature in _ALL_FEATURES.items()
            if getattr(config.features, name).enabled
        }

    def score_all(self, tracks: dict[int, PersonTrack], video_meta: VideoMeta) -> dict[int, PersonScore]:
        raw_by_feature: dict[str, dict[int, float]] = {
            name: {track_id: feature.compute_raw(track, video_meta) for track_id, track in tracks.items()}
            for name, feature in self._enabled_features.items()
        }

        normalized_by_feature: dict[str, dict[int, float]] = {
            name: normalize_min_max(values, invert=name in self._score_module.INVERT_FEATURES)
            for name, values in raw_by_feature.items()
        }

        weights = self.config.scoring.weights.model_dump()
        output_scale = self.config.scoring.output_scale

        scores: dict[int, PersonScore] = {}
        for track_id in tracks:
            raw_features = {name: raw_by_feature[name][track_id] for name in self._enabled_features}
            normalized_features = {name: normalized_by_feature[name][track_id] for name in self._enabled_features}
            score = self._score_module.compute_score(normalized_features, weights, output_scale)
            scores[track_id] = PersonScore(track_id, raw_features, normalized_features, score)

        return scores
