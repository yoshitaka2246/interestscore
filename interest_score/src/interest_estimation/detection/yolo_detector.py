"""YOLOv11による人物検出。legacy_reference/track_video.py のモデル呼び出しを移植。"""
from __future__ import annotations

import numpy as np
from ultralytics import YOLO

from interest_estimation.detection.detector import Detection, Detector
from interest_estimation.utils.device import resolve_device

PERSON_CLASS_ID = 0


class YoloDetector(Detector):
    def __init__(
        self,
        model_path: str,
        confidence: float = 0.3,
        iou_threshold: float = 0.5,
        device: str = "auto",
        classes: tuple[int, ...] = (PERSON_CLASS_ID,),
    ) -> None:
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.device = resolve_device(device)
        self.classes = list(classes)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self.model.predict(
            frame,
            conf=self.confidence,
            iou=self.iou_threshold,
            classes=self.classes,
            device=self.device,
            verbose=False,
        )
        result = results[0]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        cls_ids = boxes.cls.cpu().numpy().astype(int)

        return [
            Detection(bbox=tuple(box.tolist()), confidence=float(conf), class_id=int(cls_id))
            for box, conf, cls_id in zip(xyxy, confs, cls_ids)
        ]
