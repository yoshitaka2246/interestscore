"""実行デバイスの解決。runtime.device: auto でCUDA優先・CPUフォールバックする。"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def resolve_device(device: str) -> str:
    if device in ("cuda", "cpu"):
        return device

    if device != "auto":
        raise ValueError(f"未対応のdevice指定です: {device}")

    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        logger.warning("torchが利用できないためcpuにフォールバックします")

    return "cpu"
