"""Score engine: composite deltas and metric log persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from whitebox.metrics import ControlFlowMetrics, compute_composite_score
from whitebox.repo_profiler import REPO_DATA_DIR

METRIC_LOG_PATH = REPO_DATA_DIR / "metric_log.json"


def load_metrics_from_repo_data(data: dict[str, Any]) -> ControlFlowMetrics:
    """Load and validate ControlFlowMetrics from a repo data payload.

    Raises ValueError with 'Malformed' if the payload lacks the required key.
    """
    if "control_flow_metrics" not in data:
        raise ValueError(
            f"Malformed repo data: missing 'control_flow_metrics' key. "
            f"Available keys: {list(data.keys())}"
        )
    return ControlFlowMetrics.from_dict(data["control_flow_metrics"])


def score_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compute per-metric and composite delta between two repo data snapshots.

    Returns a dict with keys:
      - before_composite: float
      - after_composite: float
      - delta: float
      - improved: bool
      - regressed: bool
      - per_metric_delta: dict[str, float]
    """
    before_metrics = load_metrics_from_repo_data(before)
    after_metrics = load_metrics_from_repo_data(after)
    before_composite = compute_composite_score(before_metrics)
    after_composite = compute_composite_score(after_metrics)
    delta = round(after_composite - before_composite, 2)

    per_metric: dict[str, float] = {}
    for key in before_metrics.to_dict():
        per_metric[key] = round(getattr(after_metrics, key) - getattr(before_metrics, key), 2)

    return {
        "before_composite": before_composite,
        "after_composite": after_composite,
        "delta": delta,
        "improved": delta > 0,
        "regressed": delta < 0,
        "per_metric_delta": per_metric,
    }


def append_score_history(entry: dict[str, Any]) -> Path:
    """Append a scored entry to the metric log JSON file."""
    METRIC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    if METRIC_LOG_PATH.exists():
        history = json.loads(METRIC_LOG_PATH.read_text(encoding="utf-8"))

    entry.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
    history.append(entry)
    METRIC_LOG_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return METRIC_LOG_PATH


def get_latest_score(language: str) -> dict[str, Any] | None:
    """Return the most recent log entry for the given language, or None."""
    if not METRIC_LOG_PATH.exists():
        return None
    history: list[dict[str, Any]] = json.loads(METRIC_LOG_PATH.read_text(encoding="utf-8"))
    for entry in reversed(history):
        if entry.get("language") == language:
            return entry
    return None
