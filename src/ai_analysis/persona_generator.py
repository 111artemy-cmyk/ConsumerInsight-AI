"""消费者画像（Persona）生成器。

输入：聚类后的细分受众 + 每个受众的代表性评论
输出：结构化的 Persona 卡片（昵称、年龄、职业、痛点、首选渠道…）

实现方式
--------
1. 用 scikit-learn 的 KMeans 在 TF-IDF 特征上对评论做软聚类
2. 每个聚类取代表性评论（离质心最近的若干条）
3. 调用 LLM 把代表性评论合成 Persona 卡片
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from ..llm import BaseLLMClient, PromptLibrary


@dataclass
class PersonaResult:
    personas: pd.DataFrame
    cluster_assignments: pd.DataFrame
    cluster_keywords: pd.DataFrame


class PersonaGenerator:
    """Synthesise consumer personas from review clusters."""

    def __init__(
        self,
        llm: BaseLLMClient,
        n_clusters: int = 4,
        random_state: int = 42,
    ):
        self.llm = llm
        self.n_clusters = n_clusters
        self.random_state = random_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, df: pd.DataFrame, text_col: str = "text") -> PersonaResult:
        if df.empty:
            raise ValueError("Input DataFrame is empty.")
        corpus = df[text_col].astype(str).tolist()

        # ---- Step 1: TF-IDF + KMeans ----------------------------------
        try:
            vec = TfidfVectorizer(
                analyzer="char_wb", ngram_range=(2, 4), max_features=1500
            )
        except Exception:
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        X = vec.fit_transform(corpus)
        n_clusters = min(self.n_clusters, max(1, X.shape[0] // 20))
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=self.random_state)
        labels = km.fit_predict(X)

        # ---- Step 2: per-cluster representative reviews ---------------
        reps: Dict[int, List[str]] = {}
        cluster_kw_rows: List[Dict[str, Any]] = []
        feature_names = vec.get_feature_names_out()
        for cid in range(n_clusters):
            mask = labels == cid
            if not mask.any():
                reps[cid] = []
                continue
            cluster_docs = X[mask]
            # Top features by total tfidf in cluster
            top_idx = np.asarray(cluster_docs.sum(axis=0)).ravel().argsort()[::-1][:8]
            cluster_kw_rows.append(
                {
                    "cluster_id": cid,
                    "keywords": [feature_names[i] for i in top_idx],
                }
            )
            # Representative docs: closest to centroid
            centroid = km.cluster_centers_[cid]
            sims = cluster_docs @ centroid
            # 兼容不同 scipy 版本：boolean mask 索引可能返回 ndarray 而不是 csr_matrix
            if hasattr(sims, "toarray"):
                sims = sims.toarray().ravel()
            else:
                sims = np.asarray(sims).ravel()
            top_doc_idx = np.argsort(-sims)[:3]
            reps[cid] = [corpus[i] for i in top_doc_idx]

        # ---- Step 3: LLM persona synthesis ----------------------------
        personas: List[Dict[str, Any]] = []
        for cid, snippets in reps.items():
            persona = self._persona_for_cluster(cid, snippets)
            persona["cluster_id"] = cid
            persona["cluster_keywords"] = cluster_kw_rows[cid]["keywords"]
            personas.append(persona)

        personas_df = pd.DataFrame(personas)
        cluster_assignments = pd.DataFrame(
            {
                "review_id": df.get("review_id"),
                "user_segment": df.get("user_segment"),
                "cluster_id": labels,
            }
        )
        return PersonaResult(
            personas=personas_df,
            cluster_assignments=cluster_assignments,
            cluster_keywords=pd.DataFrame(cluster_kw_rows),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _persona_for_cluster(self, cid: int, snippets: List[str]) -> Dict[str, Any]:
        """Ask the LLM to synthesise a persona card from cluster snippets."""
        import json as _json

        corpus = "\n".join(f"  - {s}" for s in snippets) or "（无代表评论）"
        system = PromptLibrary.PERSONA_SYSTEM
        user = PromptLibrary.PERSONA_USER_TEMPLATE.format(
            n_clusters=1,  # we synthesise one at a time
            cid=cid + 1,
            corpus_cid=corpus,
        )
        resp = self.llm.complete_json(system, user)
        parsed = resp.parsed
        # 兼容 Mock LLM 返回 list-of-dict 的情况：
        # base.py 的 _try_parse_json 只识别 Dict，所以这里手动 fallback 解析一次。
        if parsed is None and resp.text:
            try:
                parsed = _json.loads(resp.text)
            except Exception:
                parsed = None
        if isinstance(parsed, list) and parsed:
            return dict(parsed[0])
        if isinstance(parsed, dict) and parsed:
            return dict(parsed)
        return {"persona_id": f"P{cid + 1:02d}", "_raw": resp.text}
