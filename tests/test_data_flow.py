"""
Data flow tests — variable definition-to-use tracing across whitebox modules.
"""

from __future__ import annotations

import pytest

from whitebox.metrics import (
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.repo_profiler import build_language_repo_data, profile_language
from whitebox.score_engine import score_delta


def test_profile_file_count_equals_len_files() -> None:
    profile = profile_language("java")
    assert profile["file_count"] == len(profile["files"])


def test_profile_qa_hours_bounded_below() -> None:
    profile = profile_language("java")
    assert profile["estimated_qa_hours"] >= 0.5


def test_build_repo_data_profile_flows_to_composite() -> None:
    data = build_language_repo_data("java")
    recomputed = compute_metrics_from_profile(data["profile"])
    assert compute_composite_score(recomputed) == data["composite_score"]


def test_metrics_all_50_composite_is_50() -> None:
    m = ControlFlowMetrics(**{k: 50.0 for k in (
        "execution_path_integrity", "decision_outcome_verification",
        "logical_subexpression_validation", "total_logical_combinatorial_coverage",
        "technical_debt_impact", "qa_resource_allocation",
    )})
    assert compute_composite_score(m) == 50.0


def test_score_delta_before_after_flow_to_delta_value() -> None:
    low  = {k: 0.0   for k in ("execution_path_integrity", "decision_outcome_verification",
                                 "logical_subexpression_validation", "total_logical_combinatorial_coverage",
                                 "technical_debt_impact", "qa_resource_allocation")}
    high = {k: 100.0 for k in low}
    result = score_delta({"control_flow_metrics": low}, {"control_flow_metrics": high})
    assert result["delta"] == round(result["after_composite"] - result["before_composite"], 2)


def test_score_delta_per_metric_all_zero_when_same() -> None:
    data = build_language_repo_data("java")
    result = score_delta(data, data)
    assert all(v == 0.0 for v in result["per_metric_delta"].values())


def test_profile_branch_points_positive() -> None:
    profile = profile_language("java")
    assert profile["branch_points"] > 0


def test_profile_covered_paths_le_execution_paths() -> None:
    profile = profile_language("java")
    assert profile["covered_paths"] <= profile["execution_paths"]


def test_profile_covered_sub_le_logical_sub() -> None:
    profile = profile_language("java")
    assert profile["covered_subexpressions"] <= profile["logical_subexpressions"]


def test_full_coverage_profile_produces_high_integrity() -> None:
    profile = {
        "execution_paths": 10, "covered_paths": 10,
        "decision_nodes": 10,  "verified_decisions": 10,
        "logical_subexpressions": 5, "covered_subexpressions": 5,
        "truth_table_rows": 8,  "covered_combinations": 8,
        "branch_points": 10,    "cyclomatic_complexity": 3,
        "lines_of_code": 100,   "test_assertions": 20,
        "estimated_qa_hours": 1.0,
    }
    metrics = compute_metrics_from_profile(profile)
    assert metrics.execution_path_integrity == 100.0
    assert metrics.decision_outcome_verification == 100.0
