# ConsumerInsight-AI — Pipeline Report

**品牌**：花西子 Florasis  
**行业**：美妆 (Beauty / Cosmetics)  
**平台**：小红书, 微博, 天猫  
**评论数**：1500  
**随机种子**：42  

> **重要声明：本报告所有数字均来自程序化合成的 review 数据（synthetic data），不构成任何真实业务结论。ROI 与模拟点击率均为示意性指标。**

## 1. 多维度情感概览

![情感概览](outputs/figures/01_sentiment_by_dimension.png)

### 维度均值表

| dimension          |   avg_score |
|:-------------------|------------:|
| Product Quality    |   0.211662  |
| Value for Money    |   0.103153  |
| Packaging Design   |   0.168543  |
| Skin Feel          |   0.118231  |
| Long Wear          |   0.0807667 |
| Service Experience |   0.0307913 |

## 2. 受众细分

![细分占比](outputs/figures/03_segment_share.png)

### 细分群画像表

|   segment_id |   volume |   avg_rating |    天猫 |   小红书 |    微博 |    抖音 |   朋友圈 |   18-23 |   24-30 |   31-40 |   40+ |
|-------------:|---------:|-------------:|------:|------:|------:|------:|------:|--------:|--------:|--------:|------:|
|            0 |      618 |      4.78641 | 0.278 | 0.249 | 0.388 | 0     | 0.084 |   0     |   0.362 |   0.453 | 0.184 |
|            1 |      456 |      3.1557  | 0.213 | 0.463 | 0.239 | 0.044 | 0.042 |   0.193 |   0.342 |   0.362 | 0.103 |
|            2 |      248 |      4.68548 | 0.347 | 0.48  | 0     | 0.173 | 0     |   1     |   0     |   0     | 0     |
|            3 |      178 |      1.26404 | 0.242 | 0.449 | 0.247 | 0.045 | 0.017 |   0.23  |   0.337 |   0.343 | 0.09  |

## 3. 核心话题

![话题占比](outputs/figures/04_topic_share.png)

| topic_id            | topic_label_cn   | description           | representative_keywords         |   share_estimate |
|:--------------------|:-----------------|:----------------------|:--------------------------------|-----------------:|
| skin_feel_long_wear | 上脸肤感与持久度         | 用户反复提及上脸服帖度与全天持妆效果    | ['服帖', '持久', '持妆', '不拔干', '细腻'] |            0.333 |
| packaging_design    | 包装设计             | 消费者高度关注产品的视觉设计与国风文化表达 | ['包装', '颜值', '设计', '好看', '国风']  |            0.222 |
| skin_sensitivity    | 敏感肌与刺激           | 敏感肌人群对成分与刺激性的担忧       | ['过敏', '刺激', '敏感肌', '爆痘', '闷痘'] |            0.148 |
| logistics_service   | 物流与服务            | 对快递时效、客服响应、赠品体验的反馈    | ['快递', '物流', '客服', '售后', '包装']  |            0.111 |
| color_shade         | 色号与妆效            | 对色号匹配度、不同肤色妆效差异的关注    | ['色号', '显白', '自然', '氧化', '暗沉']  |            0.111 |
| value_for_money     | 性价比              | 对定价、促销和性价比高度敏感        | ['平价', '超值', '划算', '性价比', '贵']  |            0.074 |

## 4. 消费者 Persona

| persona_id   | nickname   | age_range   | occupation   | core_need               | recommended_campaign_angle   | why_matters                              |
|:-------------|:-----------|:------------|:-------------|:------------------------|:-----------------------------|:-----------------------------------------|
| P01          | 通勤奶油肌Lisa  | 25-30       | 互联网公司市场运营    | 快速打造持久自然的奶油肌通勤底妆        | 30 秒奶油肌挑战 + 国风限定礼盒           | 规模较大的通勤主力人群，客单价提升与社交分享潜力兼备，适合作为重点沟通对象    |
| P02          | 成分党小美      | 28-35       | 美妆博主 / 内容创作者 | 找到成分安全、性价比高、妆效在线的国货底妆   | 成分透明化对比测评 + 敏感肌打卡挑战          | 对成分与安全性要求高的口碑型人群，社交传播力强，适合用测评内容撬动 UGC 传播 |
| P03          | 学生党阿月      | 18-23       | 在校大学生        | 百元内打造约会 / 答辩 / 面试的伪素颜底妆 | 百元平价奶油肌 + 学生党开箱视频            | 预算敏感但复购意愿强的年轻人群，是品牌未来的增量市场与 LTV 基本盘      |
| P04          | 精致妈妈Amy    | 32-40       | 全职妈妈 / 自由职业  | 出门送娃、聚会、上班一妆多用的自然底妆     | 一妆多用场景剧 + 妈妈群口碑裂变            | 对物流与售后体验敏感的高客单人群，服务体验是挽回与转化的关键抓手         |

