"""多维度细粒度情感分析。

设计目标
--------
1. 不依赖任何付费 API：默认调用 :class:`MockLLMClient` 完成推理。
2. 支持真实 LLM（OpenAI / 智谱 GLM / DeepSeek …）：传入任何
   :class:`BaseLLMClient` 子类即可。
3. 输出结果既包含**每条评论的细粒度情感分数**，也提供**整体统计**
   （平均分、维度分布、时间趋势），可直接喂给下游可视化模块。

情感维度
--------
默认六个维度，覆盖美妆品类最常被讨论的体验切面：

* Product Quality       — 产品质量（粉质、服帖度、持妆力）
* Value for Money       — 性价比（价格、促销、赠品）
* Packaging Design      — 包装设计（颜值、国风、雕花）
* Skin Feel             — 上脸肤感（服帖、拔干、刺激）
* Long Wear             — 持久度（脱妆、氧化、斑驳）
* Service Experience    — 服务体验（快递、客服、售后）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import SENTIMENT_DIMENSIONS
from ..llm import BaseLLMClient, PromptLibrary


@dataclass
class SentimentResult:
    """Container for sentiment analysis outputs."""

    per_review: pd.DataFrame   # 一行一条评论，列包含各维度分数 + overall
    summary: pd.DataFrame      # 整体：每个维度的平均分
    by_segment: pd.DataFrame   # 按用户细分交叉的均值


class SentimentAnalyzer:
    """Run multi-aspect sentiment analysis on a review DataFrame."""

    def __init__(
        self,
        llm: BaseLLMClient,
        dimensions: Optional[List[str]] = None,
    ):
        self.llm = llm
        self.dimensions = dimensions or list(SENTIMENT_DIMENSIONS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        df: pd.DataFrame,
        text_col: str = "text",
        platform_col: str = "platform",
    ) -> SentimentResult:
        """对 DataFrame 中的每条评论做多维度情感分析。"""
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        rows: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            payload = self._analyze_one(str(row[text_col]), str(row[platform_col]))
            payload["review_id"] = row.get("review_id")
            payload["platform"] = row.get(platform_col)
            payload["user_segment"] = row.get("user_segment")
            payload["user_age_band"] = row.get("user_age_band")
            payload["rating"] = row.get("rating")
            payload["timestamp"] = row.get("timestamp")
            rows.append(payload)

        per_review = pd.DataFrame(rows)

        # Build dimension summary
        dim_cols = [d for d in self.dimensions if d in per_review.columns]
        summary = (
            per_review[dim_cols]
            .mean()
            .rename("avg_score")
            .reset_index()
            .rename(columns={"index": "dimension"})
        )

        # Cross-tab by user_segment
        if "user_segment" in per_review.columns:
            by_segment = (
                per_review.groupby("user_segment")[dim_cols]
                .mean()
                .reset_index()
            )
        else:
            by_segment = pd.DataFrame()

        return SentimentResult(per_review=per_review, summary=summary, by_segment=by_segment)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _analyze_one(self, text: str, platform: str) -> Dict[str, Any]:
        """对单条评论做 LLM 调用并解析结果。"""
        system = PromptLibrary.SENTIMENT_SYSTEM
        user = PromptLibrary.SENTIMENT_USER_TEMPLATE.format(
            platform=platform,
            n_dims=len(self.dimensions),
            dimensions="、".join(self.dimensions),
            text=text,
        )
        resp = self.llm.complete_json(system, user)
        data = resp.as_dict()
        overall = float(data.get("overall", 0.0))
        out: Dict[str, Any] = {"overall": overall}
        dims = data.get("dimensions") or {}
        for d in self.dimensions:
            entry = dims.get(d) or {}
            out[d] = float(entry.get("score", 0.0)) if isinstance(entry, dict) else 0.0
        return out
