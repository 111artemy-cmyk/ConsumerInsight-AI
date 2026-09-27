"""Visualization helpers for ConsumerInsight-AI.

A thin wrapper that produces static (matplotlib) figures which are
saved to ``outputs/figures/``.  All functions return the file path of
the generated PNG so callers can include them in reports.
"""

from .charts import (
    plot_sentiment_by_dimension,
    plot_sentiment_by_segment,
    plot_segment_share,
    plot_topic_share,
    plot_weekly_trend,
    plot_funnel,
    plot_roi_by_segment,
)

__all__ = [
    "plot_sentiment_by_dimension",
    "plot_sentiment_by_segment",
    "plot_segment_share",
    "plot_topic_share",
    "plot_weekly_trend",
    "plot_funnel",
    "plot_roi_by_segment",
]
