"""趋势检测模块。

功能
----
* 将评论按周聚合，统计**好评率 / 差评率 / 平均情感分**随时间的演化；
* 基于线性回归给出"上升 / 下降 / 平稳"的方向判断；
* 标出当周最显著的关键词（TF-IDF 角度），作为事件解释。

输出
----
:meth:`TrendDetector.run` 返回 :class:`TrendResult`：

* ``weekly_stats``  : 每周聚合的统计指标
* ``events``        : 显著事件列表
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class TrendResult:
    weekly_stats: pd.DataFrame
    events: pd.DataFrame


class TrendDetector:
    """Detect sentiment/keyword trends over time."""

    def __init__(self, freq: str = "W"):
        # 'W' = weekly, 'D' = daily.  Weekly is the most stable default.
        self.freq = freq

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        df: pd.DataFrame,
        sentiment_col: str = "overall",
        text_col: str = "text",
        timestamp_col: str = "timestamp",
    ) -> TrendResult:
        if df.empty:
            raise ValueError("Input DataFrame is empty.")
        df = df.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
        df = df.dropna(subset=[timestamp_col])
        df["week"] = df[timestamp_col].dt.to_period(self.freq).dt.start_time

        grouped = df.groupby("week").agg(
            volume=(sentiment_col, "size"),
            avg_sentiment=(sentiment_col, "mean"),
            rating=("rating", "mean") if "rating" in df.columns else (sentiment_col, "size"),
        ).reset_index()

        # Slope of sentiment over time
        grouped["sentiment_slope"] = _rolling_slope(grouped["avg_sentiment"].fillna(0))

        # Direction label
        def _label(s: float) -> str:
            if s > 0.02:
                return "上升"
            if s < -0.02:
                return "下降"
            return "平稳"

        grouped["direction"] = grouped["sentiment_slope"].map(_label)

        # Weekly top keywords
        events = self._weekly_events(df, text_col=text_col, timestamp_col=timestamp_col)

        return TrendResult(weekly_stats=grouped, events=events)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _weekly_events(
        self,
        df: pd.DataFrame,
        text_col: str,
        timestamp_col: str,
    ) -> pd.DataFrame:
        weeks = sorted(df["week"].unique())
        rows = []
        for w in weeks:
            sub = df[df["week"] == w][text_col].astype(str).tolist()
            if len(sub) < 3:
                continue
            try:
                vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3), max_features=400)
            except Exception:
                continue
            vec.fit(sub)
            scores = vec.transform(sub).sum(axis=0).A1
            vocab = vec.get_feature_names_out()
            top_idx = scores.argsort()[::-1][:5]
            rows.append(
                {
                    "week": w,
                    "volume": len(sub),
                    "top_keywords": ", ".join(vocab[top_idx]),
                }
            )
        return pd.DataFrame(rows)


def _rolling_slope(series: pd.Series, window: int = 3) -> pd.Series:
    """Return the slope of a simple linear regression in a rolling window."""
    out = pd.Series(np.zeros(len(series)), index=series.index)
    for i in range(len(series)):
        lo = max(0, i - window + 1)
        seg = series.iloc[lo : i + 1].values
        if len(seg) < 2:
            continue
        x = np.arange(len(seg))
        out.iloc[i] = np.polyfit(x, seg, 1)[0]
    return out
