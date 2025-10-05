# Proposal: Hierarchical Task Decomposition System

## 1. Problem Statement

The current agent architecture struggles with complex, multi-step tasks due to the inherent context window limitations of Large Language Models (LLMs). As the number of interactions and tool outputs grows, the agent loses track of the original goal, leading to errors, loops, and incomplete work. This prevents the agent from being truly autonomous on sophisticated software engineering tasks.

## 2. Research Findings

Research into advanced agent architectures, particularly the "Hierarchical LLM-Based Agents" model, reveals a robust solution to this problem. The key principles are:

*   **Hierarchical Decomposition:** Instead of a single, monolithic thought process, a high-level "manager" agent breaks down a complex goal into a tree of smaller, logically connected sub-tasks.
*   **Specialized Execution:** A "worker" agent (or the same agent adopting a "worker" persona) executes each sub-task in isolation. This is the most critical aspect for managing context. By focusing on a single, well-defined sub-task, the context provided to the LLM is minimal, relevant, and fits comfortably within the token limit.
*   **Stateful Task Management:** The system relies on a set of tools to manage the lifecycle of these tasks (create, update status, fetch the next one). This creates a structured workflow that the agent can follow reliably.
*   **Dependency Management:** The system understands the relationships between tasks. A parent task cannot be started until its children (sub-tasks) are all complete. This ensures a logical and orderly execution flow.

## 3. Proposed Design

To implement this system, I propose a new workflow driven by a smarter toolset and clearer instructions for the agent. This design is simpler and more robust than my previous failed attempt at a two-phase orchestrator.

### Core Idea: Agent-Driven Execution

Instead of a complex, hard-coded state machine in the orchestrator, we will empower the agent to drive its own planning and execution cycle. The orchestrator will remain a simple, single-loop processor, while the agent's "intelligence" will be guided by a clear set of instructions and a powerful new tool.

### Key Components:

**1. New System Prompt:**
The `system_prompt.txt` will be updated to instruct the agent to follow this new workflow:
    *   **Phase 1: Plan.** Analyze the user's request and create a comprehensive, hierarchical plan using the `create_task` tool. The agent should be instructed to be as detailed as possible.
    *   **Phase 2: Execute.** After planning, the agent should enter an execution loop. In each step of the loop, it must:
        a. Call the `get_next_executable_task()` tool to find the next available task.
        b. Focus exclusively on completing that single task.
        c. Upon completion, call `update_task_status` with the task's ID and the result (`completed` or `failed`).
        d. Repeat this cycle until no more executable tasks are available.
    *   **Phase 3: Complete.** Once the execution loop is finished, the agent should call `task_complete` to signal the end of the mission.

**2. A Smarter Planning Tool:**
The `mcp_servers/planning_server.py` will be modified to include a single, powerful new tool that simplifies the agent's workflow:
*   **`get_next_executable_task()`**: This tool encapsulates the complex logic of determining what to do next. It will scan the `TASK_DATABASE` and find the first task that is in the `'new'` state **and** for which all its sub-tasks are marked as `'completed'`. This is the core of the dependency management. It frees the agent from having to reason about the complex task tree and dependencies on its own.

**3. No Orchestrator Changes Needed:**
Crucially, with this design, the `core/orchestrator.py` can remain in its simple, stable, single-loop form. The complexity is shifted from hard-coded logic to the agent's reasoning, guided by the prompt and the powerful `get_next_executable_task` tool. This is a much more flexible and robust approach.

## 4. Implementation Steps (for the next task)

1.  **Modify `mcp_servers/planning_server.py`:**
    *   Remove the `planning_complete` and `get_next_task` functions.
    *   Implement the new `get_next_executable_task` function with the dependency-checking logic.
    *   Update the `tools` dictionary to register the new tool and remove the old ones.
2.  **Update `prompts/system_prompt.txt`:**
    *   Rewrite the "STRATEGICKÝ PRACOVNÍ POSTUP" section to clearly explain the new Plan -> Execute loop using `get_next_executable_task`.
3.  **Testing:**
    *   Update `tests/test_planning_tools.py` to test the new `get_next_executable_task` logic thoroughly.

This approach provides a clear, robust, and achievable path to implementing a true hierarchical planning system, solving the context window problem and significantly upgrading the agent's capabilities.