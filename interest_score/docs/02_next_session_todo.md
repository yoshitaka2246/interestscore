# 次セッションのTODO(実装着手ガイド)

## Phase 1: End-to-End CLI — 完了

`動画 → Detection → Tracking → Feature → Score → result.mp4 + persons.csv` が
sample01.mp4で動作確認済み(24トラック検出、`results/<run_id>/`に全出力あり)。

実装場所:

- `src/interest_estimation/detection/` — `detector.py`(抽象IF)+ `yolo_detector.py`
- `src/interest_estimation/tracking/` — `tracker.py`(抽象IF・PersonTrack)+ `bytetrack_tracker.py`
- `src/interest_estimation/features/` — `dwell_time.py`, `speed.py`(実装済み)、
  `body_direction.py`, `face_direction.py`(ダミー、`enabled: false`)
- `src/interest_estimation/scoring/` — `normalization.py`, `score_v1.py`, `scorer.py`
- `src/interest_estimation/pipeline/video_pipeline.py` — 全体を統合する中心クラス
- `src/interest_estimation/visualization/video_renderer.py` — bbox/ID/Score描画
- `src/interest_estimation/experiment/result_writer.py` — run_id・metadata.json・config.yaml出力
- `scripts/run_video.py` — CLIエントリポイント
- `tests/` — GPUなしで動くロジック(config, normalization, dwell_time, speed, score_v1)のテスト済み

### 環境構築メモ

このMac(Apple Silicon)はターミナルがRosetta経由でIntel版Homebrew(`/usr/local`)を使っており、
PyTorchはmacOS x86_64向けに`2.2.2`までしか提供されていない。`.venv`は
`brew install python@3.12`(Intel版)で作成したPython 3.12を使用している。
`numpy<2`・`opencv-python<4.10`にピン留めしないと、torch(numpy1向けビルド)と
opencv-python 5.x(numpy2必須)が衝突するため、`requirements.txt`で固定済み。
`ultralytics`が`lap`パッケージを自動インストールしようとするため、`requirements.txt`に明示追加済み。

## Phase 2: Experiment Infrastructure — 次に着手

`docs/01_phase_plan.md`参照。Run ID・metadata.json(git commit hash等)・config.yaml保存・
Result Directoryは`experiment/result_writer.py`で既に実装済み。残っているのは:

- **Experiment Runner**: `configs/experiments/`配下に複数の実験設定(重みや閾値違い)を置き、
  一括実行して`results/`に比較可能な形で出力する仕組み。
- 複数動画・複数configの一括実行CLI(`scripts/run_experiment.py`等)。

## その後

Phase 3(Web UI)→ Phase 4(Evaluation)→ Phase 5(Research Improvement)の順で進める。
詳細は `01_phase_plan.md`。Web UIより先にCLI・実験基盤を安定させる方針は変わらない。
