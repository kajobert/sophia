# Architecture: Stateful Mission-Driven Core

This document describes the current technical architecture of the project, which is based on a stateful, mission-driven model. This design enhances the agent's ability to handle complex, multi-step tasks by maintaining a clear state and context throughout the mission lifecycle.

## Key Principles

1.  **Stateful Mission Management:** A central `MissionManager` maintains the entire state of the user's high-level goal (the "mission"), including the overall plan and progress.
2.  **Clear Separation of Roles:** The architecture is divided into three distinct layers of responsibility:
    *   **Project Manager (`MissionManager`):** Understands the "why." Owns the overall goal, creates the plan, and tracks its execution.
    *   **Task Dispatcher (`ConversationalManager`):** Understands the "what." Manages the execution of a single task from the plan. It is stateless regarding the overall mission.
    *   **Focused Specialist (`WorkerOrchestrator`):** Understands the "how." Executes the specific, low-level actions required to complete one task, using tools and reasoning.
3.  **Asynchronous and Modular:** The system remains fully asynchronous, and tools are modularized in MCP servers.

## Core Components

The following diagram illustrates the information flow between the core components:

```
+--------------+   (1) User Prompt   +--------------------+   (2) Create Plan &   +-------------------------+   (4) Execute Task   +--------------------+
|              | ----------------> |                    | ----------------->  |                         | -------------------> |                    |
| TUI (app.py) |                   |  MissionManager    | (using PlanningServer)| ConversationalManager   |                      | WorkerOrchestrator |
|              | <---------------- |  (Project Manager) | <-----------------  | (Task Dispatcher)       | <------------------- | (Focused Specialist)|
+--------------+   (6) Final Rsp   +--------------------+   (3) Dispatch Task   +-------------------------+   (5) Task Result    +--------------------+
                                           |                                                                        |
                                           | (Manages overall mission state)                                        | (Executes steps using tools)
                                           |                                                                        |
                                           v                                                                        v
                                 +---------------------+                                                  +---------------------+
                                 |                     |                                                  |                     |
                                 | Planning &          |                                                  |   All Other MCP     |
                                 | Reflection Servers  |                                                  |   Servers (Tools)   |
                                 +---------------------+                                                  +---------------------+
```

### 1. Textual User Interface (TUI)
- **File:** `tui/app.py`
- **Description:** The primary user interface. It captures the initial user prompt and passes it to the `MissionManager` to start a new mission. It displays progress and final results.

### 2. MissionManager (The Project Manager)
- **File:** `core/mission_manager.py`
- **Description:** The new heart of the agent's "brain." It is the **single source of truth for the mission state.**
    - **Initiation:** Receives the high-level prompt from the TUI.
    - **Planning:** Uses the `PlanningServer` to break down the high-level prompt into a concrete, step-by-step plan (a list of sub-tasks).
    - **State Management:** Holds the `mission_prompt`, the list of `sub_tasks`, and the `current_task_index`.
    - **Execution Loop:** Iterates through the plan, dispatching one sub-task at a time to the `ConversationalManager`.
    - **Lifecycle Management:** Determines when the entire mission is complete or has failed. It is the only component that can mark the overall mission as `completed`.
    - **Reflection:** After a mission is complete or has failed, it orchestrates a reflection process to generate learnings for the LTM.

### 3. ConversationalManager (The Task Dispatcher)
- **File:** `core/conversational_manager.py`
- **Description:** Its role has been greatly simplified. It is now a **stateless dispatcher** that focuses on a single task.
    - Receives a specific sub-task description (e.g., "Refactor the `database.py` file to use the new connection pool") and the overall mission goal for context from the `MissionManager`.
    - Determines the appropriate budget for the task.
    - Delegates the execution of this single task to the `WorkerOrchestrator`.
    - Returns the result (e.g., `completed`, `failed`) of that one task back to the `MissionManager`.
    - **It has no knowledge of the overall plan or other sub-tasks.**

### 4. WorkerOrchestrator (The Focused Specialist)
- **File:** `core/orchestrator.py`
- **Description:** The "hands" of the system, focused on execution.
    - Receives a single, well-defined task and the overall mission context from the `ConversationalManager`.
    - Uses its LLM and tools (`MCPClient`) to execute the steps required to complete its given task.
    - **Crucially, it does NOT have a `task_complete` tool.** It can only signal that its own, specific sub-task is complete (using `subtask_complete`), at which point control returns to the `MissionManager`.
    - Its goal is to successfully complete its current sub-task or report a failure if it cannot.

### 5. MCP (Modular Component Protocol) Servers
- **Folder:** `mcp_servers/`
- **Description:** The collection of tools available to the `WorkerOrchestrator`. The `PlanningServer` and `ReflectionServer` are now primarily used by the `MissionManager` to manage the mission lifecycle.

---

This stateful, hierarchical architecture resolves the "mission amnesia" problem by ensuring the agent always has access to the high-level context while working on low-level tasks, creating a more robust and truly autonomous system.