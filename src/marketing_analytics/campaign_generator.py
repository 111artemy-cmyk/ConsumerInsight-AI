"""营销文案生成器。

输入
----
* :class:`PersonaGenerator` 生成的 Persona 列表（DataFrame）
* 营销活动目标（objective）
* 卖点（highlights）

输出
----
每条 Persona 对应多渠道、多版本的文案候选，并附带：

* predicted_ctr        : 预测点击率
* rationale            : 选择该渠道的理由
* recommended_budget   : 建议预算分配（占总预算比例）
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import IndustryConfig
from ..llm import BaseLLMClient, PromptLibrary


@dataclass
class CampaignResult:
    creatives: pd.DataFrame
    budget_plan: pd.DataFrame


class CampaignGenerator:
    """Generate persona-targeted marketing copy."""

    def __init__(
        self,
        llm: BaseLLMClient,
        industry: Optional[IndustryConfig] = None,
        n_variants_per_persona: int = 3,
    ):
        self.llm = llm
        self.industry = industry or IndustryConfig()
        self.n_variants = max(1, n_variants_per_persona)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        personas: pd.DataFrame,
        objective: Optional[str] = None,
        highlights: Optional[List[str]] = None,
    ) -> CampaignResult:
        if personas.empty:
            raise ValueError("Persona DataFrame is empty.")
        objective = objective or self.industry.campaign_objective
        highlights = highlights or [
            "空气蜜粉：粉质细腻，8小时持妆不暗沉",
            "国风限定礼盒：雕花包装，自用送礼两相宜",
            "敏感肌友好：通过 SGS 敏感肌测试",
        ]
        highlights_str = "\n".join(f"- {h}" for h in highlights)

        all_creatives: List[Dict[str, Any]] = []
        for _, persona in personas.iterrows():
            variants = self._variants_for(persona, objective, highlights_str)
            for v in variants:
                v["persona_id"] = persona.get("persona_id", "")
                v["persona_nickname"] = persona.get("nickname", "")
                all_creatives.append(v)

        creatives_df = pd.DataFrame(all_creatives)

        # Budget plan: weight by predicted CTR
        if not creatives_df.empty and "predicted_ctr" in creatives_df.columns:
            budget = (
                creatives_df.groupby("channel")["predicted_ctr"]
                .mean()
                .reset_index()
                .rename(columns={"predicted_ctr": "avg_ctr"})
            )
            total = budget["avg_ctr"].sum() or 1.0
            budget["budget_share"] = (budget["avg_ctr"] / total).round(3)
        else:
            budget = pd.DataFrame()

        return CampaignResult(creatives=creatives_df, budget_plan=budget)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _variants_for(
        self,
        persona: pd.Series,
        objective: str,
        highlights: str,
    ) -> List[Dict[str, Any]]:
        persona_dict = persona.to_dict()
        # Stringify everything so it can be serialised into the prompt
        persona_json = json.dumps(persona_dict, ensure_ascii=False, default=str)
        system = PromptLibrary.CAMPAIGN_SYSTEM
        user = PromptLibrary.CAMPAIGN_USER_TEMPLATE.format(
            persona=persona_json,
            objective=objective,
            highlights=highlights,
            n_variants=self.n_variants,
        )
        resp = self.llm.complete_json(system, user)
        if isinstance(resp.parsed, list):
            return resp.parsed
        return [{"variant_id": "V01", "channel": "通用", "headline": "", "body": resp.text}]
