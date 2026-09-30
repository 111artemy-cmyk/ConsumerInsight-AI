"""Keep README's Evaluation table in sync with the latest pipeline run.

Why this module exists
----------------------
Without this, ``README.md`` and ``outputs/reports/pipeline_report.md`` drift
apart across runs — they are produced by separate code paths and updated
manually. Reviewers who open the public GitHub README see one set of numbers,
and anyone who re-runs the pipeline locally sees a different set in
``pipeline_report.md``. This is the kind of inconsistency that breaks trust
in a portfolio piece.

This module provides a single function
:func:`sync_readme_evaluation_table` that rewrites the README's Evaluation
table in place, using the values from a freshly-produced pipeline run.
It is called from :mod:`scripts.run_pipeline` after the pipeline finishes,
so that "what's in the README" always matches "what the pipeline produced".

What it edits
~~~~~~~~~~~~~
Only rows in README whose **metric column** matches one of the seven metric
patterns below (``Silhouette score``, ``ARI vs synthetic``, ``NMI vs
synthetic``, ``Pearson sentiment``, ``Spearman sentiment``, ``ROI 5-fold CV
R``, ``ROI CV MAE``). Rows that don't match are left untouched. The metric
names and descriptions in the README are preserved — only the bold numerical
value is replaced.

Failure mode
~~~~~~~~~~~~
If the README has no Evaluation table, or if the cluster / sentiment / ROI
evaluations were skipped (``None``), the function returns ``0`` and prints a
single-line notice. It never raises — silent drift is worse than a clear
"0 cells replaced" message.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Metric key → README column regex + formatter
# ---------------------------------------------------------------------------
# Each entry maps a regex (matched against the metric column of a README
# table row) to a key. The key is looked up in `_format_value` below to
# produce the new bold value.

_METRIC_REGEXES: list[tuple[str, str]] = [
    (r"Silhouette score\b", "silhouette"),
    (r"ARI vs synthetic\b", "ari"),
    (r"NMI vs synthetic\b", "nmi"),
    (r"Pearson sentiment\b", "pearson"),
    (r"Spearman sentiment\b", "spearman"),
    (r"ROI 5-fold CV R", "roi_r2"),
    (r"ROI CV MAE\b", "roi_mae"),
]


def _format_value(key: str, evals: dict) -> str:
    """Format a metric value following the README's existing convention.

    Most metrics use the ``+X.XXXX`` format (with leading +); ``roi_mae``
    uses plain ``X.XXXX``. Returns ``"n/a"`` if the corresponding eval is
    missing / None — the caller leaves such rows alone.
    """
    clustering = evals.get("clustering")
    sentiment = evals.get("sentiment")
    roi = evals.get("roi")

    if key == "silhouette":
        return f"{clustering.silhouette:+.4f}" if clustering is not None else "n/a"
    if key == "ari":
        if clustering is None or clustering.ari is None:
            return "n/a"
        return f"{clustering.ari:+.4f}"
    if key == "nmi":
        if clustering is None or clustering.nmi is None:
            return "n/a"
        return f"{clustering.nmi:+.4f}"
    if key == "pearson":
        return f"{sentiment.pearson_r:+.4f}" if sentiment is not None else "n/a"
    if key == "spearman":
        return f"{sentiment.spearman_r:+.4f}" if sentiment is not None else "n/a"
    if key == "roi_r2":
        return f"{roi.cv_r2:+.4f}" if roi is not None else "n/a"
    if key == "roi_mae":
        # MAE is reported without leading '+' in the README convention.
        return f"{roi.cv_mae:.4f}" if roi is not None else "n/a"
    raise KeyError(f"Unknown metric key: {key!r}")


# Match a README evaluation row of the shape:
#   | <metric> | **<value>** | <description> |
# or (less commonly) | <metric> | <value> | <description> | — value may be
# unbolded if it was hand-written without `**` around it. We accept both so
# the sync works on either style; the output always re-emits bold.
# Capture groups: (leading pipe+space, metric text, space, value, tail)
_ROW_RE = re.compile(
    r"^(\|\s*)([^|]+?)(\s*)\|\s*(\*\*[+\-]?\d+\.\d+\*\*|[+\-]?\d+\.\d+)\s*(\|.*)$",
    re.MULTILINE,
)


def sync_readme_evaluation_table(
    readme_path: Path,
    *,
    clustering_eval,
    sentiment_rating_eval,
    roi_cv_eval,
) -> int:
    """Rewrite README's Evaluation table to match a real pipeline run.

    Parameters
    ----------
    readme_path
        Path to the README to edit. If it does not exist, the function
        returns 0 and prints a notice — it never raises.
    clustering_eval, sentiment_rating_eval, roi_cv_eval
        The ``ClusteringEval``, ``SentimentRatingEval``, ``ROICVEval``
        dataclasses produced by the pipeline. Any of them can be ``None``
        (e.g. when ``skip_evaluation=True``); corresponding cells are
        left untouched.

    Returns
    -------
    int
        The number of cells that were replaced. Useful for tests and for
        logging from the caller.
    """
    if not readme_path.exists():
        print(f"[readme_sync] {readme_path} not found; skipping")
        return 0

    text = readme_path.read_text(encoding="utf-8")
    evals = {
        "clustering": clustering_eval,
        "sentiment": sentiment_rating_eval,
        "roi": roi_cv_eval,
    }

    n_replaced = 0

    def _replace(match: "re.Match[str]") -> str:
        nonlocal n_replaced
        leading, metric_text, sep, _old_value, tail = match.groups()
        metric_text_stripped = metric_text.strip()

        for regex, key in _METRIC_REGEXES:
            if re.search(regex, metric_text_stripped):
                new_value = _format_value(key, evals)
                if new_value == "n/a":
                    # No data for this metric — leave the README's value alone.
                    return match.group(0)
                n_replaced += 1
                # Reconstruct the row preserving leading/trailing whitespace.
                # Always emit bold (handles the unbolded-MAE legacy case too).
                return f"{leading}{metric_text}{sep}| **{new_value}** {tail}"

        # Metric name didn't match any known pattern — leave the row alone.
        return match.group(0)

    new_text = _ROW_RE.sub(_replace, text)

    if n_replaced > 0:
        readme_path.write_text(new_text, encoding="utf-8")
        print(f"[readme_sync] updated {n_replaced} cells in {readme_path.name}")

    return n_replaced