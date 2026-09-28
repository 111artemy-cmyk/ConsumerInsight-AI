# ConsumerInsight-AI

> **一条端到端的 LLM + 营销分析 pipeline：把社交媒体评论变成细分人群画像、软漏斗诊断、示意性 ROI 指数、以及分人群营销文案。**

![示意性 ROI 指数（按细分群）](outputs/figures/07_roi_by_segment.png)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)
[![CI](https://img.shields.io/badge/CI-pending-lightgrey)](#-工程化--ci)
[![Pipeline](https://img.shields.io/badge/pipeline-end--to--end-success)](#-快速开始)
[![No API key](https://img.shields.io/badge/API%20key-not%20required-orange)](#-技术栈)

[English](README.md) · [项目简介](#-项目简介)

> **本仓库的所有数字均来自程序生成的合成评论（synthetic data）。** 没有真实用户数据、默认运行不需要任何 LLM API key、报告中没有任何数字应被理解为真实业务 KPI。Pipeline 的目的是展示方法论与工程实现，不是产出商业结论。详见 [Limitations](#-limitations诚实声明)。

---

<a id="project-at-a-glance"></a>

## 📊 项目一览（Project at a Glance）

下表所有数字都可复现：`git clone` 后跑 `python scripts/run_pipeline.py --n 1500 --backend mock`。"Single seed (42)" 列来自这条命令的产物，与 `outputs/reports/pipeline_report.md` 字段一一对应；"Multi-seed (10×1500)" 列来自 `python scripts/run_stability_eval.py --seeds 1,2,3,4,5,6,7,8,9,42 --n-reviews 1500`（约 21 秒），与 `outputs/reports/stability_report.md` 字段一一对应。

| 指标 | Single seed (42) | Multi-seed (10×1500) mean ± std | 来源 |
|---|---|---|---|
| 处理评论数 | **1500** | 1500 (固定) | `data/processed/sample_processed.csv` |
| 受众细分群 (KMeans) | **4** | 4 (固定) | `outputs/figures/03_segment_share.png` |
| 最大细分群占比 (%) | **41.6**（segment 2） | **35.78 ± 3.56**（区间 32.87–42.67） | `pipeline_report.md` §2 / `stability_report.md` |
| 消费者 Persona | **4** | 4 (固定) | `pipeline_report.md` §4 |
| 核心话题 | **5** | 5 (固定) | `pipeline_report.md` §3 |
| 营销文案候选 | **12**（3 渠道 × 4 persona） | 12 (固定) | `pipeline_report.md` §7 |
| **示意性 ROI 指数** 峰值 | **+7.901** | **7.867 ± 0.046**（区间 7.799–7.959） | `pipeline_report.md` §6 / `stability_report.md` |
| **示意性 ROI 指数** 峰值 segment | **0** | **0 (mode 5×)**，3:2×, 1:2×, 2:1× | `pipeline_report.md` §6 / `stability_report.md` |
| **软漏斗** 最差阶段留存率 | **0.409** | **0.401 ± 0.018**（区间 0.375–0.425） | `pipeline_report.md` §5 / `stability_report.md` |
| **软漏斗** 最差阶段 | **`05_Repurchase`** | **`05_Repurchase` (10/10 seeds)** | `pipeline_report.md` §5 / `stability_report.md` |
| **模拟点击率** 区间 | uniform `[0.04, 0.09)` | 同上（每个 seed 由确定性） | `pipeline_report.md` §7 |
| Silhouette score | **+0.1507** | (单 seed only) | `pipeline_report.md` §8.1 |
| ARI vs synthetic `user_segment` | **+0.0467** *(循环验证 — 见 Limitations)* | (单 seed only) | `pipeline_report.md` §8.1 |
| NMI vs synthetic `user_segment` | **+0.0664** *(循环验证)* | (单 seed only) | `pipeline_report.md` §8.1 |
| Pearson sentiment ↔ rating | **+0.8327** *(同源词典生成)* | (单 seed only) | `pipeline_report.md` §8.3 |
| Spearman sentiment ↔ rating | **+0.7820** | (单 seed only) | `pipeline_report.md` §8.3 |
| ROI CV R² (per-review proxy) | **+0.9793** *(proxy 是 4 特征的确定性函数)* | (单 seed only) | `pipeline_report.md` §8.4 |
| ROI CV MAE | **0.3180** | (单 seed only) | `pipeline_report.md` §8.4 |
| 可视化图表 | **7 张**（`outputs/figures/`） | — | `outputs/figures/*.png` |
| Markdown 报告 | `outputs/reports/pipeline_report.md` | — | §8 评估 + 7 个章节 |
| 稳定性报告 | `outputs/reports/stability_report.md` | — | 10 seeds × 1500 |

> "Single seed" 和 "Multi-seed" 是两次独立运行。两列数字均来自本机真实的 `python` 调用，并已 commit 到仓库作为证据（见 `outputs/reports/`）。端到端运行时间：**单 seed pipeline 约 5-10 秒**，**10-seed 稳定性报告约 21 秒**。注意 "largest segment id" 在单 seed（segment 2）和多 seed（mode 0）下不同——该指标对采样敏感，**不应**作为稳定业务 KPI。

---

<a id="limitations"></a>

## ⚠️ Limitations（诚实声明）

本项目对自己"不是什么"非常坦诚。读任何数字之前请先读这一节。

* **所有评论文本都是合成的。** 1500 条评论由 `src/data_loader.py::generate_synthetic_reviews()` 从 50 条手写种子模板扩展而来。没有真实用户、没有爬取的真实评论、没有第三方数据。Pipeline 输出描述的是这份**合成**语料的属性，不是别的。
* **默认 LLM 是基于规则的 Mock。** 复现本 README 中任何数字不需要 API key。Mock 客户端用一个小型词典 + 强化/否定修饰规则实现（见 `src/llm/mock_client.py`），它**不是**真实 LLM 的替代品，是一个确定性的离线基线。任何本仓库中以"the LLM..."开头的句子都指代"当前配置的 LLM"——默认是 Mock。
* **"ROI" 是 *示意性* ROI 指数。** 它由 `sigmoid(overall + 0.6·high_rating + 0.3·long_text + 0.2·repurchase_intent)` 与 `src/config.py::ROIConfig` 里的成本/收入假设共同计算（默认 ARPU=¥120、CAC=¥5、baseline gate=0.5）。它**不是**营销花费回报的测度，是一个教学工件，使 segment 聚合步骤有数字可输出。
* **"漏斗" 是 *软* 漏斗。** 5 个阶段（Awareness → Interest → Trial → Satisfaction → Repurchase）由 `src/funnel_analyzer.py` 中的关键词规则从评论文本推断。没有曝光、点击、订单。漏斗图与报告中都明确标注 `Soft funnel — inferred from review text + rating, not real behavioural conversion`。
* **聚类可能反映合成模板结构，而非真实人群。** KMeans 跑在 `TF-IDF(2,3 char-wb) + OneHot(platform, age_band) + rating` 之上。合成生成器本身按 `user_segment`（学生党/通勤族/成分党/精致妈妈）组织评论，所以预测聚类 vs `user_segment` 的 ARI / NMI 是**循环验证**——高分意味着"KMeans 还原了合成结构"，**不**意味着"KMeans 找到了真实消费者群体"。
* **"Simulated CTR" 是均匀随机采样。** 渠道级 `simulated_ctr` 从 `Uniform[0.04, 0.09)` 采样，由 `MockLLMClient._compose_campaign` 生成。它让渠道预算分配步骤有一个相对权重的输入，**不是**真实 CTR 预测。

这些限制同样在 `docs/TECHNICAL_REPORT.md` §6、每张图与每份报告中标注。

---

<a id="about-this-project"></a>

## 👋 关于本项目

作者 **Xintong Wang**（王欣桐），作品集项目，用于申请 **澳门大学 — 数据科学理学硕士**（AI track + Marketing Analytics track）。

作者是社会学背景，**在开始这个项目前没有 Python 或市场营销经验**。目标是亲手实现一个完整的消费者研究工作流（情感 → 细分 → 漏斗 → ROI → 文案），用一条可复现的 LLM 增强 pipeline，并把每一步都写得让非 CS 读者能看懂。

> **品牌名免责声明。** 合成评论以"花西子 Florasis"作为示例品牌调性，让生成的文本读起来像真实的中文美妆评论。**本项目与真实的花西子 / Florasis 品牌无任何关联、授权、合作或业务关系**——该名称仅作为风格占位符，所有输出均来自合成数据，不是对该品牌或其产品的任何声明。详见 `src/config.py::IndustryConfig` 上方的代码块（也是中文版本）。

---

<a id="screenshots"></a>

## 📸 Streamlit Demo（截图）

Pipeline 自带一个交互式 Streamlit dashboard，sidebar **10 个 section**，对应下方 10 张截图。所有截图都是 `streamlit run app/streamlit_app.py` 的真实截图，由 `python scripts/capture_streamlit_screenshots.py` 重新生成。

### 1. 项目概览 / Project overview

![Overview](docs/screenshots/01_overview.png)

### 2. 数据概览 / Data overview

![Data overview](docs/screenshots/02_data.png)

### 3. 多维度情感 / Multi-aspect sentiment

![Sentiment](docs/screenshots/03_sentiment.png)

### 4. 核心话题 / Core topics

![Topics](docs/screenshots/04_topics.png)

### 5. 消费者 Persona / Personas

![Personas](docs/screenshots/05_personas.png)

### 6. 受众细分 / Audience segmentation

![Segmentation](docs/screenshots/06_segmentation.png)

### 7. 趋势 & 漏斗 / Trends & funnel

![Funnel](docs/screenshots/07_funnel.png)

### 8. ROI 预估 / Illustrative ROI index

![ROI](docs/screenshots/08_roi.png)

### 9. 营销文案候选 / Marketing copy candidates

![Creatives](docs/screenshots/09_creatives.png)

### 10. 方法说明 / Methodology

![Methodology](docs/screenshots/10_methodology.png)

> 启动 demo：`streamlit run app/streamlit_app.py` → 浏览器打开 `http://localhost:8501`。

---

<a id="key-visualizations"></a>

## 🎨 关键可视化（pipeline 输出）

同一份数据除了驱动上面的 Streamlit dashboard，还会作为静态 PNG 输出到 `outputs/figures/`。README 在这里复用了**两张**给非交互式读者看核心图：

### 软漏斗 — Awareness → Repurchase

![Funnel](outputs/figures/06_funnel.png)

### 受众细分 — 4 个行为聚类

![Segmentation](outputs/figures/03_segment_share.png)

### 示意性 ROI 指数 — 按细分群

![ROI](outputs/figures/07_roi_by_segment.png)

> 全部 7 张图见 [`outputs/figures/`](outputs/figures/)。每张图都带数据来源行（`Source: synthetic reviews (n=…)`）+ 底部 insight 框（纯英文标签，无 emoji）。ROI 图标题为"Illustrative ROI Index (Synthetic — Illustrative Only)"，漏斗图标题为"Soft Funnel (Not Real Behavioural Conversion)"。Streamlit 截图与静态 PNG 内容重叠是有意为之——前者面向想**交互**的审稿人，后者面向只能读 README 的读者。

---

<a id="built-with"></a>

## 🛠️ 技术栈

| 类别 | 工具 |
|---|---|
| **核心语言** | Python 3.10+ |
| **数据处理** | pandas, numpy |
| **机器学习** | scikit-learn（KMeans · TF-IDF · Ridge 回归） |
| **LLM 接口** | 可插拔 — Mock（默认）/ OpenAI / 智谱 GLM / DeepSeek / Moonshot |
| **可视化** | matplotlib |
| **Web Demo** | Streamlit |
| **工程化** | pytest · pyproject.toml · GitHub Actions（见 [CI](#-工程化--ci)） |

---

<a id="data-provenance"></a>

## 🗂️ 数据来源声明（Data Provenance）

> **本仓库的所有数据均为合成数据（Synthetic Data）。** 目的是让 pipeline 在任何环境下 100% 可复现，零 API key、零合规审批、零爬取。

| 数据层 | 来源 | 说明 |
|---|---|---|
| `data/raw/sample_reviews.csv`（50 条种子） | 手写 | 用 Florasis 风格撰写——见上方免责声明；覆盖 4 类细分群、3 个平台 |
| `src/data_loader.py::generate_synthetic_reviews()` | 自动合成 | 由 50 条种子 + 模板 + 关键词替换扩展到 1500 条 |
| Pipeline 输出 | 派生 | 全部基于上述 1500 条合成评论计算 |

**如何换成你自己的真实数据：**

1. 把你的真实评论写入 `data/raw/sample_reviews.csv`
2. 字段保持一致：`review_id, platform, user_id, product, rating, text, timestamp, user_age_band, user_segment`
3. 重新跑 `python scripts/run_pipeline.py` —— 所有图表、报告、文案自动基于新数据刷新

**为什么用合成数据：**

- ✅ 零成本、零 API key、零合规风险
- ✅ 任何 clone 仓库的人都能 1:1 复现
- ✅ 焦点在 **方法论 + pipeline 工程**，而非数据本身
- ✅ 与真实数据接口完全一致（plug-in 设计）

> **验证方法**：删掉 `data/raw/sample_reviews.csv` 后重新跑 pipeline，会得到结构完全相同但内容不同的输出 —— 这证明**代码独立于数据**。

---

<a id="project-overview"></a>

## 📖 项目简介

**ConsumerInsight-AI** 是一个端到端的「消费者洞察 + 营销内容生成」框架，把**大语言模型 (LLM)** 与**经典营销分析方法**整合到一条可一键运行的 pipeline 里，覆盖：

> *如何从海量社交媒体评论中，**自动**提炼出可指导营销决策的消费者洞察，并针对不同细分人群**自动**生成高质量的营销文案？*

它体现：

- **跨方向** —— AI 工程能力（LLM 集成、prompt 设计、JSON 结构化输出）+ Marketing Analytics 落地能力（情感 / 漏斗 / ROI / 细分 / 文案）
- **可复现** —— 默认离线 Mock LLM
- **可升级** —— 一个环境变量切换到 OpenAI / 智谱 / DeepSeek
- **可交互** —— 内置 Streamlit Dashboard（10 个 section），用户可直接点开体验
- **可解释** —— 每一段分析都有可视化图表 + Markdown 报告 + insight 文本
- **诚实评估** —— silhouette / ARI / NMI、LLM↔TF-IDF 重合、情感↔评分相关、K-fold CV、多 seed 稳定性——所有数字来自真实运行

### What it does（8 步 + 1 评估层）

1. **多维度情感评分** — 6 个产品体验维度（`Product Quality`、`Value for Money`、`Packaging Design`、`Skin Feel`、`Long Wear`、`Service Experience`；见 [情感维度 vs. 主题](#情感维度-vs-主题)）
2. **主题提取** — 5 个主题，LLM + TF-IDF 交叉验证（`包装设计`、`上脸肤感与持久度`、`性价比`、`色号与妆效`、`敏感肌与刺激`、`物流与服务`；见 [情感维度 vs. 主题](#情感维度-vs-主题)）
3. **Persona 生成** — 4 张画像，KMeans + LLM
4. **受众细分** — KMeans on TF-IDF + 行为特征
5. **趋势检测** — 周度聚合 + 线性回归斜率
6. **软漏斗** — Awareness → Interest → Trial → Satisfaction → Repurchase（**从评论文本推断，不是真实行为转化**）
7. **示意性 ROI 指数** — Ridge 回归 on soft-conversion 信号（**合成成本/收入假设，不是真实业务 KPI**）
8. **营销文案生成** — LLM、多渠道、多版本，附 **simulated_ctr**（**[0.04, 0.09) 均匀采样，不是真实点击率预测**）
9. **评估层** (`src/evaluation.py`) — silhouette / ARI / NMI、LLM↔TF-IDF 关键词重合、sentiment↔rating 相关、K-fold CV on ROI、多 seed 稳定性（默认 10 seeds）

<a id="sentiment-dimensions-vs-topics"></a>

### 情感维度 vs. 主题

Pipeline 输出两种很容易混淆的不同概念产物：

| 情感维度（6 个，定义在 `src/config.py::SENTIMENT_DIMENSIONS`） | 核心主题（5 个，由 `TopicModeler` 输出） |
|---|---|
| `Product Quality` — 产品质量（粉质、服帖度、持妆力） | `包装设计` — 视觉设计与国风文化表达 |
| `Value for Money` — 性价比（价格、促销、赠品） | `上脸肤感与持久度` — 服帖度与全天持妆 |
| `Packaging Design` — 包装设计（颜值、国风、雕花） | `性价比` — 定价、促销、性价比敏感 |
| `Skin Feel` — 上脸肤感（服帖、拔干、刺激） | `色号与妆效` — 色号匹配、肤色妆效差异 |
| `Long Wear` — 持久度（脱妆、氧化、斑驳） | `敏感肌与刺激` — 敏感肌对成分与刺激性的担忧 |
| `Service Experience` — 服务体验（快递、客服、售后） | `物流与服务` — 快递时效、客服响应、赠品体验 |

情感维度给 **每条评论每个方面一个数值分数**（在 `[-1, +1]`）。主题给**每条评论一个标签**，指示它属于哪个对话主题。两者由不同 prompt（`PromptLibrary.SENTIMENT_*` vs `PromptLibrary.TOPIC_*`）计算得到，**应分开报告**。

---

<a id="repository-structure"></a>

## 📁 目录结构

```text
ConsumerInsight-AI/
├── app/                          # Streamlit web demo
│   └── streamlit_app.py
├── data/
│   ├── raw/                      # 用户可放入自己的原始评论 CSV
│   └── processed/                # pipeline 输出的清洗后数据（gitignored）
├── docs/                         # 文档
│   ├── TECHNICAL_REPORT.md       # 学术风格技术报告
│   ├── COURSE_MAPPING.md         # 项目能力 ↔ 课程方向对应表
│   ├── ARCHITECTURE.md           # 系统架构图与数据流
│   └── screenshots/              # 10 张 dashboard 截图（与 sidebar 1-10 一一对应）
├── notebooks/                    # 零 LLM 的可读 notebook
│   └── 01_consumer_basics.py
├── outputs/
│   ├── figures/                  # 7 张 matplotlib 图表（已 commit）
│   └── reports/                  # Markdown 报告（gitignored，重新生成）
├── scripts/
│   ├── run_pipeline.py                 # 入口
│   ├── run_all.py                      # 一键运行（虚拟环境 + 依赖安装）
│   ├── run_stability_eval.py           # 多 seed 稳定性评估
│   ├── generate_sample_data.py         # 单独生成示例数据
│   └── capture_streamlit_screenshots.py # 重新生成 README 截图
├── src/
│   ├── ai_analysis/              # 情感 / 主题 / Persona / 趋势
│   ├── llm/                      # 可插拔 LLM 客户端（base / mock / openai）
│   ├── marketing_analytics/      # 细分 / ROI / 漏斗 / 文案
│   ├── visualization/            # matplotlib 图表函数
│   ├── evaluation.py             # 诚实评估原语
│   ├── pipeline.py               # 主流程编排
│   ├── data_loader.py            # 数据加载 / 合成
│   └── config.py                 # 全局配置（含 ROIConfig）
└── tests/                        # 单元测试（pytest，27 个测试）
```

---

<a id="quickstart"></a>

## 🚀 快速开始（Quickstart）

> 设计支持Windows、macOS和Linux系统。

### 1. 安装 Python（仅一次）

推荐 Python 3.10 或更高版本。从 [python.org](https://www.python.org/downloads/) 下载安装即可。

### 2. 一键运行

```bash
git clone https://github.com/111artemy-cmyk/ConsumerInsight-AI.git
cd ConsumerInsight-AI
python scripts/run_all.py
```

脚本会**自动**：

1. 检查 / 创建虚拟环境
2. 安装 `requirements.txt` 中的依赖
3. 生成 1500 条贴近真实业务的示例评论
4. 跑通完整 pipeline，输出 `outputs/reports/pipeline_report.md` 与 7 张图表
5. 告诉你下一步怎么启动 Streamlit Demo

### 3. 启动可视化 Demo

```bash
streamlit run app/streamlit_app.py
```

浏览器打开 `http://localhost:8501` 即可与所有结果交互。

### 4. 跑多 seed 稳定性报告（可选，约 21 秒）

```bash
python scripts/run_stability_eval.py                # 10 seeds × 1500 评论
python scripts/run_stability_eval.py --n-seeds 5 --n-reviews 500
```

### 5. （可选）用真实 LLM API

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"   # 或国内兼容端点
$env:CI_LLM_BACKEND = "openai"
python scripts\run_pipeline.py
```

支持的兼容端点示例：

- 智谱 GLM：`https://open.bigmodel.cn/api/paas/v4`
- DeepSeek：`https://api.deepseek.com/v1`
- Moonshot：`https://api.moonshot.cn/v1`

---

<a id="deploy"></a>

## ☁️ 部署（Streamlit Community Cloud）

Streamlit dashboard 已具备部署条件。把你 fork 的仓库发到 Streamlit Community Cloud：

1. 在 GitHub 上 fork 本仓库。
2. 打开 [share.streamlit.io](https://share.streamlit.io/) → **New app** → 选你的 fork。
3. **Main file path**：`app/streamlit_app.py`
4. **Python version**：3.10 或 3.11（与 `.github/workflows/ci.yml` 一致）。
5. **Advanced settings → Requirements file**：`requirements.txt`（平台会自动识别）。
6. 点 **Deploy**。第一次启动会跑一次 pipeline，由 `@st.cache_resource` 缓存结果，之后访问瞬时返回。
7. （可选）在 fork 的 *Settings → Secrets* 里加 `OPENAI_API_KEY` / `OPENAI_BASE_URL`，以便用真实 LLM 而非 Mock 演示。

> README 没有声称 demo 当前已部署——见 [Limitations](#-limitations诚实声明) 关于诚实承诺的说明。上面提供的部署配方让审稿人能一键复现。

---

<a id="pipeline-overview"></a>

## 🔬 方法概览

```text
┌──────────────────────────────────────────────────────────────────┐
│                    评论数据（CSV / 合成）                          │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. 多维度情感分析 (LLM JSON) ─ 6 个维度                           │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. 主题建模 (LLM + TF-IDF 交叉验证) ─ 5 个核心话题                │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. Persona 生成 (KMeans + LLM) ─ 4 个细分群 + 画像卡片           │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. 受众细分 (KMeans on TF-IDF + 行为特征)                        │
│ 5. 趋势检测 (周度聚合 + 线性回归斜率)                            │
│ 6. 软漏斗 (认知 → 兴趣 → 试用 → 满意 → 复购)                     │
│ 7. 示意性 ROI 指数 (Ridge 回归 on 软转化代理信号)                 │
│ 8. 营销文案生成 (LLM · 多渠道 · 多版本 · simulated_ctr)           │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
   outputs/figures/*.png  +  outputs/reports/pipeline_report.md
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 9. 评估层 (src/evaluation.py)                                    │
│    silhouette / ARI / NMI · LLM↔TF-IDF 重合 · sentiment↔rating 相关│
│    · K-fold CV R²/MAE · 10-seed 稳定性                            │
└──────────────────────────────────────────────────────────────────┘
```

---

<a id="evaluation-zh"></a>

## 🧪 评估与诚实声明 (Honest Evaluation)

由于本项目的全部数字来自合成数据，pipeline 自带一个评估层（而非依赖外部 benchmark）。目标是让每个指标都能回溯到一次具体的运行，并在文档里暴露循环论证风险。

**5 类诚实评估指标**（详见 `src/evaluation.py` 与 `outputs/reports/pipeline_report.md` 的 §8）：

| # | 指标 | 真实含义 |
|---|---|---|
| 1 | Silhouette score | TF-IDF + 行为特征空间中聚类的分离度 |
| 1 | ARI / NMI vs 合成 `user_segment` | 聚类是否"还原"了合成阶段的 segment 结构（**循环验证**，高分不等于"聚类找到了有意义的真实消费者群体"） |
| 2 | LLM 关键词 vs TF-IDF 关键词重合率 | LLM 主题抽取是否覆盖了 TF-IDF 高频 n-gram |
| 3 | 情感分 vs 评分 Pearson / Spearman 相关 | LLM 情感分数是否与用户给的 1-5 星评分一致 |
| 4 | Per-review ROI K-fold CV R² / MAE | 4 个代理特征能否预测 per-review ROI proxy（R² 接近 1 **是预期的**——proxy 本身就是这 4 个特征的 deterministic 函数） |
| 5 | 多 seed 稳定性 | 在 **10 个不同 RANDOM_SEED**（默认）下，头部指标的 mean / std / min / max |

**多 seed 稳定性脚本**（与主 pipeline 解耦，保持主流程 5-10 秒速度）：

```bash
python scripts/run_stability_eval.py                # 10 seeds × 1500 评论（约 21 秒）
python scripts/run_stability_eval.py --n-seeds 5 --n-reviews 500
```

输出：`outputs/reports/stability_report.md`。

> **关于命名。** README 之前宣传过"约 +19-20 倍预测 ROI"——这个数字来自合成数据上各聚类 ROI 的最大值，没有真实业务意义。已重命名为 **示意性 ROI 指数（Illustrative ROI Index）**，计算公式集中在 `src/config.py::ROIConfig`（ARPU=¥120、CAC=¥5、baseline soft-conversion gate=0.5），便于读者替换为真实成本/收入假设。"Predicted CTR" 字段已重命名为 **Simulated CTR score** —— 它是 `[0.04, 0.09)` 区间的均匀采样，**绝不代表真实点击率**。"营销漏斗"图明确标注为 **软漏斗**（从评论文本推断，非真实行为转化）。

---

<a id="engineering-ci"></a>

## 🔧 工程化 & CI

* **`pyproject.toml`** — package 元数据 + setuptools 自动发现；源码可 `pip install -e .` 安装。
* **`tests/`** — 27 个 pytest 测试（5 segmentation + 6 funnel + 4 ROI + 3 campaign + 3 sentiment + 13 evaluation）。运行 `python -m pytest tests/ -q`。
* **`.github/workflows/ci.yml`** — Python 3.10 / 3.11 matrix CI：装包 → 跑测试 → 跑一次 smoke `run_pipeline.py`。（上面的徽章在远端仓库启用 workflow 后会变绿。）
* **`requirements.txt`** — 主要依赖固定到主/次版本号（`pandas>=2.0`、`numpy>=1.24`、`scikit-learn>=1.3`、`matplotlib>=3.7`、`streamlit>=1.28`、`openai>=1.0`、`jieba>=0.42`）。
* **可复现性** — `src/config.py` 里 `RANDOM_SEED = 42`；`MockLLMClient` 用 MD5 派生 stable seed（跨进程确定性）。

---

<a id="roadmap"></a>

## 🧭 Roadmap（可选扩展方向）

- [ ] 接入 RAG，让 Persona / 文案基于品牌知识库而非纯 prompt
- [ ] 把 Mock LLM 替换为本地 7B 模型（Llama / Qwen）
- [ ] A/B 模拟：with-AI vs without-AI 文案转化的对比实验
- [ ] 真实数据接入：品牌方授权 / 商业评论 API
- [ ] 通过 bootstrap 给 per-cluster KPI 加置信区间

---

## License

MIT —— see [`LICENSE`](LICENSE).

---

## 致谢

本项目以教育与开源展示为目的。示例数据为程序化合成，不涉及任何真实用户隐私。"花西子 Florasis" 名称仅作为风格占位符使用，完整声明见 `src/config.py::IndustryConfig` 顶部的代码块。