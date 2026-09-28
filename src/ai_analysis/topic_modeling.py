"""主题提取（Topic Modeling）模块。

策略
----
1. 词袋 + TF-IDF 提取关键词（传统 NLP 基线）
2. 把评论按文本块喂给 LLM，让它以 JSON 数组形式返回核心话题
3. 将 LLM 输出的话题与 TF-IDF 关键词做交叉验证，得到最终主题列表

输出
----
:meth:`TopicModeler.run` 返回 :class:`TopicResult`，包含：

* ``topics``        : 主题列表（DataFrame）
* ``keywords``      : 每个主题的代表关键词
* ``reviews_topic`` : 每条评论对应的主题（DataFrame）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from ..llm import BaseLLMClient, PromptLibrary


@dataclass
class TopicResult:
    topics: pd.DataFrame
    keywords: pd.DataFrame
    reviews_topic: pd.DataFrame


class TopicModeler:
    """Extract topics from a corpus of reviews."""

    def __init__(
        self,
        llm: BaseLLMClient,
        n_topics: int = 5,
        brand_name: str = "花西子 Florasis",
    ):
        self.llm = llm
        self.n_topics = n_topics
        self.brand_name = brand_name

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, df: pd.DataFrame, text_col: str = "text") -> TopicResult:
        if df.empty:
            raise ValueError("Input DataFrame is empty.")
        corpus = df[text_col].astype(str).tolist()

        # ---- LLM-based topic extraction ------------------------------
        joined_corpus = "\n".join(f"- {c}" for c in corpus[:120])  # cap prompt size
        system = PromptLibrary.TOPIC_SYSTEM
        user = PromptLibrary.TOPIC_USER_TEMPLATE.format(
            brand=self.brand_name,
            n_reviews=len(corpus),
            n_topics=self.n_topics,
            corpus=joined_corpus,
        )
        resp = self.llm.complete_json(system, user)
        topics_data = resp.parsed if isinstance(resp.parsed, list) else []
        topics_df = pd.DataFrame(topics_data) if topics_data else pd.DataFrame()

        # ---- TF-IDF keywords per topic -------------------------------
        # 用 sklearn 的 TF-IDF 提取全语料关键词，作为对 LLM 输出的补充校验
        kw_df = self._tfidf_keywords(corpus, top_k=15)

        # ---- Assign each review to its closest topic -----------------
        reviews_topic = self._assign_topics(df, topics_df)

        return TopicResult(topics=topics_df, keywords=kw_df, reviews_topic=reviews_topic)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _tfidf_keywords(self, corpus: List[str], top_k: int = 15) -> pd.DataFrame:
        """Return top-K TF-IDF keywords for the whole corpus."""
        # 中文停用词只在 word analyzer 下生效 —— char_wb + ngram 场景下 sklearn
        # 会静默忽略 stop_words 并打 UserWarning。这里改用预处理阶段清洗语料，
        # 既真正生效，又不依赖 jieba 这类分词器。
        stop_chars = set("的了和是在就都也很有我你他她它这那一个一些啊吗呢吧嗯哈哦呀是也就")
        cleaned_corpus = [
            "".join(ch for ch in doc if ch not in stop_chars) for doc in corpus
        ]
        # 全部是停用字会导致空字符串，TF-IDF 会抛 ValueError；退化到原语料。
        if all(not c.strip() for c in cleaned_corpus):
            cleaned_corpus = corpus
        # ngram_range=(2, 3) 输出 char-2-grams + char-3-grams，
        # 让 word-level LLM 关键词（多数 2-3 字）能与之做精确匹配，
        # 用于在 eval_topic_llm_vs_tfidf 中计算 overlap_ratio / Jaccard。
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3), max_features=2000)
        vec.fit(cleaned_corpus)
        # 用同一份清洗语料 transform，保证 vocab 与统计对齐。
        scores = vec.transform(cleaned_corpus).sum(axis=0).A1
        vocab = vec.get_feature_names_out()
        order = scores.argsort()[::-1][:top_k]
        return pd.DataFrame(
            {"keyword": vocab[order], "tfidf_sum": scores[order]}
        )

    def _assign_topics(
        self,
        df: pd.DataFrame,
        topics_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Assign each review to the topic whose keywords overlap most."""
        if topics_df.empty:
            return pd.DataFrame(
                {"review_id": df.get("review_id"), "topic_id": None}
            )
        out_rows = []
        topic_keywords = {
            row["topic_id"]: list(row.get("representative_keywords") or [])
            for _, row in topics_df.iterrows()
        }
        for _, row in df.iterrows():
            text = str(row["text"])
            best_id, best_hits = None, -1
            for tid, kws in topic_keywords.items():
                hits = sum(1 for k in kws if k and k in text)
                if hits > best_hits:
                    best_hits = hits
                    best_id = tid
            out_rows.append({"review_id": row.get("review_id"), "topic_id": best_id})
        return pd.DataFrame(out_rows)
