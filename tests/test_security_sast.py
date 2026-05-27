"""
Security SAST tests — input validation, data-flow security, dependency scanning,
authentication/authorization checks, and compliance validation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from whitebox.metrics import (
    METRIC_KEYS,
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.repo_profiler import build_language_repo_data, profile_language
from whitebox.score_engine import load_metrics_from_repo_data, score_delta
from whitebox.commit_trigger import on_commit, load_language_repo_data as load_current


# ---------------------------------------------------------------------------
# Input Validation Testing
# ---------------------------------------------------------------------------

class TestInputValidation:
    """Validates that all public APIs reject invalid/malicious inputs."""

    def test_compute_metrics_rejects_none_profile(self) -> None:
        with pytest.raises((TypeError, AttributeError, KeyError)):
            compute_metrics_from_profile(None)  # type: ignore[arg-type]

    def test_compute_composite_rejects_out_of_range_high(self) -> None:
        bad = ControlFlowMetrics(**{k: 101.0 if k == list(METRIC_KEYS)[0] else 50.0 for k in METRIC_KEYS})
        with pytest.raises(ValueError, match="out of range"):
            compute_composite_score(bad)

    def test_compute_composite_rejects_out_of_range_low(self) -> None:
        bad = ControlFlowMetrics(**{k: -1.0 if k == list(METRIC_KEYS)[1] else 50.0 for k in METRIC_KEYS})
        with pytest.raises(ValueError, match="out of range"):
            compute_composite_score(bad)

    def test_from_dict_rejects_missing_keys(self) -> None:
        incomplete = {k: 50.0 for k in METRIC_KEYS}
        incomplete.pop(list(METRIC_KEYS)[0])
        with pytest.raises(ValueError, match="Invalid metric data"):
            ControlFlowMetrics.from_dict(incomplete)

    def test_from_dict_rejects_non_numeric_values(self) -> None:
        bad = {k: "not-a-number" if k == list(METRIC_KEYS)[0] else 50.0 for k in METRIC_KEYS}
        with pytest.raises(ValueError):
            ControlFlowMetrics.from_dict(bad)

    def test_from_dict_rejects_empty_dict(self) -> None:
        with pytest.raises(ValueError, match="Invalid metric data"):
            ControlFlowMetrics.from_dict({})

    def test_on_commit_rejects_empty_sha(self) -> None:
        with pytest.raises(ValueError, match="commit_sha"):
            on_commit("")

    def test_on_commit_rejects_whitespace_sha(self) -> None:
        with pytest.raises(ValueError, match="commit_sha"):
            on_commit("   ")

    def test_load_metrics_rejects_missing_key(self) -> None:
        with pytest.raises(ValueError, match="Malformed"):
            load_metrics_from_repo_data({"language": "java"})

    def test_load_metrics_rejects_empty_dict(self) -> None:
        with pytest.raises(ValueError, match="Malformed"):
            load_metrics_from_repo_data({})

    def test_profile_language_rejects_unsupported(self) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            profile_language("ruby")

    def test_profile_language_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError):
            profile_language("")

    def test_profile_language_rejects_sql_injection(self) -> None:
        with pytest.raises(ValueError):
            profile_language("'; DROP TABLE --")

    def test_profile_language_rejects_path_traversal(self) -> None:
        with pytest.raises(ValueError):
            profile_language("../../etc/passwd")

    def test_from_dict_rejects_none_value(self) -> None:
        bad = {k: None if k == list(METRIC_KEYS)[0] else 50.0 for k in METRIC_KEYS}
        with pytest.raises((ValueError, TypeError)):
            ControlFlowMetrics.from_dict(bad)


# ---------------------------------------------------------------------------
# Data Flow Security Analysis
# ---------------------------------------------------------------------------

class TestDataFlowSecurity:
    """Tests that data flows through the pipeline without corruption or leakage."""

    def test_profile_to_metrics_data_integrity(self) -> None:
        profile = profile_language("java")
        metrics = compute_metrics_from_profile(profile)
        for key in METRIC_KEYS:
            val = getattr(metrics, key)
            assert 0.0 <= val <= 100.0, f"{key} out of bounds: {val}"

    def test_metrics_to_composite_data_integrity(self) -> None:
        metrics = compute_metrics_from_profile(profile_language("java"))
        score = compute_composite_score(metrics)
        assert 0.0 <= score <= 100.0

    def test_repo_data_structure_integrity(self) -> None:
        data = build_language_repo_data("java")
        assert "control_flow_metrics" in data
        assert "composite_score" in data
        assert "profile" in data
        assert isinstance(data["composite_score"], float)
        assert 0.0 <= data["composite_score"] <= 100.0

    def test_score_delta_does_not_leak_internal_state(self) -> None:
        data = build_language_repo_data("java")
        result = score_delta(data, data)
        assert result["delta"] == 0.0
        assert "control_flow_metrics" not in result

    def test_metrics_from_dict_does_not_accept_extra_keys(self) -> None:
        valid = {k: 50.0 for k in METRIC_KEYS}
        valid["injected_key"] = "malicious_value"
        metrics = ControlFlowMetrics.from_dict(valid)
        assert not hasattr(metrics, "injected_key")

    def test_profile_file_list_is_present(self) -> None:
        profile = profile_language("java")
        assert "files" in profile
        assert isinstance(profile["files"], list)

    def test_no_credentials_in_repo_data_output(self) -> None:
        data = build_language_repo_data("java")
        data_str = json.dumps(data)
        suspicious_patterns = [
            r"password\s*=",
            r"api_key\s*=",
            r"bearer\s+\w{20,}",
        ]
        for pattern in suspicious_patterns:
            assert not re.search(pattern, data_str, re.IGNORECASE), f"Credential leak: {pattern}"


# ---------------------------------------------------------------------------
# Authorization Control Checks
# ---------------------------------------------------------------------------

class TestAuthorizationControls:
    """Verifies that authorization controls are robust and not bypassable."""

    def test_on_commit_requires_valid_sha(self) -> None:
        for bad_sha in ["", "  "]:
            with pytest.raises(ValueError):
                on_commit(bad_sha)

    def test_profile_language_enforces_allowlist(self) -> None:
        for unsupported in ["python", "go", "rust", "javascript", "php", "ruby"]:
            with pytest.raises(ValueError, match="Unsupported"):
                profile_language(unsupported)

    def test_load_metrics_enforces_required_schema_key(self) -> None:
        with pytest.raises(ValueError, match="Malformed"):
            load_metrics_from_repo_data({"wrong_key": {}})

    def test_composite_score_cannot_be_negative(self) -> None:
        m = ControlFlowMetrics(**{k: 0.0 for k in METRIC_KEYS})
        score = compute_composite_score(m)
        assert score >= 0.0

    def test_composite_score_cannot_exceed_100(self) -> None:
        m = ControlFlowMetrics(**{k: 100.0 for k in METRIC_KEYS})
        score = compute_composite_score(m)
        assert score <= 100.0

    def test_metrics_from_dict_enforces_all_keys_present(self) -> None:
        for missing_key in list(METRIC_KEYS)[:3]:
            incomplete = {k: 50.0 for k in METRIC_KEYS if k != missing_key}
            with pytest.raises(ValueError):
                ControlFlowMetrics.from_dict(incomplete)


# ---------------------------------------------------------------------------
# Dependency & Library Vulnerability Detection
# ---------------------------------------------------------------------------

class TestDependencyVulnerabilityDetection:
    """Checks that dependency declarations are present and properly constrained."""

    def test_requirements_txt_exists(self) -> None:
        req = Path(__file__).resolve().parent.parent / "requirements.txt"
        assert req.exists(), "requirements.txt must exist for dependency tracking"

    def test_requirements_txt_has_version_constraints(self) -> None:
        req = Path(__file__).resolve().parent.parent / "requirements.txt"
        content = req.read_text()
        assert ">=" in content or "==" in content or "<" in content

    def test_sbom_exists(self) -> None:
        sbom = Path(__file__).resolve().parent.parent / "sbom.json"
        assert sbom.exists(), "sbom.json (CycloneDX SBOM) must exist"

    def test_sbom_is_valid_json(self) -> None:
        sbom_path = Path(__file__).resolve().parent.parent / "sbom.json"
        if sbom_path.exists():
            data = json.loads(sbom_path.read_text())
            assert "components" in data or "bomFormat" in data

    def test_sbom_has_license_info(self) -> None:
        sbom_path = Path(__file__).resolve().parent.parent / "sbom.json"
        if sbom_path.exists():
            content = sbom_path.read_text()
            assert "license" in content.lower() or "MIT" in content

    def test_no_known_unsafe_patterns_in_source(self) -> None:
        src_dir = Path(__file__).resolve().parent.parent / "whitebox"
        for py_file in src_dir.glob("*.py"):
            content = py_file.read_text()
            assert "pickle.loads" not in content, f"Unsafe pickle.loads in {py_file}"
            assert "__import__(" not in content, f"Unsafe __import__ in {py_file}"

    def test_no_hardcoded_credentials_in_source(self) -> None:
        src_dir = Path(__file__).resolve().parent.parent / "whitebox"
        credential_patterns = [
            r'password\s*=\s*["\'][^"\']{4,}["\']',
            r'api_key\s*=\s*["\'][^"\']{4,}["\']',
        ]
        for py_file in src_dir.glob("*.py"):
            content = py_file.read_text()
            for pattern in credential_patterns:
                assert not re.search(pattern, content, re.IGNORECASE), \
                    f"Possible hardcoded credential in {py_file}"


# ---------------------------------------------------------------------------
# Compliance & Security Standard Validation
# ---------------------------------------------------------------------------

class TestComplianceValidation:
    """Validates that security compliance artifacts are present and correct."""

    def test_license_file_exists(self) -> None:
        license_path = Path(__file__).resolve().parent.parent / "LICENSE"
        assert license_path.exists(), "LICENSE file must exist"

    def test_license_is_osi_approved(self) -> None:
        license_path = Path(__file__).resolve().parent.parent / "LICENSE"
        if license_path.exists():
            content = license_path.read_text()
            osi_keywords = ["MIT", "Apache", "BSD", "GPL", "LGPL", "ISC", "Mozilla"]
            assert any(kw in content for kw in osi_keywords)

    def test_pyproject_has_license_metadata(self) -> None:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            assert "license" in content.lower()

    def test_security_policy_exists(self) -> None:
        security = Path(__file__).resolve().parent.parent / "SECURITY.md"
        assert security.exists(), "SECURITY.md must exist"

    def test_all_metric_values_in_valid_range(self) -> None:
        data = build_language_repo_data("java")
        metrics = data["control_flow_metrics"]
        for key, value in metrics.items():
            assert 0.0 <= value <= 100.0, f"{key}={value} out of range"

    def test_whitebox_domain_is_correct(self) -> None:
        data = build_language_repo_data("java")
        assert data["whitebox_domain"] == "control_flow_testing"

    def test_metric_weights_sum_to_one(self) -> None:
        from whitebox.metrics import METRIC_WEIGHTS
        total = sum(METRIC_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Weights do not sum to 1.0: {total}"

    def test_metric_thresholds_defined_for_all_keys(self) -> None:
        from whitebox.metrics import METRIC_THRESHOLDS
        for key in METRIC_KEYS:
            assert key in METRIC_THRESHOLDS
            assert 0 <= METRIC_THRESHOLDS[key] <= 100
