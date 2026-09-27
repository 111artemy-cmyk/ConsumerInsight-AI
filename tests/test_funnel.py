"""Unit tests for the funnel_analyzer module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.marketing_analytics.funnel_analyzer import FunnelAnalyzer  # noqa: E402


def _reviews(n: int = 100) -> pd.DataFrame:
    """Build a frame where ~40% mention 复购 intent."""
    rows = []
    for i in range(n):
        if i < 40:
            # High intent + satisfaction + repurchase
            text = "回购第三次了，粉质细腻服帖，持妆一整天"
            rating = 5
            overall = 0.9
        elif i < 70:
            # Trial + satisfaction, no repurchase
            text = "上脸试了，奶油肌，满意"
            rating = 4
            overall = 0.5
        elif i < 90:
            # Trial only
            text = "收到货，用了一下"
            rating = 3
            overall = 0.0
        else:
            # Just aware (commented but no signal)
            text = "随便说说"
            rating = 3
            overall = 0.0
        rows.append(
            {
                "review_id": f"R{i:04d}",
                "text": text,
                "rating": rating,
                "overall": overall,
            }
        )
    return pd.DataFrame(rows)


def test_funnel_analyzer_rejects_empty_input():
    analyzer = FunnelAnalyzer()
    try:
        analyzer.run(pd.DataFrame())
    except ValueError:
        return
    raise AssertionError("Expected ValueError for empty input")


def test_funnel_stages_are_strictly_monotonic():
    """Awareness must be >= Interest >= Trial >= Satisfaction >= Repurchase."""
    analyzer = FunnelAnalyzer()
    result = analyzer.run(_reviews())
    counts = result.stage_counts["count"].tolist()
    for i in range(1, len(counts)):
        assert counts[i] <= counts[i - 1], (
            f"Funnel stage {i} ({counts[i]}) > stage {i-1} ({counts[i-1]}); "
            "a funnel must be non-increasing."
        )


def test_funnel_starts_with_all_reviews():
    """Awareness stage counts everyone who left a comment."""
    analyzer = FunnelAnalyzer()
    df = _reviews(n=87)
    result = analyzer.run(df)
    first = int(result.stage_counts.iloc[0]["count"])
    assert first == len(df)


def test_funnel_summary_references_a_real_stage():
    analyzer = FunnelAnalyzer()
    result = analyzer.run(_reviews())
    # Summary must mention one of the known stage labels
    known = {"01_Awareness", "02_Interest", "03_Trial", "04_Satisfaction", "05_Repurchase"}
    mentioned = [s for s in known if s in result.stage_summary]
    assert mentioned, f"Summary does not mention any stage: {result.stage_summary!r}"


if __name__ == "__main__":
    test_funnel_analyzer_rejects_empty_input()
    test_funnel_stages_are_strictly_monotonic()
    test_funnel_starts_with_all_reviews()
    test_funnel_summary_references_a_real_stage()
    print("✅ funnel tests passed")