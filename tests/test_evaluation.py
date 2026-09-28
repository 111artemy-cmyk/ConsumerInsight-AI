"""Unit tests for src/evaluation.

The evaluation module is the centerpiece of the "honest, rigorous,
reproducible" claim. These tests make sure each evaluator:

1. Returns a structured result object with the expected fields.
2. Rejects pathological inputs (empty / too-few-rows / wrong columns).
3. Produces values in the documented ranges.

All numbers below come from real computations on the same synthetic
fixtures used elsewhere in the test-suite; no values are fabricated.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.evaluation import (  # noqa: E402
    ClusteringEval,
    ROICVEval,
    SentimentRatingEval,
    StabilityReport,
    TopicAgreementEval,
    eval_clustering,
    eval_roi_cv,
    eval_sentiment_vs_rating,
    eval_topic_llm_vs_tfidf,
    run_stability,
)


# ---------------------------------------------------------------------------
# 1. Clustering
# ---------------------------------------------------------------------------
def test_eval_clustering_returns_structured_result():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(40, 5))
    labels = np.array([0] * 10 + [1] * 10 + [2] * 10 + [3] * 10)
    res = eval_clustering(X, labels, labels_true=None)
    assert isinstance(res, ClusteringEval)
    assert -1.0 <= res.silhouette <= 1.0
    assert res.ari is None  # 未提供 true labels
    assert res.n_samples == 40
    assert res.n_clusters == 4
    assert "circular" in res.disclosure.lower() or "synthetic" in res.disclosure.lower()


def test_eval_clustering_with_true_labels():
    rng = np.random.default_rng(0)
    # 4 个簇，特征明显可分
    centers = rng.normal(size=(4, 5)) * 5
    X = np.vstack([c + rng.normal(size=(20, 5)) * 0.5 for c in centers])
    labels_pred = np.repeat([0, 1, 2, 3], 20)
    labels_true = np.repeat(["A", "B", "C", "D"], 20)
    res = eval_clustering(X, labels_pred, labels_true=labels_true)
    assert res.ari is not None and 0.7 < res.ari <= 1.0
    assert res.nmi is not None and 0.7 < res.nmi <= 1.0
    assert res.n_true_labels == 4


def test_eval_clustering_rejects_single_cluster_for_silhouette():
    X = np.zeros((5, 2))
    labels = np.zeros(5, dtype=int)
    res = eval_clustering(X, labels, labels_true=None)
    # 1 cluster → silhouette 无法计算 → NaN
    assert np.isnan(res.silhouette)


# ---------------------------------------------------------------------------
# 2. Topic agreement
# ---------------------------------------------------------------------------
def test_eval_topic_llm_vs_tfidf_perfect_overlap():
    llm = [["包装", "设计", "好看"], ["价格", "划算"]]
    tfidf = ["包装", "设计", "好看", "价格", "划算", "快递"]
    res = eval_topic_llm_vs_tfidf(llm, tfidf)
    assert isinstance(res, TopicAgreementEval)
    # 6 个 tfidf 关键词中，5 个出现在 llm 集合 → overlap_ratio = 5/6
    assert abs(res.overlap_ratio - 5 / 6) < 1e-9
    # union = 6 (包装 设计 好看 价格 划算 快递) → jaccard = 5/6
    assert abs(res.jaccard - 5 / 6) < 1e-9
    assert res.n_llm_keywords == 5  # 5 个 unique llm 关键词
    assert res.n_tfidf_keywords == 6
    assert res.n_overlap == 5


def test_eval_topic_llm_vs_tfidf_zero_overlap():
    res = eval_topic_llm_vs_tfidf([["苹果", "香蕉"]], ["西瓜", "葡萄"])
    assert res.overlap_ratio == 0.0
    assert res.jaccard == 0.0
    assert res.n_overlap == 0


def test_eval_topic_llm_vs_tfidf_empty_inputs_are_safe():
    res = eval_topic_llm_vs_tfidf([], [])
    assert res.n_overlap == 0
    assert res.overlap_ratio == 0.0
    assert res.jaccard == 0.0


# ---------------------------------------------------------------------------
# 3. Sentiment vs rating
# ---------------------------------------------------------------------------
def test_eval_sentiment_vs_rating_returns_positive_correlation():
    rng = np.random.default_rng(42)
    n = 200
    rating = rng.choice([1, 2, 3, 4, 5], size=n)
    overall = (rating - 3) / 2 + rng.normal(0, 0.05, size=n)
    df = pd.DataFrame({"overall": overall, "rating": rating})
    res = eval_sentiment_vs_rating(df)
    assert isinstance(res, SentimentRatingEval)
    assert res.pearson_r > 0.95
    assert res.spearman_r > 0.9
    assert res.n == n
    assert "synthetic" in res.disclosure.lower() or "sanity" in res.disclosure.lower()


def test_eval_sentiment_vs_rating_rejects_missing_columns():
    df = pd.DataFrame({"overall": [0.1, 0.2]})  # no 'rating'
    try:
        eval_sentiment_vs_rating(df)
    except ValueError:
        return
    raise AssertionError("Expected ValueError when rating column is missing")


def test_eval_sentiment_vs_rating_rejects_too_few_rows():
    df = pd.DataFrame({"overall": [0.1, 0.2], "rating": [3, 4]})
    try:
        eval_sentiment_vs_rating(df)
    except ValueError:
        return
    raise AssertionError("Expected ValueError when n<3")


# ---------------------------------------------------------------------------
# 4. ROI K-fold CV
# ---------------------------------------------------------------------------
def test_eval_roi_cv_reports_r2_and_mae_in_range():
    rng = np.random.default_rng(7)
    n = 200
    X = pd.DataFrame({
        "a": rng.normal(size=n),
        "b": rng.normal(size=n),
    })
    y = 1.5 * X["a"] + 2.0 * X["b"] + 0.1 * rng.normal(size=n)
    res = eval_roi_cv(X, y.to_numpy(), n_folds=5)
    assert isinstance(res, ROICVEval)
    assert 0.9 < res.cv_r2 <= 1.0
    assert res.cv_mae >= 0.0
    assert res.n_folds == 5
    assert res.n_samples == n
    assert "proxy" in res.disclosure.lower() or "deterministic" in res.disclosure.lower()


def test_eval_roi_cv_coefficients_have_correct_length():
    rng = np.random.default_rng(7)
    n = 200
    X = pd.DataFrame({
        "a": rng.normal(size=n),
        "b": rng.normal(size=n),
        "c": rng.normal(size=n),
    })
    y = X["a"] + X["b"] + X["c"]
    res = eval_roi_cv(X, y.to_numpy(), feature_cols=["a", "b", "c"])
    assert len(res.cv_coefficients) == 3
    assert set(res.cv_coefficients["feature"]) == {"a", "b", "c"}


def test_eval_roi_cv_caps_folds_at_n_samples():
    # 当 n_folds 大于 n_samples 时，函数自动降到 min(n_folds, n_samples)，
    # 同时保证 >= 2。n_samples=4 时，n_folds=10 → 退化到 4-fold。
    X = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [4.0, 3.0, 2.0, 1.0]})
    y = np.array([0.1, 0.2, 0.3, 0.4])
    res = eval_roi_cv(X, y, n_folds=10)
    # 不大于 n_samples=4，不小于 2
    assert 2 <= res.n_folds <= 4
    assert res.n_samples == 4


# ---------------------------------------------------------------------------
# 5. Multi-seed stability (lightweight, n_reviews 很小)
# ---------------------------------------------------------------------------
def test_run_stability_produces_expected_n_runs():
    rep = run_stability(n_seeds=3, n_reviews=80)
    assert isinstance(rep, StabilityReport)
    assert len(rep.runs) == 3
    # 每行至少包含 headline 字段
    first = rep.runs[0]
    assert isinstance(first.seed, int)
    assert 0.0 <= first.largest_segment_share_pct <= 100.0
    assert first.peak_roi_index >= -1.0  # ROI 可以是负数（成本 > 收益）
    # worst_retention ∈ [0, 1]
    assert 0.0 <= first.funnel_worst_retention <= 1.0
    # disclosure 不能空
    assert rep.disclosure and len(rep.disclosure) > 50


# ---------------------------------------------------------------------------
# 6. ClusteringEval additional edge cases
# ---------------------------------------------------------------------------
def test_eval_clustering_ari_is_negative_when_completely_wrong():
    """当预测标签与真实标签的*配对*完全错位时，ARI 应明显小于 0。

    注意：单纯把 0/1 反过来不会降 ARI，因为 ARI 看的是配对的对错，
    而「前 30 个一类、后 30 个另一类」这个配对模式不变。
    这里要构造的是「真实两个簇，但预测是交错打乱」的情况。
    """
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 4))
    # 真实：前 30 一类、后 30 另一类
    labels_true = np.array([0] * 30 + [1] * 30)
    # 预测：交错 — 偶数 index 聚类 0、奇数 index 聚类 1
    # 配对 (0,0) 出现在 idx=0,2,...,58 共 30 次，正确；
    # 配对 (0,1) 出现在 idx=1,3,...,59 共 30 次，错误；
    # 配对 (1,0) 出现在 idx=1,3,...,57 共 29 次，错误；
    # 配对 (1,1) 出现在 idx=0,2,...,58 但只对前 30 idx 的 0,2,...,28 算正确 = 15 次
    # 总 60 对，正确配对 = 15 + 30 - 15 = ... 总之远低于显式配对，ARI 应该为负或近 0
    labels_pred = np.array([i % 2 for i in range(60)])
    res = eval_clustering(X, labels_pred, labels_true=labels_true)
    assert res.ari is not None
    assert res.ari < 0.0
    assert res.n_true_labels == 2


def test_eval_clustering_handles_nan_in_truth():
    """真实标签里有 NaN — 应被 mask 掉。剩余样本预测对的话 ARI 应明显为正。"""
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, 3))
    # 真实：4 组 (0, 0, 1, 1, NaN)，NaN 占 1/5
    labels_true = np.array([0, 0, 1, 1, None] * 4)
    # 预测：valid 样本上完全 = 真实值
    labels_pred = np.where(
        pd.Series(labels_true).isna().to_numpy(),
        0,  # NaN 位置上随便给一个值，会被 mask 掉
        labels_true,
    ).astype(int)
    res = eval_clustering(X, labels_pred, labels_true=labels_true)
    assert res.ari is not None
    # valid 样本上预测==真实，ARI 应该接近 1
    assert res.ari > 0.8


# ---------------------------------------------------------------------------
# 7. ROI CV additional edge cases
# ---------------------------------------------------------------------------
def test_eval_roi_cv_can_report_negative_r2_for_pure_noise():
    """对完全无关的 y，CV R² 应接近 0（或负）。证明我们**没有**把 CV 当 KPI 包装。"""
    rng = np.random.default_rng(0)
    n = 200
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    # y 完全是噪声，跟 X 没关系
    y = rng.normal(size=n)
    res = eval_roi_cv(X, y, n_folds=5)
    # 噪声 y 的 R² 应远低于 1（合理上限 ~0.05）。
    assert res.cv_r2 < 0.1
    # MAE 应是噪声的标准差量级
    assert 0.5 < res.cv_mae < 1.5


# ---------------------------------------------------------------------------
# 8. Stability summary structure
# ---------------------------------------------------------------------------
def test_run_stability_summary_separates_numeric_and_categorical():
    """summary_by_metric 应该同时包含 numeric 和 categorical 两类指标。"""
    rep = run_stability(n_seeds=3, n_reviews=80)
    df = rep.summary_by_metric
    assert "kind" in df.columns
    kinds = set(df["kind"])
    assert "numeric" in kinds
    assert "categorical" in kinds
    # categorical 行：mean 应该是字符串（mode），std 应该是整数（计数）
    cat_rows = df[df["kind"] == "categorical"]
    # 用 is_object_dtype 替代 `dtype == object`（后者对 Series 返回的是单值 bool）
    assert pd.api.types.is_object_dtype(cat_rows["mean"])
    assert (cat_rows["std"].astype(int) >= 1).all()


def test_run_stability_with_explicit_seeds_uses_those_seeds():
    rep = run_stability(seeds=[7, 13, 21], n_reviews=50)
    assert [r.seed for r in rep.runs] == [7, 13, 21]


# ---------------------------------------------------------------------------
# 9. End-to-end pipeline integration
# ---------------------------------------------------------------------------
def test_pipeline_integration_produces_all_evaluations():
    """跑一次真实的 pipeline，确认 4 个 evaluation 字段都不为 None。"""
    from src.pipeline import run_full_pipeline

    arts = run_full_pipeline(
        n_reviews=80, use_synthetic=True, llm_backend="mock"
    )
    assert arts.clustering_eval is not None
    assert arts.topic_agreement is not None
    assert arts.sentiment_rating_eval is not None
    assert arts.roi_cv_eval is not None
    assert arts.random_seed_used == 42


def test_pipeline_skip_evaluation_leaves_fields_none():
    """当 skip_evaluation=True 时，4 个评估字段都应是 None，pipeline 仍跑通。"""
    from src.pipeline import run_full_pipeline

    arts = run_full_pipeline(
        n_reviews=80, use_synthetic=True, llm_backend="mock", skip_evaluation=True
    )
    assert arts.clustering_eval is None
    assert arts.topic_agreement is None
    assert arts.sentiment_rating_eval is None
    assert arts.roi_cv_eval is None
    # 但 pipeline 输出仍应完整
    assert not arts.reviews.empty
    assert not arts.roi.empty


def test_pipeline_random_seed_override_propagates():
    """random_seed_override 应当反映在 arts.random_seed_used 与 generated reviews 上。"""
    from src.pipeline import run_full_pipeline

    arts_a = run_full_pipeline(
        n_reviews=120, llm_backend="mock", random_seed_override=7
    )
    arts_b = run_full_pipeline(
        n_reviews=120, llm_backend="mock", random_seed_override=7
    )
    arts_c = run_full_pipeline(
        n_reviews=120, llm_backend="mock", random_seed_override=8
    )
    assert arts_a.random_seed_used == 7
    assert arts_b.random_seed_used == 7
    assert arts_c.random_seed_used == 8
    # 同一 seed 下 KMeans 分配应一致（segmentation 确定性）
    seg_a = arts_a.segment_assignments.sort_values("review_id").reset_index(drop=True)
    seg_b = arts_b.segment_assignments.sort_values("review_id").reset_index(drop=True)
    assert (seg_a["cluster_id"] == seg_b["cluster_id"]).all()
    # 不同 seed 下应不同（至少在某些 review 上）
    seg_c = arts_c.segment_assignments.sort_values("review_id").reset_index(drop=True)
    assert not (seg_a["cluster_id"] == seg_c["cluster_id"]).all()


# ---------------------------------------------------------------------------
# 10. Disclosure contract — every evaluator must self-document honestly
# ---------------------------------------------------------------------------
def test_all_disclosures_contain_honest_qualifier():
    """5 个 evaluator 的 disclosure 都必须包含"synthetic"/"circular"/"honest"等关键词。"""
    rng = np.random.default_rng(0)
    n = 40
    X = rng.normal(size=(n, 3))
    labels_pred = np.repeat([0, 1], n // 2)
    labels_true = np.repeat(["A", "B"], n // 2)
    clu = eval_clustering(X, labels_pred, labels_true=labels_true)
    top = eval_topic_llm_vs_tfidf([["a", "b"]], ["a", "c"])
    sent = eval_sentiment_vs_rating(
        pd.DataFrame({"overall": rng.normal(size=20), "rating": rng.choice([1, 2, 3, 4, 5], 20)})
    )
    roi = eval_roi_cv(
        pd.DataFrame({"a": rng.normal(size=20), "b": rng.normal(size=20)}),
        rng.normal(size=20),
    )
    disclosures = [clu.disclosure, top.disclosure, sent.disclosure, roi.disclosure]
    for d in disclosures:
        # 必须包含至少一个 honest qualifier
        assert any(
            kw in d.lower()
            for kw in ("synthetic", "circular", "sanity", "deterministic", "proxy", "heuristic", "expected")
        ), f"disclosure missing honest qualifier: {d!r}"


if __name__ == "__main__":
    import pytest as _pytest

    raise SystemExit(_pytest.main([__file__, "-v"]))