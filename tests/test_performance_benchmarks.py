"""
Performance benchmarks for whitebox modules.
"""

from __future__ import annotations

import pytest

from whitebox.metrics import (
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.repo_profiler import build_language_repo_data, profile_language


def test_benchmark_compute_metrics_from_profile(benchmark) -> None:
    profile = {
        "branch_points": 20, "decision_nodes": 20, "execution_paths": 20,
        "covered_paths": 18, "logical_subexpressions": 10, "covered_subexpressions": 9,
        "truth_table_rows": 32, "covered_combinations": 28, "verified_decisions": 18,
        "cyclomatic_complexity": 5, "lines_of_code": 200,
        "test_assertions": 40, "estimated_qa_hours": 2.0,
    }
    benchmark(lambda: compute_metrics_from_profile(profile))


def test_benchmark_compute_composite_score(benchmark) -> None:
    m = ControlFlowMetrics(
        execution_path_integrity=90.0,
        decision_outcome_verification=88.0,
        logical_subexpression_validation=85.0,
        total_logical_combinatorial_coverage=87.0,
        technical_debt_impact=75.0,
        qa_resource_allocation=80.0,
    )
    benchmark(lambda: compute_composite_score(m))


def test_benchmark_profile_language(benchmark) -> None:
    benchmark(lambda: profile_language("java"))


def test_benchmark_build_language_repo_data(benchmark) -> None:
    benchmark(lambda: build_language_repo_data("java"))
