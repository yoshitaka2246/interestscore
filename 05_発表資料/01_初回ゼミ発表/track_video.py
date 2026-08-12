from ultralytics import YOLO
import csv
import math
from collections import defaultdict


INPUT_VIDEO = "input.mp4"
MODEL_PATH = "yolo11n.pt"
TRACKER = "bytetrack.yaml"

OUTPUT_DETAIL_CSV = "tracking_detail.csv"
OUTPUT_SUMMARY_CSV = "tracking_summary.csv"


def main():
    model = YOLO(MODEL_PATH)

    # track_idごとに中心座標などを保存する
    tracks = defaultdict(list)

    results = model.track(
        source=INPUT_VIDEO,
        classes=[0],              # personのみ
        tracker=TRACKER,
        conf=0.3,
        imgsz=640,
        stream=True,
        persist=True,
        show=False,
        save=False,
        verbose=True,
    )

    # 各フレームの検出結果を取得
    for frame_idx, result in enumerate(results):
        boxes = result.boxes

        # 検出なし、またはtrack_idなしの場合はスキップ
        if boxes is None or boxes.id is None:
            continue

        xyxy = boxes.xyxy.cpu().numpy()
        ids = boxes.id.cpu().numpy().astype(int)
        confs = boxes.conf.cpu().numpy()

        for box, track_id, conf in zip(xyxy, ids, confs):
            x1, y1, x2, y2 = box

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            tracks[track_id].append({
                "frame": frame_idx,
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "center_x": float(center_x),
                "center_y": float(center_y),
                "confidence": float(conf),
            })

    # 詳細CSVを出力
    with open(OUTPUT_DETAIL_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "track_id",
            "frame",
            "x1",
            "y1",
            "x2",
            "y2",
            "center_x",
            "center_y",
            "confidence",
        ])

        for track_id, points in tracks.items():
            for p in points:
                writer.writerow([
                    track_id,
                    p["frame"],
                    p["x1"],
                    p["y1"],
                    p["x2"],
                    p["y2"],
                    p["center_x"],
                    p["center_y"],
                    p["confidence"],
                ])

    # サマリーCSVを出力
    with open(OUTPUT_SUMMARY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "track_id",
            "appearance_frames",
            "total_distance_px",
            "average_speed_px_per_frame",
            "start_frame",
            "end_frame",
        ])

        for track_id, points in tracks.items():
            # 念のためフレーム順に並べる
            points = sorted(points, key=lambda p: p["frame"])

            appearance_frames = len(points)
            total_distance = 0.0

            for prev, curr in zip(points[:-1], points[1:]):
                dx = curr["center_x"] - prev["center_x"]
                dy = curr["center_y"] - prev["center_y"]
                distance = math.sqrt(dx ** 2 + dy ** 2)
                total_distance += distance

            if appearance_frames > 1:
                average_speed = total_distance / (appearance_frames - 1)
            else:
                average_speed = 0.0

            start_frame = points[0]["frame"]
            end_frame = points[-1]["frame"]

            writer.writerow([
                track_id,
                appearance_frames,
                total_distance,
                average_speed,
                start_frame,
                end_frame,
            ])

    print("完了")
    print(f"詳細CSV: {OUTPUT_DETAIL_CSV}")
    print(f"集計CSV: {OUTPUT_SUMMARY_CSV}")
    print(f"検出された人物ID数: {len(tracks)}")


if __name__ == "__main__":
    main()