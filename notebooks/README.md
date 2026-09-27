# 补充 Notebook：ConsumerPulse-Basics

> 这是为**零代码经验**的同学准备的"能逐行讲清"的基础 Notebook。
> 它只用了 **pandas + matplotlib + 纯 Python**，不依赖 LLM 或任何高级 ML 库。

## 为什么需要这个 Notebook？

主项目 `ConsumerInsight-AI` 是一个**完整的工程化 pipeline**，
代码量较大、依赖较多。在申请文书里你很难逐行讲清楚。
这个补充 Notebook 故意做得**极简**，目标：

- ✅ 你能在面试中**逐行解释**每一步做了什么
- ✅ 你能在 PS 里写"我有 Python / pandas / 数据可视化基础"
- ✅ 招生官看 GitHub commit 历史时，能看到**真实进步曲线**

## 怎么跑？

### 方式 A：VSCode / PyCharm 的 Jupyter 模式（推荐）
1. 打开 VSCode，安装 Jupyter 扩展
2. 打开 `notebooks/01_consumer_basics.py`
3. 右上角选择 "Run Cell" 或 "Run All"
4. 每段 `# %%` 是一个 cell，可以单独跑

### 方式 B：终端直接跑
```bash
cd ConsumerInsight-AI
python notebooks/01_consumer_basics.py
```
会保存 3 张图到 `outputs/figures/`：
- `basics_01_platform_counts.png`
- `basics_02_rating_pie.png`
- `basics_03_my_sentiment.png`

并把带情感标签的数据保存到 `data/processed/basics_with_sentiment.csv`。

## 学完这个 Notebook 你能讲清的事

在面试 / 文书里你可以说：

> *我用 Python + pandas + matplotlib 自学了数据分析基础。
> 我读 CSV、做 value_counts、画柱状图/饼图、用纯 Python 写过简易情感分析器，
> 并把结果保存成 CSV 与 PNG。
> 在此基础上，我用 scikit-learn + LLM 构建了 ConsumerInsight-AI
> 项目（GitHub: <URL>）。*

## 这个 Notebook 与主项目的关系

```
ConsumerPulse-Basics (基础)         ConsumerInsight-AI (进阶)
   pandas / matplotlib              scikit-learn + LLM + Streamlit
        │                                  │
        └──────────── 同一份数据 ──────────┘
```

两个项目**数据互通**——主项目跑完后，本 Notebook 直接读
`data/processed/sample_processed.csv` 即可。这让你在 GitHub 上
展示的是**完整的能力递进**。
