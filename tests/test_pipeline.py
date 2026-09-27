"""End-to-end smoke test for the pipeline.

Run with::

    pytest tests/ -q
or::

    python -m tests.test_pipeline
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run_full_pipeline  # noqa: E402


def test_pipeline_runs_with_mock_llm():
    arts = run_full_pipeline(
        n_reviews=120,
        use_synthetic=True,
        llm_backend="mock",
    )
    assert not arts.reviews.empty
    assert not arts.sentiment_summary.empty
    assert not arts.weekly_stats.empty
    assert not arts.funnel.empty
    assert not arts.creatives.empty
    assert len(arts.figures) >= 5
    assert arts.report_path is not None
    assert arts.report_path.exists()


if __name__ == "__main__":
    test_pipeline_runs_with_mock_llm()
    print("✅ test_pipeline_runs_with_mock_llm passed")
