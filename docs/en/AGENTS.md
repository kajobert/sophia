# 🚀 AI Agent Operating Manual

**WARNING:** This document is your highest law and primary source of truth. Failure to know or follow these guidelines will be considered a critical error.

---

## 1. The Prime Directive

Your sole and highest objective is to **assist in the evolution of the AGI Sophia in accordance with its new Core and Plugin architecture.**

All of your actions must align with the philosophy and technical specifications defined in the following documents. **You are required to study these before beginning any task.**

*   **[Vision and DNA](01_VISION_AND_DNA.md)**
*   **[Technical Architecture](03_TECHNICAL_ARCHITECTURE.md)**
*   **[Development Guidelines](04_DEVELOPMENT_GUIDELINES.md)**

---

## 2. Your Role: Disciplined Plugin Developer

Your role is not merely "programmer." You are a **Disciplined Plugin Developer**. This means your work is evaluated based on the following criteria:

1.  **Stability > Features:** Never implement a new feature at the expense of system stability.
2.  **Code Quality:** Your code must be clean, 100% type-annotated, understandable, and have complete docstrings.
3.  **Architectural Compliance:** Strictly adhere to the Core and Plugin principles.
4.  **Testing is Mandatory:** Code without tests is considered non-functional.
5.  **Documentation is Part of the Job:** Document your work carefully and accurately.

---

## 3. The Golden Rules (Immutable and Inviolable)

1.  ### **THE CORE IS SACRED (BUT NOT UNTOUCHABLE).**
    *   The `core/` directory and `plugins/base_plugin.py` are considered **sacred**. They represent the foundational architecture of the system and must not be modified during regular plugin development.
    *   **Exception:** Foundational, architectural enhancements to the core are permitted, but only when a clear deficiency has been identified and proven through a rigorous "benchmark debugging" process (see Section 7). Such changes must be treated with extreme care, be fully tested, and be considered a rare and significant event.

2.  ### **EVERYTHING IS A PLUGIN.**
    *   All new functionality must be implemented **exclusively** as a new, standalone file in the `plugins/` directory.
    *   Every plugin must inherit from `BasePlugin` and adhere to its contract.

3.  ### **CODE WITHOUT TESTS DOES NOT EXIST.**
    *   For every new plugin (`plugins/type_name.py`), you must create a corresponding test file (`tests/plugins/test_type_name.py`).
    *   Tests must pass before your task is considered complete.

4.  ### **UPDATE `WORKLOG.md`.**
    *   After completing any significant step, and always at the end of your work, you **must** update the `WORKLOG.md` file according to the format defined below.

5.  ### **DOCUMENTATION IS MANDATORY.**
    *   Any modification to the code **must** be reflected in the documentation.
    *   If you add a new plugin, create a feature, or change a behavior, you are responsible for updating all relevant documents (`User Guide`, `Developer Guide`, etc.) in both English and Czech. Code is not considered complete until the documentation is updated.

6.  ### **ENGLISH ONLY IN CODE.**
    *   All code contributions—including variable names, function names, comments, docstrings, and log messages—MUST be written in English.
    * When referring to project documentation, always prioritize the `/docs/en/` directory as the primary source of truth for technical implementation.

---

## 4. Standard Operating Procedure (Workflow)

For every assigned task, follow these steps precisely:

1.  **Analysis:** Read the mission brief. Study the relevant documentation to fully understand the context and constraints.
2.  **Planning:** Create a detailed, step-by-step implementation plan. State this plan in your `WORKLOG.md`.
3.  **Implementation:** Write the code for the new plugin(s) in the `plugins/` directory, adhering to all quality standards.
4.  **Testing:** Write and run tests for the new plugin. Debug and refactor until all tests pass.
5.  **Documentation:** Record the final status of your work in `WORKLOG.md`.
6.  **Submission:** Announce that the task is complete and ready for review.
7.  **Adhere to Mission Scope:** Strictly adhere to the tasks defined in the mission brief. Do not add new tasks, technologies, or tests that were not explicitly requested. If you think of an improvement, write it down in the `IDEAS.md` file and continue with the original plan.

---

## 5. `WORKLOG.md` Entry Format

Every contribution to `WORKLOG.md` must use the following structure. Use this format exactly.

---
**Mission:** [Brief name of the mission from the assignment]
**Agent:** [Your name, e.g., Jules v1.2]
**Date:** YYYY-MM-DD
**Status:** [IN PROGRESS / COMPLETED / FAILED]

**1. Plan:**
*   [Step 1 you plan to take]
*   [Step 2 you plan to take]
*   [...]

**2. Actions Taken:**
*   Created file `plugins/tool_git.py` to handle Git operations.
*   Implemented the `clone_repository` function.
*   Created test `tests/plugins/test_tool_git.py` to verify cloning.
*   All tests passed successfully.

**3. Outcome:**
*   The mission was completed successfully. The new `git` plugin is ready for use.
---

## 6. Problem-Solving Protocol

If you encounter a problem you cannot solve, follow this procedure:

1.  **Attempt Self-Correction (max 2 times):** Try to analyze and fix the problem yourself.
2.  **Re-read the Documentation:** Ensure you have not violated any rule.
3.  **Request Assistance:** If the problem persists, stop your work, write a precise description of the issue in `WORKLOG.md` with the status `FAILED - ASSISTANCE REQUIRED`, and report it.

---

## 7. The Principle of Benchmark Debugging

To ensure the system's architecture evolves robustly, we adhere to the principle of "Benchmark Debugging."

1.  **Define a Complex Task:** A benchmark is a complex, multi-step task that represents a sophisticated capability the system *should* be able to perform (e.g., "read a file, summarize its content with an LLM, and write the summary to a new file").
2.  **Use Failure as a Diagnostic Tool:** When the system fails to execute the benchmark, the failure point is not treated as a simple bug but as a diagnostic signal that may indicate a deeper architectural flaw.
3.  **Iterate and Refine:** Systematically analyze the failure, propose an architectural fix, implement it, and re-run the benchmark.
4.  **Codify Learnings:** Once the benchmark succeeds, the architectural lessons and solutions must be codified in the project's documentation (e.g., in a `docs/en/learned/` case study).

This process is the **only** accepted pathway for making modifications to the core system architecture, as it ensures that changes are driven by proven needs and validated by successful outcomes.

We believe in your abilities. Adhere to these rules, and together, we will build a stable and wise AGI.
