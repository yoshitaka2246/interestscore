"""実行可能なconfig一覧API。"""
from __future__ import annotations

from fastapi import APIRouter

from app.paths import CONFIGS_DIR
from app.schemas import ConfigInfo
from interest_estimation.utils.config import load_config

router = APIRouter(prefix="/api/configs", tags=["configs"])


@router.get("", response_model=list[ConfigInfo])
def list_configs() -> list[ConfigInfo]:
    configs: list[ConfigInfo] = []
    for path in sorted(CONFIGS_DIR.glob("*.yaml")):
        try:
            load_config(path)
            valid = True
        except Exception:
            valid = False
        configs.append(ConfigInfo(name=path.name, valid=valid))
    return configs
