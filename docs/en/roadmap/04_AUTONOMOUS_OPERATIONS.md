# Roadmap 04: Autonomous Operations

**Phase Goal:** To achieve the project's ultimate vision: enabling Sophia to manage her own development lifecycle. This phase involves creating a master cognitive plugin that leverages all previously developed tools and analytical capabilities to delegate tasks, review results, and integrate new functionality into her own system.

The detailed implementation plan for this phase is the final frontier and will be created upon the successful completion of the Self-Analysis Framework.

---

### Implementation Guide: Dynamic Cognitive Engine V3

**Author:** Gemini & Robert Kajzer
**Date:** October 30, 2025
**Objective:** To enhance Sophia's cognitive core with hierarchical planning, dynamic replanning, and internal "thinking" capabilities, leading to a more robust and truly adaptive agent.

This guide details the transition from the current architecture, which executes a predetermined plan from start to finish, to a more advanced model built on three pillars.

#### 1. Key Concepts and Philosophy

**A. Hierarchical Planning**

Instead of a single, monolithic list of steps, the system will operate with a hierarchy. It will maintain awareness of the main goal (e.g., "analyze and report project status") while focusing on executing a sub-plan (e.g., "step 1: list files, step 2: read file X"). This allows for targeted correction of small failures without losing the overall context.

**B. Dynamic Replanning**

The executor (Kernel) becomes smarter. Instead of blindly executing a plan, it now proceeds step-by-step. After each step, it analyzes the result. If a step fails or returns an unexpected output, the Executor immediately stops, discards the invalid sub-plan, and requests a new sub-plan from the Planner to achieve the main goal, taking the new situation (including the error information) into account.

**C. Internal Monologue**

Sophia learns that she does not need to call an external tool for every operation. She realizes she can use her own "brain" (`tool_llm`) as one of the steps in a plan. This allows her to perform data transformations, summarizations, or any other language operations "in her head" as part of a more complex task.

#### 2. Architectural Changes

Most changes will occur in the heart of the system—`core/kernel.py`—and in how we work with context and plans.

**2.1. Extending `SharedContext` (`core/context.py`)**

The current `SharedContext` is excellent for a single cycle, but to maintain a long-term goal, we need to extend it slightly. We need to separate the main goal from the currently executing plan.

*   `main_goal: Optional[str] = None`
*   `current_plan: Optional[List[Dict]] = None`

*Note: Alternatively, `main_goal` can remain in `user_input`, and `current_plan` can replace the existing `payload['plan']`.*

**2.2. Refactoring the Executor (`consciousness_loop` in `core/kernel.py`)**

The main loop will no longer iterate through all steps of a plan. Its logic will be simplified to a "single-step cycle":

1.  **Get Goal:** At the beginning of the cycle (if there is no `main_goal`), get input from the user and set it as the `main_goal`.
2.  **Plan (if needed):** If `current_plan` is empty but `main_goal` exists, call the `cognitive_planner` to create a new plan to achieve the goal.
3.  **Execute One Step:** Take only the first step from `current_plan`.
4.  **Validate and Repair Arguments:** Perform the existing "Validation & Repair Loop" for this single step.
5.  **Run Tool:** Call the appropriate tool (e.g., `tool_file_system.read_file`).
6.  **Analyze Result:** Check the outcome of the step.
    *   **SUCCESS:** Write the result to `step_outputs` (as before), remove the executed step from `current_plan` (`current_plan.pop(0)`), and continue to the next iteration of the loop.
    *   **FAILURE:**
        *   Write the failure information to `history` (e.g., "Step 'read_file' failed: File not found.").
        *   Clear the entire `current_plan`.
        *   The loop returns to the beginning, where it will re-invoke the Planner in step 2 to create a new plan, taking the new error information in `history` into account.

#### 3. Implementation Guide (Mission for Jules)

This is a step-by-step plan for implementing the Dynamic Cognitive Engine.

**Mission:** Implementation of Hierarchical and Dynamic Planning (V3)
**Agent:** Jules
**Status:** READY

