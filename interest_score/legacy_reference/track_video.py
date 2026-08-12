from ultralytics import YOLO
import cv2
import csv
import subprocess

INPUT_VIDEO = "input.mp4"
MODEL_PATH = "yolo11n.pt"

OUTPUT_AVI = "output.avi"
OUTPUT_MP4 = "output.mp4"
OUTPUT_CSV = "output.csv"

# 入力動画のfps・サイズを取得する
cap = cv2.VideoCapture(INPUT_VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.release()

# 追跡結果を描画した動画を書き出すためのVideoWriterを準備する
fourcc = cv2.VideoWriter_fourcc(*"XVID")
writer = cv2.VideoWriter(OUTPUT_AVI, fourcc, fps, (width, height))

# YOLOv11 + ByteTrackで人物(class 0)を検出・追跡する
model = YOLO(MODEL_PATH)
results = model.track(
    source=INPUT_VIDEO,
    classes=[0],
    tracker="bytetrack.yaml",
    conf=0.3,
    stream=True,
    persist=True,
    verbose=False,
)

rows = []

# フレームごとに検出・追跡結果を取り出す
for frame_idx, result in enumerate(results):
    frame = result.orig_img.copy()
    boxes = result.boxes

    # 追跡IDが付いた人物がいるフレームのみ処理する
    if boxes is not None and boxes.id is not None:
        xyxy = boxes.xyxy.cpu().numpy()
        track_ids = boxes.id.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), track_id in zip(xyxy, track_ids):
            rows.append([frame_idx, track_id, x1, y1, x2, y2])

            # バウンディングボックスとIDを描画する
            p1 = (int(x1), int(y1))
            p2 = (int(x2), int(y2))
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2)
            cv2.putText(
                frame, f"ID:{track_id}", (p1[0], p1[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2,
            )

    writer.write(frame)

writer.release()

# frame, track_id, x1, y1, x2, y2 だけをCSVに書き出す
with open(OUTPUT_CSV, "w", newline="") as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(["frame", "track_id", "x1", "y1", "x2", "y2"])
    csv_writer.writerows(rows)

# AVIのままだと再生しづらいのでMP4に変換する
subprocess.run([
    "ffmpeg", "-y", "-i", OUTPUT_AVI,
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    OUTPUT_MP4,
])

print(f"完了: {OUTPUT_CSV}, {OUTPUT_MP4}")
