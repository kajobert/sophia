[📚 Documentation Index](INDEX.md) | [⬅️ 07 Developer Guide](07_DEVELOPER_GUIDE.md) | **08**

---

# Sophia V2 - Project Overview

**Executive Summary** | Quick Reference | For Project Owners & New Contributors

This document provides a high-level overview of the Sophia V2 project, its architecture, current status, and roadmap. It is intended as a quick reference for project owners and newcomers.

> 📌 **Current Status:** Sophia 2.0 - MVP Phases 1-3 complete (100%), Phase 4 partial (60%), implementing autonomous operations roadmap.  
> 🎯 **Next Milestone:** Continuous event-driven loop, process management, memory consolidation  
> 📅 **Last Updated:** November 3, 2025

## 1. Quick Start Command Reference

Here is a "cheat sheet" of the most common commands for managing the project:

-   **User Setup (first time):**
    ```bash
    uv venv && source .venv/bin/activate && uv pip sync requirements.in
    ```

-   **Developer Setup (first time):**
    ```bash
    uv venv && source .venv/bin/activate && uv pip install -r requirements.in -r requirements-dev.in
    ```

-   **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

-   **Install/update dependencies (User):**
    ```bash
    uv pip sync requirements.in
    ```

-   **Install/update dependencies (Developer):**
    ```bash
    uv pip install -r requirements.in -r requirements-dev.in
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

### ✅ Phase 1: MVP Implementation (COMPLETE)
-   **Goal:** Establish a stable core architecture and a basic set of functional plugins.
-   **Completion:** 100% - All foundational systems operational
-   **Achievements:**
    1.  ✅ Core Skeleton & Plugin Contract
    2.  ✅ Dynamic Plugin Manager
    3.  ✅ Kernel & Terminal Interface
    4.  ✅ Consciousness Loop (5 phases)
    5.  ✅ Web UI Interface
    6.  ✅ File System & Bash Tools

**Status:** Production-ready foundation established.

---

### ✅ Phase 2: Tool Integration & Expansion (COMPLETE)
-   **Goal:** Expand Sophia's capabilities by adding more tools and improving her ability to use them.
-   **Completion:** 100% - 27 plugins operational
-   **Achievements:**
    -   ✅ Internet search (Tavily, Web Search)
    -   ✅ Code execution and file system interaction
    -   ✅ Long-term memory (SQLite + ChromaDB vector database)
    -   ✅ Git & GitHub integration
    -   ✅ Jules API/CLI integration
    -   ✅ Langfuse observability
    -   ✅ Model evaluation & performance monitoring

**Current Plugin Count:** 27 (2 interfaces, 15 tools, 7 cognitive, 2 memory, 1 core)

---

### ✅ Phase 3: Self-Analysis and Improvement (COMPLETE)
-   **Goal:** Enable Sophia to analyze her own performance and suggest improvements.
-   **Completion:** 100% - Self-analysis framework operational
-   **Achievements:**
    -   ✅ Logging and metrics for all actions (Langfuse integration)
    -   ✅ Model evaluator plugin for LLM performance analysis
    -   ✅ Performance monitoring plugin
    -   ✅ Cognitive historian for reviewing past decisions
    -   ✅ Benchmark framework for continuous testing

**Status:** Sophia can measure, analyze, and report on her own performance.

---

### 🟡 Phase 4: Autonomous Operations (60% COMPLETE)
-   **Goal:** Achieve a higher degree of autonomy, allowing Sophia to operate with less direct human supervision.
-   **Completion:** 60% - Jules integration complete, continuous loop pending
-   **Current State:**
    -   ✅ Jules integration (API + CLI) for async task execution
    -   ✅ Jules monitoring system
    -   ✅ Cognitive planner for task routing
    -   🚧 Continuous event-driven loop (blocking → non-blocking refactor needed)
    -   🚧 Process management for background tasks
    -   🚧 Memory consolidation ("dreaming")
    -   🚧 State persistence for crash recovery

**Next Steps:** See [Autonomous MVP Roadmap](AUTONOMOUS_MVP_ROADMAP.md) for detailed implementation plan.

---

### 🚀 Sophia 2.0: Full Autonomy (IN PROGRESS)

**Vision:** Sophia operates continuously with human-like life rhythm:
- 🏃 **Work:** Autonomous task execution, self-improvement, idea implementation
- 😴 **Rest:** Sleep cycles with memory consolidation
- 💭 **Dream:** Pattern recognition, insight generation from memory
- 🌱 **Grow:** Self-initiated improvements based on performance analysis

**Target Architecture:**
1. **Event-Driven Core** - Non-blocking consciousness loop
2. **Task Queue** - Prioritized async task management
3. **Process Manager** - Long-running background operations (Jules monitoring, roberts-notes.txt watcher)
4. **Memory Consolidation** - Automatic compression, archiving, pattern extraction
5. **Self-Improvement Engine** - Automated implementation of ideas (with HITL approval for Core changes)
6. **State Persistence** - Crash recovery, graceful shutdown/restart

**Timeline:** 20-25 days (see [Implementation Action Plan](IMPLEMENTATION_ACTION_PLAN.md))

**Key Resources:**
- 📋 [Autonomous MVP Roadmap](AUTONOMOUS_MVP_ROADMAP.md) - 6-phase detailed plan
- ⚙️ [Autonomy Configuration](../../config/autonomy.yaml) - Operational boundaries
- ✅ [Critical Questions Answered](CRITICAL_QUESTIONS_ANSWERED.md) - Strategic decisions
- 📊 [Implementation Action Plan](IMPLEMENTATION_ACTION_PLAN.md) - Week-by-week schedule

---

## Related Documentation

- 🎯 **[Vision & DNA](01_VISION_AND_DNA.md)** - Core philosophy and principles
- 🧠 **[Cognitive Architecture](02_COGNITIVE_ARCHITECTURE.md)** - How Sophia thinks
- ⚙️ **[Technical Architecture](03_TECHNICAL_ARCHITECTURE.md)** - Implementation details
- 👤 **[User Guide](06_USER_GUIDE.md)** - How to interact with Sophia
- 🧑‍💻 **[Developer Guide](07_DEVELOPER_GUIDE.md)** - How to extend Sophia
- 📋 **[Roadmaps](roadmap/)** - Detailed phase-by-phase plans

---

**Navigation:** [📚 Index](INDEX.md) | [🏠 Home](../../README.md) | [⬅️ Previous: Developer Guide](07_DEVELOPER_GUIDE.md)

---

*Last Updated: November 3, 2025 | Status: ✅ Current | Sophia 2.0 Roadmap Active*
