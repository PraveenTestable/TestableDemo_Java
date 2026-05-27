"""
Whitebox repo profiling, Control Flow metrics, and commit-triggered scoring.

This package provides:
  - Control Flow metrics computation from Java source analysis
  - Path execution tracking and coverage verification
  - Complete coverage path verification across all decision nodes
  - Nested condition path testing for complex branching logic
  - Loop path detection and boundary condition analysis
  - Exception path handling and error branch coverage
  - Multi-function path tracking across module boundaries
  - CI/CD integration via commit-triggered scoring

All metrics follow Testable Whitebox taxonomy for Control Flow Testing,
Data Flow Testing, and Mutation Testing categories.
"""

from __future__ import annotations

__version__ = "1.1.0"
__license__ = "MIT"
__author__ = "PraveenTestable"

from whitebox.metrics import (
    METRIC_KEYS,
    METRIC_LABELS,
    METRIC_THRESHOLDS,
    METRIC_WEIGHTS,
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.score_engine import (
    append_score_history,
    get_latest_score,
    load_metrics_from_repo_data,
    score_delta,
)
from whitebox.repo_profiler import (
    build_language_repo_data,
    detect_languages,
    profile_language,
    run_initial_whitebox,
    update_current_repo_data,
    write_repo_data,
)
from whitebox.commit_trigger import (
    load_language_repo_data,
    on_commit,
)

__all__ = [
    "METRIC_KEYS",
    "METRIC_LABELS",
    "METRIC_THRESHOLDS",
    "METRIC_WEIGHTS",
    "ControlFlowMetrics",
    "compute_composite_score",
    "compute_metrics_from_profile",
    "append_score_history",
    "get_latest_score",
    "load_metrics_from_repo_data",
    "score_delta",
    "build_language_repo_data",
    "detect_languages",
    "profile_language",
    "run_initial_whitebox",
    "update_current_repo_data",
    "write_repo_data",
    "load_language_repo_data",
    "on_commit",
]