1.  **Implementation Plan:**
    *   **Step 1: Update Data Structure**
        *   In `core/context.py`, modify `SharedContext` to better represent `main_goal` and `current_plan`.
    *   **Step 2: Refactor `consciousness_loop` to a Single-Step Cycle**
        *   In `core/kernel.py`, rewrite the `EXECUTING` phase. Instead of `for step in plan:`, use logic that processes only `plan[0]`.
        *   Ensure the rest of the loop (like Validation & Repair) works with this single step.
    *   **Step 3: Implement the Replanning Loop**
        *   Add logic to the `consciousness_loop` to detect an error after a step is executed (e.g., by checking a `try...except` block or a return value).
        *   In case of an error, implement the logic to:
            *   Write the error to `context.history`.
            *   Clear `context.current_plan`.
            *   Let the loop continue naturally, which will automatically trigger the `cognitive_planner` in the next iteration.
    *   **Step 4: Enhance the Planner Prompt**
        *   Modify the `config/prompts/planner_prompt_template.txt` file.
        *   Add instructions that explicitly encourage the LLM to use `tool_llm.execute` for tasks like formatting, summarization, or data transformation if no other specific tool exists.
        *   Add an example showing `tool_llm` as an intermediate step.
    *   **Step 5: Verify with a Benchmark**
        *   Create a new test scenario (benchmark) that verifies all new capabilities at once.
        *   **Scenario:** "List the contents of the `/` directory, take this list, reformat it using the LLM into a numbered list, and then try to write the result to the file `/non_existent_dir/output.txt`."
        *   **Expected Behavior:**
            1.  Sophia creates a plan: `list_directory` -> `tool_llm.execute` -> `write_file`.
            2.  `list_directory` and `tool_llm.execute` succeed.
            3.  `write_file` fails because the directory does not exist.
            4.  The Kernel records the error and triggers replanning.
            5.  The Planner creates a new plan, which might look like: "Create the directory `/non_existent_dir`" and then "Write the result to `/non_existent_dir/output.txt`."
            6.  The new plan is completed successfully.

#### 4. Expected Outcome

*   Sophia is able to solve complex, multi-step tasks that require both external tools and internal "thought" steps.
*   Sophia can recover from errors during step execution without losing awareness of the main goal and can adaptively create a new plan to achieve it.
*   The architecture is prepared for future extensions with even more advanced Hierarchical Task Networks (HTN).

---

### Key Objectives:

1.  **Task Planning & Delegation Plugin (`cognitive_overseer`):**
    *   **Purpose:** The master plugin that orchestrates Sophia's autonomous development.
    *   **Core Capabilities:**
        *   `formulate_plan`: Analyze a high-level goal (e.g., from `roberts-notes.txt`) and create a detailed, step-by-step implementation plan.
        *   `delegate_task`: Interface with an external AI programmer API (the "Jules API") to assign a specific, well-defined coding task.
        *   `monitor_progress`: Periodically check the status of the delegated task.

2.  **Code Review & Verification Plugin (`cognitive_quality_assurance`):**
    *   **Purpose:** Allow Sophia to review and verify the code produced by the external AI programmer.
    *   **Core Capabilities:**
        *   `review_code_changes`: Use self-analysis tools to ensure the new code adheres to all development guidelines.
        *   `run_verification_tests`: Execute the tests associated with the new code to confirm functionality.
        *   `provide_feedback`: Request revisions from the external programmer if the code is not satisfactory.

3.  **Integration & Deployment Plugin (`cognitive_integrator`):**
    *   **Purpose:** Enable Sophia to safely integrate and deploy the approved new code into her own system.
    *   **Core Capabilities:**
        *   `merge_code`: Use the Git plugin to merge the new feature branch into `develop`.
        *   `update_documentation`: Automatically update `PROJECT_STRUCTURE.md` and other relevant documents.
        *   `trigger_reload`: Instruct the Kernel to reload the plugin registry to activate the new functionality.

---

**Success Criteria:** The project lead can write a single line in `roberts-notes.txt`, such as: "Create a plugin that can translate text using an external API." Sophia, on her own initiative, can then plan the task, delegate the coding to an external agent, review the code, approve it, and integrate the new, functional translation plugin into her system without any further human intervention.
