from ultralytics import YOLO
import csv
import math
from collections import defaultdict
import cv2
import os
import subprocess


INPUT_VIDEO = "input.mp4"
MODEL_PATH = "yolo11n.pt"
TRACKER = "bytetrack.yaml"

OUTPUT_RAW_VIDEO = "output_raw.avi"
OUTPUT_VIDEO = "output.mp4"

OUTPUT_DETAIL_CSV = "tracking_detail.csv"
OUTPUT_SUMMARY_CSV = "tracking_summary.csv"


def convert_avi_to_mp4(input_avi, output_mp4):
    print("\n===== ffmpegでMP4へ変換します =====")

    if not os.path.exists(input_avi):
        raise FileNotFoundError(f"{input_avi} が存在しません")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_avi,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4,
    ]

    print("実行コマンド:")
    print(" ".join(cmd))

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("\n===== ffmpeg stdout =====")
    print(result.stdout)

    print("\n===== ffmpeg stderr =====")
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError("ffmpegによるMP4変換に失敗しました")

    if not os.path.exists(output_mp4):
        raise FileNotFoundError(f"{output_mp4} が作成されませんでした")

    print(f"MP4変換完了: {output_mp4}")
    print(f"ファイルサイズ: {os.path.getsize(output_mp4):,} bytes")


def main():
    print("===== 動画情報を取得します =====")

    cap = cv2.VideoCapture(INPUT_VIDEO)
    if not cap.isOpened():
        raise FileNotFoundError(f"入力動画を開けませんでした: {INPUT_VIDEO}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()

    if fps <= 0:
        print("WARNING: FPSが取得できなかったため、30fpsとして処理します")
        fps = 30.0

    print(f"入力動画: {INPUT_VIDEO}")
    print(f"fps: {fps}")
    print(f"width: {width}")
    print(f"height: {height}")
    print(f"frame_count: {frame_count}")

    if width <= 0 or height <= 0:
        raise RuntimeError("動画サイズを取得できませんでした")

    print("\n===== AVI出力設定 =====")

    # AVIはOpenCVで比較的安定して書き出せる
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_writer = cv2.VideoWriter(
        OUTPUT_RAW_VIDEO,
        fourcc,
        fps,
        (width, height)
    )

    print(f"出力AVI: {OUTPUT_RAW_VIDEO}")
    print(f"video_writer.isOpened(): {video_writer.isOpened()}")

    if not video_writer.isOpened():
        raise RuntimeError("VideoWriterを開けませんでした")

    model = YOLO(MODEL_PATH)
    tracks = defaultdict(list)

    print("\n===== トラッキング開始 =====")

    results = model.track(
        source=INPUT_VIDEO,
        classes=[0],
        tracker=TRACKER,
        conf=0.3,
        imgsz=640,
        stream=True,
        persist=True,
        show=False,
        save=False,
        verbose=True,
    )

    written_frames = 0

    for frame_idx, result in enumerate(results):
        frame = result.orig_img

        if frame is None:
            print(f"WARNING: frame {frame_idx} が None のためスキップ")
            continue

        frame = frame.copy()

        if frame.shape[1] != width or frame.shape[0] != height:
            print(
                f"WARNING: frame {frame_idx} のサイズが異なるためリサイズします "
                f"{frame.shape[1]}x{frame.shape[0]} -> {width}x{height}"
            )
            frame = cv2.resize(frame, (width, height))

        boxes = result.boxes

        if boxes is not None and boxes.id is not None:
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

                x1_i, y1_i, x2_i, y2_i = map(int, [x1, y1, x2, y2])

                cv2.rectangle(
                    frame,
                    (x1_i, y1_i),
                    (x2_i, y2_i),
                    (255, 0, 0),
                    2
                )

                label = f"ID:{track_id} person {conf:.2f}"

                cv2.putText(
                    frame,
                    label,
                    (x1_i, max(y1_i - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                    cv2.LINE_AA,
                )

        video_writer.write(frame)
        written_frames += 1

        if frame_idx % 30 == 0:
            print(f"処理中: frame {frame_idx}")

    video_writer.release()

    print("\n===== AVI出力完了 =====")
    print(f"書き込みフレーム数: {written_frames}")

    if not os.path.exists(OUTPUT_RAW_VIDEO):
        raise FileNotFoundError("output_raw.avi が作成されませんでした")

    print(f"AVIファイルサイズ: {os.path.getsize(OUTPUT_RAW_VIDEO):,} bytes")

    print("\n===== CSV出力 =====")

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
            points = sorted(points, key=lambda p: p["frame"])

            appearance_frames = len(points)
            total_distance = 0.0

            for prev, curr in zip(points[:-1], points[1:]):
                dx = curr["center_x"] - prev["center_x"]
                dy = curr["center_y"] - prev["center_y"]
                total_distance += math.sqrt(dx ** 2 + dy ** 2)

            average_speed = total_distance / (appearance_frames - 1) if appearance_frames > 1 else 0.0

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

    print(f"詳細CSV: {OUTPUT_DETAIL_CSV}")
    print(f"集計CSV: {OUTPUT_SUMMARY_CSV}")
    print(f"検出された人物ID数: {len(tracks)}")

    # AVIをH.264 MP4へ変換
    convert_avi_to_mp4(OUTPUT_RAW_VIDEO, OUTPUT_VIDEO)

    print("\n===== 完了 =====")
    print(f"確認用動画: {OUTPUT_VIDEO}")
    print("この output.mp4 をVSCodeまたはQuickTimeで開いてください")


if __name__ == "__main__":
    main()


