"""一键运行脚本 —— 给零代码经验的同学准备的"开箱即用"入口。

用法（Windows PowerShell）
    cd "D:\Mcode 储存点\ConsumerInsight-AI"
    python scripts\run_all.py

脚本会自动：
1. 检查 / 创建 Python 虚拟环境
2. 安装依赖（如果缺失）
3. 生成示例数据（如不存在）
4. 跑通完整 pipeline
5. 把结果写到 outputs/figures 和 outputs/reports

如果你想用真实的 LLM API（OpenAI / 智谱 / DeepSeek），先：
    setx OPENAI_API_KEY "sk-..."
    setx OPENAI_BASE_URL "https://api.openai.com/v1"
然后再运行本脚本，并设置环境变量 CI_LLM_BACKEND=openai。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ_FILE = ROOT / "requirements.txt"
VENV_DIR = ROOT / ".venv"


def _run(cmd: list[str], **kwargs) -> None:
    print("\n>>>", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)


def ensure_python() -> str:
    """Return path to a usable Python interpreter (creating a venv if needed)."""
    # Try current interpreter first
    py = sys.executable
    try:
        import importlib
        importlib.import_module("pandas")
        return py
    except ImportError:
        pass

    # Try to create a venv
    print("未检测到依赖。正在创建虚拟环境并安装依赖…")
    _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if os.name == "nt":
        py = str(VENV_DIR / "Scripts" / "python.exe")
    else:
        py = str(VENV_DIR / "bin" / "python")

    _run([py, "-m", "pip", "install", "--upgrade", "pip"])
    _run([py, "-m", "pip", "install", "-r", str(REQ_FILE)])
    return py


def main() -> int:
    py = ensure_python()
    env = os.environ.copy()
    pipeline_cmd = [
        py,
        str(ROOT / "scripts" / "run_pipeline.py"),
        "--n", "1500",
        "--backend", env.get("CI_LLM_BACKEND", "auto"),
        "--model", env.get("CI_LLM_MODEL", "gpt-4o-mini"),
    ]
    _run(pipeline_cmd, cwd=str(ROOT))
    print(
        "\n✅ 全部完成。\n"
        f"   报告: {ROOT / 'outputs' / 'reports' / 'pipeline_report.md'}\n"
        f"   图表: {ROOT / 'outputs' / 'figures'}\n"
        f"   Demo: streamlit run {ROOT / 'app' / 'streamlit_app.py'}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
