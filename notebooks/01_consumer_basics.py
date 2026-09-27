"""
================================================================================
 ConsumerPulse-Basics — 给「零代码经验」申请者的入门级 Python 数据分析
================================================================================

目标
----
让你**完全能讲清楚**自己写过的每一行代码，作为申请文书里"我有 Python
与数据分析基础"这一主张的硬证据。

这个 Notebook 故意只用了：
    - pandas  （数据处理）
    - matplotlib （画图）
    - 基础的 Python 语法（for / if / 列表推导）

不依赖：LLM、sklearn、深度学习。

怎么跑
----
方式 A（推荐）：VSCode / PyCharm 装好 Jupyter 扩展，直接打开本文件运行。
方式 B：在终端跑 `python notebooks/01_consumer_basics.py`，
         会把图表保存到 outputs/figures/，并把关键结果打印到屏幕。

学完这个 Notebook 你能说清楚的事
---------------------------------
- 怎么用 pandas 读 CSV、做基本统计；
- 怎么用 matplotlib 画柱状图、饼图、折线图；
- 怎么用纯 Python（for/if）写一个"简易情感分析器"；
- 怎么把分析结果保存成 CSV 与 PNG，让招生官看到完整产物。
================================================================================
"""

# %% [markdown]
# # 第 1 步：导入工具包
#
# 我们需要三个工具：
# - **pandas**：处理表格数据（类似 Excel，但用代码操作）
# - **matplotlib.pyplot**：画图
# - **pathlib.Path**：方便处理文件路径

import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 让 matplotlib 在没有显示器的服务器上也能保存图片
import matplotlib.pyplot as plt  # 画图主力

import pandas as pd  # 数据处理主力

# 让 matplotlib 尽量显示中文（如果没有中文字体也不影响，只是图里的中文会变方块）
plt.rcParams["axes.unicode_minus"] = False

# %% [markdown]
# # 第 2 步：准备数据
#
# 我们用项目自带的合成评论数据。如果你已经跑过主项目，数据会在这里：
#     data/processed/sample_processed.csv
#
# 如果还没跑过主项目，我们就在这里现场生成一份。

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / "data" / "processed" / "sample_processed.csv"

if not DATA_CSV.exists():
    print("没找到数据，尝试跑一次主项目的 pipeline...")
    # 动态导入主项目的 pipeline（懒加载，避免本 Notebook 引入所有依赖）
    import sys
    sys.path.insert(0, str(ROOT))  # 把项目根目录加入 path，让 src 能被识别为 package
    from src.pipeline import run_full_pipeline  # noqa: E402
    run_full_pipeline(n_reviews=300, use_synthetic=True, llm_backend="mock")

# 现在读 CSV
df = pd.read_csv(DATA_CSV)
print(f"加载了 {len(df)} 条评论")
print("前 5 条：")
print(df.head())

# %% [markdown]
# # 第 3 步：基本统计分析
#
# pandas 的 `.value_counts()` 是数据分析最常用的工具之一，
# 等价于 Excel 的"数据透视表"。

# 不同平台有多少条评论？
platform_counts = df["platform"].value_counts()
print("\n各平台评论数：")
print(platform_counts)

# 不同细分人群有多少条？
segment_counts = df["user_segment"].value_counts()
print("\n各细分人群评论数：")
print(segment_counts)

# 平均评分
print(f"\n平均评分: {df['rating'].mean():.2f}")
print(f"评分分布:\n{df['rating'].value_counts().sort_index()}")

# %% [markdown]
# # 第 4 步：画第一张图 —— 平台分布柱状图
#
# matplotlib 画图的"三步曲"：
# 1. plt.figure(figsize=(8, 4)) ——  创建一张画布
# 2. ax.bar(...) / ax.pie(...) —— 在画布上画东西
# 3. plt.savefig(...) —— 保存图片

fig, ax = plt.subplots(figsize=(7, 4))
platform_counts.plot(kind="bar", ax=ax, color=["#ff6f91", "#7b68ee", "#06d6a0"])
ax.set_title("各平台评论数")
ax.set_xlabel("平台")
ax.set_ylabel("评论数")
ax.tick_params(axis="x", rotation=0)
fig.tight_layout()

