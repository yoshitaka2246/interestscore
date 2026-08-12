Interest Score Web UIのバックエンド(FastAPI)。DB不使用、`data/raw/`・`configs/`・`results/`を
直接読み書きする。フロントエンドは `../frontend` を参照。

## 開発

```bash
cd ../..                       # interest_score/ ルートで依存関係をインストール済みであること
source .venv/bin/activate
cd web/backend
CORS_ORIGINS="http://localhost:3000" uvicorn app.main:app --reload --port 8000
```

`GET /api/health` で疎通確認できる。API定義は `/docs` (Swagger UI) 参照。

## デプロイ

Vercel(フロントエンド)からHTTPS経由で呼び出すため、このバックエンドもHTTPSで公開する必要がある。
詳細は `../../docs/03_deployment.md` 参照。
