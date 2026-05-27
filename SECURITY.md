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
- `PaymentRouter.route()` — validates HTTP method against allowlist.
- `whitebox.commit_trigger.on_commit()` — validates commit SHA is non-empty.
- `whitebox.metrics.ControlFlowMetrics.from_dict()` — validates all required keys present and numeric.

## Data Flow Security

- No PII is logged or persisted. All metric keys refer to code-structure measurements only.
- Repository data stored in `repo_data/` contains only aggregate scores and timestamps.
- No user data, credentials, or secrets are processed by this tool.

## Authentication & Authorization

- The whitebox scoring tool does not handle user authentication.
- Access to the CI/CD pipeline is controlled via GitHub Actions secrets.
- No hardcoded credentials exist in this repository (verified via `detect-secrets` pre-commit hook).

## Reporting a Vulnerability

Please report security issues by opening a GitHub issue marked `[SECURITY]`.
We aim to respond within 48 hours and patch within 7 days for critical issues.
