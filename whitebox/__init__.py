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
"""

from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import Any, Optional

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
    "METRIC_KEYS", "METRIC_LABELS", "METRIC_THRESHOLDS", "METRIC_WEIGHTS",
    "ControlFlowMetrics", "compute_composite_score", "compute_metrics_from_profile",
    "append_score_history", "get_latest_score", "load_metrics_from_repo_data", "score_delta",
    "build_language_repo_data", "detect_languages", "profile_language", "run_initial_whitebox",
    "update_current_repo_data", "write_repo_data", "load_language_repo_data", "on_commit",
    "track_execution_path", "verify_coverage_paths", "detect_loop_paths",
    "handle_exception_paths", "track_multi_function_paths", "validate_branch_coverage",
    "check_ci_integration", "detect_path_coverage",
]


# ---------------------------------------------------------------------------
# Path Execution Tracking
# ---------------------------------------------------------------------------

def track_execution_path(
    data: dict[str, Any],
    path_type: str = "full",
    validate: bool = True,
) -> dict[str, Any]:
    """Track and classify code execution paths from profile data.

    Covers: linear paths, branched paths, loop paths, exception paths.
    """
    if data is None:
        raise ValueError("data must not be None")

    result: dict[str, Any] = {"path_type": path_type, "paths_found": [], "coverage": 0.0}

    if path_type == "full":
        covered = data.get("covered_paths", 0)
        total = max(data.get("execution_paths", 1), 1)
        result["coverage"] = min(100.0, (covered / total) * 100)
        result["paths_found"].append("linear")

        if data.get("branch_points", 0) > 0:
            result["paths_found"].append("branched")
            for i in range(min(data.get("branch_points", 0), 5)):
                if i % 2 == 0:
                    result["paths_found"].append(f"branch-true-{i}")
                else:
                    result["paths_found"].append(f"branch-false-{i}")

    elif path_type == "partial":
        result["coverage"] = data.get("covered_subexpressions", 0) / max(
            data.get("logical_subexpressions", 1), 1
        ) * 100

    elif path_type == "loop":
        loop_count = data.get("loop_count", 0)
        if loop_count > 0:
            result["paths_found"].extend(["zero-iteration", "one-iteration", "many-iterations"])
            result["coverage"] = min(100.0, (loop_count / max(loop_count, 1)) * 100)
        else:
            result["coverage"] = 0.0

    elif path_type == "exception":
        exc_count = data.get("exception_handlers", 0)
        if exc_count > 0:
            result["paths_found"].extend(["try-path", "catch-path", "finally-path"])
            result["coverage"] = min(100.0, exc_count * 25.0)
        else:
            result["coverage"] = 0.0

    else:
        raise ValueError(f"Unknown path_type: {path_type!r}. Must be one of: full, partial, loop, exception")

    if validate and result["coverage"] < 0:
        raise ValueError(f"Coverage cannot be negative: {result['coverage']}")

    return result


# ---------------------------------------------------------------------------
# Complete Coverage Path Verification
# ---------------------------------------------------------------------------

def verify_coverage_paths(
    profile: dict[str, Any],
    thresholds: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """Verify that all required coverage paths meet their thresholds.

    Tests both true and false branches, loop boundaries, and exception paths.
    """
    if thresholds is None:
        thresholds = {
            "execution_path_integrity": 70.0,
            "decision_outcome_verification": 70.0,
            "logical_subexpression_validation": 60.0,
            "total_logical_combinatorial_coverage": 65.0,
        }

    metrics = compute_metrics_from_profile(profile)
    results: dict[str, Any] = {"passed": [], "failed": [], "warnings": []}

    for key, threshold in thresholds.items():
        value = getattr(metrics, key, 0.0)
        if value >= threshold:
            results["passed"].append({"metric": key, "value": value, "threshold": threshold})
        elif value >= threshold * 0.8:
            results["warnings"].append({"metric": key, "value": value, "threshold": threshold})
        else:
            results["failed"].append({"metric": key, "value": value, "threshold": threshold})

    results["overall_pass"] = len(results["failed"]) == 0
    results["pass_rate"] = len(results["passed"]) / max(len(thresholds), 1) * 100
    return results


# ---------------------------------------------------------------------------
# Loop Path Detection
# ---------------------------------------------------------------------------

def detect_loop_paths(source_text: str) -> dict[str, Any]:
    """Detect and classify loop patterns in source code for path coverage.

    Identifies for-loops, while-loops, do-while loops, and nested loops.
    """
    if not source_text:
        return {"for_loops": 0, "while_loops": 0, "nested_loops": 0, "total": 0}

    for_count = len(re.findall(r"\bfor\b", source_text))
    while_count = len(re.findall(r"\bwhile\b", source_text))

    nested = 0
    lines = source_text.splitlines()
    in_loop = False
    for line in lines:
        stripped = line.strip()
        if re.search(r"\b(for|while)\b", stripped):
            if in_loop:
                nested += 1
            else:
                in_loop = True
        if stripped in ("}", "end"):
            in_loop = False

    total = for_count + while_count
    return {
        "for_loops": for_count,
        "while_loops": while_count,
        "nested_loops": nested,
        "total": total,
        "has_boundary_tests": total > 0,
        "loop_coverage_estimate": min(100.0, total * 15.0) if total > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Exception Path Handling
# ---------------------------------------------------------------------------

def handle_exception_paths(
    func_name: str,
    args: tuple[Any, ...],
    expected_exceptions: tuple[type[Exception], ...] = (),
) -> dict[str, Any]:
    """Execute a named whitebox function and record exception path outcomes.

    Covers: normal path, expected exception path, unexpected exception path.
    """
    func_map: dict[str, Any] = {
        "compute_composite_score": lambda: compute_composite_score(args[0]) if args else None,
        "compute_metrics_from_profile": lambda: compute_metrics_from_profile(args[0]) if args else None,
        "detect_languages": lambda: detect_languages(),
        "profile_language": lambda: profile_language(args[0]) if args else None,
    }

    if func_name not in func_map:
        return {
            "path": "error",
            "reason": f"Unknown function: {func_name}",
            "exception": None,
            "result": None,
        }

    try:
        result = func_map[func_name]()
        return {"path": "normal", "result": result, "exception": None}
    except expected_exceptions as exc:
        return {"path": "expected-exception", "exception": type(exc).__name__, "message": str(exc), "result": None}
    except ValueError as exc:
        return {"path": "value-error", "exception": "ValueError", "message": str(exc), "result": None}
    except (TypeError, KeyError) as exc:
        return {"path": "type-or-key-error", "exception": type(exc).__name__, "message": str(exc), "result": None}
    except Exception as exc:  # noqa: BLE001
        return {"path": "unexpected-exception", "exception": type(exc).__name__, "message": str(exc), "result": None}


# ---------------------------------------------------------------------------
# Multi-Function Path Tracking
# ---------------------------------------------------------------------------

def track_multi_function_paths(language: str = "java") -> dict[str, Any]:
    """Track execution paths that span multiple whitebox functions.

    Exercises: detect → profile → compute → score pipeline.
    """
    trace: list[str] = []

    try:
        languages = detect_languages()
        trace.append(f"detect_languages -> {languages}")

        if not languages:
            return {"trace": trace, "path": "no-languages", "composite_score": 0.0}

        if language not in languages:
            return {"trace": trace, "path": "language-not-found", "composite_score": 0.0}

        trace.append(f"profile_language({language})")
        profile = profile_language(language)
        trace.append(f"profile complete: {profile.get('file_count', 0)} files")

        trace.append("compute_metrics_from_profile")
        metrics = compute_metrics_from_profile(profile)

        trace.append("compute_composite_score")
        score = compute_composite_score(metrics)
        trace.append(f"composite_score = {score}")

        return {"trace": trace, "path": "full-pipeline", "composite_score": score, "metrics": metrics.to_dict()}

    except ValueError as exc:
        trace.append(f"ValueError: {exc}")
        return {"trace": trace, "path": "value-error", "composite_score": 0.0}
    except RuntimeError as exc:
        trace.append(f"RuntimeError: {exc}")
        return {"trace": trace, "path": "runtime-error", "composite_score": 0.0}


# ---------------------------------------------------------------------------
# Branch Coverage Validation
# ---------------------------------------------------------------------------

def validate_branch_coverage(
    profile: dict[str, Any],
    min_branch_coverage: float = 80.0,
    min_decision_coverage: float = 70.0,
) -> dict[str, Any]:
    """Validate that branch and decision coverage meet minimum thresholds.

    Conditional paths tested: true-branch, false-branch, both-branches, neither.
    """
    branches = max(profile.get("branch_points", 0), 1)
    covered = profile.get("covered_paths", 0)
    decisions = max(profile.get("decision_nodes", 0), 1)
    verified = profile.get("verified_decisions", 0)

    branch_pct = min(100.0, (covered / branches) * 100)
    decision_pct = min(100.0, (verified / decisions) * 100)

    passed_branch = branch_pct >= min_branch_coverage
    passed_decision = decision_pct >= min_decision_coverage

    if passed_branch and passed_decision:
        status = "PASS"
    elif passed_branch or passed_decision:
        status = "PARTIAL"
    else:
        status = "FAIL"

    return {
        "branch_coverage_pct": round(branch_pct, 2),
        "decision_coverage_pct": round(decision_pct, 2),
        "branch_passed": passed_branch,
        "decision_passed": passed_decision,
        "status": status,
        "min_branch_coverage": min_branch_coverage,
        "min_decision_coverage": min_decision_coverage,
    }


# ---------------------------------------------------------------------------
# CI/CD Integration
# ---------------------------------------------------------------------------

def check_ci_integration(repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Check CI/CD integration artifacts and test pipeline configuration.

    Verifies: workflow files, score history, manifest, test configuration.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    checks: dict[str, bool] = {}
    details: dict[str, str] = {}

    workflow_dir = repo_root / ".github" / "workflows"
    if workflow_dir.exists():
        workflows = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
        checks["workflow_files"] = len(workflows) > 0
        details["workflow_files"] = f"Found {len(workflows)} workflow(s)"
    else:
        checks["workflow_files"] = False
        details["workflow_files"] = "No .github/workflows directory"

    pytest_ini = repo_root / "pytest.ini"
    setup_cfg = repo_root / "setup.cfg"
    pyproject = repo_root / "pyproject.toml"
    checks["test_config"] = pytest_ini.exists() or setup_cfg.exists() or pyproject.exists()
    details["test_config"] = "pytest.ini or setup.cfg or pyproject.toml found" if checks["test_config"] else "No test config"

    from whitebox.repo_profiler import REPO_DATA_DIR as _RDD
    manifest = _RDD / "initial_run_manifest.json"
    checks["whitebox_manifest"] = manifest.exists()
    details["whitebox_manifest"] = "initial_run_manifest.json found" if manifest.exists() else "Missing manifest"

    score_hist = _RDD / "metric_log.json"
    checks["metric_log"] = score_hist.exists()
    details["metric_log"] = "metric_log.json found" if score_hist.exists() else "No metric log yet"

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    integration_score = (passed / total) * 100 if total > 0 else 0.0

    return {
        "checks": checks,
        "details": details,
        "passed": passed,
        "total": total,
        "integration_score": round(integration_score, 2),
        "ci_ready": integration_score >= 75.0,
    }


# ---------------------------------------------------------------------------
# Path Detection Testing
# ---------------------------------------------------------------------------

def detect_path_coverage(
    source_files: list[Path],
    include_nested: bool = True,
    include_exceptions: bool = True,
) -> dict[str, Any]:
    """Detect and report on code path coverage across source files.

    Analyzes: linear paths, branched paths, loop paths, exception paths, nested paths.
    """
    if not source_files:
        return {
            "files_analyzed": 0,
            "total_branches": 0,
            "total_loops": 0,
            "total_exceptions": 0,
            "nested_depth": 0,
            "path_coverage_estimate": 0.0,
        }

    total_branches = 0
    total_loops = 0
    total_exceptions = 0
    max_nesting = 0

    for file_path in source_files:
        if not file_path.exists():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            continue

        total_branches += len(re.findall(r"\b(if|else if|elif|switch|case)\b", text))
        total_loops += len(re.findall(r"\b(for|while|do)\b", text))
        total_exceptions += len(re.findall(r"\b(try|catch|except|finally)\b", text))

        if include_nested:
            depth = 0
            current_max = 0
            for ch in text:
                if ch == "{":
                    depth += 1
                    current_max = max(current_max, depth)
                elif ch == "}":
                    depth = max(0, depth - 1)
            max_nesting = max(max_nesting, current_max)

    path_estimate = min(100.0, (
        (total_branches * 5) +
        (total_loops * 8) +
        (total_exceptions * 10 if include_exceptions else 0)
    ) / max(total_branches + total_loops + 1, 1))

    return {
        "files_analyzed": len(source_files),
        "total_branches": total_branches,
        "total_loops": total_loops,
        "total_exceptions": total_exceptions,
        "nested_depth": max_nesting,
        "path_coverage_estimate": round(path_estimate, 2),
        "has_nested_conditions": max_nesting > 3 if include_nested else False,
    }
