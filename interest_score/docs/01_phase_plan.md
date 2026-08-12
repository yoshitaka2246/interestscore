# 開発フェーズ計画

仕様書セクション57-61に基づく。順序厳守。Web UIやDocker化をPhase 1より先に着手しない。

- [x] **Phase 0: Repository inspection / 既存コード整理**
  既存研究コード（`legacy_reference/`）を確認・保存。ディレクトリ整理。Config雛形作成。

- [ ] **Phase 1: End-to-End CLI**（最重要マイルストーン）
  `video.mp4 → Detection → Tracking → Feature → Score → result.mp4 + persons.csv` が安定動作すること。
  完了条件は `docs/02_next_session_todo.md` 参照。

- [ ] **Phase 2: Experiment Infrastructure**
  YAML Config運用、Run ID、metadata.json（git commit hash・Pythonバージョン等）、Result Directory、Experiment Runner。

- [ ] **Phase 3: Web UI**
  動画アップロード、Config編集、実行、進捗表示、結果閲覧、Experiment History。
  FastAPI + (Next.js or Streamlit/Gradio)。DB不使用（ファイルベース）。

- [ ] **Phase 4: Evaluation**
  Ground Truth loader、Tracking evaluation（ID Switch等）、Score evaluation（Spearman/Pearson/MAE）、Ablation Study。

- [ ] **Phase 5: Research Improvement**
  実験結果を見た上でのみ着手。Score式改善、新Feature、Pose estimation、Weight最適化等。

## ゼミ発表スケジュールとの対応（親CLAUDE.md参照）

| ゼミ回 | 内容 | 対応Phase |
|---|---|---|
| 第1回 | 人物検出・追跡 | Phase 1の一部（`legacy_reference`で既に動作実績あり） |
| 第2回 | 滞在時間・歩行速度 | Phase 1 |
| 第3回 | 顔向き・体向き推定 | Phase 1（feature enabled=falseから開始可） |
| 第4回 | Interest Score 1.0・評価方法 | Phase 1〜2 |
| 第5回 | Interest Score 1.0 改善 | Phase 4〜5 |
| 第6回 | Interest Score 2.0（ML） | Phase 5 |
| 第7回 | エリア関心度 | Phase 1〜2（Area Interest = Σ Interest Score） |
