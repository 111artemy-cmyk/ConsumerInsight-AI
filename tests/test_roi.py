"""Unit tests for the roi_predictor module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.marketing_analytics.roi_predictor import ROIPredictor  # noqa: E402


def _reviews(n: int = 200, repurchase_share: float = 0.2) -> pd.DataFrame:
    """Build a minimal per-review frame with three clusters."""
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n):
        cluster = i % 3
        # Cluster 0: positive, Cluster 1: negative, Cluster 2: neutral
        if cluster == 0:
            text = f"回购第{i}次了，粉质细腻服帖，持妆一整天{('，回购' if rng.random() < repurchase_share else '')}"
            rating = 5
            overall = 0.9
        elif cluster == 1:
            text = f"拔干起皮，飞粉到我怀疑人生{('，回购' if rng.random() < repurchase_share else '')}"
            rating = 1
            overall = -0.9
        else:
            text = f"还行吧，一般般{('，回购' if rng.random() < repurchase_share else '')}"
            rating = 3
            overall = 0.0
        rows.append(
            {
                "review_id": f"R{i:04d}",
                "text": text,
                "rating": rating,
                "overall": overall,
                "cluster_id": cluster,
            }
        )
    return pd.DataFrame(rows)


def test_roi_predictor_rejects_empty_input():
    pred = ROIPredictor()
    try:
        pred.fit_predict(pd.DataFrame())
    except ValueError:
        return
    raise AssertionError("Expected ValueError for empty input")


def test_roi_predictor_returns_expected_columns():
    pred = ROIPredictor()
    result = pred.fit_predict(_reviews())
    # Per-segment aggregation must include the key columns
    expected = {
        "cluster_id",
        "volume",
        "avg_sentiment",
        "avg_rating",
        "predicted_soft_conversion",
        "expected_revenue",
        "expected_cost",
        "expected_roi",
    }
    assert expected.issubset(set(result.segment_roi.columns))
    # Coefficients frame has one row per feature
    assert len(result.coefficients) == 4
    assert set(result.coefficients["feature"]) == {
        "overall",
        "high_rating",
        "long_text",
        "repurchase_intent",
    }


def test_roi_predictor_positive_segment_outranks_negative():
    pred = ROIPredictor()
    result = pred.fit_predict(_reviews())
    segs = result.segment_roi.set_index("cluster_id")
    # Cluster 0 has positive sentiment + repurchase intent;
    # Cluster 1 is strongly negative. Expected ROI must reflect this.
    assert segs.loc[0, "expected_roi"] > segs.loc[1, "expected_roi"]
    # Sanity: positive segment's predicted soft_conversion > negative segment's
    assert (
        segs.loc[0, "predicted_soft_conversion"]
        > segs.loc[1, "predicted_soft_conversion"]
    )


if __name__ == "__main__":
    test_roi_predictor_rejects_empty_input()
    test_roi_predictor_returns_expected_columns()
    test_roi_predictor_positive_segment_outranks_negative()
    print("✅ roi tests passed")