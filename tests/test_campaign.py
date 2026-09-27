"""Unit tests for the campaign_generator module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.llm.mock_client import MockLLMClient  # noqa: E402
from src.marketing_analytics.campaign_generator import CampaignGenerator  # noqa: E402


def _personas() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "persona_id": "P01",
                "nickname": "通勤奶油肌Lisa",
                "age_range": "25-30",
                "occupation": "互联网公司市场运营",
                "core_need": "快速打造持久自然的奶油肌通勤底妆",
                "recommended_campaign_angle": "30 秒奶油肌挑战 + 国风限定礼盒",
                "why_matters": "规模最大 + ROI 峰值之一，是 GMV 基本盘",
            },
            {
                "persona_id": "P02",
                "nickname": "成分党小美",
                "age_range": "28-35",
                "occupation": "美妆博主",
                "core_need": "成分安全、性价比高",
                "recommended_campaign_angle": "成分透明化对比测评",
                "why_matters": "中等规模，社交传播力强",
            },
        ]
    )


def test_campaign_generator_rejects_empty_personas():
    gen = CampaignGenerator(MockLLMClient(), n_variants_per_persona=3)
    try:
        gen.run(personas=pd.DataFrame())
    except ValueError:
        return
    raise AssertionError("Expected ValueError for empty persona DataFrame")


def test_campaign_generator_produces_n_personas_x_n_variants_rows():
    gen = CampaignGenerator(MockLLMClient(), n_variants_per_persona=3)
    personas = _personas()
    result = gen.run(personas=personas)
    # 2 personas × 3 variants per persona = 6 rows
    assert len(result.creatives) == 6
    # persona_id / persona_nickname must be propagated
    assert set(result.creatives["persona_id"]) == {"P01", "P02"}
    assert set(result.creatives["persona_nickname"]) == {
        "通勤奶油肌Lisa",
        "成分党小美",
    }
    # predicted_ctr column must exist and be a numeric range
    assert "predicted_ctr" in result.creatives.columns
    ctrs = result.creatives["predicted_ctr"].astype(float)
    assert ctrs.between(0.0, 1.0).all()


def test_campaign_generator_budget_plan_sums_to_one():
    gen = CampaignGenerator(MockLLMClient(), n_variants_per_persona=3)
    result = gen.run(personas=_personas())
    # Budget plan: per-channel CTR-weighted share, must sum to ~1.0
    assert not result.budget_plan.empty
    total = result.budget_plan["budget_share"].sum()
    assert abs(total - 1.0) < 0.05, f"budget share should sum to ~1.0, got {total}"


if __name__ == "__main__":
    test_campaign_generator_rejects_empty_personas()
    test_campaign_generator_produces_n_personas_x_n_variants_rows()
    test_campaign_generator_budget_plan_sums_to_one()
    print("✅ campaign tests passed")