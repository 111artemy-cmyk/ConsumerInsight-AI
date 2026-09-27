# 申请素材包 — ConsumerInsight-AI

> 配套申请澳门大学（UM）数据分析师硕士 **AI 方向** 与 **市场营销分析方向** 的素材包。
> 你可以**直接复制**其中的句子/段落作为 Personal Statement / CV 的素材。

---

## 0. 一页式项目摘要（适合放在简历里）

> **ConsumerInsight-AI** · GitHub: <你的 GitHub 仓库 URL>
>
> 一个端到端框架，从社交媒体评论中**自动**提炼消费者洞察并生成数据驱动的营销内容。
> 技术栈：Python · scikit-learn · TF-IDF + KMeans · Ridge Regression ·
> LLM (OpenAI 兼容 + Mock 后端) · Streamlit · matplotlib。
>
> - **6 维度情感分析**：把单条评论拆解为产品质量 / 性价比 / 包装 / 肤感 / 持久 / 服务 6 个可解释分数。
> - **Persona 合成**：用聚类 + LLM 自动生成可执行的消费者画像卡片。
> - **多渠道文案生成**：每 Persona × 多渠道 × 多版本，附预测 CTR 与预算分配。
> - **完整 pipeline 一键跑通**：600 条评论 → 4 个 Persona → 7 张图表 → 1 份 Markdown 报告。
> - 完整代码 + 技术报告 + Streamlit Demo，零 API 成本可复现。

---

## 1. 项目亮点 Bullet Points（直接放进 CV 的 Projects 区块）

> - Designed and implemented a hybrid LLM + Marketing Analytics pipeline
>   that converts raw social-commerce reviews into six-aspect sentiment
>   scores, four consumer personas, funnel diagnostics and per-segment
>   ROI estimates, demonstrating both AI engineering and business
>   analytics capability.
> - Built a **pluggable LLM backend** (Mock + OpenAI-compatible) so the
>   entire pipeline runs offline without paid APIs, with a one-line
>   environment switch to use OpenAI / 智谱 GLM / DeepSeek in
>   production.
> - Combined **TF-IDF topic modelling** with **LLM topic extraction**
>   to identify five core discussion themes (包装设计, 上脸肤感与持久度,
>   性价比, 色号与妆效, 敏感肌) and quantify their share of voice.
> - Trained a **Ridge regression** on a soft-conversion proxy (情感 +
>   评分 + 文本长度 + 复购意愿) to produce per-segment ROI estimates
>   with interpretable coefficients.
> - Authored a **Streamlit dashboard** that exposes every artefact
>   interactively, including multi-channel campaign copy with
>   predicted CTRs and budget allocation.

---

## 2. CV 中英文关键词（中英混排方便你直接选用）

**AI 方向关键词**
- Large Language Model (LLM) · Prompt Engineering · LLM JSON Output
- Multi-aspect Sentiment Analysis · Topic Modeling · TF-IDF · KMeans
- Scikit-learn · Ridge Regression · Pandas · NumPy · Streamlit
- Reproducible Pipeline · Pluggable Backend · Offline-first Design

**Marketing Analytics 方向关键词**
- Consumer Insights · Audience Segmentation · Persona Synthesis
- Conversion Funnel · Soft Conversion · ROI Estimation · Budget Allocation
- Social Listening · Social Commerce (小红书/微博/天猫) · Beauty Industry
- A/B Testing · Uplift Modeling (future) · Customer Journey

**跨学科关键词**
- Mixed Methods · Qualitative Coding · Survey Design · SPSS
- Sociology of Consumption · Gender & Consumer Behaviour

---

## 3. Personal Statement 写作模板

> 以下两段是**可以直接拿来改**的模板。**不要照抄**——务必替换成你自己的真实经历和动机。

### 3.1 申请 AI 方向的 PS 段落（强调技术深度）

