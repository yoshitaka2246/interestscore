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
自宅PC/研究室PCで動かす場合は、Cloudflare Tunnel・ngrok・Tailscale Funnel等でHTTPSの
公開URLを払い出すか、VPS+リバースプロキシ(Caddy等)でHTTPS終端する。

環境変数:

| 変数 | 例 | 説明 |
|---|---|---|
| `CORS_ORIGINS` | `https://interestscore.vercel.app` | 本番Vercel URL(カンマ区切りで複数指定可) |
| `CORS_ORIGIN_REGEX` | `https://.*-yoshitaka2246s-projects\.vercel\.app` | Vercelのプレビューデプロイ(PRごとに変わるURL)を許可する場合に指定。未使用なら省略可 |

起動コマンド例:

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

## 既知の制約

- **DB不使用**: run一覧は `results/` ディレクトリを都度スキャンして返す(`interest_score/CLAUDE.md`方針)。
  バックエンドを再起動しても`results/`が残っていれば履歴は失われない。
- **同時実行**: 実行中のパイプラインはPythonの`threading.Thread`で1本ずつ動く(Celery等は導入しない方針)。
  同時に大量のrunを捌く用途は想定していない。
- **動画コーデック**: `result.mp4`はOpenCVで書き出した後、ffmpegでH.264に変換している
  (`visualization/video_renderer.py`の`transcode_to_h264`)。バックエンドホストに`ffmpeg`が
  無い場合、動画は生成されるがブラウザの`<video>`タグでは再生できない(OpenCVの`mp4v`は
  ブラウザ非対応のため)。`brew install ffmpeg` 等で用意すること。
