"""Tests for src/readme_sync.py — README Evaluation table synchroniser."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import pytest

from src.evaluation import ClusteringEval, ROICVEval, SentimentRatingEval
from src.readme_sync import sync_readme_evaluation_table


# ---------------------------------------------------------------------------
# Fixture data — minimal dataclass instances with realistic values
# ---------------------------------------------------------------------------

def _make_clustering(
    sil: float = 0.15,
    ari: Optional[float] = 0.05,
    nmi: Optional[float] = 0.07,
) -> ClusteringEval:
    return ClusteringEval(
        silhouette=sil,
        ari=ari,
        nmi=nmi,
        n_samples=120,
        n_clusters=4,
        n_true_labels=4,
        disclosure="placeholder",
    )


def _make_sentiment(
    pearson: float = 0.83,
    spearman: float = 0.78,
) -> SentimentRatingEval:
    return SentimentRatingEval(
        pearson_r=pearson,
        pearson_p=0.0,
        spearman_r=spearman,
        spearman_p=0.0,
        n=1500,
        disclosure="placeholder",
    )


def _make_roi(r2: float = 0.98, mae: float = 0.32) -> ROICVEval:
    import pandas as pd
    coef = pd.DataFrame({"feature": ["a"], "coef": [0.1]})
    return ROICVEval(
        cv_r2=r2,
        cv_mae=mae,
        cv_coefficients=coef,
        n_folds=5,
        n_samples=1500,
        intercept_mean=0.0,
        disclosure="placeholder",
    )


README_TEMPLATE = """\
# Project README

Some intro text here. Not in the Evaluation table.

| Metric (seed 42) | Value | How to read it |
|---|---|---|
| Silhouette score | **+0.1507** | Weak cluster separation. |
| ARI vs synthetic `user_segment` | **+0.0467** | Circular check. |
| NMI vs synthetic `user_segment` | **+0.0664** | Same reading as ARI. |
| Pearson sentiment ↔ rating | **+0.8327** | Internal consistency only. |
| Spearman sentiment ↔ rating | **+0.7820** | Same caveat. |
| ROI 5-fold CV R² (per-review proxy) | **+0.9793** | Deterministic proxy. |
| ROI CV MAE | **0.3180** | Same caveat. |

More text after the table — must not be touched.
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sync_replaces_all_seven_cells(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE, encoding="utf-8")

    n = sync_readme_evaluation_table(
        readme,
        clustering_eval=_make_clustering(sil=0.18, ari=0.06, nmi=0.09),
        sentiment_rating_eval=_make_sentiment(pearson=0.85, spearman=0.80),
        roi_cv_eval=_make_roi(r2=0.97, mae=0.30),
    )

    assert n == 7
    text = readme.read_text(encoding="utf-8")
    assert "**+0.1800**" in text  # silhouette
    assert "**+0.0600**" in text  # ARI
    assert "**+0.0900**" in text  # NMI
    assert "**+0.8500**" in text  # Pearson
    assert "**+0.8000**" in text  # Spearman
    assert "**+0.9700**" in text  # ROI R²
    assert "**0.3000**" in text  # ROI MAE (no leading +)
    # Old values must be gone
    assert "0.1507" not in text
    assert "0.8327" not in text
    # Surrounding text preserved
    assert "Some intro text here" in text
    assert "must not be touched" in text


def test_sync_preserves_metric_names_and_descriptions(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE, encoding="utf-8")

    sync_readme_evaluation_table(
        readme,
        clustering_eval=_make_clustering(),
        sentiment_rating_eval=_make_sentiment(),
        roi_cv_eval=_make_roi(),
    )

    text = readme.read_text(encoding="utf-8")
    # Metric names untouched
    assert "Silhouette score" in text
    assert "ARI vs synthetic" in text
    assert "NMI vs synthetic" in text
    assert "Pearson sentiment" in text
    assert "Spearman sentiment" in text
    assert "ROI 5-fold CV R" in text
    assert "ROI CV MAE" in text
    # Descriptions untouched
    assert "Weak cluster separation" in text
    assert "Circular check" in text
    assert "Internal consistency only" in text


def test_sync_does_not_touch_unrelated_rows(tmp_path: Path):
    extra = """\
| Some other table | **+99.9999** | Should not change. |
"""
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE + extra, encoding="utf-8")

    n = sync_readme_evaluation_table(
        readme,
        clustering_eval=_make_clustering(),
        sentiment_rating_eval=_make_sentiment(),
        roi_cv_eval=_make_roi(),
    )

    assert n == 7
    text = readme.read_text(encoding="utf-8")
    assert "**+99.9999**" in text  # untouched
    assert "Should not change." in text


