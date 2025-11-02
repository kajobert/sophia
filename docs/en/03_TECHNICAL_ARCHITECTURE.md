# Document 3: Technical Architecture

This document outlines the technical design of the Sophia AGI system, focusing on the Core-Plugin model.

## 1. Core Philosophy: Stability and Extensibility

*   **The Core is Sacred:** The `core` of the application is minimal, stable, and protected. It provides the essential scaffolding and orchestration but contains no domain-specific logic.
*   **Everything is a Plugin:** All functionality, from cognitive processes to tool integrations, is implemented as a self-contained plugin. This makes the system modular, easy to test, and safe to extend.

## 2. Main Components

### 2.1. The `Core` (`core/`)

*   **Responsibility:** Orchestrates the main application loop, manages plugins, and handles the flow of data.
*   **The Consciousness Loop:** The `kernel.py` module contains the core logic cycle, which proceeds in a defined order:
    1.  **Listening Phase:** An `INTERFACE` plugin waits for and receives user input.
    2.  **Routing Phase (New):** The `CognitiveTaskRouter` plugin analyzes the input to select the most appropriate LLM model for the task.
    3.  **Planning Phase:** A `COGNITIVE` plugin (like the `CognitivePlanner`) receives the user input and creates a step-by-step plan for a `TOOL` plugin to execute.
    4.  **Executing Phase:** The Kernel executes the plan, calling the necessary tools and chaining their results.
    5.  **Responding Phase:** An `INTERFACE` plugin delivers the final result back to the user.
    6.  **Memorizing Phase:** A `MEMORY` plugin saves the interaction to long-term storage.
*   **Key Modules:**
    *   `run.py`: The application entry point.
    *   `kernel.py`: Implements the `Consciousness Loop` and orchestrates the phases.
    *   `plugin_manager.py`: Discovers, loads, and validates plugins.
    *   `context.py`: Defines the `SharedContext` data structure.
    *   `logging_config.py`: Configures the central logging system.

#### 2.1.1. Advanced Kernel Features

The `Kernel` includes several advanced features to enable complex, multi-step operations:

*   **Validation & Repair Loop:** Before executing a tool, the Kernel validates the arguments provided by the AI against a Pydantic schema. If validation fails, it automatically triggers a "repair loop," using a specialized LLM prompt to correct the faulty arguments.
*   **Context Injection:** The Kernel intelligently inspects the signature of a tool's method. If it detects a `context` parameter, it automatically injects the current `SharedContext` object, giving the tool access to the logger, session ID, and conversation history.
*   **History Propagation:** For each step in a multi-step plan, the Kernel creates a new, history-aware `SharedContext`. This context includes the original user request plus the results of all previous steps, ensuring the AI has a complete understanding of the task's progress.

### 2.2. `Plugins` (`plugins/`)

*   **Responsibility:** Encapsulates a specific piece of functionality.
*   **Structure:**
    *   Each plugin is a single Python file (e.g., `plugins/tool_file_system.py`).
    *   Every plugin **must** inherit from the `BasePlugin` class defined in `plugins/base_plugin.py`.
    *   Plugins are discovered and loaded at runtime by the `PluginManager`.

#### 2.2.1. Available Tool Plugins

*   **`FileSystemTool`:** Provides a secure, sandboxed environment for the agent to read, write, and list files. All file operations are restricted to a designated `sandbox/` directory to prevent unintended access to the system.
*   **`BashTool`:** Allows the agent to execute shell commands within a secure, isolated environment. This is useful for running scripts, managing processes, or interacting with the operating system in a controlled manner.
*   **`GitTool`:** Enables the agent to interact with its own source code repository. It can check the status, view diffs of changes, and get the current branch name, providing a basic level of self-awareness of its own code.
*   **`WebSearchTool`:** Gives the agent the ability to perform Google searches to access real-time information from the internet. This is a crucial tool for research and staying up-to-date.
*   **`JulesAPITool`:** Integrates with Google's Jules API to enable AI-powered coding assistance. Features include:
    *   Creating and managing coding sessions
    *   Listing available GitHub repositories
    *   Monitoring session progress and activities
    *   Sending follow-up instructions to active sessions
    *   Full Pydantic v2 data validation for type safety
    *   Secure API key management via environment variables

#### 2.2.2. Cognitive Plugins

Cognitive plugins are responsible for the "thinking" processes of the agent. They interpret user input, create plans, and make decisions.

*   **`CognitivePlanner`:** This is the default cognitive plugin. It analyzes the user's request and the available tools to generate a step-by-step plan that the Kernel can execute.
*   **`CognitiveTaskRouter` (Strategic Model Orchestrator):** This plugin acts as a strategic layer *before* the planner. It analyzes the user's input and classifies the task's complexity (e.g., "simple question," "complex analysis," "code generation"). Based on this classification, it dynamically selects the most appropriate and cost-effective LLM model for the job. This allows the system to use smaller, faster models for simple tasks and reserve the more powerful, expensive models for complex reasoning, optimizing both performance and operational cost.

### 2.3. `SharedContext` (`core/context.py`)

*   **Responsibility:** The data bus and "lifeblood" of the system.
1.  It is a `dataclass`, an instance of which is passed to every plugin in every cycle.
2.  It contains the entire state for the current cycle, including `session_id`, `current_state`, `user_input`, `history`, a flexible `payload` for inter-plugin data sharing, and a **session-specific logger**.
*   **Structure (`dataclass`):**
    *   `session_id: str`: A unique ID for the current session.
    *   `current_state: str`: The current state of the main loop (`LISTENING`, `THINKING`, etc.).
    *   `user_input: str | None`: The latest input from the user.
    *   `history: list`: A short-term history of the current conversation.
    *   `payload: dict`: A "cargo space" for data passed between plugins.
    *   `logger: logging.Logger`: A configured logger that automatically injects the `session_id` into all records, ensuring clear, contextual logging across all plugins.
