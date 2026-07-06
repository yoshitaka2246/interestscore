import csv
import os
import cv2

INPUT_VIDEO = "input.mp4"
INPUT_CSV = "output.csv"
OUTPUT_DIR = "track_frames"

MARGIN = 30  # バウンディングボックスの周りに足す余白(px)

# track_idごとに、最初と最後に登場したフレーム番号とbboxを記録する
first_seen = {}
last_seen = {}

with open(INPUT_CSV, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        track_id = int(row["track_id"])
        frame = int(row["frame"])
        box = tuple(map(float, [row["x1"], row["y1"], row["x2"], row["y2"]]))

        if track_id not in first_seen or frame < first_seen[track_id][0]:
            first_seen[track_id] = (frame, box)
        if track_id not in last_seen or frame > last_seen[track_id][0]:
            last_seen[track_id] = (frame, box)

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(INPUT_VIDEO)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


def save_crop(frame_idx, track_id, box, label):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    if not ok:
        print(f"WARNING: frame {frame_idx} を読み込めませんでした (track_id={track_id})")
        return

    x1, y1, x2, y2 = box
    x1 = max(int(x1) - MARGIN, 0)
    y1 = max(int(y1) - MARGIN, 0)
    x2 = min(int(x2) + MARGIN, width)
    y2 = min(int(y2) + MARGIN, height)

    crop = frame[y1:y2, x1:x2]
    filename = f"{OUTPUT_DIR}/frame{frame_idx:05d}_track{track_id}_{label}.png"
    cv2.imwrite(filename, crop)


# 各track_idの登場開始時点と終了時点の姿を切り出す
for track_id, (frame_idx, box) in first_seen.items():
    save_crop(frame_idx, track_id, box, "start")

for track_id, (frame_idx, box) in last_seen.items():
    save_crop(frame_idx, track_id, box, "end")

cap.release()
print(f"完了: {OUTPUT_DIR}/ に切り出し画像を保存しました")