def test_sync_handles_missing_ari_and_nmi(tmp_path: Path):
    """When ARI/NMI are None (synthetic labels missing), leave the row alone."""
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE, encoding="utf-8")

    n = sync_readme_evaluation_table(
        readme,
        clustering_eval=_make_clustering(ari=None, nmi=None),
        sentiment_rating_eval=_make_sentiment(),
        roi_cv_eval=_make_roi(),
    )

    # silhouette + Pearson + Spearman + ROI R² + ROI MAE = 5 (ARI/NMI skipped)
    assert n == 5
    text = readme.read_text(encoding="utf-8")
    # ARI / NMI old values still there
    assert "**+0.0467**" in text
    assert "**+0.0664**" in text
    # silhouette still updated
    assert "**+0.1500**" in text


def test_sync_handles_all_evals_none(tmp_path: Path):
    """When evaluation was skipped (skip_evaluation=True), nothing changes."""
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE, encoding="utf-8")

    n = sync_readme_evaluation_table(
        readme,
        clustering_eval=None,
        sentiment_rating_eval=None,
        roi_cv_eval=None,
    )

    assert n == 0
    text = readme.read_text(encoding="utf-8")
    assert text == README_TEMPLATE  # byte-for-byte unchanged


def test_sync_returns_zero_when_readme_missing(tmp_path: Path):
    """Missing README must NOT raise — just returns 0."""
    n = sync_readme_evaluation_table(
        tmp_path / "no_such_file.md",
        clustering_eval=_make_clustering(),
        sentiment_rating_eval=_make_sentiment(),
        roi_cv_eval=_make_roi(),
    )
    assert n == 0


def test_sync_returns_zero_when_table_missing(tmp_path: Path):
    """README exists but has no Evaluation table — return 0 silently."""
    readme = tmp_path / "README.md"
    readme.write_text("# Project\n\nNo table here.\n", encoding="utf-8")

    n = sync_readme_evaluation_table(
        readme,
        clustering_eval=_make_clustering(),
        sentiment_rating_eval=_make_sentiment(),
        roi_cv_eval=_make_roi(),
    )
    assert n == 0


def test_sync_is_idempotent(tmp_path: Path):
    """Running sync twice with the same inputs should produce the same output."""
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE, encoding="utf-8")

    clustering = _make_clustering(sil=0.1234)
    sentiment = _make_sentiment()
    roi = _make_roi()

    n1 = sync_readme_evaluation_table(
        readme,
        clustering_eval=clustering,
        sentiment_rating_eval=sentiment,
        roi_cv_eval=roi,
    )
    after_first = readme.read_text(encoding="utf-8")
    n2 = sync_readme_evaluation_table(
        readme,
        clustering_eval=clustering,
        sentiment_rating_eval=sentiment,
        roi_cv_eval=roi,
    )
    after_second = readme.read_text(encoding="utf-8")

    assert n1 == n2 == 7
    assert after_first == after_second


def test_sync_negative_values(tmp_path: Path):
    """silhouette can be negative; ensure the regex/format handle it."""
    readme = tmp_path / "README.md"
    readme.write_text(README_TEMPLATE, encoding="utf-8")

    sync_readme_evaluation_table(
        readme,
        clustering_eval=_make_clustering(sil=-0.05),
        sentiment_rating_eval=_make_sentiment(),
        roi_cv_eval=_make_roi(),
    )

    text = readme.read_text(encoding="utf-8")
    assert "**-0.0500**" in text


def test_sync_normalizes_unbolded_mae(tmp_path: Path):
    """If MAE was hand-written without `**`, sync still updates it AND
    re-emits bold for consistency with the rest of the table."""
    legacy = (
        "# README\n\n"
        "| Metric (seed 42) | Value | How to read it |\n"
        "|---|---|---|\n"
        "| Silhouette score | **+0.1507** | desc |\n"
        "| ROI CV MAE | 0.3180 | desc |\n"
    )
    readme = tmp_path / "README.md"
    readme.write_text(legacy, encoding="utf-8")

    n = sync_readme_evaluation_table(
        readme,
        clustering_eval=None,
        sentiment_rating_eval=None,
        roi_cv_eval=_make_roi(mae=0.25),
    )
    assert n == 1
    text = readme.read_text(encoding="utf-8")
    assert "**0.2500**" in text
    assert " 0.25" not in text  # no stray plain "0.25"