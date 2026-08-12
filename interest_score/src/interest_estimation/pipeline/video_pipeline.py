"""動画からInterest Score算出までを一気通貫で処理するVideoPipeline。

Detector/Tracker/Feature/Scorerを疎結合に組み合わせる中心クラス(仕様書セクション10)。
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import cv2

from interest_estimation.experiment.result_writer import create_run_dir, write_config, write_metadata
from interest_estimation.scoring.scorer import PersonScore, Scorer
from interest_estimation.tracking.bytetrack_tracker import ByteTrackTracker
from interest_estimation.tracking.tracker import PersonTrack, TrackedBox, TrackObservation, VideoMeta
from interest_estimation.utils.config import AppConfig
from interest_estimation.utils.logging import setup_run_logger
from interest_estimation.visualization.video_renderer import VideoRenderer

FrameRecord = tuple[int, float, list[TrackedBox]]


@dataclass
class RunResult:
    run_dir: Path
    num_tracks: int
    num_frames: int


class VideoPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def run(self, input_video: str | Path, results_root: str | Path = "results") -> RunResult:
        run_dir = create_run_dir(results_root, self.config.experiment.name)
        logger = setup_run_logger(run_dir)
        logger.info("run開始: input=%s run_dir=%s", input_video, run_dir)

        write_config(run_dir, self.config)

        tracker = ByteTrackTracker(
            model_path=self.config.detection.model,
            confidence=self.config.detection.confidence,
            iou_threshold=self.config.detection.iou_threshold,
            device=self.config.runtime.device,
        )

        frame_records: list[FrameRecord] = []
        tracks: dict[int, PersonTrack] = {}

        for frame_result in tracker.track_video(input_video):
            frame_records.append((frame_result.frame_idx, frame_result.timestamp_sec, frame_result.boxes))
            for box in frame_result.boxes:
                track = tracks.setdefault(box.track_id, PersonTrack(track_id=box.track_id))
                track.add(
                    TrackObservation(
                        frame_idx=frame_result.frame_idx,
                        timestamp_sec=frame_result.timestamp_sec,
                        bbox=box.bbox,
                        confidence=box.confidence,
                    )
                )

        video_meta = tracker.get_video_meta()
        logger.info("追跡完了: frames=%d tracks=%d", len(frame_records), len(tracks))

        scorer = Scorer(self.config)
        scores = scorer.score_all(tracks, video_meta)

        if self.config.output.save_frame_data:
            self._write_frames_csv(run_dir / "frames.csv", frame_records)
            logger.info("frames.csv を出力しました")

        if self.config.output.save_person_data:
            self._write_persons_csv(run_dir / "persons.csv", tracks, scores)
            logger.info("persons.csv を出力しました")

        if self.config.output.save_video:
            self._render_result_video(run_dir / "result.mp4", input_video, video_meta, frame_records, scores)
            logger.info("result.mp4 を出力しました")

        write_metadata(
            run_dir,
            str(input_video),
            extra={"num_tracks": len(tracks), "num_frames": len(frame_records)},
        )

        logger.info("run完了: run_dir=%s", run_dir)
        return RunResult(run_dir=run_dir, num_tracks=len(tracks), num_frames=len(frame_records))

    @staticmethod
    def _write_frames_csv(path: Path, frame_records: list[FrameRecord]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["frame", "timestamp_sec", "track_id", "x1", "y1", "x2", "y2", "confidence"])
            for frame_idx, timestamp_sec, boxes in frame_records:
                for box in boxes:
                    x1, y1, x2, y2 = box.bbox
                    writer.writerow(
                        [frame_idx, round(timestamp_sec, 3), box.track_id, x1, y1, x2, y2, box.confidence]
                    )

    @staticmethod
    def _write_persons_csv(
        path: Path, tracks: dict[int, PersonTrack], scores: dict[int, PersonScore]
    ) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "track_id",
                    "start_frame",
                    "end_frame",
                    "num_frames",
                    "start_time_sec",
                    "end_time_sec",
                    "dwell_time_raw",
                    "speed_raw",
                    "interest_score",
                ]
            )
            for track_id, track in sorted(tracks.items()):
                score = scores[track_id]
                writer.writerow(
                    [
                        track_id,
                        track.start_frame,
                        track.end_frame,
                        track.num_frames,
                        round(track.start_time_sec, 3),
                        round(track.end_time_sec, 3),
                        round(score.raw_features.get("dwell_time", 0.0), 3),
                        round(score.raw_features.get("speed", 0.0), 3),
                        round(score.score, 2),
                    ]
                )

    @staticmethod
    def _render_result_video(
        output_path: Path,
        input_video: str | Path,
        video_meta: VideoMeta,
        frame_records: list[FrameRecord],
        scores: dict[int, PersonScore],
    ) -> None:
        boxes_by_frame: dict[int, list[TrackedBox]] = {
            frame_idx: boxes for frame_idx, _, boxes in frame_records
        }

        renderer = VideoRenderer(output_path, video_meta.fps, video_meta.width, video_meta.height)
        cap = cv2.VideoCapture(str(input_video))
        try:
            frame_idx = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                render_items = [
                    (box.track_id, box.bbox, scores[box.track_id].score)
                    for box in boxes_by_frame.get(frame_idx, [])
                    if box.track_id in scores
                ]
                renderer.draw_and_write(frame, render_items)
                frame_idx += 1
        finally:
            cap.release()
            renderer.release()
