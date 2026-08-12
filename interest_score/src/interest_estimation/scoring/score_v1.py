"""Interest Score 1.0(ルールベース)。

I = wd*dwell_time + ws*speed + wb*body_direction + wf*face_direction

重みは実験結果を見ながら手動調整する(configs/score_v1.yaml)。
このファイルは仕様書の方針により上書きしない。改善する場合は score_v2.py を新規作成する。
"""
from __future__ import annotations

VERSION = "v1"

# 正規化時にスコアの向きを反転する特徴量(値が小さいほど関心が高い)
INVERT_FEATURES = {"speed"}


def compute_score(normalized_features: dict[str, float], weights: dict[str, float], output_scale: float) -> float:
    raw_score = sum(weights.get(name, 0.0) * value for name, value in normalized_features.items())
    return raw_score * output_scale
