"""Offline, rule-based LLM mock.

This module implements a deterministic stand-in for a real LLM that
works without any API key.  It is **intentionally simple** so that the
pipeline can be:

* demoed on any laptop (no network, no paid APIs);
* unit-tested deterministically;
* used as a fallback when an upstream provider rate-limits the request.

The mock produces JSON-shaped responses for the four prompts we use
in the pipeline:

* multi-aspect sentiment,
* topic extraction,
* persona generation,
* campaign message generation.

It is **not** a substitute for a real LLM in production — it is a
deterministic, fast, free baseline that lets reviewers reproduce the
entire pipeline end-to-end.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from typing import Any, Dict, List, Optional

from .base import BaseLLMClient, LLMResponse


class MockLLMClient(BaseLLMClient):
    """A deterministic, offline rule-based LLM stand-in.

    Strategy:

    1.  Match the user prompt against a small set of *intent
        classifiers* (regex / keywords) to figure out which task the
        caller is asking for.
    2.  Build the response from hand-crafted templates that combine
        keyword-based scoring (sentiment), heuristic rules
        (topic/keyword extraction) and a touch of stochasticity so that
        repeated runs feel realistic.
    """

    name = "mock"

    # ------------------------------------------------------------------
    # Sentiment lexicons (small but expressive)
    # ------------------------------------------------------------------
    POS = {
        "好", "棒", "喜欢", "推荐", "惊艳", "完美", "超值", "满意", "回购",
        "持久", "细腻", "高级感", "服帖", "自然", "显白", "精致", "好用",
        "颜值高", "设计感", "质感", "丝滑", "清透", "持妆", "奶油肌",
        "妈生皮", "磨皮", "平价", "大牌", "包装好看", "送礼", "被夸",
        "没踩雷", "惊喜", "回购", "囤货", "上镜", "约会",
    }
    NEG = {
        "差", "失望", "难用", "浮粉", "拔干", "卡粉", "脱妆", "暗沉", "厚重",
        "假白", "刺激", "过敏", "爆痘", "闷痘", "踩雷", "不推荐", "退货",
        "包装差", "漏粉", "飞粉", "色差", "氧化", "暗沉", "假面", "拔干起皮",
        "不服帖", "难推开", "颗粒感", "结块", "斑驳",
    }
    INTENSIFIERS = {"非常", "特别", "超", "太", "巨", "真的", "简直", "绝对"}
    NEGATORS = {"不", "没", "无", "别", "不是"}

    # ------------------------------------------------------------------
    # Topic keyword pools
    # ------------------------------------------------------------------
    TOPIC_POOL: Dict[str, Dict[str, Any]] = {
        "packaging_design": {
            "label": "包装设计",
            "keywords": ["包装", "颜值", "设计", "好看", "国风", "雕花", "精致", "高级感"],
            "description": "消费者高度关注产品的视觉设计与国风文化表达",
        },
        "skin_feel_long_wear": {
            "label": "上脸肤感与持久度",
            "keywords": ["服帖", "持久", "持妆", "不拔干", "细腻", "奶油肌", "妈生皮", "不卡粉", "自然"],
            "description": "用户反复提及上脸服帖度与全天持妆效果",
        },
        "value_for_money": {
            "label": "性价比",
            "keywords": ["平价", "超值", "划算", "性价比", "贵", "便宜", "值得", "价位"],
            "description": "对定价、促销和性价比高度敏感",
        },
        "color_shade": {
            "label": "色号与妆效",
            "keywords": ["色号", "显白", "自然", "氧化", "暗沉", "白皮", "黄皮", "妆效"],
            "description": "对色号匹配度、不同肤色妆效差异的关注",
        },
        "skin_sensitivity": {
            "label": "敏感肌与刺激",
            "keywords": ["过敏", "刺激", "敏感肌", "爆痘", "闷痘", "泛红", "刺痛"],
            "description": "敏感肌人群对成分与刺激性的担忧",
        },
        "logistics_service": {
            "label": "物流与服务",
            "keywords": ["快递", "物流", "客服", "售后", "包装", "赠品", "破损"],
            "description": "对快递时效、客服响应、赠品体验的反馈",
        },
    }

    # ------------------------------------------------------------------
    # Channel-specific writing styles
    # ------------------------------------------------------------------
    CHANNEL_HASHTAGS: Dict[str, List[str]] = {
        "小红书": ["#花西子", "#美妆测评", "#空气蜜粉", "#平价彩妆", "#国货之光"],
        "微博": ["#花西子#", "#彩妆测评#", "#持妆一整天#"],
        "抖音": ["#花西子", "#美妆教程", "#底妆神器"],
        "朋友圈": ["#今日妆容", "#好物分享"],
    }

    CHANNEL_STYLE_TIPS: Dict[str, str] = {
        "小红书": "种草语气，多用 emoji，分点描述使用场景",
        "微博": "话题驱动，简短有力，互动感强",
        "抖音": "节奏感强，描述镜头与画面，多用反差词",
        "朋友圈": "私人化、情绪化，强调自我感受",
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def complete(self, system: str, user: str) -> LLMResponse:
        """Dispatch the request to a specialised handler based on prompt content.

        IMPORTANT: campaign must be checked BEFORE persona, because the
        campaign prompt embeds the persona JSON (which itself contains
        ``persona_id``) and would otherwise be misrouted to the persona
        handler — yielding only 1 dict instead of the requested N.
        """
        text = user
        # Pick a handler by inspecting the user message
        if "维度的情感分数" in text or "维度列表" in text:
            payload = self._handle_sentiment(text)
        elif "候选营销文案" in text or "variant_id" in text:
            payload = self._handle_campaign(text)
        elif "核心话题" in text or "topic_label_cn" in text:
            payload = self._handle_topics(text)
        elif "Persona 卡片" in text or "persona_id" in text:
            payload = self._handle_persona(text)
        else:
            payload = {"text": self._generic_chat(system, user)}

        text_out = json.dumps(payload, ensure_ascii=False, indent=2)
        usage = {"prompt_tokens": len(user), "completion_tokens": len(text_out)}
        return LLMResponse(text=text_out, parsed=payload, raw=None, usage=usage)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _handle_sentiment(self, user: str) -> Dict[str, Any]:
        # Extract the user text between triple quotes
        text_match = re.search(r'"""(.*?)"""', user, re.DOTALL)
        body = text_match.group(1).strip() if text_match else user
        # Extract dimensions list
        dim_match = re.search(r"维度列表：(.+)", user)
        dims_raw = dim_match.group(1).strip() if dim_match else ""
        dims = [d.strip() for d in re.split(r"[、，,]", dims_raw) if d.strip()]

        score = self._score_text(body)
        per_dim: Dict[str, Dict[str, Any]] = {}
        for dim in dims:
            relevance = self._dimension_relevance(body, dim)
            per_dim[dim] = {
                "score": round(score * relevance, 3),
                "rationale": self._rationale_for(body, dim, score * relevance),
            }
        return {"dimensions": per_dim, "overall": round(score, 3)}

    def _handle_topics(self, user: str) -> List[Dict[str, Any]]:
        # Extract corpus between triple quotes
        corpus_match = re.search(r'"""(.*?)"""', user, re.DOTALL)
        corpus = corpus_match.group(1).strip() if corpus_match else user
        n_match = re.search(r"提炼出\s*(\d+)\s*个核心话题", user)
        n = int(n_match.group(1)) if n_match else 5
        # Score each topic
        scored = []
        for tid, info in self.TOPIC_POOL.items():
            hits = sum(1 for kw in info["keywords"] if kw in corpus)
            if hits:
                scored.append((hits, tid, info))
        scored.sort(reverse=True)
        scored = scored[:n] or [self.TOPIC_POOL[k] for k in list(self.TOPIC_POOL)[:n]]
        # Normalise share
        total = sum(s[0] for s in scored) or 1
        out = []
        for hits, tid, info in scored:
            out.append(
                {
                    "topic_id": tid,
                    "topic_label_cn": info["label"],
                    "description": info["description"],
                    "representative_keywords": info["keywords"][:5],
                    "share_estimate": round(hits / total, 3),
                }
            )
        return out

    def _handle_persona(self, user: str) -> List[Dict[str, Any]]:
        cid_match = re.search(r"群体\s*(\d+)", user)
        cid = int(cid_match.group(1)) if cid_match else 1
        corpus_match = re.search(r'"""(.*?)"""', user, re.DOTALL)
        corpus = corpus_match.group(1).strip() if corpus_match else ""
        persona = self._synthesize_persona(cid, corpus)
        return [persona]

    def _handle_campaign(self, user: str) -> List[Dict[str, Any]]:
        persona_match = re.search(r"Persona：(.+?)\n\n", user, re.DOTALL)
        persona_raw = persona_match.group(1).strip() if persona_match else user
        try:
            persona = json.loads(persona_raw)
        except Exception:
            persona = {"nickname": "目标用户", "core_need": "日常通勤妆容"}

        objective_match = re.search(r"营销活动目标：(.+?)\n", user)
        objective = objective_match.group(1).strip() if objective_match else "提升新品转化率"
        highlights_match = re.search(r"活动卖点：\n(.+)", user, re.DOTALL)
        highlights = highlights_match.group(1).strip() if highlights_match else ""

        n_match = re.search(r"生成\s*(\d+)\s*条", user)
        n = int(n_match.group(1)) if n_match else 3
        # Pick channels based on persona
        channels = persona.get("preferred_channels") or ["小红书", "微博", "朋友圈"]
        out = []
        for i in range(n):
            channel = channels[i % len(channels)]
            variant = self._compose_campaign(i, channel, persona, objective, highlights)
            out.append(variant)
        return out

    def _generic_chat(self, system: str, user: str) -> str:
        # Fallback: echo with a friendly confirmation.
        return (
            "（Mock LLM）已收到请求。基于规则化策略生成的简短回复："
            + user[:120]
            + " ..."
        )

    # ------------------------------------------------------------------
    # Reusable building blocks
    # ------------------------------------------------------------------
    def _score_text(self, text: str) -> float:
        """Return an overall sentiment polarity in [-1, 1]."""
        pos = sum(1 for w in self.POS if w in text)
        neg = sum(1 for w in self.NEG if w in text)
        if pos == 0 and neg == 0:
            return 0.0
        score = (pos - neg) / max(pos + neg, 1)
        # Intensity boost
        if any(w in text for w in self.INTENSIFIERS):
            score *= 1.1
        # Negation flips polarity if it sits immediately before a polarity word
        if any(f"不{w}" in text or f"没{w}" in text for w in self.POS):
            score -= 0.3
        if any(f"不{w}" in text or f"没{w}" in text for w in self.NEG):
            score += 0.3
        return max(min(score, 1.0), -1.0)

    def _dimension_relevance(self, text: str, dim: str) -> float:
        dim_keyword_map: Dict[str, List[str]] = {
            "Product Quality": ["粉质", "细腻", "服帖", "质感", "好用", "高级感"],
            "Value for Money": ["平价", "超值", "划算", "性价比", "贵", "便宜"],
            "Packaging Design": ["包装", "颜值", "设计", "国风", "雕花", "好看"],
            "Skin Feel": ["上脸", "服帖", "拔干", "卡粉", "刺痛", "舒适"],
            "Long Wear": ["持久", "脱妆", "持妆", "氧化", "暗沉", "8小时"],
            "Service Experience": ["快递", "客服", "售后", "赠品", "包装"],
        }
        keywords = dim_keyword_map.get(dim, [])
        if not keywords:
            return 0.0
        hits = sum(1 for k in keywords if k in text)
        if hits == 0:
            return 0.0
        # Relevance decays if hit count is low
        return min(0.4 + 0.2 * hits, 1.0)

    def _rationale_for(self, text: str, dim: str, score: float) -> str:
        if score == 0.0:
            return "无关"
        if score > 0.3:
            return f"用户在文本中正面提及{dim}相关体验"
        if score < -0.3:
            return f"用户在文本中负面提及{dim}相关体验"
        return f"用户对{dim}的态度较为中性"

    def _synthesize_persona(self, cid: int, corpus: str) -> Dict[str, Any]:
        """Build a deterministic but realistic persona from a corpus."""
        seed = int(hashlib.md5((str(cid) + corpus[:80]).encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed)

        persona_templates = [
            {
                "persona_id": f"P{cid:02d}",
                "nickname": "通勤奶油肌Lisa",
                "age_range": "25-30",
                "occupation": "互联网公司市场运营",
                "core_need": "快速打造持久自然的奶油肌通勤底妆",
                "pain_points": [
                    "早八通勤赶时间，底妆不服帖",
                    "T区出油导致 3 小时就斑驳",
                    "对国风包装缺乏场景化搭配",
                ],
                "preferred_channels": ["小红书", "抖音"],
                "recommended_campaign_angle": "30 秒奶油肌挑战 + 国风限定礼盒",
                "why_matters": "规模最大 (26.5%) + ROI 峰值之一 (+19.41)，是 GMV 基本盘；用 国风礼盒 切入可同时拉动客单价与社交分享",
            },
            {
                "persona_id": f"P{cid:02d}",
                "nickname": "成分党小美",
                "age_range": "28-35",
                "occupation": "美妆博主 / 内容创作者",
                "core_need": "找到成分安全、性价比高、妆效在线的国货底妆",
                "pain_points": [
                    "敏感肌怕闷痘，对成分表要求高",
                    "色号难选，黄皮显灰",
                    "国货与国际大牌妆效差距",
                ],
                "preferred_channels": ["小红书", "微博"],
                "recommended_campaign_angle": "成分透明化对比测评 + 敏感肌打卡挑战",
                "why_matters": "中等规模 (21.2%)，平均评分高 (★4.69)，社交传播力强，是品牌口碑放大器；用 UGC 裂变可降低获客成本",
            },
            {
                "persona_id": f"P{cid:02d}",
                "nickname": "学生党阿月",
                "age_range": "18-23",
                "occupation": "在校大学生",
                "core_need": "百元内打造约会 / 答辩 / 面试的伪素颜底妆",
                "pain_points": [
                    "预算有限，怕踩雷",
                    "化妆手法生疏，怕卡粉",
                    "对包装颜值非常敏感",
                ],
                "preferred_channels": ["小红书", "抖音", "朋友圈"],
                "recommended_campaign_angle": "百元平价奶油肌 + 学生党开箱视频",
                "why_matters": "小众但 ROI 最高 (+19.55)，用户复购意愿强；学生群体是未来 5-10 年消费主力，提前卡位 LTV 价值大",
            },
            {
                "persona_id": f"P{cid:02d}",
                "nickname": "精致妈妈Amy",
                "age_range": "32-40",
                "occupation": "全职妈妈 / 自由职业",
                "core_need": "出门送娃、聚会、上班一妆多用的自然底妆",
                "pain_points": [
                    "没时间补妆，需要长时间持妆",
                    "既要显白又不能假白",
                    "包装不能太幼稚",
                ],
                "preferred_channels": ["微博", "朋友圈"],
                "recommended_campaign_angle": "一妆多用场景剧 + 妈妈群口碑裂变",
                "why_matters": "人数最少 (11.0%) 但满意度最低 (★1.23)，是流失重灾区；优先修复物流 / 客服可挽回这批高客单用户",
            },
        ]
        base = persona_templates[(cid - 1) % len(persona_templates)]
        persona = dict(base)
        persona["sample_message"] = self._compose_sample_message(persona)
        return persona

    def _compose_sample_message(self, persona: Dict[str, Any]) -> str:
        nick = persona["nickname"]
        need = persona["core_need"]
        rng = random.Random(hash(nick) & 0xFFFFFFFF)
        templates = [
            f"姐妹们，{nick}亲测：{need}！30 秒奶油肌真的不是梦～",
            f"今天被同事追问链接的{nick}：{need}，花西子空气蜜粉 yyds！",
            f"{nick}的小心机：{need}，这款国货真的可以闭眼入。",
        ]
        return rng.choice(templates)

    def _compose_campaign(
        self,
        idx: int,
        channel: str,
        persona: Dict[str, Any],
        objective: str,
        highlights: str,
    ) -> Dict[str, Any]:
        rng = random.Random(idx + hash(channel + persona["nickname"]) & 0xFFFFFFFF)
        style_tip = self.CHANNEL_STYLE_TIPS.get(channel, "")
        headline_pool = [
            f"花西子空气蜜粉｜{persona['nickname']}的奶油肌速成指南",
            f"30 秒打造 {persona['age_range']} 通勤妆容的秘密",
            f"持妆 8 小时不暗沉？{persona['nickname']}实测告诉你",
            f"被夸爆的国货底妆｜{persona['core_need']}",
        ]
        body_pool = [
            (
                f"针对{persona['core_need']}，{persona['nickname']}实测：粉质细腻、上脸服帖，"
                f"全天不拔干。{highlights or '空气蜜粉轻盈贴妆'}。"
            ),
            (
                f"场景：早八通勤 / 约会 / 答辩都适用。"
                f"{persona['nickname']}用了 {persona['age_range']} 段位的实测真心推荐。"
            ),
        ]
        variant = {
            "variant_id": f"V{idx + 1:02d}",
            "channel": channel,
            "headline": rng.choice(headline_pool),
            "body": rng.choice(body_pool),
            "hashtags": self.CHANNEL_HASHTAGS.get(channel, ["#花西子"]),
            "predicted_ctr": round(0.04 + rng.random() * 0.05, 3),
            "rationale": (
                f"匹配 {persona['nickname']}（{persona['core_need']}）的核心诉求；"
                f"渠道 = {channel}，调性 = {style_tip}"
            ),
        }
        return variant
