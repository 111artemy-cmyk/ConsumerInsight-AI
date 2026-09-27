"""Command-line entry point for the full pipeline.

Usage
-----
    python scripts/run_pipeline.py                # default: 1500 synthetic reviews
    python scripts/run_pipeline.py --n 2500       # more synthetic reviews
    python scripts/run_pipeline.py --csv path.csv # use your own CSV
    python scripts/run_pipeline.py --backend openai --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
# 把项目根目录加入 sys.path，让 `src` 能被识别为 package，
# 这样 src/pipeline.py 里的相对导入（`from .ai_analysis import ...`）才能工作。
sys.path.insert(0, str(ROOT))

from src.pipeline import run_full_pipeline  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Run the ConsumerInsight-AI pipeline.")
    p.add_argument("--csv", type=Path, default=None, help="CSV file with reviews.")
    p.add_argument("--n", type=int, default=1500, help="Synthetic review count (default 1500).")
    p.add_argument(
        "--backend",
        choices=["auto", "mock", "openai"],
        default="auto",
        help="LLM backend (default: auto → mock if no key).",
    )
    p.add_argument("--model", default="gpt-4o-mini", help="LLM model name.")
    p.add_argument("--out", type=Path, default=None, help="Override output directory.")
    args = p.parse_args()

    artifacts = run_full_pipeline(
        n_reviews=args.n,
        use_synthetic=args.csv is None,
        csv_path=args.csv,
        llm_backend=args.backend,
        llm_model=args.model,
        output_dir=args.out,
    )
    print("\n=== ConsumerInsight-AI  pipeline complete ===")
    print(f"  reviews          : {len(artifacts.reviews)}")
    print(f"  personas         : {len(artifacts.personas)}")
    print(f"  segments         : {artifacts.segment_profile.shape[0]}")
    print(f"  creatives        : {len(artifacts.creatives)}")
    print(f"  figures          : {len(artifacts.figures)}")
    print(f"  report           : {artifacts.report_path}")
    print(f"  processed csv    : {ROOT / 'data' / 'processed' / 'sample_processed.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
