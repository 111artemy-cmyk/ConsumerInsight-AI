"""Data loading and synthetic sample-data generation.

For reproducibility the project ships with a small but realistic
synthetic dataset (~1500 reviews across 小红书 / 微博 / 天猫).
The generator is **deterministic** (controlled by ``RANDOM_SEED``) so
that every reviewer running the pipeline sees the same numbers.

Brand-name disclaimer
---------------------
The synthetic review corpus uses "花西子 Florasis" as the example brand
voice (see `src/config.py::IndustryConfig`). **This project is not
affiliated with, endorsed by, or related to the real Florasis / 花西子
brand** — the brand name is used purely as a stylistic placeholder so
the generated reviews read like real-world Chinese beauty reviews. All
reviews are programmatically synthesised; no real customer data is
involved and no statement is made about the real brand or its products.

The loader exposes a single function :func:`load_reviews` that returns a
cleaned ``pandas.DataFrame`` with the following columns:

* ``review_id``     — unique id
* ``platform``      — 小红书 / 微博 / 天猫
* ``user_id``       — anonymised user handle
* ``product``       — 产品名（如 空气蜜粉）
* ``rating``        — 1-5 星
* ``text``          — 评论原文
* ``timestamp``     — 评论时间
* ``user_age_band`` — 18-23 / 24-30 / 31-40 / 40+
* ``user_segment``  — 学生党 / 通勤族 / 成分党 / 精致妈妈
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .config import RANDOM_SEED


# ---------------------------------------------------------------------------
# Synthetic review corpus
# ---------------------------------------------------------------------------
# Each entry is a (segment, polarity, template) triple used by the
# generator below.  Templates use ``{kw_pos}`` / ``{kw_neg}`` placeholders
# that the generator fills from the corresponding lexicon so that the
# resulting text matches the assigned polarity.
# ---------------------------------------------------------------------------
POSITIVE_HOOKS = [
    "绝了", "太好用了", "回购第三次了", "被同事追问链接", "今天被夸了",
    "出门约会一整天都没脱妆", "早八通勤30秒搞定", "敏感肌友好",
    "粉质细腻到没朋友", "上脸就是奶油肌", "国货之光", "包装高级感拉满",
    "送礼首选", "被闺蜜抢走", "学生党闭眼入",
]
NEGATIVE_HOOKS = [
    "真的踩雷了", "姐妹们慎重", "用了一次就闲置", "完全不是宣传的那样",
    "拔干起皮到怀疑人生", "T区两小时就斑驳", "暗沉到我哭",
    "包装好看但是难用", "飞粉到我怀疑人生", "闷痘了", "敏感肌别碰",
    "客服不回消息", "快递压坏了包装",
]

POSITIVE_KW_POOL = [
    "粉质细腻", "服帖", "持妆", "奶油肌", "高级感", "包装好看", "国风设计",
    "平价", "敏感肌友好", "不拔干", "不卡粉", "显白", "回购", "送礼",
    "颜值高", "性价比", "妈生皮", "自然", "持久", "上镜",
]
NEGATIVE_KW_POOL = [
    "拔干", "卡粉", "脱妆", "暗沉", "氧化", "飞粉", "漏粉", "假白",
    "厚重", "闷痘", "刺激", "过敏", "色差", "包装差", "快递慢", "客服差",
    "踩雷", "不推荐", "退货",
]


@dataclass(frozen=True)
class _Segment:
    """A behavioural segment + the language patterns it tends to produce."""

    name: str                # user_segment
    age_bands: List[str]     # user_age_band options
    age_weights: List[float] # sampling weights aligned with age_bands
    platforms: List[str]
    platform_weights: List[float]
    pos_lex: List[str]
    neg_lex: List[str]
    pos_lex_extra: List[str]
    neg_lex_extra: List[str]


SEGMENTS: List[_Segment] = [
    _Segment(
        name="学生党",
        age_bands=["18-23"],
        age_weights=[1.0],
        platforms=["小红书", "抖音", "天猫"],
        platform_weights=[0.5, 0.2, 0.3],
        pos_lex=["平价", "颜值高", "回购", "学生党"],
        neg_lex=["踩雷", "预算有限"],
        pos_lex_extra=["约会", "答辩", "面试"],
        neg_lex_extra=["难用", "闲置"],
    ),
    _Segment(
        name="通勤族",
        age_bands=["24-30", "31-40"],
        age_weights=[0.7, 0.3],
        platforms=["小红书", "微博", "天猫"],
        platform_weights=[0.4, 0.3, 0.3],
        pos_lex=["持妆", "奶油肌", "快速", "通勤"],
        neg_lex=["斑驳", "脱妆"],
        pos_lex_extra=["早八", "加班", "通勤"],
        neg_lex_extra=["T区出油", "拔干起皮"],
    ),
    _Segment(
        name="成分党",
        age_bands=["24-30", "31-40"],
        age_weights=[0.5, 0.5],
        platforms=["小红书", "微博"],
        platform_weights=[0.6, 0.4],
        pos_lex=["成分", "敏感肌友好", "无刺激"],
        neg_lex=["刺激", "闷痘", "敏感肌"],
        pos_lex_extra=["成分透明", "无香精"],
        neg_lex_extra=["闷痘了", "成分看不懂"],
    ),
    _Segment(
        name="精致妈妈",
        age_bands=["31-40", "40+"],
        age_weights=[0.6, 0.4],
        platforms=["微博", "朋友圈", "天猫"],
        platform_weights=[0.4, 0.2, 0.4],
        pos_lex=["自然", "显白", "高级感", "不假白"],
        neg_lex=["假白", "厚重"],
        pos_lex_extra=["接送娃", "家长会", "聚会"],
        neg_lex_extra=["没时间补妆", "幼稚"],
    ),
]


def _weighted_choice(rng: random.Random, items: List, weights: List[float]):
    return rng.choices(items, weights=weights, k=1)[0]


def _synthesize_one(
    rng: random.Random,
    idx: int,
    product: str,
    base_ts,
) -> dict:
    """Build a single synthetic review record."""
    seg = rng.choice(SEGMENTS)
    age_band = _weighted_choice(rng, seg.age_bands, seg.age_weights)
    platform = _weighted_choice(rng, seg.platforms, seg.platform_weights)

    # Polarity: 65% positive, 25% neutral, 10% negative — realistic skew.
    polarity_roll = rng.random()
    if polarity_roll < 0.65:
        polarity = "pos"
        rating = rng.choices([4, 5], weights=[0.3, 0.7])[0]
        hooks = POSITIVE_HOOKS
        kw_pool = seg.pos_lex + POSITIVE_KW_POOL + seg.pos_lex_extra
    elif polarity_roll < 0.90:
        polarity = "neu"
        rating = 3
        hooks = ["还行吧", "一般般", "无功无过", "可以接受"]
        kw_pool = seg.pos_lex + seg.neg_lex
    else:
        polarity = "neg"
        rating = rng.choices([1, 2], weights=[0.7, 0.3])[0]
        hooks = NEGATIVE_HOOKS
        kw_pool = seg.neg_lex + NEGATIVE_KW_POOL + seg.neg_lex_extra

    n_kw = rng.randint(2, 4)
    keywords = rng.sample(list(set(kw_pool)), k=min(n_kw, len(set(kw_pool))))
    hook = rng.choice(hooks)
    body = f"{hook}，{ '、'.join(keywords) }。"

    # Platform-specific style tweak
    if platform == "小红书":
        body += " #花西子 #空气蜜粉"
    elif platform == "微博":
        body += " @花西子官方"
    elif platform == "天猫":
        body += "（已确认收货）"

    # Timestamp: spread across 90 days starting from base_ts
    days_offset = rng.randint(0, 89)
    hours_offset = rng.randint(8, 23)
    ts = base_ts + pd.Timedelta(days=days_offset, hours=hours_offset)

    user_id = "u_" + hashlib.md5(
        f"{seg.name}-{idx}".encode("utf-8")
    ).hexdigest()[:8]

    return {
        "review_id": f"R{idx:05d}",
        "platform": platform,
        "user_id": user_id,
        "product": product,
        "rating": int(rating),
        "text": body,
        "timestamp": ts,
        "user_age_band": age_band,
        "user_segment": seg.name,
        "_polarity": polarity,  # internal use, dropped by cleaner
    }


def generate_synthetic_reviews(
    n: int = 1500,
    product: str = "花西子 空气蜜粉",
    seed: int = RANDOM_SEED,
    start: str = "2025-06-01",
) -> pd.DataFrame:
    """Generate a deterministic synthetic review DataFrame."""
    rng = random.Random(seed)
    base_ts = pd.Timestamp(start)
    rows = [
        _synthesize_one(rng, i, product, base_ts) for i in range(1, n + 1)
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "review_id",
    "platform",
    "user_id",
    "product",
    "rating",
    "text",
    "timestamp",
    "user_age_band",
    "user_segment",
]


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Apply standard cleaning rules and return a tidy DataFrame."""
    if df.empty:
        return df.copy()

    out = df.copy()

    # Drop helper columns if present
    for col in ["_polarity"]:
        if col in out.columns:
            out = out.drop(columns=col)

    # Strip whitespace, normalise text
    out["text"] = out["text"].astype(str).map(lambda s: re.sub(r"\s+", " ", s).strip())
    out = out[out["text"].astype(bool)]

    # Deduplicate by (user_id, text)
    out = out.drop_duplicates(subset=["user_id", "text"])

    # Ensure required columns exist
    missing = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Force types
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["timestamp", "rating", "text"])

    return out.reset_index(drop=True)


def load_reviews(
    csv_path: Optional[Path] = None,
    *,
    use_synthetic: bool = True,
    n_synthetic: int = 1500,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Load review data from CSV, falling back to synthetic data.

    Parameters
    ----------
    csv_path:
        Optional path to a user-supplied CSV.  When provided and the
        file exists it is loaded and cleaned; when missing we generate
        synthetic data instead.
    use_synthetic:
        If True (default) and no CSV is supplied, generate synthetic
        data on the fly.  Set False to require a real file.
    n_synthetic:
        How many synthetic rows to generate when falling back.
    seed:
        Random seed for the synthetic generator. Used by the stability
        evaluation script to re-run the pipeline with multiple seeds.
        Ignored when ``csv_path`` is provided.
    """
    if csv_path is not None and Path(csv_path).exists():
        df = pd.read_csv(csv_path)
        return clean_reviews(df)
    if not use_synthetic:
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    df = generate_synthetic_reviews(n=n_synthetic, seed=seed)
    return clean_reviews(df)


def write_sample_csv(
    df: pd.DataFrame,
    out_path: Path,
) -> Path:
    """Persist a DataFrame to CSV for reproducibility."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path
