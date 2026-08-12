"""pytest用のsrcレイアウト対応。

`pip install -e .` のeditable install(.pthファイル経由のsys.path追加)が、この開発環境では
site.addpackage()が.pthファイルを処理しない既知の問題により機能しないため、明示的にsrcを
sys.pathへ追加する。
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
