"""追跡結果とInterest Scoreを描画した動画を書き出す。

legacy_reference/track_video.py はXVID(avi)出力後にffmpegでmp4へ変換していたが、
opencv-pythonの'mp4v'フォーマットで直接mp4を書き出せるため、外部ffmpeg依存を避けている。
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

BOX_COLOR = (255, 0, 0)
TEXT_COLOR = (255, 0, 0)


class VideoRenderer:
    def __init__(self, output_path: str | Path, fps: float, width: int, height: int) -> None:
        self.output_path = Path(output_path)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(str(self.output_path), fourcc, fps, (width, height))
        if not self.writer.isOpened():
            raise RuntimeError(f"VideoWriterを初期化できません: {self.output_path}")

    def draw_and_write(
        self,
        frame: np.ndarray,
        boxes: list[tuple[int, tuple[float, float, float, float], float]],
    ) -> None:
        """boxes: (track_id, bbox, interest_score) のリスト。"""
        for track_id, bbox, score in boxes:
            x1, y1, x2, y2 = (int(v) for v in bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
            label = f"ID:{track_id} Score:{score:.1f}"
            cv2.putText(frame, label, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2)

        self.writer.write(frame)

    def release(self) -> None:
        self.writer.release()
