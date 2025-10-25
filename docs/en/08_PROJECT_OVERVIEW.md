# Sophia V2 - Project Overview

This document provides a high-level overview of the Sophia V2 project, its architecture, and its long-term goals. It is intended as a quick reference for the project owner.

## 1. Quick Start Command Reference

Here is a "cheat sheet" of the most common commands for managing the project:

-   **Set up the environment (first time):**
    ```bash
    uv venv && source .venv/bin/activate && uv pip sync requirements.in
    ```

-   **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

-   **Install/update dependencies:**
    ```bash
    uv pip sync requirements.in
    ```

-   **Run the application (Terminal and Web UI):**
    ```bash
    python run.py
    ```

-   **Run the test suite:**
    ```bash
    PYTHONPATH=. .venv/bin/python -m pytest
    ```

-   **Run code quality and formatting checks:**
    ```bash
    pre-commit run --all-files
    ```

## 2. High-Level Architecture & Data Flow

Sophia V2 is built on a modular, asynchronous, core-plugin architecture designed for extensibility.

### 2.1. Core Components

-   **`run.py`:** The main entry point of the application. It initializes and starts the Kernel.
-   **`core/kernel.py`:** The heart of the application. It contains the `consciousness_loop`, which orchestrates the different phases of operation (Listening, Thinking, Responding, Memorizing). It is responsible for loading, configuring, and executing plugins.
-   **`core/plugin_manager.py`:** Discovers and loads all valid plugins from the `plugins/` directory. It categorizes them by type (`INTERFACE`, `TOOL`, `MEMORY`) for the Kernel to use.
-   **`core/context.py`:** Defines the `SharedContext` data object. This object is the lifeblood of the application, passed between the Kernel and plugins in each cycle of the `consciousness_loop`. It carries the user input, conversation history, and a `payload` dictionary for inter-plugin communication.
-   **`plugins/base_plugin.py`:** Defines the abstract `BasePlugin` class, which serves as the contract for all plugins.

### 2.2. Data Flow in a Single Cycle

1.  **LISTENING Phase:**
    - The Kernel's `consciousness_loop` starts.
    - It calls the `execute` method on all `INTERFACE` plugins (e.g., `TerminalInterface`, `WebUIInterface`).
    - These plugins wait for user input (e.g., from the command line or a WebSocket).
    - When input is received, the plugin places it in `context.user_input` and, in the case of the Web UI, adds a `_response_callback` function to `context.payload`.
    - The first interface to receive input completes its task, and the loop moves to the next phase.

2.  **THINKING Phase:**
    - The Kernel iterates through all `TOOL` plugins (e.g., `LLMTool`).
    - The `LLMTool` takes the `context.history` (which now includes the new user input), sends it to the configured LLM, and places the response in `context.payload["llm_response"]`.

3.  **RESPONDING Phase:**
    - The Kernel prints the `llm_response` to the console for the terminal interface.
    - It then checks if a `_response_callback` exists in `context.payload`. If so (i.e., the input came from the Web UI), it calls this function, which sends the response back over the appropriate WebSocket connection.

4.  **MEMORIZING Phase:**
    - The Kernel iterates through all `MEMORY` plugins (e.g., `SQLiteMemory`).
    - The `SQLiteMemory` plugin takes the latest user message and AI response from `context.history` and saves them to the database.

5.  **Cleanup:**
    - The `context` is reset for the next cycle, and the loop repeats.

## 3. Long-Term Vision & Roadmap

This project aims to develop a sophisticated, extensible Artificial General Intelligence (AGI) named Sophia V2. The architecture is designed to evolve through distinct phases.

### Phase 1: MVP Implementation (Current)
-   **Goal:** Establish a stable core architecture and a basic set of functional plugins.
-   **Steps:**
    1.  Core Skeleton & Plugin Contract **(Done)**
    2.  Dynamic Plugin Manager **(Done)**
    3.  Kernel & Terminal Interface **(Done)**
    4.  Thought & Short-Term Memory **(Done)**
    5.  Web UI Interface **(Done)**
    6.  **[Next]** Basic File System Tool

### Phase 2: Tool Integration & Expansion
-   **Goal:** Expand Sophia's capabilities by adding more tools and improving her ability to use them.
-   **Key Areas:**
    -   Internet search capabilities.
    -   Code execution and file system interaction.
    -   Long-term memory and knowledge retrieval (e.g., using vector databases).
    -   More sophisticated planning and task decomposition.

### Phase 3: Self-Analysis and Improvement
-   **Goal:** Enable Sophia to analyze her own performance and suggest improvements.
-   **Key Areas:**
    -   Logging and metrics for all actions.
    -   A "meta-plugin" that can review logs and performance data.
    -   The ability to suggest or even write code modifications for herself.

### Phase 4: Autonomous Operations
-   **Goal:** Achieve a higher degree of autonomy, allowing Sophia to operate with less direct human supervision.
-   **Key Areas:**
    -   Proactive goal-seeking.
    -   Running as a continuous, long-running service.
    -   More complex, multi-step task execution.
