# Interest Estimation System

店頭広告・デジタルサイネージ前を通行する人物の映像から、人物検出・追跡・行動特徴量解析を行い、
広告に対する関心度を **Interest Score** として定量化するシステム（卒業研究）。

「人が多い時間帯」と「売れる時間帯」が一致しないという観察から出発し、通行人数ではなく
「関心度」を定量化することを目的とする。詳細は親ディレクトリの `CLAUDE.md` および
`docs/` を参照。

## 現在のステータス: Phase 1（CLI）・Phase 3（Web UI）完了

`動画 → 人物検出 → 追跡 → 特徴量 → Interest Score → result.mp4/persons.csv` の
CLIパイプラインが動作します(`src/interest_estimation/`)。

Web UI(`web/backend`=FastAPI, `web/frontend`=Next.js)から動画アップロード・実行・結果閲覧が
可能です。デプロイ手順(Vercel + バックエンド別ホスト)は `docs/03_deployment.md` を参照してください。

Phase 4(評価)は人間が付与したGround Truthデータが必要なため未着手です。
詳細は `docs/02_next_session_todo.md` を参照してください。

## パイプライン

```
動画 → 人物検出 (YOLOv11) → 人物追跡 (ByteTrack) → 特徴量抽出 → Interest Score → 可視化・出力
```

## ディレクトリ構成

```
interest_score/
├── configs/                # 実験設定 (YAML)
├── src/interest_estimation/  # 実装コード（Phase 1で着手）
│   ├── detection/
│   ├── tracking/
│   ├── features/
│   ├── scoring/
│   ├── pipeline/
│   ├── visualization/
│   ├── experiment/
│   └── utils/
├── web/                     # Web UI (Phase 3)
│   ├── frontend/
│   └── backend/
├── scripts/                 # CLIエントリポイント
├── data/                    # 動画・アノテーション（Git管理外）
├── experiments/             # 実験定義
├── results/                 # 実験結果（Git管理外）
├── tests/
├── docker/
├── legacy_reference/        # 移行済みの旧研究コード（03_プログラムより）
└── docs/                    # 設計方針・フェーズ計画
```

## セットアップ（Phase 1着手時）

```bash
cd interest_score
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI使用方法（実装後の想定）

```bash
python scripts/run_video.py \
  --input data/raw/sample01.mp4 \
  --config configs/default.yaml
```

出力先: `results/<run_id>/`（result.mp4, persons.csv, frames.csv, config.yaml, metadata.json, run.log）

## 既存コードの再利用

`legacy_reference/` に、YOLOv11 + ByteTrackによる人物検出・追跡の動作実績があるコードを配置している。
Phase 1の実装ではこれを最大限再利用する（詳細は `legacy_reference/README.md`）。

## Research Pipeline Doc

Web UIを含むシステム全体の詳細仕様は `docs/00_architecture.md` にまとめている。
