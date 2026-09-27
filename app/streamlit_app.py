"""Streamlit demo for ConsumerInsight-AI.

Run with::

    streamlit run app/streamlit_app.py

The app loads (or runs) the pipeline and exposes every artefact in an
interactive dashboard so reviewers can experience the project without
touching the code.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `src` importable as a package when running `streamlit run app/streamlit_app.py`.
# 把项目根目录加入 sys.path，让 `src` 能被识别为 package，
# 这样 src/pipeline.py 里的相对导入才能工作。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.config import IndustryConfig
from src.pipeline import run_full_pipeline

st.set_page_config(
    page_title="ConsumerInsight-AI",
    page_icon="💄",
    layout="wide",
)

st.title("ConsumerInsight-AI")
st.caption(
    "A hybrid framework combining LLM and Marketing Analytics for "
    "automated consumer insights and campaign generation."
)


@st.cache_resource(show_spinner="Running full pipeline (first run only)...")
def _run_pipeline_cached():
    return run_full_pipeline(
        n_reviews=600,
        use_synthetic=True,
        llm_backend="auto",
        llm_model="gpt-4o-mini",
    )


with st.spinner("Loading artefacts…"):
    arts = _run_pipeline_cached()

# ---------------------------------------------------------------------------
# Sidebar — navigation + filters
# ---------------------------------------------------------------------------
section = st.sidebar.radio(
    "导航",
    [
        "1. 项目概览",
        "2. 数据概览",
        "3. 多维度情感",
        "4. 核心话题",
        "5. 消费者 Persona",
        "6. 受众细分",
        "7. 趋势 & 漏斗",
        "8. ROI 预估",
        "9. 营销文案候选",
        "10. 方法说明",
    ],
)

# ---------------------------------------------------------------------------
# Section 1: Overview
# ---------------------------------------------------------------------------
if section == "1. 项目概览":
    st.header("项目概览")
    st.markdown(
        """
        **研究问题**：如何把大语言模型 (LLM) 与经典营销分析方法结合，
        从社交媒体评论中**自动提炼消费者洞察**并**生成数据驱动的
        营销内容**？

        **方法亮点**：
        1. 可插拔 LLM 客户端（Mock / OpenAI / 兼容端点），保证 0 成本可复现；
        2. **多维度细粒度情感分析**（产品 / 性价比 / 包装 / 肤感 / 持久 / 服务）；
        3. **TF-IDF + LLM 协同的主题建模**，每个主题带营销标签与代表关键词；
        4. **KMeans + LLM Persona 合成**，把聚类结果翻译为可执行的人群画像；
        5. **软漏斗 + 复购代理信号 + Ridge 回归**得到细分群 ROI 估算；
        6. 针对每个 Persona 生成**多渠道营销文案**并附预测 CTR 与预算建议。
        """
    )
    cols = st.columns(3)
    cols[0].metric("评论数", len(arts.reviews))
    cols[1].metric("细分群数", arts.segment_profile.shape[0])
    cols[2].metric("Persona 数", len(arts.personas))
    cols = st.columns(2)
    cols[0].metric("核心话题数", len(arts.topics))
    cols[1].metric("候选文案数", len(arts.creatives))

# ---------------------------------------------------------------------------
# Section 2: Data overview
# ---------------------------------------------------------------------------
elif section == "2. 数据概览":
    st.header("数据概览")
    st.dataframe(arts.reviews.head(50), use_container_width=True)
    st.bar_chart(arts.reviews["platform"].value_counts())
    st.bar_chart(arts.reviews["user_segment"].value_counts())
    st.bar_chart(arts.reviews["rating"].value_counts().sort_index())

# ---------------------------------------------------------------------------
# Section 3: Sentiment
# ---------------------------------------------------------------------------
elif section == "3. 多维度情感":
    st.header("多维度情感分析")
    st.dataframe(arts.sentiment_summary, use_container_width=True)
    if "sentiment_by_dimension" in arts.figures:
        st.image(str(arts.figures["sentiment_by_dimension"]), use_column_width=True)
    if not arts.sentiment_by_segment.empty:
        st.subheader("细分人群在各维度上的情感差异")
        st.dataframe(arts.sentiment_by_segment, use_container_width=True)
        if "sentiment_by_segment" in arts.figures:
            st.image(str(arts.figures["sentiment_by_segment"]), use_column_width=True)

# ---------------------------------------------------------------------------
# Section 4: Topics
# ---------------------------------------------------------------------------
elif section == "4. 核心话题":
    st.header("核心话题提取")
    if not arts.topics.empty:
        st.dataframe(arts.topics, use_container_width=True)
    if "topic_share" in arts.figures:
        st.image(str(arts.figures["topic_share"]), use_column_width=True)
    st.subheader("全语料 TF-IDF 关键词")
    st.dataframe(arts.topic_keywords, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 5: Personas
# ---------------------------------------------------------------------------
elif section == "5. 消费者 Persona":
    st.header("消费者 Persona")
    st.dataframe(arts.personas, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 6: Segmentation
# ---------------------------------------------------------------------------
elif section == "6. 受众细分":
    st.header("受众细分")
    st.dataframe(arts.segment_profile, use_container_width=True)
    if "segment_share" in arts.figures:
        st.image(str(arts.figures["segment_share"]), use_column_width=True)

# ---------------------------------------------------------------------------
# Section 7: Trends & Funnel
# ---------------------------------------------------------------------------
elif section == "7. 趋势 & 漏斗":
    st.header("周度趋势 & 软漏斗")
    st.dataframe(arts.weekly_stats, use_container_width=True)
    if "weekly_trend" in arts.figures:
        st.image(str(arts.figures["weekly_trend"]), use_column_width=True)
    st.subheader("软转化漏斗")
    st.dataframe(arts.funnel, use_container_width=True)
    if "funnel" in arts.figures:
        st.image(str(arts.figures["funnel"]), use_column_width=True)

# ---------------------------------------------------------------------------
# Section 8: ROI
# ---------------------------------------------------------------------------
elif section == "8. ROI 预估":
    st.header("细分群 ROI 预估")
    st.dataframe(arts.roi, use_container_width=True)
    if "roi" in arts.figures:
        st.image(str(arts.figures["roi"]), use_column_width=True)

# ---------------------------------------------------------------------------
# Section 9: Creatives
# ---------------------------------------------------------------------------
elif section == "9. 营销文案候选":
    st.header("营销文案候选")
    if not arts.creatives.empty:
        st.dataframe(arts.creatives, use_container_width=True)
    if not arts.budget_plan.empty:
        st.subheader("渠道预算分配建议")
        st.dataframe(arts.budget_plan, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 10: Methodology
# ---------------------------------------------------------------------------
elif section == "10. 方法说明":
    st.header("方法说明")
    st.markdown(
        """
        **数据**：内置 600 条合成评论，覆盖小红书 / 微博 / 天猫，
        4 类细分人群（学生党 / 通勤族 / 成分党 / 精致妈妈）。

        **情感分析**：LLM 输出 JSON，每个维度返回 [-1, +1] 情感分 + 依据。
        Mock LLM 使用关键词词典 + 强化/否定修饰规则生成确定性格式化结果。

        **主题提取**：LLM 输出主题 JSON，TF-IDF 验证关键词。
        主题 ID 与代表关键词用于将每条评论分配到最近主题。

        **Persona 生成**：TF-IDF + KMeans 聚类 → 每个聚类的代表评论
        → LLM 合成 Persona 卡片（昵称/年龄/痛点/渠道/文案样例）。

        **ROI 预估**：基于情感/评分/复购意愿构建"软转化"代理指标，
        用 Ridge 回归得到各细分群的可解释 ROI 与 95% 置信区间。

        **营销文案**：每个 Persona × 多渠道 × 多版本，
        输出包含 headline / body / hashtags / predicted_ctr / rationale。
        """
    )
