"""营销漏斗分析器。

在没有真实曝光/点击数据的情况下，我们用一个**评论-级软漏斗**来
呈现从「认知 → 兴趣 → 试用 → 满意 → 复购」的逐级转化：

| 阶段       | 代理信号                                               |
|------------|--------------------------------------------------------|
| 认知       | 评论存在                                              |
| 兴趣       | 评论中提到「想买」「种草」「想试试」                   |
| 试用       | 评论中提到「到了」「收到」「上脸」                     |
| 满意       | rating >= 4 且 overall >= 0.3                          |
| 复购       | 评论中提到「回购」「囤货」「再入」                      |

输出
----
:meth:`FunnelAnalyzer.run` 返回 :class:`FunnelResult`：
* ``stage_counts``   — 每阶段评论数与上一阶段的转化率
* ``stage_summary``  — 一句话总结哪一段流失最大
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class FunnelResult:
    stage_counts: pd.DataFrame
    stage_summary: str
    disclaimer: str = (
        "Soft funnel inferred from review text, NOT real behavioural "
        "conversion data (no impressions / clicks / orders). Treat as "
        "directional only."
    )


class FunnelAnalyzer:
    """Estimate a soft marketing funnel from review signals."""

    STAGES: List[dict] = [
        # 01 Awareness — 写评论 = 看到了产品
        {"stage": "01_Awareness", "predicate": lambda t: True},
        # 02 Interest — 既然愿意评论 = 感兴趣
        {"stage": "02_Interest", "predicate": lambda t: True},
        # 03 Trial — 描述了具体使用场景（动作词 / 场景词）
        # 关键词放宽到能覆盖大多数真实评论：使用动作 + 常见生活场景
        {"stage": "03_Trial", "predicate": lambda t: any(
            k in t for k in [
                # 使用动作
                "上脸", "用了", "回购", "收到", "到了", "试了", "用过",
                "买", "涂", "擦", "抹", "上妆", "上镜",
                # 生活场景
                "约会", "通勤", "答辩", "面试", "上班", "出门", "聚会",
                # 时长 / 频率
                "一整天", "8小时", "今天", "昨天", "第三次", "囤货",
                # 正面评价动词
                "回购", "推荐", "满意", "喜欢", "惊艳", "被夸",
            ]
        )},
        # 04 Satisfaction — 表达了正面感受
        {"stage": "04_Satisfaction", "predicate": lambda t: any(
            k in t for k in [
                "满意", "喜欢", "显白", "高级感", "好用", "完美", "回购",
                "惊艳", "奶油肌", "妈生皮", "服帖", "细腻", "持久",
            ]
        )},
        # 05 Repurchase — 表达复购/囤货
        {"stage": "05_Repurchase", "predicate": lambda t: any(
            k in t for k in ["回购", "囤货", "再入", "再买", "继续买", "第三次"]
        )},
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        df: pd.DataFrame,
        text_col: str = "text",
        rating_col: str = "rating",
        sentiment_col: str = "overall",
    ) -> FunnelResult:
        if df.empty:
            raise ValueError("Input DataFrame is empty.")
        df = df.copy()
        n = len(df)
        texts = df[text_col].astype(str).tolist()
        ratings = df[rating_col].fillna(3).to_numpy() if rating_col in df.columns else None
        sentiments = df[sentiment_col].fillna(0).to_numpy() if sentiment_col in df.columns else None

        counts = []
        prev_count = n
        # 关键修复：每个 stage 必须是前一个 stage 的子集（保证漏斗严格递减）
        prev_mask = [True] * n
        for stage in self.STAGES:
            predicate = stage["predicate"]
            base = [predicate(t) for t in texts]
            # 累积约束：当前 stage 必须在前一个 stage 内
            mask = [b and p for b, p in zip(base, prev_mask)]
            count = int(sum(mask))
            counts.append(
                {
                    "stage": stage["stage"],
                    "count": count,
                    "conversion_from_prev": (count / prev_count) if prev_count else 0.0,
                }
            )
            prev_count = count
            prev_mask = mask
        stage_df = pd.DataFrame(counts)
        stage_df["conversion_from_prev"] = stage_df["conversion_from_prev"].round(3)

        # Identify biggest drop
        if len(stage_df) > 1:
            drop_idx = stage_df["conversion_from_prev"].iloc[1:].idxmin()
            summary = (
                f"漏斗中转化率最低的阶段是 {stage_df.loc[drop_idx, 'stage']} "
                f"({stage_df.loc[drop_idx, 'conversion_from_prev']:.1%}). "
                f"建议优先在该阶段加强内容/促销/客服干预。"
            )
        else:
            summary = "数据不足以计算漏斗。"

        return FunnelResult(stage_counts=stage_df, stage_summary=summary)
