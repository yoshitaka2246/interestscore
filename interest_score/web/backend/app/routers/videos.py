"""動画一覧・アップロードAPI。"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.paths import DATA_RAW_DIR
from app.schemas import VideoInfo

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_SUFFIXES = {".mp4", ".mov", ".avi"}


@router.get("", response_model=list[VideoInfo])
def list_videos() -> list[VideoInfo]:
    return [
        VideoInfo(name=path.name, size_bytes=path.stat().st_size)
        for path in sorted(DATA_RAW_DIR.iterdir())
        if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES
    ]


@router.post("", response_model=VideoInfo)
async def upload_video(file: UploadFile) -> VideoInfo:
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名がありません")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"未対応の拡張子です: {suffix}")

    dest = DATA_RAW_DIR / file.filename
    with dest.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    return VideoInfo(name=dest.name, size_bytes=dest.stat().st_size)
