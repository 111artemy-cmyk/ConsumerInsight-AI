"""受众细分（Audience Segmentation）。

方法
----
1. 把每条评论的 TF-IDF 向量与少量行为特征（rating、平台、用户年龄层）
   拼接，形成综合特征空间。
2. 在拼接后的特征上跑 KMeans，得到 ``n_segments`` 个细分群。
3. 对每个细分群计算：平均评分、平均情感分、占比、平台分布、年龄分布。

输出
----
:meth:`Segmenter.run` 返回 :class:`SegmentationResult`：

* ``assignments``     — 每条评论对应的 cluster_id
* ``segment_profile`` — 每个细分群的画像统计
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder


@dataclass
class SegmentationResult:
    assignments: pd.DataFrame
    segment_profile: pd.DataFrame
    feature_importance: pd.DataFrame


class Segmenter:
    """Cluster reviews into behavioural / topical segments."""

    def __init__(
        self,
        n_segments: int = 4,
        random_state: int = 42,
    ):
        self.n_segments = n_segments
        self.random_state = random_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        df: pd.DataFrame,
        text_col: str = "text",
    ) -> SegmentationResult:
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        corpus = df[text_col].astype(str).tolist()
        # TF-IDF on text
        try:
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=1200)
        except Exception:
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        X_text = vec.fit_transform(corpus)

        # Behavioural features: platform + age_band + rating
        cat_cols = []
        cat_values: List[np.ndarray] = []
        for col in ["platform", "user_age_band"]:
            if col in df.columns:
                cat_cols.append(col)
                cat_values.append(df[col].astype(str).to_numpy().reshape(-1, 1))

        ohe = None  # 默认未启用分类特征
        if cat_values:
            try:
                ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
                X_cat = ohe.fit_transform(np.hstack(cat_values))
            except TypeError:
                # 兼容老版本 sklearn (sparse_output 不可用)
                try:
                    ohe = OneHotEncoder(handle_unknown="ignore", sparse=True)
                    X_cat = ohe.fit_transform(np.hstack(cat_values))
                except Exception:
                    X_cat = csr_matrix((len(df), 0))
                    ohe = None
            except Exception:
                X_cat = csr_matrix((len(df), 0))
                ohe = None
        else:
            X_cat = csr_matrix((len(df), 0))

        if "rating" in df.columns:
            rating = df["rating"].fillna(df["rating"].median()).to_numpy().reshape(-1, 1)
            X_rating = csr_matrix(rating - rating.mean())
        else:
            X_rating = csr_matrix((len(df), 0))

        X = hstack([X_text, X_cat, X_rating]).tocsr()
        n_clusters = min(self.n_segments, max(1, X.shape[0] // 25))
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=self.random_state)
        labels = km.fit_predict(X)

        assignments = pd.DataFrame(
            {
                "review_id": df.get("review_id"),
                "user_segment": df.get("user_segment"),
                "platform": df.get("platform"),
                "rating": df.get("rating"),
                "cluster_id": labels,
            }
        )

        profile = self._build_profile(df, labels)
        importance = self._feature_importance(vec, ohe, km)

        return SegmentationResult(
            assignments=assignments,
            segment_profile=profile,
            feature_importance=importance,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _build_profile(self, df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
        df = df.copy()
        df["__cluster__"] = labels
        agg = df.groupby("__cluster__").agg(
            volume=("review_id", "size") if "review_id" in df.columns else ("__cluster__", "size"),
            avg_rating=("rating", "mean") if "rating" in df.columns else ("__cluster__", "mean"),
        ).reset_index()
        # Platform mix
        if "platform" in df.columns:
            pivot = (
                df.groupby(["__cluster__", "platform"])
                .size()
                .unstack(fill_value=0)
            )
            pivot = pivot.div(pivot.sum(axis=1), axis=0).round(3)
            agg = agg.merge(
                pivot.reset_index().rename(columns={"__cluster__": "__cluster__"}),
                on="__cluster__", how="left",
            )
        # Age-band mix
        if "user_age_band" in df.columns:
            pivot = (
                df.groupby(["__cluster__", "user_age_band"])
                .size()
                .unstack(fill_value=0)
            )
            pivot = pivot.div(pivot.sum(axis=1), axis=0).round(3)
            agg = agg.merge(
                pivot.reset_index(),
                on="__cluster__", how="left",
            )
        return agg.rename(columns={"__cluster__": "segment_id"})

    def _feature_importance(
        self,
        vec: TfidfVectorizer,
        ohe,  # OneHotEncoder | None
        km: KMeans,
    ) -> pd.DataFrame:
        """Return top features by |centroid value| for cluster interpretation.

        Notes
        -----
        The centroid contains TF-IDF columns + OHE columns + rating column.
        We rank by absolute value of the TF-IDF portion to keep the
        output language-interpretable.
        """
        vocab = vec.get_feature_names_out()
        centers = km.cluster_centers_
        # 只对前 len(vocab) 个 TF-IDF 列排序，避免把 OHE/rating 列也当作"特征"，
        # 同时防止越界访问 vocab。
        rows = []
        n_vocab = len(vocab)
        for cid, row in enumerate(centers):
            order = np.argsort(-np.abs(row[:n_vocab]))[:10]
            rows.append(
                {
                    "segment_id": cid,
                    "top_features": ", ".join(vocab[i] for i in order),
                }
            )
        return pd.DataFrame(rows)
