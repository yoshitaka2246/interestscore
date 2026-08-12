"""特徴量の正規化(min-maxスケーリング)。動画内の全トラックを対象に0-1へスケールする。"""
from __future__ import annotations


def normalize_min_max(values: dict[int, float], invert: bool = False) -> dict[int, float]:
    """track_idごとの生値を0-1に正規化する。invert=Trueの場合、値が小さいほど1に近くなる
    (例: 歩行速度は遅いほど関心が高いとみなす)。

    全トラックの値が同じ(分散なし)場合はこの特徴量では差をつけられないため、全員0.0とする。
    """
    if not values:
        return {}

    raw = list(values.values())
    min_v, max_v = min(raw), max(raw)

    if max_v - min_v < 1e-9:
        return {track_id: 0.0 for track_id in values}

    normalized = {track_id: (v - min_v) / (max_v - min_v) for track_id, v in values.items()}

    if invert:
        normalized = {track_id: 1.0 - v for track_id, v in normalized.items()}

    return normalized