## 5. 趋势与漏斗

![趋势](outputs/figures/05_weekly_trend.png)

![漏斗](outputs/figures/06_funnel.png)

> 漏斗中转化率最低的阶段是 05_Repurchase (40.0%). 建议优先在该阶段加强内容/促销/客服干预。

> Soft funnel inferred from review text, NOT real behavioural conversion data (no impressions / clicks / orders). Treat as directional only.

## 6. 示意性 ROI 指数 (Illustrative ROI Index)

![ROI](outputs/figures/07_roi_by_segment.png)

|   cluster_id |   volume |   avg_sentiment |   avg_rating |   predicted_soft_conversion |   expected_cost |   expected_revenue |   expected_roi |   illustrative_roi_index |
|-------------:|---------:|----------------:|-------------:|----------------------------:|----------------:|-------------------:|---------------:|-------------------------:|
|            0 |      618 |        0.967231 |      4.78641 |                    0.867522 |            3090 |           27255.4  |          7.821 |                    7.821 |
|            1 |      456 |        0.25309  |      3.1557  |                    0.636451 |            2280 |            7466.59 |          2.275 |                    2.275 |
|            2 |      248 |        0.995968 |      4.68548 |                    0.870356 |            1240 |           11021.8  |          7.889 |                    7.889 |
|            3 |      178 |       -0.965292 |      1.26404 |                    0.337572 |             890 |               0    |         -1     |                   -1     |

> Illustrative ROI index — synthetic data only. Computed from sentiment-driven soft_conversion signals with ARPU=¥120 and CAC=¥5 (see ROIConfig in src/config.py). K-fold CV R²/MAE on per-review ROI proxy report how well the four features predict per-review ROI; this is NOT a real causal estimate of marketing spend return.

## 7. 营销文案候选 (simulated_ctr)

| persona_nickname   | channel   | headline                       |   simulated_ctr |
|:-------------------|:----------|:-------------------------------|----------------:|
| 通勤奶油肌Lisa          | 小红书       | 持妆 8 小时不暗沉？通勤奶油肌Lisa实测告诉你      |           0.044 |
| 通勤奶油肌Lisa          | 抖音        | 持妆 8 小时不暗沉？通勤奶油肌Lisa实测告诉你      |           0.073 |
| 通勤奶油肌Lisa          | 小红书       | 花西子空气蜜粉｜通勤奶油肌Lisa的奶油肌速成指南      |           0.057 |
| 成分党小美              | 小红书       | 被夸爆的国货底妆｜找到成分安全、性价比高、妆效在线的国货底妆 |           0.07  |
| 成分党小美              | 微博        | 30 秒打造 28-35 通勤妆容的秘密           |           0.049 |
| 成分党小美              | 小红书       | 30 秒打造 28-35 通勤妆容的秘密           |           0.061 |
| 学生党阿月              | 小红书       | 30 秒打造 18-23 通勤妆容的秘密           |           0.043 |
| 学生党阿月              | 抖音        | 花西子空气蜜粉｜学生党阿月的奶油肌速成指南          |           0.056 |
| 学生党阿月              | 朋友圈       | 花西子空气蜜粉｜学生党阿月的奶油肌速成指南          |           0.059 |
| 精致妈妈Amy            | 微博        | 30 秒打造 32-40 通勤妆容的秘密           |           0.086 |
| 精致妈妈Amy            | 朋友圈       | 花西子空气蜜粉｜精致妈妈Amy的奶油肌速成指南        |           0.085 |
| 精致妈妈Amy            | 微博        | 被夸爆的国货底妆｜出门送娃、聚会、上班一妆多用的自然底妆   |           0.078 |

