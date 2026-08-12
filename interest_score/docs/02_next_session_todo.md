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

## AWSデプロイ・EC2運用(2026-08-12時点)

Web UIはAWS EC2(CDK管理、`interest_score/infra/`)+ Vercelで本番稼働中。
Vercelの404トラブル(Framework Preset未検出・Deployment Protection・CLI実行ディレクトリ)は
解決済み、`docs/03_deployment.md`に記録済み。

- バックエンドURL: `https://api.yoshi-yamamoto.com`
- フロントエンドURL: `https://interestscore.vercel.app`
- EC2 instance ID: `i-055d908b321280579`(t3.large, ap-northeast-1)
- **EC2は現在stop済み**(2026-08-12夜、コスト節約のため作業終了時に停止)。
  次回使う前に `aws ec2 start-instances --instance-ids i-055d908b321280579 --region ap-northeast-1`
  または後述のフロントエンド機能で起動すること。

### 進行中・中断した作業: GPUインスタンス移行

ユーザーはg4dn.2xlarge(NVIDIA T4, 8vCPU/32GB, $1.015/時間)へのGPU移行を選択済み。
**コードは書き終わっているが、まだCDK deployできていない**(下記の理由で中断)。

実装済み(未デプロイ):
- `infra/lib/backend-stack.ts`: `computeType=gpu`時にg4dn.2xlarge + AWS Deep Learning Base AMI
  (`ami-0afd7aa8518a6f0a1`, Ubuntu 26.04, NVIDIA driver同梱)を使うよう変更済み。
  CPU/GPUどちらのAMIを使うか、AMI IDが古くなっていないかは
  `aws ec2 describe-images --owners amazon --filters "Name=name,Values=Deep Learning Base*Ubuntu*"`
  で確認すること。
- **EC2起動/停止をフロントエンドから操作する機能**(パスワード保護)も実装済み:
  - `web/frontend/src/app/api/instance/route.ts` — Next.js API route。AWS SDK(`@aws-sdk/client-ec2`)で
    EC2の状態取得(GET)・起動停止(POST、`INSTANCE_CONTROL_PASSWORD`で認証)を行う。
    EC2が停止中でもVercel側(常時稼働)から操作できるのがポイント。
  - `web/frontend/src/lib/instance-api.ts` — 型付きAPIクライアント
  - `web/frontend/src/components/instance-control.tsx` — トップページの操作UI
  - `infra/lib/backend-stack.ts`に`InstanceControlUser`(IAMユーザー、EC2のStart/Stopのみ許可の
    最小権限)と`InstanceControlAccessKey`を追加済み。**まだcdk deployしていないのでAWS上には
    存在しない**。

**次回やること(残作業)**:
1. `cd interest_score/infra && npx cdk deploy -c vercelOrigin=https://interestscore.vercel.app -c computeType=gpu`
   を実行し、g4dn.2xlargeへの切り替え + InstanceControlUser作成を反映する
   (`cdk diff`で内容を確認してから)。
2. デプロイ後、`aws cloudformation describe-stacks --stack-name InterestScoreBackendStack`から
   `InstanceControlAccessKeyId` / `InstanceControlSecretAccessKey` を取得し、Vercelの環境変数に設定:
   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION=ap-northeast-1`,
   `EC2_INSTANCE_ID=i-055d908b321280579`, `INSTANCE_CONTROL_PASSWORD=(決めたパスワード)`。
   アクセスキーは出力に平文で出るため、ターミナル履歴やログに残さないよう扱いに注意。
3. フロントエンドを再デプロイ(`vercel --prod --force --cwd .` を**リポジトリルートから**実行。
   `docs/03_deployment.md`のVercel CLIの罠を参照)。
4. トップページから起動/停止ボタンで実際に動作確認する。
5. GPU化後は`requirements.txt`のtorchが実際にCUDAを使えているか(`runtime.device: auto`が
   `cuda`を選ぶか)、`nvidia-smi`と合わせて確認すること。

**中断した理由**: このMac(ユーザーのローカル環境)で`fileproviderd`(iCloud同期デーモン)が
CPU 100%超で張り付き、`npx tsc`という単純なコンパイルすら数分〜完了せず`cdk synth`が
進まなくなった。原因は今回のセッションで`node_modules`を複数回インストールした結果、
iCloud Desktop同期(`~/Desktop`配下)が大量の小ファイルの同期に苦しんでいたため。
`mv`でnode_modulesを退避する対処も試したが`mv`自体がI/O詰まりでタイムアウトした。
ユーザーには「iCloud Driveを一時オフにする」「Macを再起動する」を提案し、今回はここで
作業を中断してiCloud処理が落ち着くのを待つことにした。**次回セッション開始時、まず
`uptime`と`ps aux | grep fileproviderd`で負荷が正常(load average <3程度)に戻っているか
確認してから`cdk synth`/`npm run build`等の重い処理を実行すること。**
再発する場合は`node_modules`をiCloud同期対象外の場所(`~/.cache`等)に置いてシンボリックリンクで
参照する回避策を検討する(今回は`mv`が詰まって完了できなかった)。

## Phase 4: Evaluation — Ground Truthデータが揃うまで着手不可

人間が動画を見て0-5点を付けたGround Truthデータ(`00_研究管理`のCLAUDE.md参照)が
存在しない限り、相関分析やAblation Studyは実施できない(結果の捏造は禁止)。
データが用意できたら `data/annotations/` に配置し、評価スクリプトを実装する。

## Phase 5: Research Improvement

Phase 4の評価結果が出てから着手する。Score式改善は`score_v2.py`として新規作成し、
既存の`score_v1.py`は上書きしない。
