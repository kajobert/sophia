# Document 5: Project Governance, Automation, and Workflow

This document defines the processes, tools, and automation that ensure the quality, efficiency, and clarity of the Sophia V2 project development.

## 1. GitHub Workflow & Branching Strategy

We follow a structured Git workflow to ensure stability and predictability.

*   **`main`:** This branch is the source of truth for stable, production-ready code. Direct pushes are disabled. Merges into `main` are only permitted through a Pull Request from the `develop` branch after thorough review and testing.
*   **`develop`:** The primary development branch. It contains the latest integrated features and represents the current "edge" version of the application. All feature branches are merged into `develop`.
*   **`feature/<plugin-name>` or `fix/<issue-name>`:** All new development, whether it's a new plugin or a bug fix, must occur in a dedicated feature or fix branch. These branches are created from the latest `develop` branch.

## 2. Pull Request (PR) Process

Every code change must be submitted through a Pull Request to the `develop` branch.

1.  **PR Template:** PRs must follow the template defined in `.github/PULL_REQUEST_TEMPLATE.md`, which requires a clear description of the changes, the "why" behind them, and a link to any relevant issues.
2.  **Mandatory CI Checks:** A PR cannot be merged until all automated checks (CI) have passed successfully.
3.  **Code Review:** At least one other developer must review and approve the PR before it can be merged.

## 3. Automation (CI/CD) with GitHub Actions

The Continuous Integration (CI) pipeline, defined in `.github/workflows/ci.yml`, runs automatically on every push and Pull Request to the `develop` and `main` branches. Its purpose is to guarantee code quality and stability.

The CI pipeline consists of the following jobs:

1.  **Linting & Formatting:**
    *   **`black`**: Enforces uncompromising code formatting.
    *   **`ruff`**: An extremely fast linter that checks for a wide range of errors and style issues.
    *   **`mypy`**: Performs static type checking to ensure 100% type annotation compliance.

2.  **Unit & Integration Testing:**
    *   **`pytest`**: Automatically discovers and runs all tests in the `tests/` directory.
    *   **Coverage Analysis**: Reports on the percentage of the codebase covered by tests. A decrease in coverage may block a PR merge.

3.  **Multi-Version Compatibility:**
    *   The test suite runs on a matrix of Python versions (e.g., 3.10, 3.11, 3.12) to ensure the code is compatible with all supported environments.

4.  **Security Scanning (Future Goal):**
    *   Integration of tools like `bandit` or `Snyk` to scan for common security vulnerabilities in the codebase and dependencies.

5.  **Docker Build Verification:**
    *   A final step attempts to build a Docker image from the provided `Dockerfile`. This ensures that the application and its dependencies can be containerized successfully, preventing runtime errors in production.

## 4. Mandatory Work Documentation

*   **`WORKLOG.md`:** As defined in the `AGENTS.md`, it is the strict duty of every agent to log their work in this file using the specified format upon task completion. This creates a human-readable audit trail of all development activities.
*   **`IDEAS.md`:** This file is a dedicated space for recording ideas, suggestions, or potential improvements that are outside the scope of the current task. This prevents good ideas from being lost.

## 5. Living Architectural Documentation

*   **`PROJECT_STRUCTURE.md`:** This file will contain a machine-readable overview of all implemented plugins, their types, and a brief description. It will be **automatically updated** by a script (`scripts/update_structure_doc.py`) triggered by a GitHub Action after every successful merge into `develop`. This ensures the documentation never becomes outdated.
