"""Centralised prompt library.

All prompts used by the analysis modules live here so they can be
audited, version-controlled, and unit-tested in one place.  This also
makes it trivial to translate the project to another language: replace
the constants below with the target-language versions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptLibrary:
    """Container for every prompt template used in the pipeline."""

    # ------------------------------------------------------------------
    # Multi-aspect sentiment analysis
    # ------------------------------------------------------------------
    SENTIMENT_SYSTEM: str = (
        "你是一名资深的中国美妆行业消费者洞察分析师，"
        "擅长从电商评论和社交媒体帖子中提炼用户对产品的多维度感受。"
    )

    SENTIMENT_USER_TEMPLATE: str = (
        "请阅读以下来自 {platform} 的用户文本，并针对以下 {n_dims} 个维度，"
        "分别给出 -1（负面）到 1（正面）的情感分数，并附一句话依据。\n\n"
        "维度列表：{dimensions}\n\n"
        "用户文本：\n\"\"\"\n{text}\n\"\"\"\n\n"
        "输出要求：\n"
        "1. 严格输出 JSON；\n"
        "2. 不要输出 JSON 之外的任何文字；\n"
        "3. 若文本与某维度无关，该维度分数为 0，依据写\"无关\"。"
    )

    # ------------------------------------------------------------------
    # Topic extraction
    # ------------------------------------------------------------------
    TOPIC_SYSTEM: str = (
        "你是一名市场研究分析师，专长是用 K-means / LDA 等主题建模思路"
        "从用户文本中提炼核心话题，并为每个话题给出可操作的营销标签。"
    )

    TOPIC_USER_TEMPLATE: str = (
        "以下是来自 {brand} 的 {n_reviews} 条用户评论（已去重）：\n\n"
        "{corpus}\n\n"
        "请提炼出 {n_topics} 个核心话题，对每个话题输出：\n"
        "- topic_id: 短英文/拼音标识符；\n"
        "- topic_label_cn: 4-6 字中文标签；\n"
        "- description: 一句话中文描述；\n"
        "- representative_keywords: 5 个关键词数组；\n"
        "- share_estimate: 占比估计（0-1 之间的小数）。\n\n"
        "严格以 JSON 数组输出。"
    )

    # ------------------------------------------------------------------
    # Persona generation
    # ------------------------------------------------------------------
    PERSONA_SYSTEM: str = (
        "你是一名资深的用户研究员，擅长基于定性文本数据合成"
        "具备明确人口学特征与消费动机的消费者画像（Persona）。"
    )

    PERSONA_USER_TEMPLATE: str = (
        "请基于以下 {n_clusters} 个细分受众群体的代表性评论，"
        "为每个群体生成一份结构化的 Persona 卡片：\n\n"
        "群体 {cid} 的代表性评论：\n{corpus_cid}\n\n"
        "Persona 卡片字段：\n"
        "- persona_id\n"
        "- nickname（2-4 字）\n"
        "- age_range\n"
        "- occupation\n"
        "- core_need（一句话）\n"
        "- pain_points（数组，3 条）\n"
        "- preferred_channels（数组，2-3 个）\n"
        "- recommended_campaign_angle（一句话）\n"
        "- sample_message: 一句可直接投放的朋友圈/小红书文案\n\n"
        "严格以 JSON 数组输出，每个群体一个对象。"
    )

    # ------------------------------------------------------------------
    # Campaign message generation
    # ------------------------------------------------------------------
    CAMPAIGN_SYSTEM: str = (
        "你是一名美妆品牌的资深内容营销官，懂 Z 世代语言、"
        "会写小红书种草文案，能针对不同细分人群输出高转化的营销内容。"
    )

    CAMPAIGN_USER_TEMPLATE: str = (
        "目标人群 Persona：\n{persona}\n\n"
        "本轮营销活动目标：{objective}\n"
        "活动卖点：\n{highlights}\n\n"
        "请生成 {n_variants} 条候选营销文案，每条包含：\n"
        "- variant_id\n"
        "- channel（小红书 / 微博 / 抖音 / 朋友圈）\n"
        "- headline（不超过 18 字）\n"
        "- body（不超过 80 字）\n"
        "- hashtags（数组，3-5 个）\n"
        "- predicted_ctr（0-1 之间的小数，基于经验估计）\n"
        "- rationale（一句话解释为什么这个人群会点开）\n\n"
        "严格以 JSON 数组输出。"
    )
