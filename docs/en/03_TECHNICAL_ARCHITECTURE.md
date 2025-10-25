# Document 3: Technical Architecture

This document outlines the technical design of the Sophia AGI system, focusing on the Core-Plugin model.

## 1. Core Philosophy: Stability and Extensibility

*   **The Core is Sacred:** The `core` of the application is minimal, stable, and protected. It provides the essential scaffolding and orchestration but contains no domain-specific logic.
*   **Everything is a Plugin:** All functionality, from cognitive processes to tool integrations, is implemented as a self-contained plugin. This makes the system modular, easy to test, and safe to extend.

## 2. Main Components

### 2.1. The `Core` (`core/`)

*   **Responsibility:** Orchestrates the main application loop, manages plugins, and handles the flow of data.
*   **Key Modules:**
    *   `main.py`: The application entry point.
    *   `plugin_manager.py`: Discovers, loads, validates, and executes plugins.
    *   `context.py`: Defines the `SharedContext` data structure.
    *   `logging.py`: Configures the central logging system.

### 2.2. `Plugins` (`plugins/`)

*   **Responsibility:** Encapsulates a specific piece of functionality.
*   **Structure:**
    *   Each plugin is a single Python file (e.g., `plugins/tool_file_system.py`).
    *   Every plugin **must** inherit from the `BasePlugin` class defined in `plugins/base_plugin.py`.
    *   Plugins are discovered and loaded at runtime by the `PluginManager`.

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
