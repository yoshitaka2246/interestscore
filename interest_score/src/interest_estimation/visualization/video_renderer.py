"""追跡結果とInterest Scoreを描画した動画を書き出す。

OpenCVの'mp4v'(MPEG-4 Part 2)はブラウザの<video>タグでは再生できないため、
legacy_reference/track_video.pyと同様にffmpegでH.264へ変換する(transcode_to_h264)。
CLI単体での確認用途などffmpegが無い環境でも動作は継続できるよう、変換失敗時は
mp4v版のファイルをそのまま結果として使うフォールバックにしている。
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

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


def transcode_to_h264(src: Path, dst: Path) -> bool:
    """srcをH.264(yuv420p, faststart)へ変換してdstに書き出す。

    ffmpegが見つからない場合は変換をスキップしてFalseを返す(呼び出し側はsrcを
    そのまま結果として使う想定)。
    """
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpegが見つからないためH.264変換をスキップします(ブラウザ再生できない場合があります)")
        return False

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(dst),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning("H.264変換に失敗しました: %s", result.stderr[-2000:])
        return False
    return True
