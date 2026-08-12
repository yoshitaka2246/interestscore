# アーキテクチャ現状整理（Phase 0時点）

仕様書（ユーザー提供の設計・実装仕様書）セクション67で要求されている、実装着手前の整理。

## 1. 現状アーキテクチャ

- リポジトリは `卒業研究_関心度推定/`（親フォルダ）を単一Gitリポジトリとして管理する構成に変更した。
- 以前は `03_プログラム/` が独立したGitリポジトリ（GitHub: `yoshitaka2246/interestscore`）として存在していたが、
  ネストしたGit管理を解消し、コードは `interest_score/legacy_reference/` に移行、旧リポジトリの履歴はGitHub上に保持されている。
- `interest_score/` に、仕様書セクション7の推奨構成に沿ったディレクトリ骨格（`configs/`, `src/interest_estimation/*`, `web/`, `scripts/`, `data/`, `experiments/`, `results/`, `tests/`, `docker/`）を作成済み。中身は空（`.gitkeep`のみ）。
- 実装コード（`src/interest_estimation/`以下のPythonモジュール、`scripts/run_video.py`等）は **まだ一切書かれていない**。

## 2. 再利用可能な既存コード（`legacy_reference/`）

| ファイル | 動作内容 | 評価 |
|---|---|---|
| `track_video.py` | Ultralytics YOLO(`yolo11n.pt`) + `bytetrack.yaml` で人物(class 0)を検出・追跡し、bbox描画済み動画(mp4)とframe/track_id/bboxのCSVを出力 | Detection + Tracking + 基本的なVisualizationの土台として十分再利用可能。`model.track(stream=True, persist=True)` のジェネレータパターンは`VideoPipeline`のフレームループ設計にそのまま流用できる |
| `summarize_tracks.py` | track_idごとに開始/終了フレーム・時刻・座標を要約したCSVを生成 | 滞在時間(dwell_time)特徴量の計算ロジックの元になる。ただし現状は「動画中に映っていた時間」であり、ROI内滞在時間ではない（仕様書セクション16のROI概念は未実装） |
| `count_idsw.py` | 手動アノテーション(person_id)を元にID Switch数を集計 | Experiment A（Tracking Performance評価）の評価指標実装の土台 |
| `extract_track_frames.py` | track開始・終了時点の人物クロップ画像を保存 | 目視確認・アノテーション作業補助。将来のGround Truth作成ワークフローに転用可能 |

これらは動作実績があるが、以下の点で仕様書の設計とギャップがある：

- 全てハードコードされたパス・パラメータ（Config Driven Architectureになっていない）
- Detector/Trackerがモジュール化されておらず、YOLOの呼び出しがVideoPipeline相当のスクリプトに直書き
- Interest Score算出（features・scoring）は未実装。現状あるのは検出・追跡・滞在時間の要約のみ
- 身体方向・顔向き・歩行速度は未実装
- Run ID・metadata・再現性の仕組みはない

## 3. 問題点・注意点

- **iCloud同期**: プロジェクト全体が `~/Desktop` 配下にあり、iCloud Desktop同期の影響で一部ファイル（`yolo11n.pt`等）が「ローカル未ダウンロード」状態になることがある（`du`で0Bと表示されても`ls -la`では正しいサイズが出る）。大きい動画・重みファイルを扱うスクリプト実行時は、初回アクセス時にダウンロードで待つ可能性がある。
- **`05_発表資料/`が約250MB**とサイズが大きい（pptxバックアップ多数）。Git管理はするが、今回のセットアップでは対象外（スコープ外）。今後大きくなる場合は個別に`.gitignore`検討の余地あり。
- 環境（GPU種別・CUDA・PyTorchバージョン等）は未確認。Phase 1着手時に実行環境を確認すること。

## 4. 今回実装した変更（Phase 0: 環境整備のみ）

- `interest_score/` にディレクトリ骨格を作成（実装コードなし）
- `legacy_reference/` に既存コードを移行
- Config雛形（`configs/default.yaml`, `score_v1.yaml`, `score_v2.yaml`）を作成
- `pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example` を作成
- `README.md`, `CLAUDE.md`, `docs/` を作成
- 親フォルダ全体をGitリポジトリとして初期化
- 次セッションから研究運用モード（Bypass Permissions）で作業できるよう `.claude/settings.local.json` を設定

**実装（Detector/Tracker/Pipeline/CLI等のコード）はまだ行っていない。**

## 5. 推奨ディレクトリ構造

仕様書セクション7の構成をそのまま採用（`interest_score/README.md`参照）。変更・逸脱なし。
