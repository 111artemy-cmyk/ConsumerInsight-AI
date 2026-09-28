"""Evaluation module for ConsumerInsight-AI.

Collects the five honest-evaluation primitives requested in the
project brief:

1. Clustering quality (silhouette) + alignment with the synthetic
   ``user_segment`` labels (ARI / NMI), with a written disclosure about
   circular-validation risk.
2. Topic-model agreement (LLM-extracted keywords vs TF-IDF keywords).
3. Sentiment-vs-rating correlation.
4. ROI regression K-fold CV (R² / MAE / coefficients).
5. Multi-seed stability summary.

设计原则
--------
* **绝不**伪造任何数字；所有指标都从真实运行结果计算。
* 每项评估都返回一个结构化的 dataclass + 一段 plain-text
  ``disclosure``，方便直接在报告里复用。
* 函数尽量不依赖 pipeline 内部的具体对象，而是接受
  DataFrame / ndarray —— 这样既容易单测，也方便多 seed 汇总。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    adjusted_rand_score,
    mean_absolute_error,
    normalized_mutual_info_score,
    r2_score,
    silhouette_score,
)
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder

from .config import RANDOM_SEED


# ---------------------------------------------------------------------------
# 1. Clustering evaluation
# ---------------------------------------------------------------------------
@dataclass
class ClusteringEval:
    silhouette: float
    ari: Optional[float]
    nmi: Optional[float]
    n_samples: int
    n_clusters: int
    n_true_labels: Optional[int]
    disclosure: str


def _sparse_to_dense(X) -> np.ndarray:
    """KMeans/silhouette 在小语料上对稀疏矩阵不友好；统一转 dense。"""
    if hasattr(X, "toarray"):
        return X.toarray()
    return np.asarray(X)


def eval_clustering(
    X,
    labels_pred: Sequence[int],
    labels_true: Optional[Sequence[Any]] = None,
    *,
    min_clusters_for_silhouette: int = 2,
) -> ClusteringEval:
    """Compute silhouette on the predicted clusters, plus ARI / NMI against
    the synthetic ``user_segment`` labels when supplied.

    Notes
    -----
    * ARI / NMI 在 synthetic data 上是"循环论证"——合成器就是按
      ``user_segment`` 选词的，而聚类又在 (TF-IDF + 行为特征) 上跑，
      词特征会把 segment 信息"泄漏"进聚类。报告里**必须**说明这一点，
      不能把高 ARI / NMI 当成"聚类与真实人群一致"的证据。
    * 当 ``labels_true`` 全空或长度不对时，ARI / NMI 返回 None。
    """
    labels_pred = np.asarray(labels_pred)
    n_samples = len(labels_pred)
    unique_pred = np.unique(labels_pred)
    n_clusters = len(unique_pred)

    # --- silhouette -----------------------------------------------------
    if n_clusters >= min_clusters_for_silhouette and n_samples >= 2:
        Xd = _sparse_to_dense(X)
        sil = float(silhouette_score(Xd, labels_pred))
    else:
        sil = float("nan")

    # --- ARI / NMI vs synthetic user_segment ---------------------------
    ari: Optional[float] = None
    nmi: Optional[float] = None
    n_true_labels: Optional[int] = None
    if labels_true is not None and len(labels_true) == n_samples:
        y_true_arr = np.asarray(labels_true)
        # 过滤掉 NaN / None，让长度对得上
        valid_mask = pd.Series(y_true_arr).notna().to_numpy()
        if valid_mask.sum() >= 2 and len(np.unique(y_true_arr[valid_mask])) >= 2:
            le = LabelEncoder()
            y_true_enc = le.fit_transform(y_true_arr[valid_mask])
            y_pred_enc = np.asarray(labels_pred)[valid_mask]
            ari = float(adjusted_rand_score(y_true_enc, y_pred_enc))
            nmi = float(normalized_mutual_info_score(y_true_enc, y_pred_enc))
            n_true_labels = int(len(le.classes_))
        elif valid_mask.sum() > 0:
            n_true_labels = int(len(np.unique(y_true_arr[valid_mask])))

    disclosure = (
        "Silhouette measures cluster separation on the feature space "
        "(higher = better separated, range [-1, +1]). "
        "ARI / NMI compare predicted clusters with the synthetic "
        "'user_segment' label used during data generation; "
        "this is a circular check — high scores mean 'the clusterer "
        "rediscovered the synthetic segment structure', NOT 'the "
        "clusterer found real consumer segments in production data'."
    )

    return ClusteringEval(
        silhouette=sil,
        ari=ari,
        nmi=nmi,
        n_samples=int(n_samples),
        n_clusters=int(n_clusters),
        n_true_labels=n_true_labels,
        disclosure=disclosure,
    )


# ---------------------------------------------------------------------------
# 2. Topic model agreement
# ---------------------------------------------------------------------------
@dataclass
class TopicAgreementEval:
    overlap_ratio: float
    jaccard: float
    n_llm_keywords: int
    n_tfidf_keywords: int
    n_overlap: int
    disclosure: str


def eval_topic_llm_vs_tfidf(
    llm_topic_keywords: Sequence[Sequence[str]],
    tfidf_top_keywords: Sequence[str],
) -> TopicAgreementEval:
    """Compare LLM-extracted topic keywords vs TF-IDF top keywords.

    The agreement is computed by **flattening** the LLM keywords
    (one topic's keywords may overlap with another's) and comparing
    against the TF-IDF top list.

    Metrics
    -------
    * overlap_ratio : |LLM ∩ TF-IDF| / |TF-IDF| — TF-IDF 中被 LLM 提及的比例。
    * jaccard       : |LLM ∩ TF-IDF| / |LLM ∪ TF-IDF|。
    """
    flat_llm = {kw for topic in llm_topic_keywords for kw in (topic or []) if kw}
    tfidf_set = {kw for kw in tfidf_top_keywords if kw}
    overlap = flat_llm & tfidf_set
    union = flat_llm | tfidf_set
    overlap_ratio = (len(overlap) / len(tfidf_set)) if tfidf_set else 0.0
    jaccard = (len(overlap) / len(union)) if union else 0.0

    disclosure = (
        "Overlap is computed by **set intersection** between the LLM's "
        "word-level keywords (e.g. ['包装', '设计', '好看']) and the TF-IDF "
        "char-2-3-gram vocabulary of the same corpus. On Chinese, even a "
        "perfect semantic topic will often show partial overlap here "
        "because LLM keywords are word-level and TF-IDF vocabulary is "
        "character-level n-grams. Both metrics are heuristic — even "
        "perfect agreement does NOT prove the LLM extracted the right "
        "topics. It only shows the LLM did not contradict the most "
        "frequent surface words."
    )

    return TopicAgreementEval(
        overlap_ratio=float(overlap_ratio),
        jaccard=float(jaccard),
        n_llm_keywords=len(flat_llm),
        n_tfidf_keywords=len(tfidf_set),
        n_overlap=len(overlap),
        disclosure=disclosure,
    )


# ---------------------------------------------------------------------------
# 3. Sentiment-vs-rating correlation
# ---------------------------------------------------------------------------
@dataclass
class SentimentRatingEval:
    pearson_r: float
    pearson_p: float
    spearman_r: float
    spearman_p: float
    n: int
    disclosure: str


def eval_sentiment_vs_rating(
    per_review: pd.DataFrame,
    *,
    sentiment_col: str = "overall",
    rating_col: str = "rating",
) -> SentimentRatingEval:
    """Pearson + Spearman correlation between LLM sentiment score and
    the user-given star rating.
    """
    if sentiment_col not in per_review.columns or rating_col not in per_review.columns:
        raise ValueError(
            f"per_review must contain both '{sentiment_col}' and '{rating_col}'"
        )
    sub = per_review[[sentiment_col, rating_col]].dropna()
    n = len(sub)
    if n < 3:
        raise ValueError(f"Need at least 3 non-null rows to compute correlation, got {n}.")
    s = sub[sentiment_col].astype(float).to_numpy()
    r = sub[rating_col].astype(float).to_numpy()
    pr, pp = pearsonr(s, r)
    sr, sp = spearmanr(s, r)
    disclosure = (
        "Pearson + Spearman between LLM-derived overall sentiment "
        "(range -1 to +1) and the user-given 1-5 star rating. "
        "On synthetic data both are derived from the same polarity "
        "lexicon, so the correlation is high by construction. "
        "Treat this as a sanity check (does the LLM agree with rating?), "
        "NOT as evidence of sentiment accuracy on real reviews."
    )
    return SentimentRatingEval(
        pearson_r=float(pr),
        pearson_p=float(pp),
        spearman_r=float(sr),
        spearman_p=float(sp),
        n=int(n),
        disclosure=disclosure,
    )


# ---------------------------------------------------------------------------
# 4. ROI regression K-fold CV
# ---------------------------------------------------------------------------
@dataclass
class ROICVEval:
    cv_r2: float
    cv_mae: float
    cv_coefficients: pd.DataFrame
    n_folds: int
    n_samples: int
    intercept_mean: float
    disclosure: str


def eval_roi_cv(
    features: pd.DataFrame,
    target: np.ndarray,
    *,
    feature_cols: Optional[List[str]] = None,
    n_folds: int = 5,
    random_state: int = RANDOM_SEED,
) -> ROICVEval:
    """K-fold CV with Ridge for ROI prediction.

    Parameters
    ----------
    features : DataFrame
        Per-review feature matrix.
    target : array-like
        Per-review target (e.g. per-review ROI proxy).
    feature_cols : list of str, optional
        Subset of feature columns to use. Defaults to all columns.
    """
    cols = feature_cols or list(features.columns)
    X = features[cols].fillna(0).to_numpy()
    y = np.asarray(target, dtype=float)
    n_samples = len(y)
    n_folds_eff = max(2, min(n_folds, n_samples))

    kf = KFold(n_splits=n_folds_eff, shuffle=True, random_state=random_state)
    r2s, maes, intercepts, coefs = [], [], [], []
    for train_idx, test_idx in kf.split(X):
        model = Ridge(alpha=1.0)
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[test_idx])
        r2s.append(r2_score(y[test_idx], preds))
        maes.append(mean_absolute_error(y[test_idx], preds))
        intercepts.append(float(model.intercept_))
        coefs.append(model.coef_)
    coef_mean = np.mean(coefs, axis=0)
    cv_coef_df = pd.DataFrame(
        {
            "feature": cols,
            "cv_coefficient": np.round(coef_mean, 4),
        }
    )
    # 把 cv-level 的标量放到第一行，其它行用 "—" 占位，避免 NaN 进 markdown。
    r2_str = f"{float(np.mean(r2s)):.4f}"
    mae_str = f"{float(np.mean(maes)):.4f}"
    cv_coef_df["cv_r2"] = [r2_str] + ["—"] * (len(cols) - 1)
    cv_coef_df["cv_mae"] = [mae_str] + ["—"] * (len(cols) - 1)
    cv_coef_df["cv_folds"] = [str(n_folds_eff)] + ["—"] * (len(cols) - 1)
    disclosure = (
        "Ridge K-fold CV on per-review ROI proxy. R² near 1 means the "
        "four proxy features can predict per-review ROI almost "
        "perfectly — expected because the proxy itself is a "
        "deterministic function of those features. The CV is still "
        "reported because it (a) confirms no numerical pathology in the "
        "proxy definition and (b) exposes the coefficient signs/magnitudes "
        "for the reviewer to sanity-check."
    )
    return ROICVEval(
        cv_r2=float(np.mean(r2s)),
        cv_mae=float(np.mean(maes)),
        cv_coefficients=cv_coef_df,
        n_folds=n_folds_eff,
        n_samples=int(n_samples),
        intercept_mean=float(np.mean(intercepts)),
        disclosure=disclosure,
    )


# ---------------------------------------------------------------------------
# 5. Multi-seed stability
# ---------------------------------------------------------------------------
@dataclass
class SeedRunSummary:
    seed: int
    largest_segment_id: int
    largest_segment_share_pct: float
    peak_roi_index: float
    peak_roi_segment: int
    funnel_worst_stage: str
    funnel_worst_retention: float


@dataclass
class StabilityReport:
    runs: List[SeedRunSummary]
    summary_by_metric: pd.DataFrame
    disclosure: str


def _safe_str_min(series: pd.Series, exclude_value=1.0):
    """Return the stage label with the smallest retention, excluding 100%."""
    valid = series[series < exclude_value]
    if valid.empty:
        return series.idxmin(), float(series.min())
    return valid.idxmin(), float(valid.min())


def _run_one_seed(
    seed: int,
    n_reviews: int,
) -> SeedRunSummary:
    """Run the full pipeline once with a fixed seed; pull headline metrics."""
    # Local imports to keep this module lightweight and avoid cycle.
    from .pipeline import run_full_pipeline

    arts = run_full_pipeline(
        n_reviews=n_reviews,
        use_synthetic=True,
        llm_backend="mock",
        random_seed_override=seed,
    )

    # 1. largest segment
    seg_counts = (
        arts.segment_assignments["cluster_id"].value_counts(normalize=True).sort_index()
    )
    largest_id = int(seg_counts.idxmax())
    largest_share = float(seg_counts.max() * 100.0)

    # 2. peak illustrative ROI
    roi_col = "illustrative_roi_index" if "illustrative_roi_index" in arts.roi.columns else "expected_roi"
    peak_idx = int(arts.roi[roi_col].idxmax())
    peak_val = float(arts.roi.loc[peak_idx, roi_col])

    # 3. funnel worst retention
    fc = arts.funnel
    # Skip Awareness (always 1.0); find min in the rest.
    worst_idx, worst_val = _safe_str_min(fc["conversion_from_prev"], exclude_value=1.0)
    worst_stage = str(fc.loc[worst_idx, "stage"])

    return SeedRunSummary(
        seed=seed,
        largest_segment_id=largest_id,
        largest_segment_share_pct=round(largest_share, 2),
        peak_roi_index=round(peak_val, 3),
        peak_roi_segment=int(arts.roi.loc[peak_idx, "cluster_id"]),
        funnel_worst_stage=worst_stage,
        funnel_worst_retention=round(worst_val, 3),
    )


def run_stability(
    n_seeds: int = 10,
    n_reviews: int = 1500,
    base_seed: int = 1,
    seeds: Optional[Sequence[int]] = None,
) -> StabilityReport:
    """Re-run the full pipeline ``n_seeds`` times and report mean/std
    of the headline metrics.

    Each seed advances ``RANDOM_SEED`` through the synthetic generator,
    producing structurally identical but content-different corpora.
    The headline metrics (largest segment share, peak ROI, worst funnel
    retention) are then compared across seeds.

    Returns
    -------
    StabilityReport
        ``runs`` is the per-seed list; ``summary_by_metric`` is a tidy
        DataFrame with mean / std / min / max for each headline metric.
    """
    if seeds is None:
        seeds = list(range(base_seed, base_seed + n_seeds))
    else:
        seeds = list(seeds)
        n_seeds = len(seeds)

    runs: List[SeedRunSummary] = []
    for s in seeds:
        summary = _run_one_seed(s, n_reviews)
        runs.append(summary)

    runs_df = pd.DataFrame([r.__dict__ for r in runs])

    # Build summary table.
    # 数值列（占比、ROI、留存） → mean / std / min / max。
    # 分类型（segment_id、peak_roi_segment、funnel_worst_stage） → mode + count。
    rows = []
    num_cols = [
        "largest_segment_share_pct",
        "peak_roi_index",
        "funnel_worst_retention",
    ]
    for col in num_cols:
        s = runs_df[col].astype(float)
        rows.append(
            {
                "metric": col,
                "kind": "numeric",
                "mean": round(float(s.mean()), 3),
                "std": round(float(s.std(ddof=1)) if len(s) > 1 else 0.0, 3),
                "min": round(float(s.min()), 3),
                "max": round(float(s.max()), 3),
            }
        )
    cat_cols = [
        "largest_segment_id",
        "peak_roi_segment",
        "funnel_worst_stage",
    ]
    for col in cat_cols:
        counts = runs_df[col].astype(str).value_counts()
        mode_val = counts.idxmax()
        mode_count = int(counts.iloc[0])
        # 也展示其它出现过的值（避免 mode 单一被忽略）
        other = ", ".join(
            f"{v}:{int(c)}" for v, c in counts.items() if v != mode_val
        )
        rows.append(
            {
                "metric": col,
                "kind": "categorical",
                "mean": mode_val,
                "std": mode_count,
                "min": other if other else "—",
                "max": "—",
            }
        )
    summary_df = pd.DataFrame(rows)

    disclosure = (
        f"Pipeline re-run {n_seeds} times with distinct RANDOM_SEED values "
        "(each seed advances the synthetic generator, so corpora are "
        "structurally identical but textually different). "
        "High std on any headline metric means that metric is sensitive "
        "to sampling noise and should not be quoted as a stable "
        "business KPI. Low std means the pipeline's structural behaviour "
        "is robust on synthetic corpora."
    )

    return StabilityReport(
        runs=runs,
        summary_by_metric=summary_df,
        disclosure=disclosure,
    )


# ---------------------------------------------------------------------------
# Convenience: rebuild the same feature matrix used by Segmentation
# ---------------------------------------------------------------------------
def _build_segmentation_feature_matrix(
    df: pd.DataFrame,
    text_col: str = "text",
) -> tuple:
    """Replicate the (TF-IDF + OHE + rating) feature matrix used by
    :class:`Segmenter`, so the silhouette score in this module is
    computed on the same space.
    """
    from scipy.sparse import csr_matrix, hstack

    corpus = df[text_col].astype(str).tolist()
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=1200)
    X_text = vec.fit_transform(corpus)
    parts = [X_text]
    cat_cols = [c for c in ["platform", "user_age_band"] if c in df.columns]
    if cat_cols:
        cat = df[cat_cols].astype(str).to_numpy()
        from sklearn.preprocessing import OneHotEncoder

        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        X_cat = ohe.fit_transform(cat)
        parts.append(csr_matrix(X_cat))
    if "rating" in df.columns:
        rating = df["rating"].fillna(df["rating"].median() or 3.0).to_numpy().reshape(-1, 1)
        parts.append(csr_matrix(rating - rating.mean()))
    X = hstack(parts).tocsr()
    return X, vec


def evaluate_segmentation_run(
    assignments: pd.DataFrame,
    original_df: pd.DataFrame,
    text_col: str = "text",
) -> ClusteringEval:
    """Helper: take segmentation output + the raw review DataFrame and
    compute silhouette / ARI / NMI against the synthetic ``user_segment``.
    """
    X, _ = _build_segmentation_feature_matrix(original_df, text_col=text_col)
    labels_pred = assignments["cluster_id"].to_numpy()
    labels_true = original_df["user_segment"].to_numpy()
    return eval_clustering(X, labels_pred, labels_true)