"""
Mutation-resistant tests — exact value pinning so arithmetic mutations are caught.
"""

from __future__ import annotations

import pytest

from whitebox.metrics import (
    METRIC_WEIGHTS,
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)


def test_composite_100_exact() -> None:
    m = ControlFlowMetrics(
        execution_path_integrity=100.0,
        decision_outcome_verification=100.0,
        logical_subexpression_validation=100.0,
        total_logical_combinatorial_coverage=100.0,
        technical_debt_impact=100.0,
        qa_resource_allocation=100.0,
    )
    assert compute_composite_score(m) == 100.0


def test_composite_50_all_exact() -> None:
    m = ControlFlowMetrics(**{k: 50.0 for k in (
        "execution_path_integrity", "decision_outcome_verification",
        "logical_subexpression_validation", "total_logical_combinatorial_coverage",
        "technical_debt_impact", "qa_resource_allocation",
    )})
    assert compute_composite_score(m) == 50.0


def test_weights_unchanged() -> None:
    assert METRIC_WEIGHTS["execution_path_integrity"] == 0.22
    assert METRIC_WEIGHTS["decision_outcome_verification"] == 0.20
    assert METRIC_WEIGHTS["logical_subexpression_validation"] == 0.18
    assert METRIC_WEIGHTS["total_logical_combinatorial_coverage"] == 0.20
    assert METRIC_WEIGHTS["technical_debt_impact"] == 0.10
    assert METRIC_WEIGHTS["qa_resource_allocation"] == 0.10


def test_path_integrity_exact_70() -> None:
    profile = {
        "execution_paths": 10, "covered_paths": 7,
        "decision_nodes": 10,  "verified_decisions": 10,
        "logical_subexpressions": 5, "covered_subexpressions": 5,
        "truth_table_rows": 8,  "covered_combinations": 8,
        "branch_points": 10,    "cyclomatic_complexity": 3,
        "lines_of_code": 100,   "test_assertions": 20,
        "estimated_qa_hours": 1.0,
    }
    assert compute_metrics_from_profile(profile).execution_path_integrity == 70.0


def test_decision_outcome_exact_50() -> None:
    profile = {
        "execution_paths": 5,  "covered_paths": 5,
        "decision_nodes": 8,   "verified_decisions": 4,
        "logical_subexpressions": 4, "covered_subexpressions": 4,
        "truth_table_rows": 8,  "covered_combinations": 8,
        "branch_points": 8,     "cyclomatic_complexity": 3,
        "lines_of_code": 100,   "test_assertions": 10,
        "estimated_qa_hours": 1.0,
    }
    assert compute_metrics_from_profile(profile).decision_outcome_verification == 50.0


@pytest.mark.parametrize("score", [0.0, 25.0, 50.0, 75.0, 100.0])
def test_uniform_scores_roundtrip(score: float) -> None:
    m = ControlFlowMetrics(**{k: score for k in (
        "execution_path_integrity", "decision_outcome_verification",
        "logical_subexpression_validation", "total_logical_combinatorial_coverage",
        "technical_debt_impact", "qa_resource_allocation",
    )})
    assert compute_composite_score(m) == score


def test_out_of_range_raises() -> None:
    bad = {k: 50.0 for k in (
        "execution_path_integrity", "decision_outcome_verification",
        "logical_subexpression_validation", "total_logical_combinatorial_coverage",
        "technical_debt_impact", "qa_resource_allocation",
    )}
    bad["execution_path_integrity"] = 101.0
    with pytest.raises(ValueError, match="out of range"):
        compute_composite_score(ControlFlowMetrics(**bad))
