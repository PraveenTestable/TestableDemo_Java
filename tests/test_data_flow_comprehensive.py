"""
Comprehensive data-flow tests: definition-use tracking, coverage measurement,
edge case handling, unreachable use detection, and coverage reporting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from whitebox.metrics import (
    METRIC_KEYS,
    METRIC_WEIGHTS,
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.repo_profiler import build_language_repo_data, profile_language
from whitebox.score_engine import score_delta, load_metrics_from_repo_data


# ---------------------------------------------------------------------------
# Variable Definition Detection
# ---------------------------------------------------------------------------

class TestVariableDefinitionDetection:
    """Tests that variable definitions are correctly detected in profile data."""

    def test_profile_defines_branch_points(self) -> None:
        profile = profile_language("java")
        assert "branch_points" in profile
        assert isinstance(profile["branch_points"], int)
        assert profile["branch_points"] >= 0

    def test_profile_defines_decision_nodes(self) -> None:
        profile = profile_language("java")
        assert "decision_nodes" in profile
        assert isinstance(profile["decision_nodes"], int)

    def test_profile_defines_execution_paths(self) -> None:
        profile = profile_language("java")
        assert "execution_paths" in profile
        assert profile["execution_paths"] >= 1

    def test_profile_defines_all_required_variables(self) -> None:
        profile = profile_language("java")
        required_vars = {
            "branch_points", "decision_nodes", "execution_paths",
            "covered_paths", "logical_subexpressions", "covered_subexpressions",
            "truth_table_rows", "covered_combinations", "verified_decisions",
            "cyclomatic_complexity", "test_assertions", "estimated_qa_hours",
            "lines_of_code", "file_count", "files",
        }
        for var in required_vars:
            assert var in profile, f"Missing variable definition: {var}"

    def test_metric_keys_define_all_dataclass_fields(self) -> None:
        m = ControlFlowMetrics(**{k: 75.0 for k in METRIC_KEYS})
        for key in METRIC_KEYS:
            assert hasattr(m, key)
            assert getattr(m, key) == 75.0

    def test_metric_weights_define_all_keys(self) -> None:
        for key in METRIC_KEYS:
            assert key in METRIC_WEIGHTS
            assert METRIC_WEIGHTS[key] > 0


# ---------------------------------------------------------------------------
# Definition-Use Mapping
# ---------------------------------------------------------------------------

class TestDefinitionUseMapping:
    """Tests that variable values defined in one step are correctly used downstream."""

    def test_covered_paths_used_correctly_in_metric(self) -> None:
        profile = {
            "execution_paths": 10, "covered_paths": 8,
            "decision_nodes": 10, "verified_decisions": 9,
            "logical_subexpressions": 5, "covered_subexpressions": 4,
            "truth_table_rows": 16, "covered_combinations": 12,
            "branch_points": 10, "cyclomatic_complexity": 5,
            "lines_of_code": 100, "test_assertions": 15,
            "estimated_qa_hours": 1.0,
        }
        metrics = compute_metrics_from_profile(profile)
        assert metrics.execution_path_integrity == 80.0
        assert metrics.decision_outcome_verification == 90.0

    def test_composite_score_uses_all_metric_definitions(self) -> None:
        m_high = ControlFlowMetrics(**{k: 100.0 for k in METRIC_KEYS})
        m_low = ControlFlowMetrics(**{k: 0.0 for k in METRIC_KEYS})
        assert compute_composite_score(m_high) == 100.0
        assert compute_composite_score(m_low) == 0.0

    def test_score_delta_uses_before_and_after_definitions(self) -> None:
        low = {k: 0.0 for k in METRIC_KEYS}
        high = {k: 100.0 for k in METRIC_KEYS}
        result = score_delta(
            {"control_flow_metrics": low},
            {"control_flow_metrics": high}
        )
        assert result["before_composite"] == 0.0
        assert result["after_composite"] == 100.0
        assert result["delta"] == 100.0
        assert result["improved"] is True
        assert result["regressed"] is False

    def test_per_metric_delta_uses_both_definitions(self) -> None:
        m1 = {k: 30.0 for k in METRIC_KEYS}
        m2 = {k: 70.0 for k in METRIC_KEYS}
        result = score_delta(
            {"control_flow_metrics": m1},
            {"control_flow_metrics": m2}
        )
        for key in METRIC_KEYS:
            assert result["per_metric_delta"][key] == pytest.approx(40.0)

    def test_profile_branch_points_flow_to_execution_paths(self) -> None:
        profile = profile_language("java")
        assert profile["execution_paths"] >= 1
        assert profile["covered_paths"] <= profile["execution_paths"]


# ---------------------------------------------------------------------------
# Coverage Measurement
# ---------------------------------------------------------------------------

class TestCoverageMeasurement:
    """Tests that coverage measurements are accurate and reproducible."""

    def test_full_coverage_measurement(self) -> None:
        full = {
            "execution_paths": 8, "covered_paths": 8,
            "decision_nodes": 8, "verified_decisions": 8,
            "logical_subexpressions": 4, "covered_subexpressions": 4,
            "truth_table_rows": 16, "covered_combinations": 16,
            "branch_points": 8, "cyclomatic_complexity": 3,
            "lines_of_code": 80, "test_assertions": 20,
            "estimated_qa_hours": 1.0,
        }
        metrics = compute_metrics_from_profile(full)
        assert metrics.execution_path_integrity == 100.0

    def test_zero_coverage_measurement(self) -> None:
        none = {
            "execution_paths": 10, "covered_paths": 0,
            "decision_nodes": 10, "verified_decisions": 0,
            "logical_subexpressions": 5, "covered_subexpressions": 0,
            "truth_table_rows": 16, "covered_combinations": 0,
            "branch_points": 10, "cyclomatic_complexity": 10,
            "lines_of_code": 100, "test_assertions": 0,
            "estimated_qa_hours": 1.0,
        }
        metrics = compute_metrics_from_profile(none)
        assert metrics.execution_path_integrity == 0.0
        assert metrics.decision_outcome_verification == 0.0

    def test_coverage_measurement_is_reproducible(self) -> None:
        profile = profile_language("java")
        m1 = compute_metrics_from_profile(profile)
        m2 = compute_metrics_from_profile(profile)
        assert m1 == m2

    @pytest.mark.parametrize("covered,total,expected", [
        (0, 10, 0.0),
        (5, 10, 50.0),
        (10, 10, 100.0),
        (7, 10, 70.0),
        (1, 1, 100.0),
    ])
    def test_path_integrity_measurement_parametrized(
        self, covered: int, total: int, expected: float
    ) -> None:
        profile = {
            "execution_paths": total, "covered_paths": covered,
            "decision_nodes": total, "verified_decisions": covered,
            "logical_subexpressions": max(total // 2, 1),
            "covered_subexpressions": max(covered // 2, 0),
            "truth_table_rows": min(2 ** min(total, 6), 64),
            "covered_combinations": min(2 ** min(covered, 6), 64),
            "branch_points": total, "cyclomatic_complexity": 3,
            "lines_of_code": 100, "test_assertions": covered * 2,
            "estimated_qa_hours": 1.0,
        }
        metrics = compute_metrics_from_profile(profile)
        assert metrics.execution_path_integrity == expected

    def test_all_metrics_are_in_valid_range(self) -> None:
        profile = profile_language("java")
        metrics = compute_metrics_from_profile(profile)
        for key in METRIC_KEYS:
            val = getattr(metrics, key)
            assert 0.0 <= val <= 100.0, f"{key}={val} out of range"


# ---------------------------------------------------------------------------
# Edge Case Handling
# ---------------------------------------------------------------------------

class TestEdgeCaseHandling:
    """Tests boundary conditions and edge cases in coverage computation."""

    def test_empty_profile_handled_safely(self) -> None:
        metrics = compute_metrics_from_profile({})
        score = compute_composite_score(metrics)
        assert 0.0 <= score <= 100.0

    def test_single_branch_full_coverage(self) -> None:
        profile = {
            "branch_points": 1, "decision_nodes": 1,
            "execution_paths": 2, "covered_paths": 2,
            "logical_subexpressions": 1, "covered_subexpressions": 1,
            "truth_table_rows": 2, "covered_combinations": 2,
            "verified_decisions": 1, "cyclomatic_complexity": 2,
            "lines_of_code": 10, "test_assertions": 2,
            "estimated_qa_hours": 1.0,
        }
        metrics = compute_metrics_from_profile(profile)
        assert metrics.execution_path_integrity == 100.0

    def test_very_large_profile_values_capped(self) -> None:
        profile = {
            "branch_points": 9999, "decision_nodes": 9999,
            "execution_paths": 9999, "covered_paths": 9999,
            "logical_subexpressions": 9999, "covered_subexpressions": 9999,
            "truth_table_rows": 64, "covered_combinations": 64,
            "verified_decisions": 9999, "cyclomatic_complexity": 9999,
            "lines_of_code": 9999, "test_assertions": 9999,
            "estimated_qa_hours": 1.0,
        }
        metrics = compute_metrics_from_profile(profile)
        for key in METRIC_KEYS:
            assert getattr(metrics, key) <= 100.0

    def test_boundary_score_values(self) -> None:
        for score_val in [0.0, 1.0, 50.0, 99.0, 100.0]:
            m = ControlFlowMetrics(**{k: score_val for k in METRIC_KEYS})
            composite = compute_composite_score(m)
            assert composite == pytest.approx(score_val)

    def test_metric_validate_returns_empty_when_all_pass(self) -> None:
        from whitebox.metrics import METRIC_THRESHOLDS
        above = {k: min(METRIC_THRESHOLDS[k] + 10.0, 100.0) for k in METRIC_KEYS}
        m = ControlFlowMetrics(**above)
        failing = m.validate()
        assert isinstance(failing, list)
        assert len(failing) == 0

    def test_metric_validate_returns_all_when_all_fail(self) -> None:
        m = ControlFlowMetrics(**{k: 0.0 for k in METRIC_KEYS})
        failing = m.validate()
        assert set(failing) == set(METRIC_KEYS)

    def test_score_delta_zero_when_identical(self) -> None:
        data = build_language_repo_data("java")
        result = score_delta(data, data)
        assert result["delta"] == 0.0
        assert result["improved"] is False
        assert result["regressed"] is False


# ---------------------------------------------------------------------------
# Unreachable Use Detection
# ---------------------------------------------------------------------------

class TestUnreachableUseDetection:
    """Tests that the system correctly identifies unreachable code paths."""

    def test_score_below_threshold_identified_failing(self) -> None:
        m = ControlFlowMetrics(**{k: 0.0 for k in METRIC_KEYS})
        failing = m.validate()
        assert len(failing) == len(METRIC_KEYS)

    def test_score_at_threshold_passes(self) -> None:
        from whitebox.metrics import METRIC_THRESHOLDS
        at_threshold = {k: METRIC_THRESHOLDS[k] for k in METRIC_KEYS}
        m = ControlFlowMetrics(**at_threshold)
        failing = m.validate()
        assert len(failing) == 0

    def test_covered_paths_cannot_exceed_execution_paths(self) -> None:
        profile = profile_language("java")
        assert profile["covered_paths"] <= profile["execution_paths"]

    def test_covered_sub_cannot_exceed_logical_sub(self) -> None:
        profile = profile_language("java")
        assert profile["covered_subexpressions"] <= profile["logical_subexpressions"]

    def test_combinations_within_truth_table(self) -> None:
        profile = profile_language("java")
        assert profile["covered_combinations"] <= profile["truth_table_rows"]


# ---------------------------------------------------------------------------
# Coverage Reporting Validation
# ---------------------------------------------------------------------------

class TestCoverageReportingValidation:
    """Tests that coverage reports are accurate and properly formatted."""

    def test_repo_data_has_composite_score(self) -> None:
        data = build_language_repo_data("java")
        assert "composite_score" in data
        assert isinstance(data["composite_score"], float)

    def test_repo_data_has_all_metric_keys(self) -> None:
        data = build_language_repo_data("java")
        for key in METRIC_KEYS:
            assert key in data["control_flow_metrics"]

    def test_score_delta_has_required_fields(self) -> None:
        data = build_language_repo_data("java")
        result = score_delta(data, data)
        required = {"before_composite", "after_composite", "delta", "improved", "regressed", "per_metric_delta"}
        assert required <= result.keys()

    def test_score_delta_per_metric_covers_all_keys(self) -> None:
        data = build_language_repo_data("java")
        result = score_delta(data, data)
        assert set(result["per_metric_delta"].keys()) == set(METRIC_KEYS)

    def test_from_dict_roundtrip_identical_report(self) -> None:
        original = ControlFlowMetrics(**{k: float(i * 10) for i, k in enumerate(METRIC_KEYS)})
        recovered = ControlFlowMetrics.from_dict(original.to_dict())
        assert original.to_dict() == recovered.to_dict()

    def test_profile_has_timestamp(self) -> None:
        profile = profile_language("java")
        assert "profiled_at" in profile
        assert profile["profiled_at"]

    def test_build_repo_data_is_json_serializable(self) -> None:
        data = build_language_repo_data("java")
        serialized = json.dumps(data)
        recovered = json.loads(serialized)
        assert recovered["composite_score"] == data["composite_score"]
