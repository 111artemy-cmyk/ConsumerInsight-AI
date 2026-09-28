"""Illustrative ROI predictor (示意性 ROI 指数).

Design
------
在没有真实转化 / 曝光数据的情况下，构造一个**示意性 ROI 指数**
作为 pipeline 端到端可跑通、可解释的输出：

1. 用评论代理信号构造 ``soft_conversion`` (sigmoid 输出)。
2. 用 :class:`ROIConfig.baseline_soft_conversion` 减去零信号基线，
   避免 sigmoid 把"零信号"误判为高 ROI（恒得 +11.0）。
3. 在 per-review 层级计算 ROI proxy，并用 K-fold CV 报告
   R² / MAE / 系数 —— 让 CV 数字有可解释性，而不是 trivial 自拟合。
4. 按 segment 聚合，得到每个细分群的 ``expected_roi``（即
   ``illustrative_roi_index`` 的别名）。

注意
----
* 这是一个**教学 / 演示级**模型。所有成本 / 收入假设都来自
  :class:`ROIConfig`，可被替换为真实值。
* 在真实业务里，应接入订单 / 曝光数据并用 uplift model 或因果推断。
* **不要把任何 ``expected_roi`` / ``illustrative_roi_index`` 数字当成
  真实的业务结果。**
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold

from ..config import ROIConfig


@dataclass
class ROIResult:
    """Container for the illustrative ROI outputs.

    Attributes
    ----------
    segment_roi
        Per-segment aggregated table. Columns include ``cluster_id``,
        ``volume``, ``avg_sentiment``, ``avg_rating``,
        ``predicted_soft_conversion``, ``expected_revenue``,
        ``expected_cost``, ``expected_roi`` and the alias
        ``illustrative_roi_index`` (= ``expected_roi``).
    coefficients
        Single Ridge fit on the full training data (legacy columns).
    cv_r2, cv_mae
        Mean K-fold CV metrics on the per-review ROI proxy. These are
        the metrics a reviewer should look at to judge whether the four
        features can predict per-review ROI at all.
    cv_coefficients
        Mean Ridge coefficients across the K folds, with the fold count.
    notes
        Plain-text disclosure explaining what the numbers mean.
    """

    segment_roi: pd.DataFrame
    coefficients: pd.DataFrame
    cv_r2: float
    cv_mae: float
    cv_coefficients: pd.DataFrame
    notes: str


class ROIPredictor:
    """Predict segment-level illustrative ROI from sentiment signals."""

    def __init__(self, config: Optional[ROIConfig] = None):
        self.config = config or ROIConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fit_predict(
        self,
        per_review: pd.DataFrame,
        segment_col: str = "cluster_id",
        text_col: str = "text",
        rating_col: str = "rating",
        sentiment_col: str = "overall",
    ) -> ROIResult:
        if per_review.empty:
            raise ValueError("Input DataFrame is empty.")
        cfg = self.config

        df = per_review.copy()
        df[text_col] = df[text_col].astype(str)
        df["text_len"] = df[text_col].str.len()
        df["high_rating"] = (df[rating_col].fillna(3) >= 4).astype(int)
        df["long_text"] = (df["text_len"] >= 18).astype(int)
        df["repurchase_intent"] = df[text_col].str.contains(
            "回购|囤货|复购|再买|再入", regex=True
        ).astype(int)

        # soft_conversion is the response proxy in the legacy formulation.
        df["soft_conversion"] = _sigmoid(
            1.0 * df[sentiment_col].fillna(0)
            + 0.6 * df["high_rating"]
            + 0.3 * df["long_text"]
            + 0.2 * df["repurchase_intent"]
        )

        # ---- per-review ROI proxy --------------------------------------
        # K-fold CV 的 y 用 per-review ROI proxy，而不是 soft_conversion，
        # 这样 CV R² / MAE 是有意义的（不是 trivial 自拟合）。
        # baseline gate 与原代码保持一致：只有 soft_conversion 显著高于
        # baseline_soft_conversion 才记为正收益。
        effective_per_review = (
            df["soft_conversion"] - cfg.baseline_soft_conversion
        ).clip(lower=0.0)
        df["per_review_revenue"] = effective_per_review * cfg.baseline_arpu
        df["per_review_cost"] = cfg.cost_per_user
        df["per_review_roi"] = (
            (df["per_review_revenue"] - df["per_review_cost"])
            / df["per_review_cost"]
        )

        # ---- K-fold CV on per-review ROI proxy -------------------------
        feature_cols = [sentiment_col, "high_rating", "long_text", "repurchase_intent"]
        X = df[feature_cols].fillna(0).to_numpy()
        y = df["per_review_roi"].to_numpy()
        cv_r2, cv_mae, cv_coefs = _cv_ridge(
            X,
            y,
            n_folds=cfg.roi_cv_folds,
            random_state=cfg.roi_cv_random_state,
        )

        # ---- aggregate by segment --------------------------------------
        agg = df.groupby(segment_col).agg(
            volume=(sentiment_col, "size"),
            avg_sentiment=(sentiment_col, "mean"),
            avg_rating=(rating_col, "mean") if rating_col in df.columns else (sentiment_col, "mean"),
            predicted_soft_conversion=("soft_conversion", "mean"),
        ).reset_index()
        agg["expected_cost"] = (agg["volume"] * cfg.cost_per_user).round(2)
        # 与原代码一致的 baseline gate：避免 sigmoid 把零信号误判为高 ROI
        effective_conv = (
            agg["predicted_soft_conversion"] - cfg.baseline_soft_conversion
        ).clip(lower=0.0)
        agg["expected_revenue"] = (
            effective_conv * cfg.baseline_arpu * agg["volume"]
        ).round(2)
        agg["expected_roi"] = (
            (agg["expected_revenue"] - agg["expected_cost"]) / agg["expected_cost"]
        ).round(3)
        # illustrative_ 前缀的别名：与原列同步值，方便下游 / 报告统一引用
        agg["illustrative_roi_index"] = agg["expected_roi"]

        coef_df = pd.DataFrame(
            {
                "feature": feature_cols,
                "coefficient": cv_coefs.round(4),
                "intercept": [None] * len(feature_cols),  # 见 cv_coefficients
            }
        )
        cv_coef_df = pd.DataFrame(
            {
                "feature": feature_cols,
                "cv_coefficient": cv_coefs.round(4),
                "cv_r2": [round(cv_r2, 4)] + [None] * (len(feature_cols) - 1),
                "cv_mae": [round(cv_mae, 4)] + [None] * (len(feature_cols) - 1),
                "cv_folds": [cfg.roi_cv_folds] + [None] * (len(feature_cols) - 1),
            }
        )

        notes = (
            "Illustrative ROI index — synthetic data only. "
            "Computed from sentiment-driven soft_conversion signals "
            f"with ARPU=¥{cfg.baseline_arpu:.0f} and CAC=¥{cfg.cost_per_user:.0f} "
            "(see ROIConfig in src/config.py). "
            "K-fold CV R²/MAE on per-review ROI proxy report how well "
            "the four features predict per-review ROI; this is NOT a "
            "real causal estimate of marketing spend return."
        )

        return ROIResult(
            segment_roi=agg,
            coefficients=coef_df,
            cv_r2=float(cv_r2),
            cv_mae=float(cv_mae),
            cv_coefficients=cv_coef_df,
            notes=notes,
        )


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _cv_ridge(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: int = 5,
    random_state: int = 42,
):
    """K-fold CV with Ridge; returns mean R², MAE, and mean coefficients.

    Yields
    ------
    r2_mean, mae_mean : float
    coefs_mean : np.ndarray of shape (n_features,)
    """
    n_samples = len(X)
    # n_folds 不能大于样本数；退化到 2-fold（或留一）。
    n_folds = max(2, min(n_folds, n_samples))
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    r2s, maes, coefs = [], [], []
    for train_idx, test_idx in kf.split(X):
        model = Ridge(alpha=1.0)
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[test_idx])
        r2s.append(r2_score(y[test_idx], preds))
        maes.append(mean_absolute_error(y[test_idx], preds))
        coefs.append(model.coef_)
    return float(np.mean(r2s)), float(np.mean(maes)), np.mean(coefs, axis=0)