OUT_DIR = ROOT / "outputs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
fig_path = OUT_DIR / "basics_01_platform_counts.png"
plt.savefig(fig_path, dpi=150)
plt.close(fig)
print(f"图已保存到 {fig_path}")

# %% [markdown]
# # 第 5 步：画第二张图 —— 评分分布饼图

fig, ax = plt.subplots(figsize=(6, 6))
rating_counts = df["rating"].value_counts().sort_index()
ax.pie(
    rating_counts.values,
    labels=[f"{i} 星" for i in rating_counts.index],
    autopct="%1.1f%%",
    colors=["#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#073b4c"],
    startangle=90,
)
ax.set_title("评分分布")
fig.tight_layout()
fig_path = OUT_DIR / "basics_02_rating_pie.png"
plt.savefig(fig_path, dpi=150)
plt.close(fig)
print(f"图已保存到 {fig_path}")

# %% [markdown]
# # 第 6 步：手写一个"简易情感分析器"
#
# 思路：
# - 维护两个词表：正面词 / 负面词
# - 对每条评论，统计正/负词出现次数
# - 正面词多 → 好评；负面词多 → 差评；一样多 → 中性

POSITIVE_WORDS = {
    "好", "棒", "喜欢", "推荐", "惊艳", "完美", "超值", "满意", "回购",
    "持久", "细腻", "高级感", "服帖", "自然", "显白", "精致", "好用",
    "颜值高", "设计感", "质感", "丝滑", "清透", "持妆", "奶油肌",
}
NEGATIVE_WORDS = {
    "差", "失望", "难用", "浮粉", "拔干", "卡粉", "脱妆", "暗沉", "厚重",
    "假白", "刺激", "过敏", "爆痘", "闷痘", "踩雷", "不推荐", "退货",
    "包装差", "漏粉", "飞粉", "色差", "氧化", "假面",
}


def simple_sentiment(text: str) -> str:
    """对一条文本判断正/负/中性。"""
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    if pos > neg:
        return "正面"
    if neg > pos:
        return "负面"
    return "中性"


# 对每条评论跑一遍
df["my_sentiment"] = df["text"].astype(str).map(simple_sentiment)
print("\n情感分布：")
print(df["my_sentiment"].value_counts())

# %% [markdown]
# # 第 7 步：画第三张图 —— 自定义情感分布

fig, ax = plt.subplots(figsize=(7, 4))
counts = df["my_sentiment"].value_counts().reindex(["正面", "中性", "负面"], fill_value=0)
counts.plot(kind="bar", ax=ax, color=["#06d6a0", "#ffd166", "#ef476f"])
ax.set_title("自写情感分析器结果")
ax.set_xlabel("情感")
ax.set_ylabel("评论数")
ax.tick_params(axis="x", rotation=0)
fig.tight_layout()
fig_path = OUT_DIR / "basics_03_my_sentiment.png"
plt.savefig(fig_path, dpi=150)
plt.close(fig)
print(f"图已保存到 {fig_path}")

# %% [markdown]
# # 第 8 步：交叉分析 —— 哪个细分人群最爱打差评？

cross_tab = pd.crosstab(df["user_segment"], df["my_sentiment"], normalize="index") * 100
print("\n各细分人群的情感分布（百分比）：")
print(cross_tab.round(1))

# %% [markdown]
# # 第 9 步：把结果保存成 CSV
#
# 让招生官看到你能完整地"输入 → 处理 → 输出"。

result_csv = ROOT / "data" / "processed" / "basics_with_sentiment.csv"
df.to_csv(result_csv, index=False, encoding="utf-8-sig")
print(f"结果已保存到 {result_csv}")

# %% [markdown]
# # 第 10 步：小结
#
# 你刚刚完成了：
# - 用 pandas 读 CSV、做统计、做交叉表
# - 用 matplotlib 画了 3 张图
# - 用纯 Python 写了一个简易情感分析器
# - 把结果保存成 CSV 与 PNG
#
# 这些是数据分析师的"基本功"。能讲清楚这一页代码，
# 就比"只跑过几个 Jupyter 教程"强得多。

print("\n✅ 全部完成。请查看 outputs/figures/ 下的 PNG 与 data/processed/basics_with_sentiment.csv")