> `simulated_ctr` 字段说明：基于 [0.04, 0.09) 区间均匀随机采样，**不是**真实点击率预测，仅作渠道预算相对权重的输入。详见 `src/llm/mock_client.py::MockLLMClient._compose_campaign` 与 `SIM_CTR_LOW/HIGH`。

## 8. 评估指标 (Honest Evaluation)

> 全部数字来自本次 pipeline 运行（RANDOM_SEED=42）的真实输出。**不做任何手动调参或挑选 seed**。

### 8.1 聚类质量

| 指标 | 值 |
|---|---|
| Silhouette score (range [-1, +1]) | +0.1537 |
| Adjusted Rand Index vs synthetic user_segment | +0.1767 |
| Normalized Mutual Information vs synthetic user_segment | +0.2662 |
| N samples / N predicted clusters / N true labels | 1500 / 4 / 4 |

> Silhouette measures cluster separation on the feature space (higher = better separated, range [-1, +1]). ARI / NMI compare predicted clusters with the synthetic 'user_segment' label used during data generation; this is a circular check — high scores mean 'the clusterer rediscovered the synthetic segment structure', NOT 'the clusterer found real consumer segments in production data'.

### 8.2 主题一致性 (LLM vs TF-IDF)

| 指标 | 值 |
|---|---|
| TF-IDF 关键词中被 LLM 提及的比例 (overlap_ratio) | 0.200 |
| Jaccard | 0.073 |
| LLM 关键词总数 / TF-IDF 关键词总数 / 重合数 | 29 / 15 / 3 |

> Overlap is computed by **set intersection** between the LLM's word-level keywords (e.g. ['包装', '设计', '好看']) and the TF-IDF word-level vocabulary (jieba-segmented) of the same corpus. On Chinese, even a perfect semantic topic will often show only partial overlap here because the LLM and jieba segment the same text slightly differently. Both metrics are heuristic — even perfect agreement does NOT prove the LLM extracted the right topics. It only shows the LLM did not contradict the most frequent surface words.

### 8.3 情感分 vs 评分 相关性

| 指标 | 值 |
|---|---|
| Pearson r (p-value) | +0.8269 (p=0.00e+00) |
| Spearman ρ (p-value) | +0.7689 (p=2.71e-293) |
| N | 1500 |

> Pearson + Spearman between LLM-derived overall sentiment (range -1 to +1) and the user-given 1-5 star rating. On synthetic data both are derived from the same polarity lexicon, so the correlation is high by construction. Treat this as a sanity check (does the LLM agree with rating?), NOT as evidence of sentiment accuracy on real reviews.

### 8.4 ROI 回归 K-fold CV

| 指标 | 值 |
|---|---|
| K-fold CV R² (per-review ROI proxy) | +0.9807 |
| K-fold CV MAE | 0.3058 |
| Folds / samples | 5 / 1500 |

Coefficients (mean across folds):

| feature           |   cv_coefficient | cv_r2   | cv_mae   | cv_folds   |
|:------------------|-----------------:|:--------|:---------|:-----------|
| overall           |           3.2279 | 0.9807  | 0.3058   | 5          |
| high_rating       |           2.8077 | —       | —        | —          |
| long_text         |           0.8848 | —       | —        | —          |
| repurchase_intent |           0.6743 | —       | —        | —          |

> Ridge K-fold CV on per-review ROI proxy. R² near 1 means the four proxy features can predict per-review ROI almost perfectly — expected because the proxy itself is a deterministic function of those features. The CV is still reported because it (a) confirms no numerical pathology in the proxy definition and (b) exposes the coefficient signs/magnitudes for the reviewer to sanity-check.

### 8.5 多 seed 稳定性

完整多 seed 稳定性报告见 `outputs/reports/stability_report.md`（由 `python scripts/run_stability_eval.py` 生成，10 seeds）。**本节不重复展开**。

---

*本报告由程序自动生成；任何刻意的「挑选数字」或「手工修饰」都会让这份项目失去作品集价值。*
