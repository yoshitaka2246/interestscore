Interest Score Web UIのフロントエンド(Next.js)。バックエンド(FastAPI)は `../backend` を参照。

## 開発

```bash
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URLをバックエンドのURLに合わせる
npm install
npm run dev
```

バックエンド(`../backend`)を先に起動しておくこと。詳細は `../../docs/03_deployment.md`。

## Vercelへのデプロイ

このプロジェクトはmonorepoの一部のため、Vercelの **Root Directory** に
`interest_score/web/frontend` を指定する必要がある。詳細は `../../docs/03_deployment.md` 参照。
