"""Pipeline orchestrator — wires every module together end-to-end.

Public entry point: :func:`run_full_pipeline`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .ai_analysis import PersonaGenerator, SentimentAnalyzer, TopicModeler, TrendDetector
from .config import FIGURES_DIR, IndustryConfig, PROCESSED_DATA_DIR, REPORTS_DIR
from .data_loader import load_reviews
from .llm import build_llm_client
from .marketing_analytics import (
    CampaignGenerator,
    FunnelAnalyzer,
    ROIPredictor,
    Segmenter,
)
from .visualization import charts


@dataclass
class PipelineArtifacts:
    """All artefacts produced by the pipeline."""

    reviews: pd.DataFrame
    sentiment_per_review: pd.DataFrame
    sentiment_summary: pd.DataFrame
    sentiment_by_segment: pd.DataFrame
    topics: pd.DataFrame
    topic_keywords: pd.DataFrame
    personas: pd.DataFrame
    segment_assignments: pd.DataFrame
    segment_profile: pd.DataFrame
    weekly_stats: pd.DataFrame
    funnel: pd.DataFrame
    roi: pd.DataFrame
    creatives: pd.DataFrame
    budget_plan: pd.DataFrame
    figures: Dict[str, Path] = field(default_factory=dict)
    report_path: Optional[Path] = None


def run_full_pipeline(
    *,
    n_reviews: int = 1500,
    use_synthetic: bool = True,
    csv_path: Optional[Path] = None,
    llm_backend: str = "auto",
    llm_model: str = "gpt-4o-mini",
    industry: Optional[IndustryConfig] = None,
    output_dir: Optional[Path] = None,
) -> PipelineArtifacts:
    """End-to-end pipeline run.

    Steps
    -----
    1. Load / generate review data
    2. Multi-aspect sentiment analysis
    3. Topic extraction
    4. Persona generation
    5. Audience segmentation
    6. Trend detection
    7. Funnel analysis
    8. ROI prediction
    9. Campaign message generation
    10. Visualisations
    11. Markdown summary report
    """
    industry = industry or IndustryConfig()
    out_fig = (output_dir or FIGURES_DIR)
    out_rep = (output_dir or REPORTS_DIR)
    out_fig.mkdir(parents=True, exist_ok=True)
    out_rep.mkdir(parents=True, exist_ok=True)

    # ----- Step 1: data -----------------------------------------------
    df = load_reviews(
        csv_path=csv_path,
        use_synthetic=use_synthetic,
        n_synthetic=n_reviews,
    )

    # Persist processed data for reproducibility
    processed_csv = PROCESSED_DATA_DIR / "sample_processed.csv"
    processed_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_csv, index=False, encoding="utf-8-sig")

    # ----- Step 2: LLM client ----------------------------------------
    llm = build_llm_client(backend=llm_backend, model=llm_model)

    # ----- Step 3: sentiment -----------------------------------------
    sentiment = SentimentAnalyzer(llm=llm).run(df)
    SENTIMENT_COLS = list(sentiment.summary["dimension"])

    # ----- Step 4: topics --------------------------------------------
    topics = TopicModeler(llm=llm, n_topics=5, brand_name=industry.brand_name).run(df)

    # ----- Step 5: personas ------------------------------------------
    personas = PersonaGenerator(llm=llm, n_clusters=4).run(df)

    # ----- Step 6: segmentation --------------------------------------
    segmentation = Segmenter(n_segments=4).run(df)

    # ----- Step 7: trend ---------------------------------------------
    # merge sentiment into df
    enriched = df.merge(
        sentiment.per_review[["review_id", "overall"] + SENTIMENT_COLS],
        on="review_id",
        how="left",
    )
    trend = TrendDetector().run(enriched)

    # ----- Step 8: funnel --------------------------------------------
    funnel = FunnelAnalyzer().run(enriched)

    # ----- Step 9: ROI ------------------------------------------------
    merged_for_roi = enriched.merge(segmentation.assignments[["review_id", "cluster_id"]], on="review_id")
    roi = ROIPredictor().fit_predict(merged_for_roi)

    # ----- Step 10: campaigns ----------------------------------------
    campaigns = CampaignGenerator(llm=llm, industry=industry).run(personas.personas)

    # ----- Step 11: visualisations -----------------------------------
    figures: Dict[str, Path] = {}
    figures["sentiment_by_dimension"] = charts.plot_sentiment_by_dimension(
        sentiment.summary, out_fig / "01_sentiment_by_dimension.png"
    )
    figures["sentiment_by_segment"] = charts.plot_sentiment_by_segment(
        sentiment.by_segment,
        out_fig / "02_sentiment_by_segment.png",
        dimensions=SENTIMENT_COLS,
    )
    figures["segment_share"] = charts.plot_segment_share(
        segmentation.assignments,
        segmentation.segment_profile,
        out_fig / "03_segment_share.png",
    )
    figures["topic_share"] = charts.plot_topic_share(
        topics.topics, out_fig / "04_topic_share.png"
    )
    figures["weekly_trend"] = charts.plot_weekly_trend(
        trend.weekly_stats, out_fig / "05_weekly_trend.png"
    )
    figures["funnel"] = charts.plot_funnel(
        funnel.stage_counts, out_fig / "06_funnel.png"
    )
    figures["roi"] = charts.plot_roi_by_segment(
        roi.segment_roi, out_fig / "07_roi_by_segment.png"
    )

    # ----- Step 12: report -------------------------------------------
    report_path = _write_markdown_report(
        out_path=out_rep / "pipeline_report.md",
        industry=industry,
        df=df,
        sentiment=sentiment,
        topics=topics,
        personas=personas,
        segmentation=segmentation,
        trend=trend,
        funnel=funnel,
        roi=roi,
        campaigns=campaigns,
        figures=figures,
    )

    return PipelineArtifacts(
        reviews=df,
        sentiment_per_review=sentiment.per_review,
        sentiment_summary=sentiment.summary,
        sentiment_by_segment=sentiment.by_segment,
        topics=topics.topics,
        topic_keywords=topics.keywords,
        personas=personas.personas,
        segment_assignments=segmentation.assignments,
        segment_profile=segmentation.segment_profile,
        weekly_stats=trend.weekly_stats,
        funnel=funnel.stage_counts,
        roi=roi.segment_roi,
        creatives=campaigns.creatives,
        budget_plan=campaigns.budget_plan,
        figures=figures,
        report_path=report_path,
    )


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def _write_markdown_report(
    *,
    out_path: Path,
    industry: IndustryConfig,
    df: pd.DataFrame,
    sentiment,
    topics,
    personas,
    segmentation,
    trend,
    funnel,
    roi,
    campaigns,
    figures: Dict[str, Path],
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    a = lines.append
    a(f"# ConsumerInsight-AI — Pipeline Report")
    a("")
    a(f"**品牌**：{industry.brand_name}  ")
    a(f"**行业**：{industry.industry}  ")
    a(f"**平台**：{', '.join(industry.primary_platforms)}  ")
    a(f"**评论数**：{len(df)}  ")
    a("")
    a("## 1. 多维度情感概览")
    a("")
    a("![情感概览]({})".format(figures["sentiment_by_dimension"].as_posix()))
    a("")
    a("### 维度均值表")
    a("")
    a(sentiment.summary.to_markdown(index=False))
    a("")
    a("## 2. 受众细分")
    a("")
    a("![细分占比]({})".format(figures["segment_share"].as_posix()))
    a("")
    a("### 细分群画像表")
    a("")
    a(segmentation.segment_profile.to_markdown(index=False))
    a("")
    a("## 3. 核心话题")
    a("")
    a("![话题占比]({})".format(figures["topic_share"].as_posix()))
    if not topics.topics.empty:
        a("")
        a(topics.topics.to_markdown(index=False))
    a("")
    a("## 4. 消费者 Persona")
    a("")
    if not personas.personas.empty:
        cols = ["persona_id", "nickname", "age_range", "occupation",
                "core_need", "recommended_campaign_angle", "why_matters"]
        cols = [c for c in cols if c in personas.personas.columns]
        a(personas.personas[cols].to_markdown(index=False))
    a("")
    a("## 5. 趋势与漏斗")
    a("")
    a("![趋势]({})".format(figures["weekly_trend"].as_posix()))
    a("")
    a("![漏斗]({})".format(figures["funnel"].as_posix()))
    a("")
    a(f"> {funnel.stage_summary}")
    a("")
    a("## 6. ROI 预估")
    a("")
    a("![ROI]({})".format(figures["roi"].as_posix()))
    a("")
    a(roi.segment_roi.to_markdown(index=False))
    a("")
    a(f"> {roi.notes}")
    a("")
    a("## 7. 营销文案候选")
    a("")
    if not campaigns.creatives.empty:
        keep_cols = ["persona_nickname", "channel", "headline", "predicted_ctr"]
        keep_cols = [c for c in keep_cols if c in campaigns.creatives.columns]
        a(campaigns.creatives[keep_cols].to_markdown(index=False))
    a("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
