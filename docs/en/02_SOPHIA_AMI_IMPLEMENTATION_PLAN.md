# Sophia AMI 1.0: Detailed Implementation Roadmap

## Introduction

This document provides a detailed, technical, and phased implementation plan for transforming Sophia from a reactive tool into a proactive, autonomous agent based on the vision outlined in `docs/01_SOPHIA AMI 1.0.md`.

The plan is divided into five strategic phases. Each phase is broken down into manageable, self-contained tasks designed to be achievable within a single development session. Each task includes a clear objective, a list of affected files, a step-by-step action plan, and technical notes based on current best practices and research.

## Phase 1: Activation of the "Cognitive Loop" (Proactive 24/7 Operation)

**Objective:** To switch Sophia from a reactive, command-driven mode to a fully autonomous, 24/7 running daemon built upon its existing event-driven architecture. This phase introduces the core heartbeat and a mechanism for continuous learning from external notes.

---

### Task 1.1: Refactor `run.py` for Continuous Operation

*   **Objective:** Simplify the application entry point to exclusively launch the Kernel in a persistent, event-driven mode.
*   **Affected Files:**
    *   `run.py`
*   **Action Plan:**
    1.  Remove all command-line argument parsing logic (`argparse`) related to reactive execution (`--once`, `--no-webui`, etc.).
    2.  The `async def main()` function in `run.py` will be streamlined to perform two actions:
        *   Initialize the `Kernel`.
        *   Start the main, non-terminating event loop by calling a new method, e.g., `await kernel.run_autonomous_mode()`.
*   **Technical Notes:**
    *   This change establishes the event loop in `core/event_loop.py` as the sole and default mode of operation, simplifying the architecture.

---

### Task 1.2: Decouple User Input via an Event Bus

*   **Objective:** Reroute all external inputs, such as those from the WebUI, through the central event bus to standardize input processing.
*   **Affected Files:**
    *   `plugins/interface_webui.py`
    *   `core/event_bus.py` (if not already fully implemented)
    *   `core/kernel.py`
*   **Action Plan:**
    1.  Modify the FastAPI endpoints in `interface_webui.py` (e.g., `/chat`). These endpoints must **no longer** call Kernel methods directly.
    2.  Instead, they will publish an event, for example: `event_bus.publish(Event(EventType.USER_INPUT_RECEIVED, data={'source': 'webui', 'text': ...}))`.
    3.  The `Kernel` will subscribe to the `USER_INPUT_RECEIVED` event and trigger the appropriate processing workflow.
*   **Technical Notes:**
    *   This decouples the input interfaces from the core logic, allowing for multiple, independent sources of input in the future (e.g., Slack, email).
    *   An `asyncio.Queue` is a suitable and simple implementation for the event bus if a more complex one is not already in place.

---

### Task 1.3: Implement the Proactive Heartbeat & Idea Ingestion

*   **Objective:** Create a recurring trigger for proactive tasks and integrate a file watcher to process new ideas from `roberts-notes.txt`.
*   **Affected Files:**
    *   `core/event_loop.py`
    *   **New Plugin:** `plugins/core_proactive_agent.py`
*   **Action Plan:**
    1.  In the main loop of `core/event_loop.py`, add a periodic timer (e.g., `asyncio.sleep(60)`).
    2.  On each timer tick, publish a `PROACTIVE_HEARTBEAT` event.
    3.  Create a new plugin, `core_proactive_agent.py`. This plugin will be responsible for orchestrating autonomous activities.
    4.  The plugin will subscribe to `PROACTIVE_HEARTBEAT`.
    5.  Upon receiving the heartbeat, the plugin will:
        *   Check for modifications to `docs/roberts-notes.txt`.
        *   If the file has changed, it will read the new content, publish a `NEW_IDEA_DETECTED` event with the content, and trigger a planning sequence to analyze and schedule the idea.
*   **Technical Notes:**
    *   For file watching, the `watchdog` library provides a robust, cross-platform, event-based API that can be integrated with `asyncio` via `loop.run_in_executor`. This is more efficient than polling `os.path.getmtime`.
    *   The proactive agent acts as a central hub for autonomous behavior, keeping the main event loop clean and simple.

