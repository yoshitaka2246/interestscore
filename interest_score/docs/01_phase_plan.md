# 開発フェーズ計画

仕様書セクション57-61に基づく。順序厳守。Web UIやDocker化をPhase 1より先に着手しない。

- [x] **Phase 0: Repository inspection / 既存コード整理**
  既存研究コード（`legacy_reference/`）を確認・保存。ディレクトリ整理。Config雛形作成。

- [x] **Phase 1: End-to-End CLI**（最重要マイルストーン）
  `video.mp4 → Detection → Tracking → Feature → Score → result.mp4 + persons.csv` が安定動作すること。
  `src/interest_estimation/` 配下に実装済み。sample01.mp4での動作確認済み。

- [x] **Phase 2: Experiment Infrastructure**
  YAML Config運用・Run ID・metadata.json（git commit hash・Pythonバージョン等）・Result Directoryは
  `experiment/result_writer.py`で実装済み(Phase 1と同時に完了)。
  複数config一括実行の**Experiment Runner**(`scripts/run_experiment.py`)を実装し、
  `experiments/score_weight_sweep.yaml`(3configの重み比較)で動作確認済み。
  結果は`results/experiment_<name>_<timestamp>/summary.csv`に出力される。

- [x] **Phase 3: Web UI**
  動画アップロード、実行トリガー、進捗表示(ポーリング)、結果閲覧(動画+人物別Interest Score表)を実装。
  FastAPI(`web/backend/`) + Next.js(`web/frontend/`)。DB不使用（ファイルベース、`results/`を直接スキャン）。
  デプロイ手順は `docs/03_deployment.md` 参照。

- [ ] **Phase 4: Evaluation**
  Ground Truth loader、Tracking evaluation（ID Switch等）、Score evaluation（Spearman/Pearson/MAE）、Ablation Study。
  **人間が動画を見て0-5点を付与したGround Truthデータが前提**であり、そのデータが揃うまで着手できない。

- [ ] **Phase 5: Research Improvement**
  実験結果を見た上でのみ着手。Score式改善、新Feature、Pose estimation、Weight最適化等。
  Phase 4の評価結果が前提。

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
