"""Reusable matplotlib chart helpers.

Every function follows the same pattern:

    fig_path = plot_xxx(df_or_data, ..., out_path=Path(...))

Design principles
-----------------
* Single shared style (clean grid, muted palette, English labels)
* Every chart has a title + subtitle + source line
* Numbers are labelled directly on bars (no need to squint at axes)
* Output is 150 DPI PNG sized for an A4 portfolio page

This keeps the pipeline code declarative and makes it trivial to
swap the backend later (e.g. switch to plotly for the Streamlit demo).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

import matplotlib.font_manager as fm

# ---------------------------------------------------------------------------
# Fonts & global style
# ---------------------------------------------------------------------------
_CJK_FONTS = [
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "PingFang SC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "SimHei",
    "WenQuanYi Zen Hei",
]
for _f in _CJK_FONTS:
    if any(_f in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [_f]
        break
plt.rcParams["axes.unicode_minus"] = False

# Soft, professional palette
PALETTE = {
    "primary": "#3a5a78",     # deep blue-grey
    "accent":  "#c9532a",     # burnt orange (for emphasis)
    "good":    "#2e8b57",     # sea green (positive)
    "bad":     "#b03a2e",     # brick red (negative)
    "neutral": "#7d7d7d",     # mid grey
    "tint":    "#cfd8e3",     # light blue-grey
}

# Matplotlib defaults for portfolio-quality output
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#e8e8e8",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.7,
    "axes.axisbelow": True,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "legend.frameon": False,
})


def _save(fig, out_path: Path, dpi: int = 150) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _add_source(fig, source: str) -> None:
    """Add a small footer with the data source."""
    # Move the source line slightly higher so it sits clear of the chart's
    # x-axis label and well above the insight box (when one is present).
    fig.text(0.99, -0.04, source, ha="right", va="bottom",
             fontsize=8, color="#888888", style="italic")


def _add_insight(fig, text: str, y: float = -0.11) -> None:
    """Add a highlighted insight box at the BOTTOM of the figure (out of the way).

    Note: emoji-free to avoid CJK-font glyph warnings.
    The box is pushed further down (y=-0.11) so there is a clear gap
    between it and the source line above.
    """
    fig.text(0.5, y, text, ha="center", va="top",
             fontsize=9.5, color="#444444",
             bbox=dict(boxstyle="round,pad=0.45",
                       facecolor="#f4f1de", edgecolor="#d4cc9a", linewidth=0.8))


# ---------------------------------------------------------------------------
# Chart 01 — Sentiment by dimension
# ---------------------------------------------------------------------------
def plot_sentiment_by_dimension(
    summary: pd.DataFrame,
    out_path: Path,
    title: str = "Multi-Aspect Sentiment Score",
    subtitle: str = "Average sentiment across six product-experience dimensions (range -1 to +1)",
    n_reviews: Optional[int] = None,
) -> Path:
    df = summary.sort_values("avg_score")
    colors = [PALETTE["bad"] if v < 0 else PALETTE["good"] for v in df["avg_score"]]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.barh(df["dimension"], df["avg_score"], color=colors, edgecolor="white")
    ax.set_xlim(-1, 1)
    ax.axvline(0, color="#444", linewidth=0.6)
    ax.set_xlabel("Sentiment Score (-1 Negative · 0 Neutral · +1 Positive, unitless)")
    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")

    for bar, val in zip(bars, df["avg_score"]):
        offset = 0.03 if val >= 0 else -0.03
        ha = "left" if val >= 0 else "right"
        ax.text(val + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center", ha=ha, fontsize=9)

    _add_source(fig, _source_line(n_reviews, "Lexicon-based multi-aspect sentiment scoring"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Chart 02 — Sentiment by segment (grouped bar)
# ---------------------------------------------------------------------------
def plot_sentiment_by_segment(
    by_segment: pd.DataFrame,
    out_path: Path,
    dimensions: Optional[list] = None,
    title: str = "Sentiment Differences Across Audience Segments",
    subtitle: str = "Where each persona loves the brand and where it disappoints",
    n_reviews: Optional[int] = None,
) -> Path:
    if by_segment.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No segment data", ha="center", va="center")
        return _save(fig, out_path)
    df = by_segment.set_index("user_segment")
    cols = dimensions or [c for c in df.columns if c != "user_segment"]
    df = df[cols]

    fig, ax = plt.subplots(figsize=(10, 5))
    n_seg = len(df)
    n_dim = len(cols)
    x = np.arange(n_seg)
    width = 0.8 / n_dim
    cmap = plt.get_cmap("Set2")
    for i, dim in enumerate(cols):
        ax.bar(x + i * width - 0.4 + width / 2, df[dim], width=width, label=dim, color=cmap(i))
    ax.set_xticks(x)
    ax.set_xticklabels(df.index, rotation=0)
    ax.set_ylabel("Average Sentiment Score (unitless, range -1 to +1)")
    ax.axhline(0, color="#444", linewidth=0.6)
    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
              ncol=min(3, n_dim), frameon=False, fontsize=8)
    _add_source(fig, _source_line(n_reviews, "KMeans segments × sentiment dimensions"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Chart 03 — Audience segmentation share (horizontal bars + profile)
# ---------------------------------------------------------------------------
def plot_segment_share(
    assignments: pd.DataFrame,
    segment_profile: pd.DataFrame,
    out_path: Path,
    title: str = "Audience Segmentation (Synthetic — Illustrative Only)",
    subtitle: str = "Four behavioural clusters extracted from review text + ratings + platform",
    n_reviews: Optional[int] = None,
) -> Path:
    counts = (
        assignments["cluster_id"].value_counts(normalize=True).sort_index() * 100
    ).round(1)

    # 拼一个 "cluster_id · 代表关键词" 的标签（如果 profile 里有 cluster_keywords）
    labels = [f"Segment {i}" for i in counts.index]
    if not segment_profile.empty and "avg_rating" in segment_profile.columns:
        ratings = segment_profile.set_index("segment_id")["avg_rating"].round(2)
        labels = [
            f"Segment {i}  ·  avg ★ {ratings.get(i, '—')}"
            for i in counts.index
        ]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(labels, counts.values, color=PALETTE["primary"], edgecolor="white")
    ax.set_xlim(0, max(counts.values) * 1.25)
    ax.set_xlabel("Share of Reviews (%, within synthetic corpus)")
    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")
    ax.invert_yaxis()

    for bar, v in zip(bars, counts.values):
        ax.text(v + 1.5, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=10, fontweight="bold")

    _add_insight(
        fig,
        f"→ Insight: Segment {counts.idxmax()} dominates with "
        f"{counts.max():.1f}% share — prioritise ad targeting there.",
    )
    _add_source(fig, _source_line(n_reviews, "KMeans on TF-IDF + OneHot(platform, age) + rating"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Chart 04 — Topic share (horizontal bar with description)
# ---------------------------------------------------------------------------
def plot_topic_share(
    topics: pd.DataFrame,
    out_path: Path,
    title: str = "Core Discussion Topics (LLM + TF-IDF Cross-Check)",
    subtitle: str = "Five themes automatically extracted from consumer reviews",
    n_reviews: Optional[int] = None,
) -> Path:
    # 兼容真实 LLM 输出字段差异：real LLM（OpenAI / GLM / DeepSeek）未必给出
    # "topic_label_cn"，可能用 "name" / "label" / "title"。统一兜底到 topic_label_cn。
    if not topics.empty:
        rename_map = {
            "name": "topic_label_cn",
            "label": "topic_label_cn",
            "title": "topic_label_cn",
            "weight": "share_estimate",
            "share": "share_estimate",
            "ratio": "share_estimate",
        }
        topics = topics.rename(columns={k: v for k, v in rename_map.items() if k in topics.columns})

    if topics.empty or "share_estimate" not in topics.columns or "topic_label_cn" not in topics.columns:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.text(0.5, 0.5,
                "No topic data available — increase review volume or "
                "extend the LLM temperature.",
                ha="center", va="center", fontsize=11, color="#888")
        ax.set_axis_off()
        return _save(fig, out_path)

    df = topics.sort_values("share_estimate", ascending=True).copy()
    # Build a one-line annotation from description
    df["annotation"] = df.apply(
        lambda r: f"{(r.get('description') or '')[:48]}…"
                  f"  ({', '.join((r.get('representative_keywords') or [])[:3])})",
        axis=1,
    )

    fig, ax = plt.subplots(figsize=(10, 5.2))
    bars = ax.barh(df["topic_label_cn"], df["share_estimate"] * 100,
                   color=PALETTE["accent"], edgecolor="white")
    ax.set_xlim(0, max(df["share_estimate"] * 100) * 1.35)
    ax.set_xlabel("Share of Voice (%, within synthetic corpus)")
    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")

    for bar, val, ann in zip(bars, df["share_estimate"], df["annotation"]):
        ax.text(val * 100 + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val*100:.1f}%", va="center", fontsize=10, fontweight="bold")
        ax.text(val * 100 + 4.5, bar.get_y() + bar.get_height() / 2,
                ann, va="center", fontsize=8, color="#666", style="italic")

    if not df.empty:
        top = df.iloc[-1]
        _add_insight(
            fig,
            f"→ Insight: 「{top['topic_label_cn']}」 leads with "
            f"{top['share_estimate']*100:.1f}% share — align content strategy with it.",
        )

    _add_source(fig, _source_line(n_reviews, "LLM topic extraction + TF-IDF cross-check"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Chart 05 — Weekly trend (line + bar combo)
# ---------------------------------------------------------------------------
def plot_weekly_trend(
    weekly_stats: pd.DataFrame,
    out_path: Path,
    title: str = "Weekly Sentiment Trend (Synthetic — Illustrative Only)",
    subtitle: str = "Average sentiment (line) and review volume (bars) over time",
    n_reviews: Optional[int] = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.plot(weekly_stats["week"], weekly_stats["avg_sentiment"],
            marker="o", linewidth=2.4, markersize=6,
            color=PALETTE["primary"], label="Avg Sentiment")
    ax.fill_between(weekly_stats["week"], 0, weekly_stats["avg_sentiment"],
                    color=PALETTE["primary"], alpha=0.08)
    ax.axhline(0, color="#444", linewidth=0.5, linestyle="--")
    ax.set_ylabel("Avg Sentiment Score (unitless, range -1 to +1)")
    ax.set_ylim(-1, 1)

    ax2 = ax.twinx()
    ax2.bar(weekly_stats["week"], weekly_stats["volume"],
            width=5, alpha=0.25, color=PALETTE["neutral"], label="Review Volume")
    ax2.set_ylabel("Number of Reviews (count)")
    ax2.grid(False)

    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")
    ax.legend(loc="upper left", frameon=False)
    ax2.legend(loc="upper right", frameon=False)

    _add_source(fig, _source_line(n_reviews, "Weekly aggregation + rolling linear slope"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Chart 06 — Funnel (real funnel shape)
# ---------------------------------------------------------------------------
def plot_funnel(
    stage_counts: pd.DataFrame,
    out_path: Path,
    title: str = "Marketing Conversion Funnel — Soft Funnel (Not Real Behavioural Conversion)",
    subtitle: str = "Five-stage soft funnel inferred from review signals (top-down: Awareness → Repurchase)",
    n_reviews: Optional[int] = None,
) -> Path:
    if stage_counts.empty or stage_counts["count"].sum() == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No funnel data", ha="center", va="center")
        return _save(fig, out_path)

    stages = stage_counts["stage"].tolist()
    counts = stage_counts["count"].tolist()
    max_count = max(counts) or 1
    n = len(stages)

    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    ax.set_xlim(-0.35, 1.25)
    ax.set_ylim(-0.5, n - 0.5)
    ax.axis("off")
    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")

    # 真正的漏斗：第 0 阶段（Awareness）画在最上面（最宽），最后阶段在最下面（最窄）
    # data 顺序保持 [Awareness, Interest, Trial, Satisfaction, Repurchase]，
    # 但 y 坐标倒过来绘制。
    for i, (stage, cnt) in enumerate(zip(stages, counts)):
        # 倒序显示：i=0 画在 y = n-1（最上面），i=n-1 画在 y = 0（最下面）
        display_y = n - 1 - i
        # 当前阶段的宽度（漏斗顶）
        width_top = counts[i] / max_count
        # 下一阶段（更深处）更窄
        width_bot = counts[i + 1] / max_count if i < n - 1 else counts[i] / max_count * 0.6
        y_top = display_y + 0.45
        y_bot = display_y - 0.45
        poly = Polygon(
            [
                ((1 - width_top) / 2, y_top),
                ((1 + width_top) / 2, y_top),
                ((1 + width_bot) / 2, y_bot),
                ((1 - width_bot) / 2, y_bot),
            ],
            facecolor=PALETTE["primary"], edgecolor="white", alpha=0.90 - i * 0.10,
        )
        ax.add_patch(poly)
        # Stage label (left)
        ax.text(-0.02, display_y, stage.replace("_", " "),
                ha="right", va="center", fontsize=10, fontweight="bold")
        # Count + conversion (right)
        ax.text(1.05, display_y, f"{cnt}",
                ha="left", va="center", fontsize=12, fontweight="bold", color=PALETTE["primary"])
        if i > 0:
            conv = stage_counts.iloc[i]["conversion_from_prev"]
            ax.text(1.05, display_y - 0.20, f"({conv:.0%} of previous)",
                    ha="left", va="center", fontsize=8, color="#888", style="italic")

    # Find biggest drop (ignore the first row which is 100% Awareness)
    if len(stage_counts) > 1:
        # 找"流失最大"的阶段：count / 上一阶段 count 最低的
        convs = stage_counts["conversion_from_prev"].iloc[1:]
        valid = convs[convs < 1.0]  # 排除 100% 的
        if not valid.empty:
            drop_idx = int(valid.idxmin())
            worst_stage = stage_counts.loc[drop_idx, "stage"].replace("_", " ")
            worst_conv = stage_counts.loc[drop_idx, "conversion_from_prev"]
            _add_insight(
                fig,
                f"→ Insight: Biggest drop is at 「{worst_stage}」 "
                f"({worst_conv:.0%} retention) — focus intervention there.",
            )

    # 漏斗专属声明：不是真实行为转化数据
    fig.text(
        0.5, -0.18,
        "Soft funnel — inferred from review text + rating only; "
        "not real impressions / clicks / orders.",
        ha="center", va="top", fontsize=8, color="#a04646", style="italic",
    )
    _add_source(fig, _source_line(n_reviews, "Soft funnel from review text + rating"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Chart 07 — ROI by segment
# ---------------------------------------------------------------------------
def plot_roi_by_segment(
    roi_df: pd.DataFrame,
    out_path: Path,
    title: str = "Illustrative ROI Index by Audience Segment (Synthetic — Illustrative Only)",
    subtitle: str = "Expected return on a CNY 5 user acquisition cost, "
                    "based on sentiment + repurchase signals (NOT a real causal ROI)",
    n_reviews: Optional[int] = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.0))
    colors = [PALETTE["good"] if v >= 0 else PALETTE["bad"] for v in roi_df["expected_roi"]]
    bars = ax.bar(roi_df["cluster_id"].astype(str), roi_df["expected_roi"],
                  color=colors, edgecolor="white")
    ax.axhline(0, color="#444", linewidth=0.6)
    ax.set_xlabel("Segment ID (from KMeans, see segmentation.py)")
    ax.set_ylabel("Illustrative ROI Index (unitless ratio: revenue / cost − 1)")
    ax.set_title(title, loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666", style="italic")

    for bar, v in zip(bars, roi_df["expected_roi"]):
        offset = 0.05 if v >= 0 else -0.05
        va = "bottom" if v >= 0 else "top"
        ax.text(bar.get_x() + bar.get_width() / 2, v + offset,
                f"{v:+.2f}", ha="center", va=va, fontsize=10, fontweight="bold")

    if not roi_df.empty:
        best = roi_df.loc[roi_df["expected_roi"].idxmax()]
        worst = roi_df.loc[roi_df["expected_roi"].idxmin()]
        _add_insight(
            fig,
            f"→ Insight: Segment {int(best['cluster_id'])} has the highest index "
            f"({best['expected_roi']:+.2f}); Segment {int(worst['cluster_id'])} "
            f"the lowest ({worst['expected_roi']:+.2f}).",
        )

    _add_source(fig, _source_line(n_reviews, "Ridge regression on soft-conversion proxy (illustrative only)"))
    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Source-line helpers
# ---------------------------------------------------------------------------
def _source_line(n_reviews: Optional[int], method: str) -> str:
    """Build a standard 'Source: synthetic reviews (n=xxx) · method' line.

    If ``n_reviews`` is None, falls back to a generic marker so the
    chart still carries an honest provenance tag.
    """
    if n_reviews is None or n_reviews <= 0:
        n_str = "n unknown"
    else:
        n_str = f"n={n_reviews}"
    return f"Source: synthetic reviews ({n_str}) · {method}"
