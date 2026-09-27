"""Marketing Analytics modules for ConsumerInsight-AI.

This sub-package implements the four classical marketing-analytics
building blocks the project relies on:

* :mod:`.segmentation`     — Audience segmentation (KMeans on TF-IDF +
  engineered behavioural features).
* :mod:`.campaign_generator` — LLM-driven marketing copy generation.
* :mod:`.roi_predictor`     — Lightweight conversion-rate / ROI model.
* :mod:`.funnel_analyzer`   — Marketing funnel diagnostics.
"""

from .segmentation import Segmenter
from .campaign_generator import CampaignGenerator
from .roi_predictor import ROIPredictor
from .funnel_analyzer import FunnelAnalyzer

__all__ = [
    "Segmenter",
    "CampaignGenerator",
    "ROIPredictor",
    "FunnelAnalyzer",
]
