# Inspiration for the MVP Roadmap

This document maps the findings from the archival analysis directly to the steps outlined in the `01_MVP_IMPLEMENTATION.md` roadmap. It serves as a practical guide, providing concrete inspiration and reusable patterns for each stage of development.

---

### Step 1: Create the Core Skeleton and Plugin Contract

*   **Archival Insight (`sophia-archived`):** The `memory_systems.py` file demonstrated the power of a clean, simple API that hides a more complex backend.
*   **Inspiration:** The `BasePlugin` abstract class is the perfect place to enforce this pattern. The contract should be as simple as possible (e.g., `setup`, `execute`), allowing the internal complexity of each plugin to remain completely encapsulated.

---

### Step 2: Implement the Dynamic `PluginManager`

*   **Archival Insight (`nomad-archived`):** The `MCPClient` was a primitive plugin manager that executed tools as separate processes. This highlights a need for a central component to manage and invoke capabilities.
*   **Inspiration:** While our `PluginManager` will load modules directly, the `MCPClient`'s role as a single point of entry for tool execution is a good model. The `PluginManager` should be the *only* component that knows how to discover, validate, and execute plugins. The `Kernel` should be completely ignorant of these details, simply asking the `PluginManager` to run a plugin by name.

---

### Step 3: Implement the Core and the First "Interface" Plugin (Terminal)

*   **Archival Insight (`nomad-archived`):** The `NomadOrchestratorV2`'s proactive state machine (`THINKING` -> `EXECUTE`) is a production-grade model for an agent's core loop.
*   **Inspiration:** We should implement the `ConsciousnessLoop` in `core/kernel.py` based on this exact pattern. It's a simple, robust, and proven design. The `plugins/interface_terminal.py` will be responsible for the `input()` and `print()` calls, feeding the user input into the `SharedContext` for the `Kernel`'s loop to process.

---

### Step 4: Add Thinking and Short-Term Memory

*   **Archival Insight (`nomad-archived`):** The `_build_prompt` and `_parse_llm_response` methods provide battle-tested code for LLM interaction.
*   **Inspiration for `plugins/tool_llm.py`:** This plugin should be built using these concepts. It will read the goal and history from the `SharedContext`, build a structured prompt using the `build_system_prompt` pattern, execute the call, and parse the JSON response using the regex-based `parse_llm_json_response` pattern.

*   **Archival Insight (`sophia-archived`):** The `ShortTermMemory` class provides a clean, session-based, key-value store API.
*   **Inspiration for `plugins/memory_sqlite.py`:** This plugin should implement the simple API from the `ShortTermMemory` class (`get`, `set`, `update`, `clear`), but with an SQLite backend instead of an in-memory dictionary. The `session_id` will map directly to a table name or a primary key within a table.

---

### Step 5: Proof of Extensibility - The Second "Interface" Plugin (Web UI)

*   **Archival Insight (`nomad-archived`):** The `README.md` for this project described a full FastAPI backend with WebSocket streaming for a Textual TUI.
*   **Inspiration for `plugins/interface_webui.py`:** We have a clear precedent that this is possible and effective. This plugin should encapsulate a lightweight FastAPI server. The `setup` method will start the server in a background thread, and the `execute` method will handle passing messages between the WebSocket and the `SharedContext`. The existence of this in a prior version gives us high confidence in this extensibility goal.

---

### Step 6: Add Long-Term Memory and Complete the MVP

*   **Archival Insight (`sophia-old-archived`):** The earliest prototype used `ChromaDB` for long-term memory and had a "dreaming" process for memory consolidation.
*   **Inspiration for `plugins/memory_chroma.py`:**
    *   The plugin's API should mirror the simple `add_record` and `search` methods from the `LongTermMemory` placeholder class.
    *   While the full "dreaming" process is out of scope for the MVP, we should design the plugin with this future capability in mind. This means the `add_record` function should store not just the text, but also rich metadata (e.g., `session_id`, `timestamp`, `type_of_memory`) that would be needed for a future consolidation process.
