"""動画からInterest Scoreを算出するエンドツーエンドCLI。

使い方:
    python scripts/run_video.py --input data/raw/sample01.mp4 --config configs/default.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# pip install -e . のeditable installがこの開発環境では機能しないため(conftest.py参照)、
# srcを明示的にsys.pathへ追加する。
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interest_estimation.pipeline.video_pipeline import VideoPipeline
from interest_estimation.utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interest Score end-to-end pipeline")
    parser.add_argument("--input", type=str, default=None, help="入力動画パス(省略時はconfigのvideo.inputを使用)")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="設定YAMLパス")
    parser.add_argument("--results-root", type=str, default="results", help="結果出力先ルート")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    input_video = args.input or config.video.input
    if input_video is None:
        raise SystemExit("--input または config.video.input のいずれかで入力動画を指定してください")

    pipeline = VideoPipeline(config)
    result = pipeline.run(input_video, results_root=args.results_root)

    print(f"完了: {result.run_dir}")
    print(f"  tracks: {result.num_tracks}, frames: {result.num_frames}")


if __name__ == "__main__":
    main()
