# Web UI デプロイ手順(Phase 3)

## 全体構成

```
Next.js (web/frontend)  --- HTTPS ---  Vercel
        |
        | fetch (NEXT_PUBLIC_API_BASE_URL)
        v
FastAPI (web/backend)   --- 別ホスト(研究室PC/自宅PC/VPS/RunPod等) ---
        |
        v
YOLO/ByteTrack (PyTorch) + results/ ファイル群
```

YOLO(PyTorch)は重いモデルで、Vercelのサーバーレス関数は実行時間・パッケージサイズに
制限がありAI推論には基本的に向かない。そのため **フロントエンド(Next.js)のみVercelにデプロイし、
FastAPIバックエンド(YOLO/ByteTrack処理)は別ホストで動かす** 構成にする。

## Vercel側の設定

このリポジトリはmonorepo構成(`卒業研究_関心度推定/interest_score/web/frontend/`が
Next.jsアプリの実体)のため、Vercelプロジェクト作成時に **Root Directory** を
明示的に指定する必要がある。

1. Vercelで `yoshitaka2246/interestscore` をImport
2. **Project Settings → General → Root Directory** に以下を設定

   ```
   interest_score/web/frontend
   ```

   (Vercelがこのディレクトリの `package.json` を見て自動的にNext.jsと認識する)
3. **Environment Variables** に以下を追加

   | Key | Value | 備考 |
   |---|---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://<FastAPIバックエンドのURL>` | 後述のバックエンドホストのURL。必ずHTTPS |

4. Deploy

Build Command / Output Directory / Install Command はRoot Directoryを設定すれば
Next.jsのデフォルトのままで自動検出される(変更不要)。

## バックエンド(FastAPI)側の設定

Vercel(HTTPS)上のフロントエンドから呼び出すため、バックエンドも **HTTPSで公開する必要がある**
(HTTPSページから素のHTTPへのリクエストはブラウザのMixed Content policyでブロックされる)。

**本番はAWS EC2(CDK管理)で稼働中**: `interest_score/infra/`参照。
`api.yoshi-yamamoto.com`(Route53 Aレコード + Caddyの自動HTTPS)で公開しており、
systemdでFastAPIが常駐しているため、EC2インスタンスをStart/Stopするだけで
コマンド入力なしに使える。詳細・コスト・GPU切り替え方法は`infra/lib/backend-stack.ts`
のコメントとルート`README`のやり取りを参照。

環境変数:

| 変数 | 例 | 説明 |
|---|---|---|
| `CORS_ORIGINS` | `https://interestscore.vercel.app,https://api.yoshi-yamamoto.com` | 本番Vercel URL(カンマ区切りで複数指定可) |
| `CORS_ORIGIN_REGEX` | `https://.*-yoshitaka2246s-projects\.vercel\.app` | Vercelのプレビューデプロイ(PRごとに変わるURL)を許可する場合に指定。未使用なら省略可 |

(自宅PC/研究室PC等、EC2以外で動かす場合はCloudflare Tunnel・ngrok・Tailscale Funnel等で
HTTPSの公開URLを払い出すか、VPS+リバースプロキシ(Caddy等)でHTTPS終端する。)

起動コマンド例(ローカル/EC2以外で動かす場合):

```bash
cd interest_score/web/backend
source ../../.venv/bin/activate
CORS_ORIGINS="https://interestscore.vercel.app" \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## ローカル動作確認

```bash
# バックエンド
cd interest_score/web/backend
source ../../.venv/bin/activate
CORS_ORIGINS="http://localhost:3000" uvicorn app.main:app --reload --port 8000

# フロントエンド(別ターミナル)
cd interest_score/web/frontend
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

`http://localhost:3000` で動画アップロード → 実行 → 結果(動画・人物別Interest Score)を確認できる。

## Vercelデプロイで実際にハマった問題(2026-08-12)

Root Directoryを設定してGit連携でデプロイしても本番URLが `404: NOT_FOUND` になり続けた。
原因は以下3つの複合で、**ビルドログが成功していても本番が404になりうる**ことに注意。

1. **Project SettingsのFramework Presetが`null`(未検出)のままだった**。
   `rootDirectory`を設定しても`framework`は自動で`nextjs`にならない場合があり、
   その状態だと`next build`自体は成功する(ログ上は正常)のに、Vercelがその出力を
   サーバーレス関数用に変換できず`lambdas[].output`が空になり、静的ファイル含め
   **全ルートが404**になる。`vercel.com/<team>/<project>/settings` →
   General → Framework Preset を明示的に「Next.js」に設定する
   (APIなら `PATCH /v9/projects/{id}` に `{"framework":"nextjs"}`)。
   ビルドログに`Detected Next.js version: ...`という行が出ていれば正しく検出されている。

2. **Deployment Protection(`ssoProtection`)がデフォルトの`.vercel.app`ドメインにも
   かかっていた**(`deploymentType: "all_except_custom_domains"`)。カスタムドメインを
   使わず`<project>.vercel.app`だけで公開する場合、これが有効だと本番エイリアスすら
   認証必須になる。研究用の公開デモとして誰でもアクセスできる状態にしたい場合は、
   Settings → Deployment Protection で無効化する
   (`PATCH /v9/projects/{id}` に `{"ssoProtection": null}`)。
   ※無効化すると誰でも動画アップロード・パイプライン実行ができるようになる点に注意
   (バックエンド側の計算リソースを消費される)。

3. **Vercel CLIは、Root DirectoryをすでにScopeしたディレクトリの中から実行すると
   パスが二重になる**(`vercel link`/`vercel deploy`は必ずGitリポジトリの
   ルートから実行する。`interest_score/web/frontend`の中から実行すると
   `.../interest_score/web/frontend/interest_score/web/frontend`のような
   存在しないパスを探しにいってエラーになる)。

デプロイ後に404が出た場合の切り分け手順:
1. `curl -D - <本番URL>` で `x-vercel-error: NOT_FOUND` かどうか確認(Vercel自体が
   ルーティングできていない = 上記の問題を疑う)。SSOへの302リダイレクトなら
   Deployment Protectionが原因。
2. Vercelダッシュボードでそのデプロイの個別URL(`<project>-<hash>-<team>.vercel.app`)に
   直接アクセスし、本番エイリアスと挙動が違うか比較する。
3. `vercel deploy --prod --force`(ビルドキャッシュ無視)を**リポジトリルートから**実行し、
   ビルドログに`Detected Next.js version`が出るか確認する。

## 既知の制約

- **DB不使用**: run一覧は `results/` ディレクトリを都度スキャンして返す(`interest_score/CLAUDE.md`方針)。
  バックエンドを再起動しても`results/`が残っていれば履歴は失われない。
- **同時実行**: 実行中のパイプラインはPythonの`threading.Thread`で1本ずつ動く(Celery等は導入しない方針)。
  同時に大量のrunを捌く用途は想定していない。
- **動画コーデック**: `result.mp4`はOpenCVで書き出した後、ffmpegでH.264に変換している
  (`visualization/video_renderer.py`の`transcode_to_h264`)。バックエンドホストに`ffmpeg`が
  無い場合、動画は生成されるがブラウザの`<video>`タグでは再生できない(OpenCVの`mp4v`は
  ブラウザ非対応のため)。`brew install ffmpeg` 等で用意すること。
