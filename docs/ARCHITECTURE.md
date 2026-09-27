# System Architecture

> 数据流 + 模块依赖图。供技术审核 / 论文附录使用。

## 1. High-level 数据流

```
                   ┌──────────────────────┐
                   │  data/raw/*.csv      │
                   │  or synthetic data   │
                   └──────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   data_loader.py      │
                  │  (clean + validate)   │
                  └──────────┬────────────┘
                              │
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │                  AI Analysis Layer                    │
   │                                                        │
   │  sentiment.py ──► topic_modeling.py ──► persona_gen    │
   │       │                  │                  │          │
   │       └──────► trend_detector.py ◄─────────┘          │
   └────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │              Marketing Analytics Layer                │
   │                                                        │
   │  segmentation.py ──► funnel_analyzer.py ──► roi_pred  │
   │       │                                              │
   │       └──────► campaign_generator.py                 │
   └────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │             Visualisation & Reporting                  │
   │                                                        │
   │   charts.py (matplotlib)  +  pipeline_report.md       │
   │                  +  Streamlit app                      │
   └────────────────────────────────────────────────────────┘
```

## 2. 模块依赖（Python import 图）

```
pipeline.py
  ├── data_loader.py
  ├── llm/factory.py
  │     ├── llm/base.py
  │     ├── llm/mock_client.py
  │     └── llm/openai_client.py
  ├── ai_analysis/
  │     ├── sentiment.py
  │     ├── topic_modeling.py
  │     ├── persona_generator.py
  │     └── trend_detector.py
  ├── marketing_analytics/
  │     ├── segmentation.py
  │     ├── campaign_generator.py
  │     ├── roi_predictor.py
  │     └── funnel_analyzer.py
  └── visualization/charts.py
```

每个模块都是独立可测的（`tests/`）。

## 3. 可插拔 LLM 设计

```
            ┌──────────────────────┐
            │  BaseLLMClient       │  (abstract)
            └─────────┬────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   MockLLMClient  OpenAIClient   [Future: HF, Anthropic, Zhipu]
   (offline)      (paid API)
```

* **默认**：MockLLMClient（无需 API key，结果确定）
* **升级**：export `OPENAI_API_KEY` + `CI_LLM_BACKEND=openai`
* **兼容端点**：export `OPENAI_BASE_URL` 指向 智谱 / DeepSeek / Moonshot

## 4. 数据契约（每层之间的输入输出）

| 层 | 输入 | 输出 |
|---|---|---|
| 数据层 | (CSV / synthetic) | DataFrame (review_id, platform, user_id, product, rating, text, timestamp, user_age_band, user_segment) |
| 情感层 | DataFrame | DataFrame (+overall, product_quality, value_for_money, packaging_design, skin_feel, long_wear, service_experience) |
| 主题层 | DataFrame | topics (topic_id, topic_label_cn, description, representative_keywords, share_estimate) |
| Persona 层 | DataFrame | personas (persona_id, nickname, age_range, occupation, core_need, pain_points, preferred_channels, recommended_campaign_angle, sample_message) |
| 细分层 | DataFrame | assignments (review_id, cluster_id, ...) + segment_profile |
| 趋势层 | DataFrame | weekly_stats (week, volume, avg_sentiment, slope, direction) |
| 漏斗层 | DataFrame | stage_counts (stage, count, conversion_from_prev) |
| ROI 层 | DataFrame | segment_roi (cluster_id, predicted_soft_conversion, expected_revenue, expected_cost, expected_roi) |
| 文案层 | personas | creatives (variant_id, channel, headline, body, hashtags, predicted_ctr, rationale) |

## 5. 失败容忍策略

* LLM 返回非法 JSON → 自动 fallback 到 `_lax` 解析（去掉尾部逗号）
* 解析仍失败 → 返回 `overall=0`，各维度为 0，并记录 warning
* 数据缺失某列 → 抛 `ValueError` 提示具体缺失列名
* Streamlit 缓存 → `@st.cache_resource` 保证 pipeline 只跑一次
