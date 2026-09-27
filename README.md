# ConsumerInsight-AI

> *A Hybrid Framework Combining LLM and Marketing Analytics for Automated Consumer Insights and Campaign Generation.*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)
[![Pipeline](https://img.shields.io/badge/pipeline-end--to--end-success)](#quickstart)
[![Reproducible](https://img.shields.io/badge/reproducible-100%25-brightgreen)](#data-provenance)

---

## 📊 项目一览（Project at a Glance）

| 维度 | 数量 / 结果 |
|---|---|
| 处理评论数 | **600 条**（多平台合成） |
| 自动识别细分群 | **4 个**（最大占 41.3%） |
| 消费者 Persona | **4 张画像**（含 why_matters 战略说明） |
| 核心话题 | **5 类**（包装 / 肤感 / 敏感肌 / 色号 / 物流） |
| 自动生成营销文案 | **12 条**（每个画像 × 3 渠道变体） |
| 预测 ROI 峰值 | **+19.55 倍**（最高细分群） |
| 漏斗最大流失点 | **Repurchase 阶段（38% 留存）** |
| 可视化图表 | **7 张**（`outputs/figures/`） |
| Markdown 报告 | **1 份**（`outputs/reports/pipeline_report.md`） |

> 跑通时间：约 15-30 秒（CPU，无 GPU 依赖）。详见 [`docs/TECHNICAL_REPORT.md`](docs/TECHNICAL_REPORT.md)。

---

## 🗂️ Data Provenance（数据来源声明）

> **本仓库的所有数据均为合成数据（Synthetic Data）**，目的是让 pipeline 在任何环境下 **100% 可复现**，无需任何 API key、数据合规审批或外部爬虫。

| 数据层 | 真实度 | 说明 |
|---|---|---|
| `data/raw/sample_reviews.csv`（50 条种子） | 手写 | 按花西子真实风格手写的种子评论，覆盖 4 类细分群、3 个平台 |
| `src/data_loader.py` 内的 `generate_synthetic_reviews()` | 自动合成 | 由 50 条种子 + 模板 + 关键词替换扩展到 600 条 |
| Pipeline 输出 | 派生 | 全部基于上述 600 条合成评论计算 |

**如何换成你的真实数据：**

1. 把你的真实评论写入 `data/raw/sample_reviews.csv`
2. 字段保持一致：`review_id, platform, rating, text, age_range, gender, week` 等
3. 重新跑 `python scripts/run_pipeline.py` — 所有图表、报告、文案自动基于新数据刷新

**为什么用合成数据：**
- ✅ 零成本，零 API key，零合规风险
- ✅ 任何 clone 仓库的人都能复现
- ✅ 焦点在 **方法论 + pipeline 工程**，而不是数据本身
- ✅ 与真实数据接口完全一致（plug-in 设计）

> 招生官可以这样验证：删掉 `data/raw/sample_reviews.csv`，重新跑 pipeline，会得到结构完全相同但内容不同的输出——证明 **代码独立于数据**。

---

## 项目定位

**ConsumerInsight-AI** 是一个端到端的「消费者洞察 + 营销内容生成」框架，
把**大语言模型 (LLM)** 与**经典营销分析方法**（多维度情感分析、TF-IDF
主题建模、KMeans 受众细分、软漏斗、Ridge 回归 ROI 估计）整合到一条
可一键运行的 pipeline 里。

它的核心问题是：

> *如何从海量社交媒体评论中，**自动**提炼出可指导营销决策的消费者洞察，
> 并针对不同细分人群**自动**生成高质量的营销文案？*

它是为申请**澳门大学（UM）数据分析师硕士——人工智能方向与市场营销分析方向**
所设计的**跨方向能力证明项目**。

## 项目亮点

- **跨方向**：同一个项目同时体现 **AI 工程能力** 与 **Marketing Analytics 落地能力**。
- **可复现**：默认使用**离线 Mock LLM**，零 API 成本即可跑通完整 pipeline。
- **可升级**：通过环境变量一键切换到 OpenAI / 智谱 GLM / DeepSeek 等真实模型。
- **可交互**：内置 Streamlit Dashboard，招生官可以直接点开体验。
- **可解释**：每一段分析都附带可视化图表 + Markdown 报告。

## 目录结构

```
ConsumerInsight-AI/
├── app/                       # Streamlit Web Demo
├── data/
│   ├── raw/                   # 用户可放入自己的原始评论 CSV
│   └── processed/             # pipeline 输出的清洗后数据
├── docs/
│   ├── TECHNICAL_REPORT.md    # 学术风格技术报告
│   ├── APPLICATION_MATERIALS.md  # 申请素材包（PS 写作模板）
│   ├── COURSE_MAPPING.md      # 项目能力 ↔ 澳大课程对应表
│   └── ARCHITECTURE.md        # 系统架构与数据流图
├── outputs/
│   ├── figures/               # 可视化图表
│   └── reports/               # Markdown 报告
├── scripts/
│   ├── run_pipeline.py        # 命令行入口
│   └── run_all.py             # 一键运行（虚拟环境 + 依赖安装）
├── src/
│   ├── ai_analysis/           # 情感、主题、Persona、趋势
│   ├── llm/                   # 可插拔 LLM 客户端
│   ├── marketing_analytics/   # 细分、ROI、漏斗、文案
│   ├── visualization/         # matplotlib 图表
│   ├── pipeline.py            # 主流程编排
│   ├── data_loader.py         # 数据加载 / 合成
│   └── config.py              # 全局配置
└── tests/                     # 基础单元测试
```

## 快速开始（Quickstart）

> 适合**零代码经验**的同学。Windows / macOS / Linux 都可。

### 1. 安装 Python（仅一次）

推荐 Python 3.10 或更高版本。从 [python.org](https://www.python.org/downloads/) 下载安装即可。

### 2. 一键运行

```bash
cd ConsumerInsight-AI
python scripts/run_all.py
```

脚本会**自动**：

1. 检查/创建虚拟环境；
2. 安装 `requirements.txt` 中的依赖；
3. 生成 600 条贴近真实业务的示例评论；
4. 跑通完整 pipeline，输出 `outputs/reports/pipeline_report.md` 与 7 张图表；
5. 告诉你下一步怎么启动 Streamlit Demo。

### 3. 启动可视化 Demo

```bash
streamlit run app/streamlit_app.py
```

浏览器打开 `http://localhost:8501` 即可与所有结果交互。

### 4. （可选）用真实 LLM API

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

## 方法概览

```
┌──────────────────────────────────────────────────────────────────┐
│                          评论数据（CSV / 合成）                    │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. 多维度情感分析 (LLM JSON) ─ 6 个维度：质量/性价比/包装/肤感/  │
│                                  持久/服务                        │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. 主题建模 (LLM + TF-IDF 交叉验证) ─ 5 个核心话题 + 代表关键词   │
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
│    5. 趋势检测 (周度聚合 + 线性回归斜率)                         │
│    6. 软漏斗 (认知→兴趣→试用→满意→复购)                          │
│    7. ROI 预估 (Ridge 回归 on 软转化代理信号)                    │
│    8. 营销文案生成 (LLM, 多渠道, 多版本)                         │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
        outputs/figures/*.png + outputs/reports/pipeline_report.md
```

## 申请澳大数据分析硕士的相关材料

- 📄 **[`docs/TECHNICAL_REPORT.md`](docs/TECHNICAL_REPORT.md)** — 学术风格的技术报告，可放进作品集附录。
- 📄 **[`docs/APPLICATION_MATERIALS.md`](docs/APPLICATION_MATERIALS.md)** — PS 写作模板、关键词、与澳大方向的对应表。
- 📄 **[`docs/COURSE_MAPPING.md`](docs/COURSE_MAPPING.md)** — 项目能力 ↔ 澳大课程对应表。
- 📄 **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** — 系统架构图与数据流说明。

## License

MIT — see [`LICENSE`](LICENSE).

## 致谢

本项目以教育/申请展示为目的。示例数据为程序化生成，模拟了真实业务场景的
语言分布与情感极性，不涉及任何真实用户隐私。
