"""Generate the bundled sample CSV.

Running this script creates ``data/raw/sample_reviews.csv`` so that
reviewers can inspect the synthetic corpus without running the full
pipeline.

    python scripts/generate_sample_data.py --n 800 --out data/raw/sample_reviews.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from data_loader import clean_reviews, generate_synthetic_reviews  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=800)
    p.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "sample_reviews.csv")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    df = generate_synthetic_reviews(n=args.n, seed=args.seed)
    df = clean_reviews(df)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(df)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
