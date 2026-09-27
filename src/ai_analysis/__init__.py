"""AI analysis modules for ConsumerInsight-AI.

This sub-package groups the four LLM-driven analysis tasks that form
the consumer-insight layer:

* :mod:`.sentiment`      — multi-aspect sentiment analysis
* :mod:`.topic_modeling` — topic extraction
* :mod:`.persona_generator` — consumer persona synthesis
* :mod:`.trend_detector` — time-series trend detection
"""

from .sentiment import SentimentAnalyzer
from .topic_modeling import TopicModeler
from .persona_generator import PersonaGenerator
from .trend_detector import TrendDetector

__all__ = [
    "SentimentAnalyzer",
    "TopicModeler",
    "PersonaGenerator",
    "TrendDetector",
]
