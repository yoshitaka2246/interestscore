"""Interest Score Web API(FastAPI)。

`pip install -e .` のeditable installがこの開発環境では機能しないため(interest_score/CLAUDE.md参照)、
srcを明示的にsys.pathへ追加してからinterest_estimationパッケージをimportする。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.paths import RESULTS_DIR
from app.routers import configs, runs, videos

app = FastAPI(title="Interest Score API")

cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
# Vercelのプレビューデプロイは <branch>-<project>.vercel.app のように毎回URLが変わるため、
# 固定originリストだけでは対応できない。正規表現での許可も併用できるようにする。
cors_origin_regex = os.environ.get("CORS_ORIGIN_REGEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(configs.router)
app.include_router(runs.router)

app.mount("/static/results", StaticFiles(directory=RESULTS_DIR), name="results")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
