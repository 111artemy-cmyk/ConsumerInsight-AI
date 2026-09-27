"""Project configuration for ConsumerInsight-AI.

Centralises paths, random seeds, and feature flags so that the
pipeline can be reproduced end-to-end from a single place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"
FIGURES_DIR: Path = OUTPUT_DIR / "figures"
REPORTS_DIR: Path = OUTPUT_DIR / "reports"

for _dir in (PROCESSED_DATA_DIR, FIGURES_DIR, REPORTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED: int = 42


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------
@dataclass
class LLMConfig:
    """Configuration for the (pluggable) language model backend.

    Two backends are shipped:
        * ``mock``   — fully offline rule-based mock (default; no API key).
        * ``openai`` — OpenAI Chat Completions API. Requires ``OPENAI_API_KEY``.
    """

    backend: str = os.getenv("CI_LLM_BACKEND", "mock")
    model: str = os.getenv("CI_LLM_MODEL", "gpt-4o-mini")
    temperature: float = 0.2
    max_retries: int = 3
    request_timeout_s: float = 30.0


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class IndustryConfig:
    """Brand- and industry-level configuration used throughout the pipeline."""

    industry: str = "美妆 (Beauty / Cosmetics)"
    brand_name: str = "花西子 Florasis"
    target_markets: List[str] = field(
        default_factory=lambda: ["中国大陆", "中国香港", "海外华人市场"]
    )
    primary_platforms: List[str] = field(
        default_factory=lambda: ["小红书", "微博", "天猫"]
    )
    campaign_objective: str = (
        "提升 25-35 岁女性用户对新品（空气蜜粉）的购买转化率"
    )


# ---------------------------------------------------------------------------
# Sentiment lexicon (compact, hand-crafted; easy to extend)
# ---------------------------------------------------------------------------
POSITIVE_KEYWORDS: List[str] = [
    "好", "棒", "喜欢", "推荐", "惊艳", "完美", "超值", "满意", "回购",
    "持久", "细腻", "高级感", "服帖", "自然", "显白", "精致", "好用",
    "颜值高", "设计感", "质感", "丝滑", "清透", "持妆",
]
NEGATIVE_KEYWORDS: List[str] = [
    "差", "失望", "难用", "浮粉", "拔干", "卡粉", "脱妆", "暗沉", "厚重",
    "假白", "刺激", "过敏", "爆痘", "闷痘", "踩雷", "不推荐", "退货",
    "包装差", "漏粉", "飞粉", "色差", "氧化",
]

# Fine-grained sentiment dimensions used in the multi-aspect analysis.
# Use Title Case with spaces so they look professional in English-facing
# charts and tables (no snake_case underscores).
SENTIMENT_DIMENSIONS: List[str] = [
    "Product Quality",       # 产品质量
    "Value for Money",       # 性价比
    "Packaging Design",      # 包装设计
    "Skin Feel",             # 上脸肤感
    "Long Wear",             # 持久度
    "Service Experience",    # 服务体验
]
