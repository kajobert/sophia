[📚 Documentation Index](INDEX.md) | [⬅️ 04 Development Guidelines](04_DEVELOPMENT_GUIDELINES.md) | **05** → [06 User Guide](06_USER_GUIDE.md)

---

# Document 5: Project Governance, Automation, and Workflow

**Decision-Making** | Roles & Responsibilities | Workflow Automation

This document defines the processes, tools, and automation that ensure the quality, efficiency, and clarity of the Sophia V2 project development.

> 🔄 **Sophia 2.0 Update:** Introduction of `master-sophia` autonomous branch for Sophia's self-directed work. See [`config/autonomy.yaml`](../../config/autonomy.yaml) for autonomous operation boundaries.

## 1. GitHub Workflow & Branching Strategy

We follow a structured Git workflow to ensure stability and predictability.

*   **`master`:** This branch is the source of truth for stable, production-ready code. Direct pushes are disabled. Merges into `master` are only permitted through a Pull Request from the `develop` branch after thorough review and testing.
*   **`develop`:** The primary development branch. It contains the latest integrated features and represents the current "edge" version of the application. All feature branches are merged into `develop`.
*   **`feature/<plugin-name>` or `fix/<issue-name>`:** All new development, whether it's a new plugin or a bug fix, must occur in a dedicated feature or fix branch. These branches are created from the latest `develop` branch.

## 2. Pull Request (PR) Process

Every code change must be submitted through a Pull Request to the `develop` branch.

1.  **PR Template:** PRs must follow the template defined in `.github/PULL_REQUEST_TEMPLATE.md`, which requires a clear description of the changes, the "why" behind them, and a link to any relevant issues.
2.  **Mandatory CI Checks:** A PR cannot be merged until all automated checks (CI) have passed successfully.
3.  **Code Review:** At least one other developer must review and approve the PR before it can be merged.

## 3. Automation (CI/CD) with GitHub Actions

The Continuous Integration (CI) pipeline, defined in `.github/workflows/ci.yml`, runs automatically on every push and Pull Request to the `develop` and `master` branches. Its purpose is to guarantee code quality and stability.

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

## 6. Idea and Note Management (`roberts-notes.txt`)

To facilitate a rapid and unstructured flow of ideas from the project lead, the following workflow is established:

*   **`docs/roberts-notes.txt`:** This file serves as a dedicated log for high-level ideas, feature requests, and strategic notes from the project lead. It is intentionally unstructured.
*   **AI Agent Responsibility:** During dedicated "planning" or "ideation" tasks, an AI agent (like Jules) is expected to:
    1.  Read and parse the contents of `roberts-notes.txt`.
    2.  Analyze the notes in the context of the current project architecture, roadmap, and goals.
    3.  For any viable and actionable ideas, formulate a concrete, step-by-step implementation plan.
    4.  Present this plan for review and approval.
*   **Goal:** This "human-in-the-loop" process ensures that valuable, spontaneous ideas are captured and can be systematically integrated into the formal project backlog and documentation.

---

## Related Documentation

- 🔧 **[Development Guidelines](04_DEVELOPMENT_GUIDELINES.md)** - Code quality standards and pre-commit hooks
- 🧑‍💻 **[Developer Guide](07_DEVELOPER_GUIDE.md)** - Practical development workflow
- 🎯 **[Vision & DNA](01_VISION_AND_DNA.md)** - Immutable principles guiding governance
- ⚙️ **[Autonomy Configuration](../../config/autonomy.yaml)** - Autonomous branch strategy and HITL boundaries

**Sophia 2.0 Governance:**
- **Autonomous Branch:** `master-sophia` for Sophia's self-directed work
- **Human Approval Required:** Core modifications, DNS changes, budget > $1/day
- **Emergency Stop:** Manual intervention protocol defined in autonomy.yaml
- **Audit Trail:** All autonomous actions logged in [`WORKLOG.md`](../../WORKLOG.md)

---

**Navigation:** [📚 Index](INDEX.md) | [🏠 Home](../../README.md) | [⬅️ Previous: Development Guidelines](04_DEVELOPMENT_GUIDELINES.md) | [➡️ Next: User Guide](06_USER_GUIDE.md)

---

*Last Updated: November 3, 2025 | Status: ✅ Current | Sophia 2.0 Autonomous Governance Active*
