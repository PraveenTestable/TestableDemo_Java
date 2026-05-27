# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Dependency Security

All dependencies are tracked in `sbom.json` (CycloneDX format) and `requirements.txt`.

- **License compliance**: All direct dependencies use MIT or BSD-2-Clause licenses.
- **Vulnerability scanning**: Run `pip-audit` or `safety check` before each release.
- **Dependency pinning**: Upper bounds defined in `requirements.txt` to prevent supply-chain drift.
- **Supply-chain integrity**: SBOM regenerated on every release via CI/CD pipeline.

## Input Validation

All public APIs validate inputs before processing:
- `TransactionProcessor.processBatch()` — validates currency and amount range.
- `PaymentRouter.route()` — validates HTTP method against an allowlist.
- `whitebox.commit_trigger.on_commit()` — validates commit SHA is non-empty.
- `whitebox.metrics.ControlFlowMetrics.from_dict()` — validates all required keys are present and numeric.

## Data Flow Security

- No PII is logged or persisted. All metric keys refer to code-structure measurements only.
- Repository data stored in `repo_data/` contains only aggregate scores and timestamps.
- No external data, credentials, or secrets are processed by this tool.

## Access Control

- This tool operates in read-only mode on source repositories.
- CI/CD pipeline access is controlled via GitHub Actions environment variables.
- No hardcoded credentials exist in this repository (verified via `detect-secrets` pre-commit hook).
- All output files contain structural metrics only — no personal or sensitive information.

## Vulnerability Reporting

Please open a GitHub issue labelled `[SECURITY]` to report potential issues.
We target a 48-hour initial response and a 7-day patch turnaround for confirmed findings.
