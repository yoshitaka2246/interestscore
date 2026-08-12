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

## Phase 2: Experiment Infrastructure — 完了

`docs/01_phase_plan.md`参照。Run ID・metadata.json(git commit hash等)・config.yaml保存・
Result Directoryは`experiment/result_writer.py`で実装済み。

**Experiment Runner**(`scripts/run_experiment.py`)を実装済み:

```bash
python scripts/run_experiment.py --experiment experiments/score_weight_sweep.yaml
```

`experiments/*.yaml`に `{name, video, configs: [...]}` 形式で実験定義を書くと、各configで
通常通り`VideoPipeline`を実行(`results/<run_id>/`は個別run実行時と同じ形式)し、加えて
`results/experiment_<name>_<timestamp>/summary.csv`に config・run_id・トラック数・
Interest Scoreの平均/最大/最小をまとめる。`configs/experiments/`には重みを変えた
config例(`dwell_heavy.yaml`, `speed_heavy.yaml`)を置いてある。

## Phase 3: Web UI — 完了

FastAPI(`web/backend/`) + Next.js(`web/frontend/`)で実装済み。動画アップロード→実行トリガー→
進捗ポーリング→結果閲覧(H.264動画・人物別Interest Score表)までブラウザで実機確認済み。
DB不使用、`results/`ディレクトリを直接スキャンする方式。

- `web/backend/app/main.py` — FastAPIアプリ本体、CORS設定
- `web/backend/app/runner.py` — `threading.Thread`によるバックグラウンド実行(Celery等は不使用)
- `web/backend/app/routers/` — videos / configs / runs のAPI
- `web/frontend/src/lib/api.ts` — Zodでレスポンスを検証する型付きAPIクライアント
- `web/frontend/src/app/` — トップページ(アップロード・実行・履歴)、`/runs/[runId]`(結果詳細)

デプロイ手順(Vercelのroot directory設定含む)は `docs/03_deployment.md` を参照。

### 追加で直した既知の問題

- **editable install (`pip install -e .`) が機能しない**: `interest_score/CLAUDE.md`の
  「既知の環境問題」参照。新しいエントリポイントには`sys.path`への明示追加が必要。
- **`result.mp4`がブラウザで再生できない**: OpenCVの`mp4v`(MPEG-4 Part 2)はブラウザ非対応。
  `visualization/video_renderer.py`の`transcode_to_h264()`でffmpeg経由H.264変換を追加済み。
  バックエンドホストに`ffmpeg`が無いと変換がスキップされ再生できないので要注意。

## Phase 4: Evaluation — Ground Truthデータが揃うまで着手不可

人間が動画を見て0-5点を付けたGround Truthデータ(`00_研究管理`のCLAUDE.md参照)が
存在しない限り、相関分析やAblation Studyは実施できない(結果の捏造は禁止)。
データが用意できたら `data/annotations/` に配置し、評価スクリプトを実装する。

## Phase 5: Research Improvement

Phase 4の評価結果が出てから着手する。Score式改善は`score_v2.py`として新規作成し、
既存の`score_v1.py`は上書きしない。
