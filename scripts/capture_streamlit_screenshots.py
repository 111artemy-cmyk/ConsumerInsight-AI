"""Capture Streamlit dashboard screenshots for the README.

Launches ``streamlit run app/streamlit_app.py`` in headless mode, then uses
Playwright (Chromium) to visit each of the 10 sidebar sections and save a
PNG. Run with::

    python scripts/capture_streamlit_screenshots.py

Outputs ``docs/screenshots/01_overview.png`` … ``10_methodology.png``
(file numbering matches the sidebar section order 1 → 10).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def _wait_for_port(host: str, port: int, timeout_s: float = 60.0) -> None:
    """Block until the Streamlit port accepts connections."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(1.0)
    raise TimeoutError(f"Streamlit did not start on {host}:{port} within {timeout_s}s")


# 10 个 sidebar section → 截图文件名。顺序与 app/streamlit_app.py 的 radio 列表一致。
TARGETS: list[tuple[str, str]] = [
    ("01_overview.png",      "1. 项目概览"),
    ("02_data.png",          "2. 数据概览"),
    ("03_sentiment.png",     "3. 多维度情感"),
    ("04_topics.png",        "4. 核心话题"),
    ("05_personas.png",      "5. 消费者 Persona"),
    ("06_segmentation.png",  "6. 受众细分"),
    ("07_funnel.png",        "7. 趋势 & 漏斗"),
    ("08_roi.png",           "8. ROI 预估"),
    ("09_creatives.png",     "9. 营销文案候选"),
    ("10_methodology.png",   "10. 方法说明"),
]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT / "app" / "streamlit_app.py"),
            "--server.headless=true",
            "--server.port=8501",
            "--browser.gatherUsageStats=false",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_port("127.0.0.1", 8501, timeout_s=60.0)
        # Streamlit compiles scripts on first hit, give it a moment.
        time.sleep(2.0)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1400, "height": 900})

            for filename, label in TARGETS:
                page = context.new_page()
                page.goto("http://127.0.0.1:8501/", wait_until="domcontentloaded")
                # Streamlit re-renders on every interaction. Click the sidebar
                # radio item by visible label.
                page.get_by_text(label, exact=True).first.click()
                # Wait for the figure / dataframe to settle.
                page.wait_for_timeout(3500)
                page.screenshot(path=str(OUT / filename), full_page=True)
                page.close()
                print(f"  saved {filename}")

            browser.close()
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())