# Roadmap 01: MVP Implementation - The Extensible Core

This document defines the precise, step-by-step procedure for implementing the Minimum Viable Product (MVP) of Sophia. The goal of this roadmap is to create a stable, testable, and extensible Core and equip it with the basic plugins required for meaningful interaction.

Upon completion of this roadmap, Sophia will be able to:
*   Be managed by a stable, "locked" Core.
*   Automatically load new capabilities (plugins).
*   Communicate via a terminal and a basic web interface.
*   Maintain short-term (session) and long-term (semantic) memory.

---

### Step 1: Create the Core Skeleton and Plugin Contract

*   **Goal:** Define the immutable structure and interfaces upon which the entire system will be built.
*   **Key Components to Create:**
    *   `core/kernel.py`: An empty `Kernel` class.
    *   `core/plugin_manager.py`: An empty `PluginManager` class.
    *   `core/context.py`: The `SharedContext` dataclass with defined fields.
    *   `plugins/base_plugin.py`: The `BasePlugin` abstract class defining the contract (name, type, `setup`, `execute`).
*   **Verifiable Outcome:** The `core/` and `plugins/` directory structures exist. The files contain the skeletons of classes and interfaces. The code is not yet functional but defines the architecture.

### Step 2: Implement the Dynamic `PluginManager`

*   **Goal:** Bring the `PluginManager` to life so it can automatically find, validate, and load plugins.
*   **Key Components to Implement:**
    *   `core/plugin_manager.py`: Logic that scans the `plugins/` directory at startup, imports modules, and registers all classes that inherit from `BasePlugin`.
*   **Verifiable Outcome:** The `PluginManager` is testable. After creating a test file `plugins/dummy_plugin.py`, the `PluginManager` can find and correctly register it.

### Step 3: Implement the Core and the First "Interface" Plugin (Terminal)

*   **Goal:** Get the lifecycle in the Core running and enable the first, simplest form of interaction.
*   **Key Components to Implement:**
    *   `core/kernel.py`: Implementation of the `ConsciousnessLoop`, which manages states and calls plugins.
    *   `plugins/interface_terminal.py`: The first real plugin of type `INTERFACE`. Its `execute` method waits for `input()` from the terminal and writes the result to `context.user_input`.
*   **Verifiable Outcome:** When `run.py` is executed, the Core starts, loads the terminal plugin, and waits for user input. After text is entered, the loop completes and waits again. The system is "alive".

### Step 4: Add Thinking and Short-Term Memory

*   **Goal:** Enable Sophia to hold a coherent dialogue and remember it within a single session.
*   **Key Components to Create:**
    *   `plugins/tool_llm.py`: A `TOOL` type plugin that takes data from the context (`user_input`, `history`), calls an external LLM API, and writes the response back to the context.
    *   `plugins/memory_sqlite.py`: A `MEMORY` type plugin. At the end of a cycle, it saves the current interaction (input and response) to an SQLite database under the `session_id`. It loads the relevant history at the start of a session.
*   **Verifiable Outcome:** A fully functional conversational bot in the terminal that maintains context and saves the conversation history to a database.

### Step 5: Proof of Extensibility - The Second "Interface" Plugin (Web UI)

*   **Goal:** Demonstrate the power of the architecture by adding a new interface **without any changes to the `core/`**.
*   **Key Components to Create:**
    *   `plugins/interface_webui.py`: An `INTERFACE` type plugin that, during `setup`, starts a simple FastAPI server in the background with a WebSocket for real-time communication.
*   **Verifiable Outcome:** Sophia is accessible and can conduct dialogues simultaneously via both the terminal and a web interface. This confirms that the Core is truly modular.

### Step 6: Add Long-Term Memory and Complete the MVP

*   **Goal:** Give Sophia the ability to learn from past conversations and build a semantic knowledge base.
*   **Key Components to Create:**
    *   `plugins/memory_chroma.py`: A `MEMORY` type plugin. It will contain logic to analyze the conversation at the end of a session. If it identifies a key insight, it will create an embedding for it and save it to a ChromaDB vector database.
*   **Verifiable Outcome:** The MVP is complete. Sophia has a stable core, multiple communication channels, and functional short-term and long-term memory, making her ready for further development and learning.