> During the past year, I designed and built **ConsumerInsight-AI**, an
> end-to-end pipeline that couples large language models with classical
> machine learning to extract consumer insights from Chinese
> social-commerce reviews. My role spanned the full stack: data
> generation, sentiment modelling, topic extraction, persona synthesis,
> and an interactive Streamlit dashboard.
>
> Technically, I implemented a **pluggable LLM backend** that runs
> deterministically without paid APIs, and a **multi-aspect sentiment
> module** that prompts the LLM to return JSON scores on six
> product-experience dimensions. To keep the system reproducible, I
> validated LLM-derived topics with classical TF-IDF keywords and used
> Ridge regression to estimate per-segment ROI from interpretable
> features. The result is a pipeline that produces *decision-grade*
> artefacts (personas, funnel diagnostics, multi-channel copy) rather
> than mere text summaries.
>
> This project convinced me that the most interesting research questions
> in modern AI sit at the intersection of language understanding and
> structured decision-making. I am particularly eager to deepen my
> expertise in **causal inference for marketing**, **LLM evaluation &
> alignment**, and **multi-modal consumer understanding** during the
> MSc programme at UM.

### 3.2 申请 Marketing Analytics 方向的 PS 段落（强调商业洞察）

> ConsumerInsight-AI is the project that brought my two academic
> interests together: **sociology of consumer behaviour** and **data
> driven marketing**. Growing up with a Chinese household that
> constantly debated product reviews on 小红书, I became fascinated by
> the gap between *what brands say* and *what consumers actually feel*.
> The MSc in Data Analytics at UM, with its Marketing Analytics
> specialisation, is the ideal place for me to formalise that interest.
>
> Technically, I built a pipeline that translates raw reviews into the
> artefacts marketers actually use: a **six-aspect sentiment model**
> that surfaces the precise dimension on which a brand is winning or
> losing; **four LLM-synthesised personas** with explicit pain points
> and preferred channels; a **soft funnel** that pinpoints the
> conversion stage with the highest drop-off; a **per-segment ROI
> estimate** with interpretable coefficients; and **multi-channel
> campaign copy** with predicted CTRs and budget allocation.
>
> What excites me most about this work is the *interpretability*. Each
> output traces back to a specific set of consumer voices. As a
> sociologist, I am trained to honour the texture of qualitative data
> while still extracting generalisable patterns. I want to bring that
> sensibility into UM's Marketing Analytics track, where I hope to
> study **uplift modelling, A/B testing at scale, and consumer
> journey analytics**, and to work on projects that translate
> academic insight into measurable business lift.

### 3.3 共同的"动机段"（两个方向都可以用）

> I hold a Bachelor's degree in [你的专业] from [你的学校], where I
> studied [质性研究方法 / 社会统计学 / SPSS 软件应用] in depth. Those
> courses taught me to listen carefully to *what people say* before
> drawing quantitative conclusions — a habit I carried into my first
> encounter with social-media data. When I scraped my first batch of
> 小红书 reviews, I was struck by how much nuance was hiding behind
> simple star ratings. That moment led directly to ConsumerInsight-AI.

---

## 4. 与澳大课程对应表（详见 `COURSE_MAPPING.md`）

简版：

| 项目模块 | 对应澳大课程 |
|---|---|
| 多维度情感分析 | DAAN 522 — Text & Web Analytics / 自然语言处理 |
| 受众细分 + 主题建模 | DAAN 605 — Statistical Methods in Business / 多元统计 |
| Persona + 文案生成 | DAAN 730 — Generative AI for Business |
| 漏斗 + ROI | DAAN 615 — Marketing Analytics |
| Pipeline 工程化 | DAAN 511 — Data Engineering / 数据科学编程 |

---

## 5. 面试 / 文书审核可能被问到的问题（及答题要点）

### Q1: 你的项目里 LLM 输出不可靠怎么办？
**要点**：① 用结构化 Prompt（强制 JSON、列举字段、提供反例）；
② Mock LLM 提供 baseline 与对照；③ TF-IDF / 关键词做交叉验证；
④ 上线前用小批量人工评估（golden set）；⑤ 持续监控线上 LLM 输出分布漂移。

### Q2: 为什么用 KMeans 而不是更复杂的聚类？
**要点**：① 6 维小数据 + 可解释性优先；② KMeans 的质心可直接做"该人群代表"；
③ scikit-learn 内置、可复现；④ 后续可换 HDBSCAN / Spectral 做对比实验。

