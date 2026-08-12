# CLAUDE.md (interest_score)

このファイルは親ディレクトリの `CLAUDE.md` を補完する。研究テーマ・全体像は親を参照。
ここには `interest_score/` 配下でコードを書く際の実装規約を書く。

## 現在のフェーズ

**Phase 0（環境整備）完了。Phase 1（End-to-End CLI）未着手。**

フェーズ順序は厳守する。Web UIやDocker化をPhase 1より先に着手しない。

```
Phase 1: End-to-End CLI（動画→検出→追跡→特徴量→Score→result.mp4/persons.csv）
Phase 2: Experiment Infrastructure（Run ID, metadata, git commit hash記録）
Phase 3: Web UI（FastAPI + Next.js or Streamlit/Gradio）
Phase 4: Evaluation（Ground Truth, 相関分析, Ablation）
Phase 5: Research Improvement（Score式改善、新特徴量、Weight最適化）
```

詳細は `docs/01_phase_plan.md`。次にやることは `docs/02_next_session_todo.md`。

## 実装前に必ず読むもの

- `legacy_reference/` — 動作実績のある既存コード（YOLOv11+ByteTrack検出・追跡）。
  最大限再利用する。いきなり全面書き換えしない。
- `docs/00_architecture.md` — 現状アーキテクチャと再利用方針。

## 絶対に守ること

- **Score versioning**: `scoring/score_v1.py` 等、既存バージョンは絶対に上書きしない。
  改善する場合は `score_v2.py` として新規作成する。
- **Config Driven**: 実験条件（重み・閾値・モデル名等）をコードにハードコードしない。
  YAML (`configs/`) 経由で変更可能にする。
- **DB不使用**: 初期段階ではSQLite等を導入しない。ファイルベース（results/, experiments/）で十分。
- **Logging**: `print` の乱用を避け、標準`logging`を使う（INFO/WARNING/ERROR）。Runごとにログファイルを保存。
- **Research Integrity**: 実験結果が仮説と一致しなくても数値を恣意的に調整しない。

## 導入しないもの（Overengineering禁止）

Kubernetes / Redis Cluster / Celery Cluster / PostgreSQL / Supabase / Microservices /
Authentication / Multi-user対応 / Terraform / 複雑なAWS構成 / 凝ったCI/CD /
不要なデザインシステム。

研究システムであり商用SaaSではない。

## テスト方針

GPUなしで動く研究ロジック（Config loader, Score calculation, Normalization, Result writer）を優先してテストする。AIモデル部分のテストより優先度が高い。

## GPU / CPU

`runtime.device: auto` — CUDA利用可能ならCUDA、不可ならCPUにフォールバックする構造にする。
