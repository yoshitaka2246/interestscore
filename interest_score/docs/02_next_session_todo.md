# 次セッションのTODO（実装着手ガイド）

このドキュメントは「Webアプリ実装して」と指示された際に、確認を最小限にしてすぐ着手できるようにするためのもの。

## 重要な前提

仕様書の最重要方針（セクション2）により、**Web UIより先にCLIパイプラインを完成させる**。
「Webアプリ実装して」という指示は「システムの実装に着手する」という意味で受け取り、
以下のPhase 1（CLI End-to-End）から着手すること。いきなりFastAPI/Next.jsを書き始めない。

Bypass Permissionsモードは設定済み（`.claude/settings.local.json`）なので、
軽微な判断は都度確認せず自律的に進めてよい。既存コードを壊す可能性が高い変更のみ慎重に扱う。

## Phase 1: End-to-End CLI 実装順序（仕様書セクション65準拠）

1. **Detection interface** — `src/interest_estimation/detection/detector.py`（抽象IF）+ `yolo_detector.py`
   `legacy_reference/track_video.py` の `model.track(...)` 呼び出し部分を、Detector/Trackerに分離する形で移植する。
   出力形式は仕様書セクション11の `Detection(bbox, confidence, class_id)`。

2. **Tracking interface** — `tracking/tracker.py`（抽象IF）+ `bytetrack_tracker.py`
   `legacy_reference/track_video.py` の `tracker="bytetrack.yaml"` 部分を移植。`PersonTrack`（セクション13）としてbbox/position/timestampsの履歴を保持する構造にする。

3. **Feature interface** — `features/dwell_time.py`, `features/speed.py`
   `dwell_time`は `legacy_reference/summarize_tracks.py` のロジック（first_seen/last_seen）を移植して0-1正規化する。
   `speed`はbbox中心点の時間変化から新規実装（pixel/secでよい、仕様書セクション17）。
   `body_direction`, `face_direction` は最初は `enabled: false` のダミー実装（常に0を返す）でよい（仕様書セクション19）。

4. **Interest Score** — `scoring/scorer.py`, `scoring/score_v1.py`, `scoring/normalization.py`
   `configs/score_v1.yaml` の重みを使い、`I = wd*dwell + ws*speed + wb*body + wf*face` を実装。
   **`score_v1.py`は今後上書きしない**。改善時は`score_v2.py`を新規作成。

5. **VideoPipeline** — `pipeline/video_pipeline.py`
   Detector/Tracker/Feature/Scorerを疎結合に組み合わせる中心クラス。ベタ書き禁止（仕様書セクション10）。

6. **CLI** — `scripts/run_video.py`
   ```bash
   python scripts/run_video.py --input data/raw/sample01.mp4 --config configs/default.yaml
   ```

7. **Result output** — `experiment/result_writer.py`
   `results/<run_id>/` に `result.mp4`, `persons.csv`, `frames.csv`, `config.yaml`, `metadata.json`, `run.log` を出力。
   `result.mp4`にはID・Interest Score・bboxを描画（`visualization/video_renderer.py`、`legacy_reference/track_video.py`の描画部分を再利用可能）。

## Phase 1 完了条件（仕様書セクション66）

```
sample01.mp4 を入力 → result.mp4 (ID/Score/bbox描画済み) + persons.csv + frames.csv + config.yaml + metadata.json + run.log が出力される
```

## その後

Phase 2（Experiment Infrastructure: Run ID, metadata, git commit hash）→
Phase 3（Web UI）→ Phase 4（Evaluation）→ Phase 5（Research Improvement）
の順で進める。詳細は `01_phase_plan.md`。

## 実行環境について

- Python 3.11想定。`requirements.txt`は用意済みだが、まだ `pip install` は実行していない。
- GPU環境（研究室PC/自宅PC/RunPod等）はセッションごとに異なる可能性がある。`runtime.device: auto` でCPUフォールバックする前提で実装する。
- iCloud同期の影響で大きいファイル（動画・重み）の初回アクセスが遅い場合がある（`docs/00_architecture.md`参照）。