---

### Task 1.4: Activate the Sleep Scheduler

*   **Objective:** Enable Sophia to enter a low-activity "sleep" state to perform memory consolidation and self-reflection tasks.
*   **Affected Files:**
    *   `plugins/core_sleep_scheduler.py`
*   **Action Plan:**
    1.  The existing `core_sleep_scheduler.py` plugin will subscribe to the `PROACTIVE_HEARTBEAT` event.
    2.  Upon receiving the event, it will check conditions for sleep (e.g., time of day, no user activity for X minutes) based on a configuration file (e.g., `config/autonomy.yaml`).
    3.  If conditions are met, it will publish a `DREAM_TRIGGER` event, signaling the start of the sleep cycle.
*   **Technical Notes:**
    *   This re-activates existing functionality (as per Mission #13) and integrates it into the new autonomous loop.

## Phase 2: Implementation of the Intelligent Hybrid Router

**Objective:** To build the core of Sophia's operational efficiency by enabling autonomous management and selection of local and cloud-based LLM providers.

---

### Task 2.1: Enhance the Router for Provider Awareness

*   **Objective:** Upgrade the `CognitiveTaskRouter` to select not just a model, but the correct *provider* (and thus, the correct tool plugin) for a given task.
*   **Affected Files:**
    *   `plugins/cognitive_task_router.py`
    *   `config/model_strategy.yaml`
*   **Action Plan:**
    1.  Extend the `config/model_strategy.yaml` schema. Each model entry must now include a `provider` key (e.g., `provider: 'openrouter'` or `provider: 'ollama'`).
    2.  Modify the router's logic. After selecting a model for a task, it must read the `provider` key.
    3.  Based on the provider, the router will format the `tool_call` to target the appropriate plugin:
        *   `openrouter` -> `tool_llm.execute(...)`
        *   `ollama` -> `tool_local_llm.execute(...)` (assuming this plugin exists).
*   **Technical Notes:**
    *   This makes the router the central decision-making point for LLM execution, abstracting the choice of provider from other plugins.

---

### Task 2.2: Create the `ModelManager` Plugin

*   **Objective:** Empower Sophia to manage its own local LLM environment using a dedicated tool plugin.
*   **Affected Files:**
    *   **New Plugin:** `plugins/tool_model_manager.py`
    *   `plugins/tool_bash.py` (as a dependency)
*   **Action Plan:**
    1.  Create the new `tool_model_manager.py` plugin.
    2.  Implement the following methods, which will internally use `tool_bash.execute` to interact with the `ollama` CLI:
        *   `list_local_models()`: Executes `ollama list`, parses the output, and returns a structured list (e.g., JSON).
        *   `pull_local_model(model_name: str)`: Executes `ollama pull [model_name]`, streaming the output.
        *   `get_model_info(model_name: str)`: Executes `ollama show --json [model_name]` and returns the parsed JSON info.
*   **Technical Notes:**
    *   This plugin provides a crucial layer of abstraction. Other plugins can now manage models without needing to know the specific shell commands, making the system more modular and robust.

---

### Task 2.3: Implement Self-Configuration of Models

*   **Objective:** Allow Sophia to autonomously update its own model strategy configuration.
*   **Affected Files:**
    *   `plugins/tool_model_manager.py`
    *   `plugins/tool_file_system.py` (as a dependency)
*   **Action Plan:**
    1.  Add a new method to `tool_model_manager.py`: `add_model_to_strategy(task_type: str, model_name: str, provider: str, size: str)`.
    2.  This method will use `tool_file_system.read_file` to load `config/model_strategy.yaml`.
    3.  It will then programmatically add the new model configuration under the specified `task_type`.
    4.  Finally, it will use `tool_file_system.write_file` to save the updated configuration.
*   **Technical Notes:**
    *   Using a library like `PyYAML` is essential for safe and reliable modification of YAML files, preserving comments and structure where possible. This method gives Sophia a powerful self-configuration capability.

## Phase 3: The "Self-Tuning Framework" (Autonomous Growth)

**Objective:** To establish a complete feedback loop where Sophia can dream, reflect on its failures, formulate hypotheses for improvement, and automatically implement and test those improvements.

---

### Task 3.1: Activate the Memory Consolidator ("Dreaming")

*   **Objective:** Trigger the existing memory consolidation logic as the first step in the "sleep" cycle.
*   **Affected Files:**
    *   `plugins/cognitive_memory_consolidator.py`
*   **Action Plan:**
    1.  The `cognitive_memory_consolidator.py` plugin will subscribe to the `DREAM_TRIGGER` event (published by the Sleep Scheduler in Task 1.4).
    2.  Upon receiving the event, it will execute its existing logic for memory consolidation (e.g., summarizing recent events, moving data from operational memory to long-term semantic memory).
    3.  Once completed, it will publish a `DREAM_COMPLETE` event to signal the start of the next phase: reflection.
*   **Technical Notes:**
    *   This formally integrates the "dreaming" concept into the autonomous loop, making it a prerequisite for self-reflection.

---

### Task 3.2: Create the `CognitiveReflection` Plugin

*   **Objective:** Develop a plugin that analyzes past failures and generates concrete, testable hypotheses for how to improve.
*   **Affected Files:**
    *   **New Plugin:** `plugins/cognitive_reflection.py`
    *   `plugins/memory_sqlite.py`
*   **Action Plan:**
    1.  Create the new `cognitive_reflection.py` plugin. It will subscribe to the `DREAM_COMPLETE` event.
    2.  Upon activation, it will use `memory_sqlite.py` to query the operational tracking database for all operations where `success = False`.
    3.  For each failure, it will use a powerful "Planner" LLM to analyze the context, logs, and user request.
    4.  The goal of the analysis is to generate a **hypothesis** for the root cause (e.g., "Hypothesis H1: The docstring for `fs.write` is ambiguous for smaller models. Adding a JSON example would improve clarity.").
    5.  The generated hypothesis will be stored in a new `hypotheses` table in the SQLite database and a `HYPOTHESIS_CREATED` event will be published.
*   **Technical Notes:**
    *   This is the analytical core of the self-tuning loop. The quality of the hypotheses is critical, so using the most capable LLM available is recommended for this step.

---

### Task 3.3: Create the `CognitiveSelfTuning` Plugin

*   **Objective:** To act on a hypothesis by modifying the codebase in a safe, sandboxed environment, testing the change, and creating a pull request if the change is beneficial.
*   **Affected Files:**
    *   **New Plugin:** `plugins/cognitive_self_tuning.py`
    *   `plugins/tool_code_reader.py` (dependency)
    *   `plugins/tool_git.py` (dependency, may need creation/enhancement)
    *   `plugins/tool_model_evaluator.py` (dependency)
*   **Action Plan:**
    1.  Create the new `cognitive_self_tuning.py` plugin, which subscribes to `HYPOTHESIS_CREATED`.
    2.  **Code Modification:**
        *   It reads the hypothesis (e.g., H1).
        *   It uses `tool_code_reader.py` to fetch the relevant file (e.g., `plugins/tool_file_system.py`).
        *   It uses an "Expert" cloud model to generate the code modification based on the hypothesis.
        *   It writes the modified code to a sandboxed location, e.g., `sandbox/tuning/v1/tool_file_system.py`.
    3.  **Sandboxed Evaluation:**
        *   It uses `tool_model_evaluator.py` to run a benchmark. This evaluator must be enhanced to dynamically load and test the sandboxed version of the plugin against a "Workhorse" (e.g., 8B local) model.
    4.  **Deployment via Git:**
        *   If the benchmark shows a clear improvement, the plugin will use a `tool_git.py` to:
            *   Create a new branch (e.g., `feature/sophia-tuning-h1`).
            *   Commit the change from the sandbox.
            *   Push the branch to the remote repository.
            *   Create a pull request into a dedicated branch (e.g., `master-sophia`), as defined in `config/autonomy.yaml`.
*   **Technical Notes:**
    *   The `GitTool` will likely need to be created or significantly enhanced, using a library like `GitPython` to provide a robust API for git operations.
    *   Dynamically loading the sandboxed module for testing is a critical step. `importlib` can be used to achieve this by manipulating `sys.path`.

## Phase 4: Advanced Insight (Graph RAG & ACI)

**Objective:** To provide Sophia with a deeper, structural understanding of her own codebase and to implement a holistic quality benchmark (ACI).

---

### Task 4.1: Create the `Neo4jTool` Plugin

*   **Objective:** Create a dedicated tool for interacting with a Neo4j graph database.
*   **Affected Files:**
    *   **New Plugin:** `plugins/tool_neo4j.py`
*   **Action Plan:**
    1.  Create the `tool_neo4j.py` plugin.
    2.  It will use the official `neo4j` Python driver.
    3.  Implement core methods:
        *   `execute_query(query: str, parameters: dict)`: Runs a Cypher query against the database.
        *   `add_node(label: str, properties: dict)`
        *   `add_relationship(source_node_id: int, target_node_id: int, rel_type: str, properties: dict)`
*   **Technical Notes:**
    *   Connection details (URI, user, password) should be managed via `config/settings.yaml`. The plugin should handle connection pooling and session management.

---

### Task 4.2: Create the `CognitiveGraphRAG` Plugin (Indexer)

*   **Objective:** To parse the entire Python codebase and represent it as a knowledge graph in Neo4j.
*   **Affected Files:**
    *   **New Plugin:** `plugins/cognitive_graph_rag.py`
    *   `plugins/tool_code_reader.py` (dependency)
    *   `plugins/tool_neo4j.py` (dependency)
*   **Action Plan:**
    1.  Create the `cognitive_graph_rag.py` plugin. It will subscribe to the `DREAM_TRIGGER` event to perform periodic re-indexing.
    2.  Use `tool_code_reader.py` to list and read all `*.py` files in the project.
    3.  For each file, use Python's built-in `ast` (Abstract Syntax Tree) module to parse the code into a tree structure.
    4.  Traverse the AST to identify nodes like classes, functions, method calls, and imports.
    5.  Use `tool_neo4j.py` to populate the graph with nodes and relationships, such as:
        *   `(Class)-[:HAS_METHOD]->(Method)`
        *   `(Method)-[:CALLS_METHOD]->(Method)`
        *   `(Module)-[:IMPORTS]->(Module)`
*   **Technical Notes:**
    *   The `ast` module is a powerful and safe way to analyze Python code without executing it. This task is complex and requires a good understanding of the AST structure.

---

### Task 4.3: Implement `analyze_code_structure` (Query Tool)

*   **Objective:** Expose the knowledge graph as a powerful new tool for Sophia to use.
*   **Affected Files:**
    *   `plugins/cognitive_graph_rag.py`
*   **Action Plan:**
    1.  Add a new tool method to `cognitive_graph_rag.py`: `analyze_code_structure(query: str) -> str`.
    2.  This method will take a natural language query (e.g., "Which plugins call the `tool_bash.execute` method?").
    3.  It will use an LLM to translate the natural language query into a formal Cypher query for Neo4j.
    4.  It will execute the Cypher query using `tool_neo4j.py`.
    5.  It will format the results into a human-readable summary and return it.
*   **Technical Notes:**
    *   This technique is known as Text-to-Cypher and is a powerful application of LLMs for interacting with structured data.

---

### Task 4.4: Implement the Holistic Benchmark (ACI)

*   **Objective:** Integrate a final quality check into the self-tuning process that evaluates changes against Sophia's core DNA principles.
*   **Affected Files:**
    *   `plugins/cognitive_self_tuning.py`
    *   `plugins/tool_model_evaluator.py`
    *   `config/prompts/sophia_dna.txt`
*   **Action Plan:**
    1.  Add a new method to `tool_model_evaluator.py`: `evaluate_holistic_quality(code_change_summary: str) -> dict`.
    2.  This method will take the summary of a proposed change and the content of `sophia_dna.txt`.
    3.  It will send this information to an "Expert" cloud model with a prompt asking it to score the change on core principles (e.g., Empathy, Growth, Ethics, Self-Awareness).
    4.  The `cognitive_self_tuning.py` plugin will call this method *after* a technical benchmark passes.
    5.  A Pull Request will only be created if both the technical benchmark and the ACI score are acceptable. The ACI score will be included in the PR description.
*   **Technical Notes:**
    *   The ACI (Autonomous Cognitive Index) score is a qualitative measure. The prompt design is crucial for getting meaningful and consistent results.

## Phase 5: The "Phoenix Protocol" (Autonomous Recovery)

**Objective:** To build a robust, external watchdog system that can recover Sophia from a critical failure, allowing her to learn from her own fatal mistakes.

---

### Task 5.1: Create the External `guardian.py` Script

*   **Objective:** Develop a simple, standalone Python script to act as a process supervisor for the main Sophia application.
*   **Affected Files:**
    *   **New Script:** `guardian.py` (at the project root)
*   **Action Plan:**
    1.  Create `guardian.py`. This script will **not** be a plugin and will have minimal dependencies.
    2.  Its primary function is to launch the main application (`python run.py`) as a subprocess using `subprocess.Popen`.
    3.  It must capture the `stdout` and `stderr` of the child process in real-time and stream them to both its own console and a combined log file (e.g., `logs/guardian.log`).
*   **Technical Notes:**
    *   Using `subprocess.Popen` with `stdout=subprocess.PIPE` and `stderr=subprocess.PIPE` allows for non-blocking, real-time log monitoring. A library like `psutil` can be used to monitor the health of the child process more deeply.

---

### Task 5.2: Implement Crash Detection and Recovery Logging

*   **Objective:** Enable the guardian to detect when the main application has crashed and to log the specific error that caused it.
*   **Action Plan:**
    1.  The main loop in `guardian.py` will periodically check `process.poll()`. A non-None value indicates the process has terminated.
    2.  If the exit code is non-zero (indicating a crash):
        *   The guardian will read any remaining output from `stderr`.
        *   It will save this final error output to a timestamped crash log file (e.g., `logs/crash_20251105_093000.log`).
        *   It will then restart the application, passing the path to this crash log as a command-line argument: `python run.py --recover-from-crash logs/crash_...log`.
*   **Technical Notes:**
    *   This creates a closed loop where the crash information is preserved and immediately fed back into the system upon restart.

---

### Task 5.3: Implement Recovery Logic in the Kernel

*   **Objective:** Allow the Kernel to recognize when it's being started in a recovery mode and to use the crash log to initiate self-reflection.
*   **Affected Files:**
    *   `core/kernel.py`
    *   `plugins/cognitive_reflection.py`
*   **Action Plan:**
    1.  In `kernel.initialize()` (or a similar startup method), add logic to check `sys.argv` for the `--recover-from-crash` flag.
    2.  If the flag is present, the Kernel will read the specified log file.
    3.  It will then publish a special `SYSTEM_RECOVERY` event, with the content of the crash log as the payload.
    4.  The `cognitive_reflection.py` plugin (from Phase 3) will subscribe to this event. Upon receiving it, it will immediately create a high-priority hypothesis to address the fatal error.
*   **Technical Notes:**
    *   This gives Sophia a "memory" of her own demise, turning a critical failure into a high-priority learning opportunity.

---

### Task 5.4: Implement the Destructive Failure Rollback

*   **Objective:** Create a final safety net where the guardian can automatically revert a bad code change if it causes repeated, rapid crashes.
*   **Action Plan:**
    1.  The `guardian.py` script will maintain a crash counter (e.g., number of crashes within a 5-minute window).
    2.  If this counter exceeds a threshold (e.g., 5 crashes), it indicates a destructive feedback loop.
    3.  The guardian will then execute a rollback command using `subprocess.run`:
        *   `git reset --hard HEAD~1` (on the branch specified in `config/autonomy.yaml`, e.g., `master-sophia`).
    4.  After the rollback, it will restart Sophia one last time, again with the `--recover-from-crash` flag, feeding it the log from the *first* crash in the series.
*   **Technical Notes:**
    *   This is the ultimate recovery mechanism. The older, stable version of Sophia is brought back online and is immediately informed of the mistake its "future self" made, allowing it to analyze and potentially fix the issue without repeating the error.