### Q3: ROI 模型用了 Ridge 而不是 XGBoost，为什么？
**要点**：① 解释性优先（系数直接对应业务假设）；
② 数据量小（600 条），树模型容易过拟合；
③ Ridge 在小样本线性可解释场景是工业经典；
④ 业务里"为什么这个细分 ROI 高"的回答权重大于"高 0.5%"。

### Q4: 你这个项目和单纯调 OpenAI API 比，区别在哪？
**要点**：① 不是调 API，是把 LLM 接进一个**端到端决策流水线**；
② 输出是 persona/漏斗/ROI/多渠道文案等**决策级产物**，不是摘要；
③ 工程上做了**可插拔**和**离线复现**，符合工业落地标准；
④ 强调 LLM 的"输出结构化"+"与传统 ML 协同"。

### Q5: 如果给你真实的订单数据，你会怎么升级 ROI 模型？
**要点**：① 用真实 soft conversion（点击/加购/成交）替换代理信号；
② 引入曝光/频次特征，做 **Marketing Mix Modeling (MMM)**；
③ 用 **uplift model / causal forest** 估计每个细分群的增量转化；
④ 用 Bayesian 方法给出 ROI 的置信区间；
⑤ 加 **budget allocation optimiser**（线性/整数规划）。

### Q6: 你的社会学背景在数据分析里有什么用？
**要点**：（这条非常加分，要讲好）
① 让我懂得**先看数据再下结论**，避免被模型牵着走；
② 让我对**消费者语言**更敏感，能写出让 LLM 稳定输出的 prompt；
③ 质性研究训练 → 我能在 Persona / 漏斗诊断时给出**有温度的解读**；
④ 文社科训练 → 让我能**把技术成果讲给非技术 stakeholder 听**。

---

## 6. 在 LinkedIn / 微博 / 小红书 发项目的文案模板

### 中文版
> 🎓 为申请澳大数据分析硕士做了一个跨方向项目：**ConsumerInsight-AI**。
>
> 它是一个端到端 pipeline：从社交媒体评论里
> ① 自动做 6 维度情感分析
> ② 提炼核心话题
> ③ 合成 4 个消费者画像
> ④ 跑受众细分 / 漏斗 / ROI
> ⑤ 生成多渠道营销文案
>
> 技术栈：Python · scikit-learn · TF-IDF · KMeans · Ridge · LLM (OpenAI + Mock) · Streamlit。
>
> 完整代码 + 技术报告 + 在线 Demo 👉 <GitHub URL>
> #数据分析 #消费者洞察 #营销分析 #LLM #留学申请 #澳门大学

### 英文版
> Thrilled to share **ConsumerInsight-AI**, an end-to-end framework I
> built for my UM MSc in Data Analytics application.
>
> It fuses LLMs with classical Marketing Analytics to turn raw
> social-commerce reviews into decision artefacts: multi-aspect
> sentiment, persona cards, funnel diagnostics, ROI per segment, and
> multi-channel campaign copy.
>
> Code + report + interactive demo 👉 <GitHub URL>
> #DataAnalytics #MarketingAnalytics #LLM #ConsumerInsights

---

## 7. 给导师套磁邮件可以引用的一句话

> *I built ConsumerInsight-AI to bridge classical Marketing Analytics
> with modern LLMs. The pipeline produces interpretable, decision-grade
> artefacts (personas, funnel drops, per-segment ROI, multi-channel
> copy) rather than mere text summaries. I would be honoured to
> extend this line of work under your supervision at UM, particularly
> in [causal inference for marketing / LLM evaluation / multi-modal
> consumer understanding].*

---

## 8. 文书自检清单（提交前必看）

- [ ] 项目名/角色/贡献描述清楚，避免"做了一个项目"这种空话
- [ ] 中英文关键术语用对，AI / Marketing 各出现至少 3 个关键词
- [ ] 至少提到一个具体的数字（评论数 / 维度数 / Persona 数 / CTR）
- [ ] 把社会学的背景讲成"加分项"而不是"无关项"
- [ ] 明确点出"我为什么要来 UM 这个方向"而不是泛泛而谈
- [ ] PS 不超过字数限制（UM 通常 500-1000 词）
- [ ] CV 中"Projects"区有 GitHub 链接和一行功能摘要
- [ ] 简历上"Skills"区分"AI 工具"和"Marketing 方法"两栏
