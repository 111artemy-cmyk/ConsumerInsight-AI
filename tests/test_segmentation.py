"""Unit tests for the segmentation module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.marketing_analytics import Segmenter  # noqa: E402


def test_segmenter_runs_on_minimal_frame():
    df = pd.DataFrame(
        {
            "review_id": [f"R{i:03d}" for i in range(30)],
            "platform": ["小红书", "天猫", "微博"] * 10,
            "user_age_band": ["18-23", "24-30", "31-40"] * 10,
            "rating": [5, 4, 3, 2, 1] * 6,
            "user_segment": ["学生党", "通勤族", "成分党", "精致妈妈"] * 7 + ["学生党", "通勤族"],
            "text": [
                "粉质细腻，服帖，奶油肌" if i % 2 else "拔干起皮，飞粉，T区斑驳"
                for i in range(30)
            ],
        }
    )
    res = Segmenter(n_segments=3).run(df)
    assert not res.assignments.empty
    assert set(res.assignments["cluster_id"]).issubset({0, 1, 2})
    assert not res.segment_profile.empty


if __name__ == "__main__":
    test_segmenter_runs_on_minimal_frame()
    print("✅ segmentation test passed")
