"""Pipeline orchestrator — wires every module together end-to-end.

Public entry point: :func:`run_full_pipeline`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .ai_analysis import PersonaGenerator, SentimentAnalyzer, TopicModeler, TrendDetector
from .config import (
    FIGURES_DIR,
    IndustryConfig,
    PROCESSED_DATA_DIR,
    RANDOM_SEED,
    REPORTS_DIR,
    ROIConfig,
)
from .data_loader import load_reviews
from .evaluation import (
    eval_clustering,
    eval_roi_cv,
    eval_sentiment_vs_rating,
    eval_topic_llm_vs_tfidf,
    evaluate_segmentation_run,
)
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
    # 评估指标（来自 src/evaluation.py）
    clustering_eval: object = None      # ClusteringEval
    topic_agreement: object = None      # TopicAgreementEval
    sentiment_rating_eval: object = None  # SentimentRatingEval
    roi_cv_eval: object = None          # ROICVEval
    random_seed_used: int = RANDOM_SEED


def run_full_pipeline(
    *,
    n_reviews: int = 1500,
    use_synthetic: bool = True,
    csv_path: Optional[Path] = None,
    llm_backend: str = "auto",
    llm_model: str = "gpt-4o-mini",
    industry: Optional[IndustryConfig] = None,
    output_dir: Optional[Path] = None,
    random_seed_override: Optional[int] = None,
    roi_config: Optional[ROIConfig] = None,
    skip_evaluation: bool = False,
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
    11. Markdown summary report (incl. evaluation section)
    """
    industry = industry or IndustryConfig()
    seed_used = int(random_seed_override) if random_seed_override is not None else RANDOM_SEED
    roi_cfg = roi_config or ROIConfig()
    # 用户传 --out 时，把 figures/ 与 reports/ 分到两个子目录，与 README 约定一致。
    if output_dir is not None:
        out_fig = output_dir / "figures"
        out_rep = output_dir / "reports"
    else:
        out_fig = FIGURES_DIR
        out_rep = REPORTS_DIR
    out_fig.mkdir(parents=True, exist_ok=True)
    out_rep.mkdir(parents=True, exist_ok=True)

    # ----- Step 1: data -----------------------------------------------
    df = load_reviews(
        csv_path=csv_path,
        use_synthetic=use_synthetic,
        n_synthetic=n_reviews,
        seed=seed_used,
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
    personas = PersonaGenerator(llm=llm, n_clusters=4, random_state=seed_used).run(df)

    # ----- Step 6: segmentation --------------------------------------
    segmentation = Segmenter(n_segments=4, random_state=seed_used).run(df)

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
    roi = ROIPredictor(config=roi_cfg).fit_predict(merged_for_roi)

    # ----- Step 10: campaigns ----------------------------------------
    campaigns = CampaignGenerator(llm=llm, industry=industry).run(personas.personas)

    # ----- Step 11: visualisations -----------------------------------
    n = len(df)
    figures: Dict[str, Path] = {}
    figures["sentiment_by_dimension"] = charts.plot_sentiment_by_dimension(
        sentiment.summary, out_fig / "01_sentiment_by_dimension.png", n_reviews=n
    )
    figures["sentiment_by_segment"] = charts.plot_sentiment_by_segment(
        sentiment.by_segment,
        out_fig / "02_sentiment_by_segment.png",
        dimensions=SENTIMENT_COLS,
        n_reviews=n,
    )
    figures["segment_share"] = charts.plot_segment_share(
        segmentation.assignments,
        segmentation.segment_profile,
        out_fig / "03_segment_share.png",
        n_reviews=n,
    )
    figures["topic_share"] = charts.plot_topic_share(
        topics.topics, out_fig / "04_topic_share.png", n_reviews=n
    )
    figures["weekly_trend"] = charts.plot_weekly_trend(
        trend.weekly_stats, out_fig / "05_weekly_trend.png", n_reviews=n
    )
    figures["funnel"] = charts.plot_funnel(
        funnel.stage_counts, out_fig / "06_funnel.png", n_reviews=n
    )
    figures["roi"] = charts.plot_roi_by_segment(
        roi.segment_roi, out_fig / "07_roi_by_segment.png", n_reviews=n
    )

    # ----- Step 12: evaluation (single-seed) -------------------------
    clustering_eval_obj = None
    topic_agreement_obj = None
    sentiment_rating_obj = None
    roi_cv_obj = None
    if not skip_evaluation:
        # 12a. Clustering: silhouette + ARI/NMI vs synthetic user_segment
        try:
            clustering_eval_obj = evaluate_segmentation_run(
                segmentation.assignments, df, text_col="text"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[evaluation] clustering eval skipped: {exc}")

        # 12b. Topic agreement: LLM keywords vs TF-IDF keywords
        try:
            llm_kws = []
            if "representative_keywords" in topics.topics.columns:
                llm_kws = [list(k or []) for k in topics.topics["representative_keywords"]]
            tfidf_kws = list(topics.keywords["keyword"]) if "keyword" in topics.keywords.columns else []
            topic_agreement_obj = eval_topic_llm_vs_tfidf(llm_kws, tfidf_kws)
        except Exception as exc:  # noqa: BLE001
            print(f"[evaluation] topic agreement eval skipped: {exc}")

        # 12c. Sentiment vs rating correlation
        try:
            sentiment_rating_obj = eval_sentiment_vs_rating(sentiment.per_review)
        except Exception as exc:  # noqa: BLE001
            print(f"[evaluation] sentiment-vs-rating eval skipped: {exc}")

        # 12d. ROI K-fold CV on per-review ROI proxy
        try:
            from .marketing_analytics.roi_predictor import _sigmoid as _roi_sigmoid
            roi_features = merged_for_roi.copy()
            # 构造 per-review ROI 所需的全部 4 个特征（与 ROIPredictor 内部一致）
            text_series = roi_features["text"].astype(str)
            text_len = text_series.str.len()
            rating_filled = pd.to_numeric(roi_features["rating"], errors="coerce").fillna(3)
            roi_features["overall"] = pd.to_numeric(roi_features["overall"], errors="coerce").fillna(0)
            roi_features["high_rating"] = (rating_filled >= 4).astype(int)
            roi_features["long_text"] = (text_len >= 18).astype(int)
            roi_features["repurchase_intent"] = (
                text_series.str.contains("回购|囤货|复购|再买|再入", regex=True).astype(int)
            )
            soft = _roi_sigmoid(
                1.0 * roi_features["overall"]
                + 0.6 * roi_features["high_rating"]
                + 0.3 * roi_features["long_text"]
                + 0.2 * roi_features["repurchase_intent"]
            )
            effective = (soft - roi_cfg.baseline_soft_conversion).clip(lower=0.0)
            revenue = effective * roi_cfg.baseline_arpu
            cost = roi_cfg.cost_per_user
            per_review_roi = (revenue - cost) / cost
            roi_feature_cols = ["overall", "high_rating", "long_text", "repurchase_intent"]
            roi_cv_obj = eval_roi_cv(
                roi_features[roi_feature_cols],
                per_review_roi.to_numpy(),
                feature_cols=roi_feature_cols,
                n_folds=roi_cfg.roi_cv_folds,
                random_state=roi_cfg.roi_cv_random_state,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[evaluation] ROI CV eval skipped: {exc}")

    # ----- Step 13: report -------------------------------------------
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
        clustering_eval=clustering_eval_obj,
        topic_agreement=topic_agreement_obj,
        sentiment_rating=sentiment_rating_obj,
        roi_cv=roi_cv_obj,
        random_seed_used=seed_used,
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
        clustering_eval=clustering_eval_obj,
        topic_agreement=topic_agreement_obj,
        sentiment_rating_eval=sentiment_rating_obj,
        roi_cv_eval=roi_cv_obj,
        random_seed_used=seed_used,
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
    clustering_eval=None,
    topic_agreement=None,
    sentiment_rating=None,
    roi_cv=None,
    random_seed_used: int = RANDOM_SEED,
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
    a(f"**随机种子**：{random_seed_used}  ")
    a("")
    a("> **重要声明：本报告所有数字均来自程序化合成的 review 数据（synthetic data），不构成任何真实业务结论。ROI 与模拟点击率均为示意性指标。**")
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
    a(f"> {funnel.disclaimer}")
    a("")
    a("## 6. 示意性 ROI 指数 (Illustrative ROI Index)")
    a("")
    a("![ROI]({})".format(figures["roi"].as_posix()))
    a("")
    a(roi.segment_roi.to_markdown(index=False))
    a("")
    a(f"> {roi.notes}")
    a("")
    a("## 7. 营销文案候选 (simulated_ctr)")
    a("")
    if not campaigns.creatives.empty:
        keep_cols = ["persona_nickname", "channel", "headline"]
        # 主字段 simulated_ctr（若无则回退到 predicted_ctr）
        ctr_col = "simulated_ctr" if "simulated_ctr" in campaigns.creatives.columns else "predicted_ctr"
        keep_cols.append(ctr_col)
        keep_cols = [c for c in keep_cols if c in campaigns.creatives.columns]
        a(campaigns.creatives[keep_cols].to_markdown(index=False))
    a("")
    a("> `simulated_ctr` 字段说明：基于 [0.04, 0.09) 区间均匀随机采样，**不是**真实点击率预测，仅作渠道预算相对权重的输入。详见 `src/llm/mock_client.py::MockLLMClient._compose_campaign` 与 `SIM_CTR_LOW/HIGH`。")
    a("")
    # ============== 评估章节 ==============
    a("## 8. 评估指标 (Honest Evaluation)")
    a("")
    a("> 全部数字来自本次 pipeline 运行（RANDOM_SEED={}）的真实输出。**不做任何手动调参或挑选 seed**。".format(random_seed_used))
    a("")
    if clustering_eval is not None:
        a("### 8.1 聚类质量")
        a("")
        a("| 指标 | 值 |")
        a("|---|---|")
        a(f"| Silhouette score (range [-1, +1]) | {clustering_eval.silhouette:+.4f} |")
        if clustering_eval.ari is not None:
            a(f"| Adjusted Rand Index vs synthetic user_segment | {clustering_eval.ari:+.4f} |")
        if clustering_eval.nmi is not None:
            a(f"| Normalized Mutual Information vs synthetic user_segment | {clustering_eval.nmi:+.4f} |")
        a(f"| N samples / N predicted clusters / N true labels | {clustering_eval.n_samples} / {clustering_eval.n_clusters} / {clustering_eval.n_true_labels} |")
        a("")
        a(f"> {clustering_eval.disclosure}")
        a("")
    if topic_agreement is not None:
        a("### 8.2 主题一致性 (LLM vs TF-IDF)")
        a("")
        a("| 指标 | 值 |")
        a("|---|---|")
        a(f"| TF-IDF 关键词中被 LLM 提及的比例 (overlap_ratio) | {topic_agreement.overlap_ratio:.3f} |")
        a(f"| Jaccard | {topic_agreement.jaccard:.3f} |")
        a(f"| LLM 关键词总数 / TF-IDF 关键词总数 / 重合数 | {topic_agreement.n_llm_keywords} / {topic_agreement.n_tfidf_keywords} / {topic_agreement.n_overlap} |")
        a("")
        a(f"> {topic_agreement.disclosure}")
        a("")
    if sentiment_rating is not None:
        a("### 8.3 情感分 vs 评分 相关性")
        a("")
        a("| 指标 | 值 |")
        a("|---|---|")
        a(f"| Pearson r (p-value) | {sentiment_rating.pearson_r:+.4f} (p={sentiment_rating.pearson_p:.2e}) |")
        a(f"| Spearman ρ (p-value) | {sentiment_rating.spearman_r:+.4f} (p={sentiment_rating.spearman_p:.2e}) |")
        a(f"| N | {sentiment_rating.n} |")
        a("")
        a(f"> {sentiment_rating.disclosure}")
        a("")
    if roi_cv is not None:
        a("### 8.4 ROI 回归 K-fold CV")
        a("")
        a("| 指标 | 值 |")
        a("|---|---|")
        a(f"| K-fold CV R² (per-review ROI proxy) | {roi_cv.cv_r2:+.4f} |")
        a(f"| K-fold CV MAE | {roi_cv.cv_mae:.4f} |")
        a(f"| Folds / samples | {roi_cv.n_folds} / {roi_cv.n_samples} |")
        a("")
        a("Coefficients (mean across folds):")
        a("")
        a(roi_cv.cv_coefficients.to_markdown(index=False))
        a("")
        a(f"> {roi_cv.disclosure}")
        a("")
    a("### 8.5 多 seed 稳定性")
    a("")
    a(f"完整多 seed 稳定性报告见 `outputs/reports/stability_report.md`（由 `python scripts/run_stability_eval.py` 生成，{10} seeds）。**本节不重复展开**。")
    a("")
    a("---")
    a("")
    a('*本报告由程序自动生成；任何刻意的「挑选数字」或「手工修饰」都会让这份项目失去作品集价值。*')
    a("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
