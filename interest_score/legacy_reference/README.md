# Legacy Reference Code

`03_プログラム/`（旧Gitリポジトリ `yoshitaka2246/interestscore`、コミット履歴はGitHub上に保存済み）から移行した、Phase 0時点で動作していたスクリプト群。

## 位置づけ

これらは **リファクタリング前の動作コード** であり、`src/interest_estimation/` の実装（Phase 1）はこれらのロジックを最大限再利用しながら進める。まだ新アーキテクチャへの移植は行っていない。

## ファイルと再利用先の対応

| ファイル | 内容 | 移植先（Phase 1予定） |
|---|---|---|
| `track_video.py` | YOLOv11 + ByteTrackで人物検出・追跡、bbox付き動画とCSVを出力 | `detection/yolo_detector.py`, `tracking/bytetrack_tracker.py`, `pipeline/video_pipeline.py` |
| `summarize_tracks.py` | track_idごとに滞在時間・始点終点座標を要約 | `features/dwell_time.py` |
| `count_idsw.py` | 手動ラベル(person_id)を使ったID Switch集計 | `experiment/`（Experiment A: Tracking Performance評価） |
| `extract_track_frames.py` | track開始・終了フレームの人物画像を切り出し（目視確認用） | `utils/`（デバッグ・アノテーション補助） |

## 動作に必要なファイル

`input.mp4`（サンプル動画）と `yolo11n.pt`（YOLOv11モデル重み）を同ディレクトリに同梱。どちらもGit管理対象外（`.gitignore`参照）。

`input.mp4` は `data/raw/sample01.mp4` としても複製済み（新パイプラインのデフォルト入力を想定）。

## 実行方法（当時のまま、パスは相対パス前提）

```bash
cd interest_score/legacy_reference
python3 track_video.py        # output.avi, output.mp4, output.csv を生成
python3 summarize_tracks.py   # tracks_summary.csv を生成（person_id列は手動記入）
python3 count_idsw.py         # IDSWを集計
python3 extract_track_frames.py  # track_frames/ に静止画を出力
```
