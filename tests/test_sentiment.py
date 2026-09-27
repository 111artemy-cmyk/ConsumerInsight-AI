"""Unit tests for sentiment scoring helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from llm.mock_client import MockLLMClient  # noqa: E402


def test_mock_sentiment_positive():
    client = MockLLMClient()
    resp = client._handle_sentiment(
        '请阅读以下来自 小红书 的用户文本，并针对以下 6 个维度，分别给出 -1（负面）到 1（正面）的情感分数。\n'
        "维度列表：product_quality, value_for_money, packaging_design, skin_feel, long_wear, service_experience\n\n"
        '用户文本：\n"""\n回购第三次了，粉质细腻服帖，持妆一整天。包装颜值高。\n"""\n\n'
    )
    assert resp["overall"] > 0.5
    assert resp["dimensions"]["product_quality"]["score"] > 0.5
    assert resp["dimensions"]["packaging_design"]["score"] > 0.0


def test_mock_sentiment_negative():
    client = MockLLMClient()
    resp = client._handle_sentiment(
        '请阅读以下来自 天猫 的用户文本，并针对以下 6 个维度，分别给出 -1（负面）到 1（正面）的情感分数。\n'
        "维度列表：product_quality, value_for_money, packaging_design, skin_feel, long_wear, service_experience\n\n"
        '用户文本：\n"""\n拔干起皮，飞粉到我怀疑人生，T区两小时就斑驳了，敏感肌别碰。\n"""\n\n'
    )
    assert resp["overall"] < -0.3
    assert resp["dimensions"]["skin_feel"]["score"] < 0.0


if __name__ == "__main__":
    test_mock_sentiment_positive()
    test_mock_sentiment_negative()
    print("✅ sentiment tests passed")
