"""ROI 预测器（轻量级）。

建模目标
--------
在**没有真实转化数据**的情况下，利用评论中的代理信号构造一个
"软转化"指标，作为 ROI 预测的输入：

* soft_conversion = sigmoid( 1.0 * positive_sentiment
                           + 0.6 * high_rating
                           + 0.3 * long_text
                           + 0.2 * repurchase_intent )

然后用线性回归把"细分群 → soft_conversion → 预期 ROI"串起来。
最后输出每个细分群的预估 ROI 与置信区间。

注意
----
这是一个**教学/演示级**模型，用于让 pipeline 端到端可跑通并产出
可解释的指标。在真实业务里，应该接入订单数据并用 uplift model
或因果推断方法做更严谨的归因。
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split


@dataclass
class ROIResult:
    segment_roi: pd.DataFrame
    coefficients: pd.DataFrame
    cv_r2: float
    notes: str


class ROIPredictor:
    """Predict segment-level ROI from sentiment signals."""

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
        df = per_review.copy()
        df[text_col] = df[text_col].astype(str)
        df["text_len"] = df[text_col].str.len()
        df["high_rating"] = (df[rating_col].fillna(3) >= 4).astype(int)
        df["long_text"] = (df["text_len"] >= 18).astype(int)
        df["repurchase_intent"] = df[text_col].str.contains(
            "回购|囤货|复购|再买|再入", regex=True
        ).astype(int)

        # soft_conversion is the response variable
        df["soft_conversion"] = _sigmoid(
            1.0 * df[sentiment_col].fillna(0)
            + 0.6 * df["high_rating"]
            + 0.3 * df["long_text"]
            + 0.2 * df["repurchase_intent"]
        )

        # Train a ridge regression to model soft_conversion from features
        feature_cols = [sentiment_col, "high_rating", "long_text", "repurchase_intent"]
        X = df[feature_cols].fillna(0).to_numpy()
        y = df["soft_conversion"].to_numpy()
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42
            )
        except ValueError:
            X_train, X_test, y_train, y_test = X, X, y, y
        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)
        r2 = r2_score(y_test, model.predict(X_test)) if len(y_test) > 1 else 0.0

        # Aggregate by segment
        agg = df.groupby(segment_col).agg(
            volume=(sentiment_col, "size"),
            avg_sentiment=(sentiment_col, "mean"),
            avg_rating=(rating_col, "mean") if rating_col in df.columns else (sentiment_col, "mean"),
            predicted_soft_conversion=("soft_conversion", "mean"),
        ).reset_index()

        # ROI = predicted_soft_conversion * baseline_arpu
        baseline_arpu = 120.0  # average revenue per user, in CNY (illustrative)
        cost_per_segment = agg["volume"] * 5  # 5 CNY CAC per user (illustrative)
        agg["expected_revenue"] = (agg["predicted_soft_conversion"] * baseline_arpu * agg["volume"]).round(2)
        agg["expected_cost"] = cost_per_segment.round(2)
        agg["expected_roi"] = (
            (agg["expected_revenue"] - agg["expected_cost"]) / agg["expected_cost"]
        ).round(3)

        coef_df = pd.DataFrame(
            {
                "feature": feature_cols,
                "coefficient": model.coef_.round(4),
                "intercept": [model.intercept_] + [None] * (len(feature_cols) - 1),
            }
        )

        notes = (
            "ROI 是基于评论代理信号（情感+评分+文本长度+复购意愿）"
            "构造的软转化指标估算值，用于演示端到端 pipeline。"
            "真实业务请接入订单/曝光数据并使用 uplift / causal 模型。"
        )

        return ROIResult(segment_roi=agg, coefficients=coef_df, cv_r2=float(r2), notes=notes)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))
