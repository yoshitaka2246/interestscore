"""ByteTrackによる人物検出・追跡。legacy_reference/track_video.py の
model.track(tracker="bytetrack.yaml") 呼び出しを移植する。
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import cv2
from ultralytics import YOLO

from interest_estimation.tracking.tracker import FrameTracks, Tracker, TrackedBox, VideoMeta
from interest_estimation.utils.device import resolve_device

PERSON_CLASS_ID = 0


class ByteTrackTracker(Tracker):
    def __init__(
        self,
        model_path: str,
        confidence: float = 0.3,
        iou_threshold: float = 0.5,
        device: str = "auto",
    ) -> None:
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.device = resolve_device(device)
        self._video_meta: VideoMeta | None = None

    def track_video(self, video_path: str | Path) -> Iterator[FrameTracks]:
        video_path = str(video_path)
        self._video_meta = self._read_video_meta(video_path)
        fps = self._video_meta.fps or 30.0

        results = self.model.track(
            source=video_path,
            classes=[PERSON_CLASS_ID],
            tracker="bytetrack.yaml",
            conf=self.confidence,
            iou=self.iou_threshold,
            device=self.device,
            stream=True,
            persist=True,
            verbose=False,
        )

        for frame_idx, result in enumerate(results):
            boxes_out: list[TrackedBox] = []
            boxes = result.boxes

            if boxes is not None and boxes.id is not None:
                xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                track_ids = boxes.id.cpu().numpy().astype(int)

                for box, conf, track_id in zip(xyxy, confs, track_ids):
                    boxes_out.append(
                        TrackedBox(track_id=int(track_id), bbox=tuple(box.tolist()), confidence=float(conf))
                    )

            yield FrameTracks(
                frame_idx=frame_idx,
                timestamp_sec=frame_idx / fps,
                frame=result.orig_img,
                boxes=boxes_out,
            )

    def get_video_meta(self) -> VideoMeta:
        if self._video_meta is None:
            raise RuntimeError("track_video() をまだ呼び出していません")
        return self._video_meta

    @staticmethod
    def _read_video_meta(video_path: str) -> VideoMeta:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"動画を開けません: {video_path}")
        meta = VideoMeta(
            fps=cap.get(cv2.CAP_PROP_FPS) or 30.0,
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )
        cap.release()
        return meta
