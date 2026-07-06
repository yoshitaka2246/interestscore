import csv
import cv2
from collections import defaultdict

INPUT_VIDEO = "input.mp4"
INPUT_CSV = "output.csv"
OUTPUT_CSV = "tracks_summary.csv"

# 時刻換算のため入力動画のfpsを取得する
cap = cv2.VideoCapture(INPUT_VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
cap.release()

# track_idごとに、登場したフレームと中心座標を集める
tracks = defaultdict(list)

with open(INPUT_CSV, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        track_id = int(row["track_id"])
        frame = int(row["frame"])
        x1, y1, x2, y2 = (float(row["x1"]), float(row["y1"]), float(row["x2"]), float(row["y2"]))
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        tracks[track_id].append((frame, center_x, center_y))

# track_idごとに1行の要約データにまとめる
rows = []

for track_id, points in tracks.items():
    points.sort(key=lambda p: p[0])
    start_frame, start_x, start_y = points[0]
    end_frame, end_x, end_y = points[-1]

    rows.append({
        "track_id": track_id,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "num_frames": len(points),
        "start_time_sec": round(start_frame / fps, 2),
        "end_time_sec": round(end_frame / fps, 2),
        "start_x": round(start_x, 1),
        "start_y": round(start_y, 1),
        "end_x": round(end_x, 1),
        "end_y": round(end_y, 1),
        "person_id": "",  # ここに動画を見ながら人物ラベル(P1, P2, ...)を書き込む
    })

rows.sort(key=lambda r: r["start_frame"])

fieldnames = [
    "track_id", "start_frame", "end_frame", "num_frames",
    "start_time_sec", "end_time_sec",
    "start_x", "start_y", "end_x", "end_y", "person_id",
]

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"完了: {OUTPUT_CSV}（track_id {len(rows)}件）")
